import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import extract_client_ip, get_current_user, require_role
from app.db.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentSubmission,
    AuditLog,
    Concept,
    Course,
    QuestionResponse,
    User,
)
from app.db.session import get_db
from app.schemas.domain import AssessmentSubmitRequest, CreateAssessmentRequest
from app.services.assessment_engine import compute_assessment_psychometrics, grade_assessment_submission

router = APIRouter(prefix="/assessments", tags=["Assessments & Evaluation"])


@router.get("")
def list_assessments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assessments = (
        db.query(Assessment)
        .options(
            joinedload(Assessment.course),
            selectinload(Assessment.questions),
            selectinload(Assessment.submissions),
        )
        .order_by(Assessment.id)
        .all()
    )

    items: List[Dict[str, Any]] = []
    for a in assessments:
        student_subs = []
        if current_user.student_profile:
            student_subs = [s for s in a.submissions if s.student_id == current_user.student_profile.id]
            student_subs.sort(key=lambda s: s.submitted_at, reverse=True)

        latest = student_subs[0] if student_subs else None
        all_scores = [s.score_pct for s in a.submissions]
        items.append(
            {
                "id": a.id,
                "course_id": a.course_id,
                "course_code": a.course.code if a.course else "",
                "course_title": a.course.title if a.course else "",
                "title": a.title,
                "assessment_type": a.assessment_type,
                "description": a.description,
                "duration_minutes": a.duration_minutes,
                "passing_score": a.passing_score,
                "total_points": a.total_points,
                "questions_count": len(a.questions),
                "is_published": a.is_published,
                "cohort_submissions_count": len(a.submissions),
                "cohort_mean_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0,
                "latest_submission": {
                    "submission_id": latest.id,
                    "score_pct": round(latest.score_pct, 1),
                    "passed": latest.passed,
                    "submitted_at": latest.submitted_at.isoformat(),
                }
                if latest
                else None,
            }
        )
    return {"assessments": items}


@router.get("/concepts/catalog")
def list_concepts_for_builder(
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    concepts = db.query(Concept).options(joinedload(Concept.course)).order_by(Concept.course_id, Concept.id).all()
    return {
        "concepts": [
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "course_id": c.course_id,
                "course_code": c.course.code if c.course else "",
            }
            for c in concepts
        ]
    }


@router.get("/submissions/{submission_id}")
def get_submission_detail(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(AssessmentSubmission)
        .options(
            joinedload(AssessmentSubmission.assessment),
            selectinload(AssessmentSubmission.responses)
            .joinedload(QuestionResponse.question)
            .joinedload(AssessmentQuestion.concept),
        )
        .filter(AssessmentSubmission.id == submission_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")

    is_owner = current_user.student_profile and current_user.student_profile.id == sub.student_id
    if current_user.role != "admin" and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    items = []
    for resp in sorted(sub.responses, key=lambda r: r.question_id):
        q = resp.question
        items.append(
            {
                "question_id": q.id,
                "prompt": q.prompt,
                "concept_name": q.concept.name if q.concept else "",
                "options": json.loads(q.options_json),
                "selected_index": resp.selected_index,
                "correct_index": q.correct_index,
                "is_correct": resp.is_correct,
                "explanation": q.explanation,
                "points_earned": q.points if resp.is_correct else 0.0,
                "points_possible": q.points,
            }
        )

    return {
        "submission_id": sub.id,
        "assessment_id": sub.assessment_id,
        "assessment_title": sub.assessment.title if sub.assessment else "",
        "score_pct": round(sub.score_pct, 1),
        "points_earned": sub.points_earned,
        "points_possible": sub.points_possible,
        "passed": sub.passed,
        "passing_score": sub.assessment.passing_score if sub.assessment else 70.0,
        "time_spent_seconds": sub.time_spent_seconds,
        "submitted_at": sub.submitted_at.isoformat(),
        "items": items,
    }


@router.get("/{assessment_id}")
def get_assessment_detail(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = (
        db.query(Assessment)
        .options(
            joinedload(Assessment.course),
            selectinload(Assessment.questions).joinedload(AssessmentQuestion.concept),
        )
        .filter(Assessment.id == assessment_id)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    is_admin = current_user.role == "admin"
    questions_out = []
    for q in sorted(assessment.questions, key=lambda x: x.id):
        item = {
            "id": q.id,
            "concept_id": q.concept_id,
            "concept_name": q.concept.name if q.concept else "",
            "prompt": q.prompt,
            "options": json.loads(q.options_json),
            "difficulty": q.difficulty,
            "points": q.points,
        }
        if is_admin:
            item["correct_index"] = q.correct_index
            item["explanation"] = q.explanation
        questions_out.append(item)

    return {
        "id": assessment.id,
        "course_id": assessment.course_id,
        "course_code": assessment.course.code if assessment.course else "",
        "course_title": assessment.course.title if assessment.course else "",
        "title": assessment.title,
        "assessment_type": assessment.assessment_type,
        "description": assessment.description,
        "duration_minutes": assessment.duration_minutes,
        "passing_score": assessment.passing_score,
        "total_points": assessment.total_points,
        "questions": questions_out,
    }


@router.post("/{assessment_id}/submit")
def submit_assessment(
    assessment_id: int,
    payload: AssessmentSubmitRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only student accounts can submit assessments.",
        )

    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    result = grade_assessment_submission(
        db=db,
        student=current_user.student_profile,
        assessment=assessment,
        answers=payload.answers,
        time_spent_seconds=payload.time_spent_seconds,
    )

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="ASSESSMENT_SUBMITTED",
            resource_type="assessment",
            resource_id=str(assessment_id),
            details=f"Score={result['score_pct']}% | Passed={result['passed']}",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: CreateAssessmentRequest,
    request: Request,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target course not found.")

    total_pts = sum(q.points for q in payload.questions)
    assessment = Assessment(
        course_id=payload.course_id,
        title=payload.title.strip(),
        assessment_type=payload.assessment_type.strip(),
        description=payload.description.strip(),
        duration_minutes=payload.duration_minutes,
        passing_score=payload.passing_score,
        total_points=total_pts,
        is_published=True,
        created_by_id=admin_user.id,
    )
    db.add(assessment)
    db.flush()

    for q_in in payload.questions:
        concept = db.query(Concept).filter(Concept.id == q_in.concept_id).first()
        if not concept:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid concept ID {q_in.concept_id}.")
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id,
                concept_id=q_in.concept_id,
                prompt=q_in.prompt.strip(),
                options_json=json.dumps([opt.strip() for opt in q_in.options]),
                correct_index=q_in.correct_index,
                explanation=q_in.explanation.strip(),
                difficulty=q_in.difficulty,
                points=q_in.points,
            )
        )

    db.add(
        AuditLog(
            user_id=admin_user.id,
            action="ASSESSMENT_CREATED",
            resource_type="assessment",
            resource_id=str(assessment.id),
            details=f"Created '{assessment.title}' with {len(payload.questions)} questions.",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    return {
        "id": assessment.id,
        "title": assessment.title,
        "course_code": course.code,
        "questions_count": len(payload.questions),
    }


@router.get("/{assessment_id}/psychometrics")
def get_assessment_psychometrics(
    assessment_id: int,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    try:
        return compute_assessment_psychometrics(db, assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
