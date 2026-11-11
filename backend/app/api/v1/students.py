from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import get_current_user
from app.db.models import (
    AssessmentSubmission,
    Concept,
    ConceptMastery,
    Enrollment,
    StudentProfile,
    User,
    WeeklyTelemetry,
)
from app.db.session import get_db
from app.ml.knowledge_tracing import forecast_score_trajectory
from app.ml.model_registry import get_student_diagnostics, refresh_student_predictions
from app.ml.recommender import generate_personalized_recommendations
from app.schemas.domain import TelemetryCheckinRequest

router = APIRouter(prefix="/students", tags=["Students"])


def _build_student_dashboard_payload(db: Session, student_id: int) -> Dict[str, Any]:
    student = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.user),
            selectinload(StudentProfile.enrollments).joinedload(Enrollment.course),
            selectinload(StudentProfile.concept_masteries)
            .joinedload(ConceptMastery.concept)
            .joinedload(Concept.course),
            selectinload(StudentProfile.submissions).joinedload(AssessmentSubmission.assessment),
            selectinload(StudentProfile.weekly_telemetry),
            selectinload(StudentProfile.interventions),
        )
        .filter(StudentProfile.id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

    diagnostics = get_student_diagnostics(db, student.id)
    trajectory = forecast_score_trajectory(student.weekly_telemetry, horizon_weeks=4)
    recommendations = generate_personalized_recommendations(db, student.id, limit=6)

    enrollments_data = [
        {
            "course_id": e.course.id,
            "course_code": e.course.code,
            "course_title": e.course.title,
            "category": e.course.category,
            "difficulty": e.course.difficulty,
            "instructor_name": e.course.instructor_name,
            "progress_pct": round(e.progress_pct, 1),
            "modules_completed": e.modules_completed,
            "modules_total": e.course.modules_count,
            "current_grade": round(e.current_grade, 1),
            "status": e.status,
        }
        for e in sorted(student.enrollments, key=lambda item: item.course.code)
    ]

    masteries_data = [
        {
            "concept_id": m.concept_id,
            "concept_code": m.concept.code if m.concept else "",
            "concept_name": m.concept.name if m.concept else "",
            "course_code": m.concept.course.code if m.concept and m.concept.course else "",
            "mastery_score": round(m.mastery_score, 1),
            "confidence": round(m.confidence, 2),
            "attempts_count": m.attempts_count,
        }
        for m in sorted(student.concept_masteries, key=lambda item: item.mastery_score)
    ]

    recent_submissions = [
        {
            "submission_id": s.id,
            "assessment_id": s.assessment_id,
            "assessment_title": s.assessment.title if s.assessment else "Assessment",
            "score_pct": round(s.score_pct, 1),
            "passed": s.passed,
            "time_spent_seconds": s.time_spent_seconds,
            "submitted_at": s.submitted_at.isoformat(),
        }
        for s in sorted(student.submissions, key=lambda item: item.submitted_at, reverse=True)[:8]
    ]

    avg_mastery = round(
        sum(m["mastery_score"] for m in masteries_data) / len(masteries_data), 1
    ) if masteries_data else 0.0

    return {
        "profile": {
            "id": student.id,
            "user_id": student.user_id,
            "full_name": student.user.full_name,
            "email": student.user.email,
            "avatar_initials": student.user.avatar_initials,
            "student_code": student.student_code,
            "cohort": student.cohort,
            "program_track": student.program_track,
            "semester": student.semester,
            "study_goal_hours_weekly": student.study_goal_hours_weekly,
            "attendance_rate": round(student.attendance_rate, 1),
            "engagement_index": round(student.engagement_index, 1),
            "assignment_timeliness": round(student.assignment_timeliness, 1),
            "current_gpa": round(student.current_gpa, 2),
            "avg_concept_mastery": avg_mastery,
        },
        "ml_intelligence": {
            "predicted_final_score": diagnostics["prediction"]["predicted_final_score"],
            "risk_score": diagnostics["prediction"]["risk_score"],
            "risk_level": diagnostics["prediction"]["risk_level"],
            "drivers": diagnostics["prediction"]["drivers"],
            "cluster": diagnostics["cluster"],
            "features": diagnostics["features"],
        },
        "trajectory": trajectory,
        "enrollments": enrollments_data,
        "concept_masteries": masteries_data,
        "recent_submissions": recent_submissions,
        "recommendations": recommendations,
        "interventions": [
            {
                "id": iv.id,
                "intervention_type": iv.intervention_type,
                "priority": iv.priority,
                "notes": iv.notes,
                "status": iv.status,
                "created_at": iv.created_at.isoformat(),
            }
            for iv in sorted(student.interventions, key=lambda x: x.created_at, reverse=True)
        ],
    }


@router.get("/me/dashboard")
def get_my_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrator accounts do not have a personal student telemetry profile.",
        )
    return _build_student_dashboard_payload(db, current_user.student_profile.id)


@router.get("/{student_id}/dashboard")
def get_student_dashboard(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_self = current_user.student_profile and current_user.student_profile.id == student_id
    if current_user.role != "admin" and not is_self:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    return _build_student_dashboard_payload(db, student_id)


@router.post("/me/telemetry")
def log_study_checkin(
    payload: TelemetryCheckinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.student_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student profile required.")

    student = current_user.student_profile
    latest_week = (
        db.query(WeeklyTelemetry)
        .filter(WeeklyTelemetry.student_id == student.id)
        .order_by(WeeklyTelemetry.week_number.desc())
        .first()
    )

    if latest_week:
        latest_week.study_hours = round(latest_week.study_hours + payload.study_hours, 2)
        latest_week.sessions_count += payload.sessions_count
        latest_week.assignments_completed += payload.assignments_completed
        latest_week.recorded_at = datetime.now(timezone.utc)
    else:
        db.add(
            WeeklyTelemetry(
                student_id=student.id,
                week_number=1,
                week_label="W01",
                study_hours=payload.study_hours,
                sessions_count=payload.sessions_count,
                avg_quiz_score=74.0,
                assignments_completed=payload.assignments_completed,
                attendance_pct=student.attendance_rate,
            )
        )

    # Update engagement smoothly
    student.engagement_index = round(min(99.0, student.engagement_index + min(4.0, payload.study_hours * 0.4)), 1)
    db.commit()

    refreshed = refresh_student_predictions(db, student.id)
    return {
        "message": "Study telemetry logged and predictive scores refreshed.",
        "engagement_index": student.engagement_index,
        "updated_prediction": refreshed["prediction"],
    }
