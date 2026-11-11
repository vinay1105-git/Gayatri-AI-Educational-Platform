from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import get_current_user
from app.db.models import (
    Concept,
    ConceptMastery,
    Course,
    Enrollment,
    LearningResource,
    ResourceInteraction,
    User,
)
from app.db.session import get_db
from app.ml.knowledge_tracing import update_mastery_from_resource_completion
from app.ml.model_registry import refresh_student_predictions
from app.ml.recommender import generate_personalized_recommendations
from app.schemas.domain import ResourceInteractionRequest

router = APIRouter(prefix="/courses", tags=["Courses & Recommendations"])


@router.get("")
def list_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = (
        db.query(Course)
        .options(selectinload(Course.concepts), selectinload(Course.resources), selectinload(Course.enrollments))
        .order_by(Course.code)
        .all()
    )

    student_enrollments: Dict[int, Enrollment] = {}
    if current_user.student_profile:
        enrolls = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == current_user.student_profile.id)
            .all()
        )
        student_enrollments = {e.course_id: e for e in enrolls}

    items: List[Dict[str, Any]] = []
    for c in courses:
        enroll = student_enrollments.get(c.id)
        cohort_avg_grade = (
            round(sum(e.current_grade for e in c.enrollments) / len(c.enrollments), 1)
            if c.enrollments
            else 0.0
        )
        items.append(
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "category": c.category,
                "difficulty": c.difficulty,
                "credit_hours": c.credit_hours,
                "instructor_name": c.instructor_name,
                "description": c.description,
                "modules_count": c.modules_count,
                "concepts_count": len(c.concepts),
                "resources_count": len(c.resources),
                "enrolled_count": len(c.enrollments),
                "cohort_avg_grade": cohort_avg_grade,
                "student_progress": round(enroll.progress_pct, 1) if enroll else None,
                "student_grade": round(enroll.current_grade, 1) if enroll else None,
                "student_status": enroll.status if enroll else None,
            }
        )
    return {"courses": items}


@router.get("/recommendations")
def get_recommendations(
    limit: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recommendations are personalized per student profile.",
        )
    recs = generate_personalized_recommendations(db, current_user.student_profile.id, limit=min(24, max(1, limit)))
    return {"recommendations": recs}


@router.get("/{course_id}")
def get_course_detail(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .options(
            selectinload(Course.concepts).joinedload(Concept.prerequisite),
            selectinload(Course.resources).joinedload(LearningResource.concept),
        )
        .filter(Course.id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    mastery_map: Dict[int, float] = {}
    interaction_map: Dict[int, str] = {}
    enrollment = None

    if current_user.student_profile:
        sid = current_user.student_profile.id
        masteries = db.query(ConceptMastery).filter(ConceptMastery.student_id == sid).all()
        mastery_map = {m.concept_id: round(m.mastery_score, 1) for m in masteries}

        interactions = db.query(ResourceInteraction).filter(ResourceInteraction.student_id == sid).all()
        interaction_map = {i.resource_id: i.status for i in interactions}

        enrollment = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == sid, Enrollment.course_id == course.id)
            .first()
        )

    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "category": course.category,
        "difficulty": course.difficulty,
        "credit_hours": course.credit_hours,
        "instructor_name": course.instructor_name,
        "description": course.description,
        "modules_count": course.modules_count,
        "enrollment": {
            "progress_pct": round(enrollment.progress_pct, 1),
            "modules_completed": enrollment.modules_completed,
            "current_grade": round(enrollment.current_grade, 1),
            "status": enrollment.status,
        }
        if enrollment
        else None,
        "concepts": [
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "description": c.description,
                "difficulty_weight": c.difficulty_weight,
                "prerequisite_name": c.prerequisite.name if c.prerequisite else None,
                "key_notes": c.key_notes,
                "mastery_score": mastery_map.get(c.id),
            }
            for c in sorted(course.concepts, key=lambda x: x.id)
        ],
        "resources": [
            {
                "id": r.id,
                "title": r.title,
                "resource_type": r.resource_type,
                "difficulty": r.difficulty,
                "estimated_minutes": r.estimated_minutes,
                "summary": r.summary,
                "content_body": r.content_body,
                "concept_id": r.concept_id,
                "concept_name": r.concept.name if r.concept else "",
                "tags": [t.strip() for t in r.tags.split(",") if t.strip()],
                "interaction_status": interaction_map.get(r.id, "unstarted"),
            }
            for r in sorted(course.resources, key=lambda x: x.id)
        ],
    }


@router.post("/resources/{resource_id}/interact")
def record_resource_interaction(
    resource_id: int,
    payload: ResourceInteractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student profile required.")

    resource = db.query(LearningResource).filter(LearningResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning resource not found.")

    sid = current_user.student_profile.id
    existing = (
        db.query(ResourceInteraction)
        .filter(ResourceInteraction.student_id == sid, ResourceInteraction.resource_id == resource_id)
        .first()
    )

    was_already_completed = existing is not None and existing.status == "completed"

    if existing:
        existing.status = payload.status
        if payload.rating is not None:
            existing.rating = payload.rating
        existing.updated_at = datetime.now(timezone.utc)
    else:
        db.add(
            ResourceInteraction(
                student_id=sid,
                resource_id=resource_id,
                status=payload.status,
                rating=payload.rating,
            )
        )

    updated_mastery = None
    if payload.status == "completed" and not was_already_completed:
        updated_mastery = update_mastery_from_resource_completion(
            db=db,
            student_id=sid,
            concept_id=resource.concept_id,
            resource_difficulty=resource.difficulty,
        )
        enrollment = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == sid, Enrollment.course_id == resource.course_id)
            .first()
        )
        if enrollment:
            enrollment.modules_completed = min(
                enrollment.course.modules_count if enrollment.course else enrollment.modules_completed + 1,
                enrollment.modules_completed + 1,
            )
            enrollment.progress_pct = round(min(100.0, enrollment.progress_pct + 7.5), 1)
            enrollment.last_accessed_at = datetime.now(timezone.utc)
            if enrollment.progress_pct >= 99.0:
                enrollment.status = "completed"

        current_user.student_profile.engagement_index = round(
            min(99.0, current_user.student_profile.engagement_index + 1.8), 1
        )

    db.commit()
    refreshed = refresh_student_predictions(db, sid)

    return {
        "resource_id": resource_id,
        "status": payload.status,
        "updated_concept_mastery": updated_mastery.mastery_score if updated_mastery else None,
        "updated_prediction": refreshed["prediction"],
    }
