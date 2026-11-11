from collections import defaultdict
from typing import Any, Dict, List
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import get_current_user, require_role
from app.db.models import (
    AssessmentSubmission,
    Concept,
    ConceptMastery,
    Course,
    Intervention,
    StudentProfile,
    User,
    WeeklyTelemetry,
)
from app.db.session import get_db
from app.ml.knowledge_tracing import forecast_score_trajectory
from app.ml.model_registry import get_loaded_models

router = APIRouter(prefix="/analytics", tags=["Learning Analytics"])


@router.get("/cohort")
def get_cohort_analytics(
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    students = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .order_by(StudentProfile.risk_score.desc())
        .all()
    )
    total = len(students)
    high_risk = sum(1 for s in students if s.risk_level == "high")
    moderate_risk = sum(1 for s in students if s.risk_level == "moderate")
    low_risk = sum(1 for s in students if s.risk_level == "low")

    avg_pred_score = round(float(np.mean([s.predicted_final_score for s in students])), 1) if students else 0.0
    avg_attendance = round(float(np.mean([s.attendance_rate for s in students])), 1) if students else 0.0
    avg_engagement = round(float(np.mean([s.engagement_index for s in students])), 1) if students else 0.0
    avg_gpa = round(float(np.mean([s.current_gpa for s in students])), 2) if students else 0.0

    open_interventions = db.query(Intervention).filter(Intervention.status != "resolved").count()
    total_submissions = db.query(AssessmentSubmission).count()

    # Cohort breakdown
    cohort_buckets: Dict[str, List[StudentProfile]] = defaultdict(list)
    for s in students:
        cohort_buckets[s.cohort].append(s)

    cohort_comparison = []
    for cohort_name, members in sorted(cohort_buckets.items()):
        cohort_comparison.append(
            {
                "cohort": cohort_name,
                "short_name": cohort_name.split(" - ")[0],
                "student_count": len(members),
                "avg_predicted_score": round(float(np.mean([m.predicted_final_score for m in members])), 1),
                "avg_attendance": round(float(np.mean([m.attendance_rate for m in members])), 1),
                "avg_engagement": round(float(np.mean([m.engagement_index for m in members])), 1),
                "high_risk_count": sum(1 for m in members if m.risk_level == "high"),
            }
        )

    # Weekly Institutional Trend
    telemetry_rows = db.query(WeeklyTelemetry).all()
    week_groups: Dict[int, List[WeeklyTelemetry]] = defaultdict(list)
    for t in telemetry_rows:
        week_groups[t.week_number].append(t)

    weekly_trends = []
    for w_num in sorted(week_groups.keys()):
        items = week_groups[w_num]
        weekly_trends.append(
            {
                "week_label": f"W{w_num:02d}",
                "avg_quiz_score": round(float(np.mean([x.avg_quiz_score for x in items])), 1),
                "avg_study_hours": round(float(np.mean([x.study_hours for x in items])), 2),
                "avg_attendance": round(float(np.mean([x.attendance_pct for x in items])), 1),
            }
        )

    # Concept Mastery Heatmap / Ranking
    concepts = db.query(Concept).options(joinedload(Concept.course)).all()
    concept_mastery_rows = db.query(ConceptMastery).all()
    mastery_by_cid: Dict[int, List[float]] = defaultdict(list)
    for cm in concept_mastery_rows:
        mastery_by_cid[cm.concept_id].append(cm.mastery_score)

    concept_analytics = []
    for c in concepts:
        vals = mastery_by_cid.get(c.id, [])
        if vals:
            concept_analytics.append(
                {
                    "concept_id": c.id,
                    "code": c.code,
                    "name": c.name,
                    "course_code": c.course.code if c.course else "",
                    "mean_mastery": round(float(np.mean(vals)), 1),
                    "below_threshold_pct": round(float(np.mean([1.0 if v < 65.0 else 0.0 for v in vals]) * 100.0), 1),
                    "difficulty_weight": c.difficulty_weight,
                }
            )
    concept_analytics.sort(key=lambda x: x["mean_mastery"])

    # Cluster scatter points
    cluster_scatter = [
        {
            "student_id": s.id,
            "student_code": s.student_code,
            "full_name": s.user.full_name,
            "cluster_id": s.cluster_id,
            "cluster_label": s.cluster_label,
            "pca_x": s.pca_x,
            "pca_y": s.pca_y,
            "predicted_score": round(s.predicted_final_score, 1),
            "risk_level": s.risk_level,
        }
        for s in students
    ]

    # Score distribution histogram bins
    scores = [s.predicted_final_score for s in students]
    bins = [(0, 55, "<55"), (55, 65, "55-64"), (65, 75, "65-74"), (75, 85, "75-84"), (85, 101, "85+")]
    score_distribution = [
        {"range": label, "count": sum(1 for sc in scores if lo <= sc < hi)}
        for lo, hi, label in bins
    ]

    models_data = get_loaded_models(db)

    return {
        "kpis": {
            "total_students": total,
            "high_risk_count": high_risk,
            "moderate_risk_count": moderate_risk,
            "low_risk_count": low_risk,
            "avg_predicted_score": avg_pred_score,
            "avg_attendance_rate": avg_attendance,
            "avg_engagement_index": avg_engagement,
            "avg_gpa": avg_gpa,
            "open_interventions": open_interventions,
            "total_submissions": total_submissions,
        },
        "risk_distribution": [
            {"tier": "Low Risk", "count": low_risk, "key": "low"},
            {"tier": "Moderate Risk", "count": moderate_risk, "key": "moderate"},
            {"tier": "High Risk", "count": high_risk, "key": "high"},
        ],
        "cohort_comparison": cohort_comparison,
        "weekly_trends": weekly_trends,
        "concept_analytics": concept_analytics,
        "cluster_scatter": cluster_scatter,
        "score_distribution": score_distribution,
        "priority_students": [
            {
                "id": s.id,
                "student_code": s.student_code,
                "full_name": s.user.full_name,
                "email": s.user.email,
                "cohort": s.cohort,
                "cluster_label": s.cluster_label,
                "attendance_rate": round(s.attendance_rate, 1),
                "engagement_index": round(s.engagement_index, 1),
                "predicted_final_score": round(s.predicted_final_score, 1),
                "risk_score": round(s.risk_score, 1),
                "risk_level": s.risk_level,
            }
            for s in students[:12]
        ],
        "ml_summary": {
            "classifier": models_data["metrics"]["risk_model"]["selected_classifier"],
            "classifier_metrics": models_data["metrics"]["risk_model"]["classifier_metrics"],
            "clustering": models_data["metrics"]["clustering_model"],
        },
    }


@router.get("/student")
def get_student_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile required for personal analytics.",
        )

    student = (
        db.query(StudentProfile)
        .options(
            selectinload(StudentProfile.weekly_telemetry),
            selectinload(StudentProfile.concept_masteries)
            .joinedload(ConceptMastery.concept)
            .joinedload(Concept.course),
            selectinload(StudentProfile.enrollments),
        )
        .filter(StudentProfile.id == current_user.student_profile.id)
        .first()
    )

    # Compare student concept mastery vs cohort mean
    all_masteries = db.query(ConceptMastery).all()
    cohort_avg_map: Dict[int, List[float]] = defaultdict(list)
    for m in all_masteries:
        cohort_avg_map[m.concept_id].append(m.mastery_score)

    concept_comparison = []
    for m in sorted(student.concept_masteries, key=lambda x: x.mastery_score):
        c_vals = cohort_avg_map.get(m.concept_id, [m.mastery_score])
        concept_comparison.append(
            {
                "concept_code": m.concept.code if m.concept else "",
                "concept_name": m.concept.name if m.concept else "",
                "course_code": m.concept.course.code if m.concept and m.concept.course else "",
                "student_mastery": round(m.mastery_score, 1),
                "cohort_mean": round(float(np.mean(c_vals)), 1),
                "attempts": m.attempts_count,
            }
        )

    trajectory = forecast_score_trajectory(student.weekly_telemetry, horizon_weeks=4)

    study_cadence = [
        {
            "week_label": t.week_label,
            "study_hours": round(t.study_hours, 1),
            "sessions_count": t.sessions_count,
            "assignments_completed": t.assignments_completed,
            "avg_quiz_score": round(t.avg_quiz_score, 1),
            "attendance_pct": round(t.attendance_pct, 1),
        }
        for t in sorted(student.weekly_telemetry, key=lambda x: x.week_number)
    ]

    return {
        "trajectory": trajectory,
        "study_cadence": study_cadence,
        "concept_comparison": concept_comparison,
    }
