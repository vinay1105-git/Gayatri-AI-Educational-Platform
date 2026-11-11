from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    AssessmentSubmission,
    ConceptMastery,
    Enrollment,
    ResourceInteraction,
    StudentProfile,
    WeeklyTelemetry,
)

FEATURE_COLUMNS: List[str] = [
    "avg_study_hours",
    "study_consistency",
    "attendance_rate",
    "assignment_timeliness",
    "engagement_index",
    "latest_quiz_score",
    "quiz_score_trend",
    "avg_concept_mastery",
    "weak_concept_ratio",
    "course_progress_avg",
    "resource_completion_count",
]

FEATURE_LABELS: Dict[str, str] = {
    "avg_study_hours": "Weekly Study Hours",
    "study_consistency": "Study Cadence Consistency",
    "attendance_rate": "Attendance Rate",
    "assignment_timeliness": "Assignment Timeliness",
    "engagement_index": "Platform Engagement Index",
    "latest_quiz_score": "Recent Quiz Performance",
    "quiz_score_trend": "10-Week Score Momentum",
    "avg_concept_mastery": "Concept Mastery Average",
    "weak_concept_ratio": "Concept Deficit Ratio",
    "course_progress_avg": "Course Completion Progress",
    "resource_completion_count": "Completed Learning Modules",
}


def compute_student_features(
    profile: StudentProfile,
    telemetry: List[WeeklyTelemetry],
    masteries: List[ConceptMastery],
    enrollments: List[Enrollment],
    submissions: List[AssessmentSubmission],
    completed_resources_count: int,
) -> Dict[str, float]:
    ordered_telemetry = sorted(telemetry, key=lambda t: t.week_number)

    if ordered_telemetry:
        hours_arr = np.array([t.study_hours for t in ordered_telemetry], dtype=float)
        scores_arr = np.array([t.avg_quiz_score for t in ordered_telemetry], dtype=float)
        avg_study_hours = float(np.mean(hours_arr))
        std_hours = float(np.std(hours_arr))
        study_consistency = float(np.clip(1.0 - (std_hours / (avg_study_hours + 1.0)), 0.0, 1.0)) * 100.0
        latest_quiz_score = float(scores_arr[-1])
        if len(scores_arr) >= 2:
            weeks = np.arange(len(scores_arr), dtype=float)
            slope = float(np.polyfit(weeks, scores_arr, 1)[0])
        else:
            slope = 0.0
    else:
        avg_study_hours = float(profile.study_goal_hours_weekly * 0.75)
        study_consistency = 65.0
        latest_quiz_score = 72.0
        slope = 0.0

    if masteries:
        mastery_scores = np.array([m.mastery_score for m in masteries], dtype=float)
        avg_concept_mastery = float(np.mean(mastery_scores))
        weak_concept_ratio = float(np.mean(mastery_scores < 62.0))
    else:
        avg_concept_mastery = 65.0
        weak_concept_ratio = 0.25

    if enrollments:
        course_progress_avg = float(np.mean([e.progress_pct for e in enrollments]))
    else:
        course_progress_avg = 0.0

    blended_latest = latest_quiz_score

    return {
        "student_id": float(profile.id),
        "avg_study_hours": round(avg_study_hours, 4),
        "study_consistency": round(study_consistency, 4),
        "attendance_rate": round(float(profile.attendance_rate), 4),
        "assignment_timeliness": round(float(profile.assignment_timeliness), 4),
        "engagement_index": round(float(profile.engagement_index), 4),
        "latest_quiz_score": round(blended_latest, 4),
        "quiz_score_trend": round(slope, 4),
        "avg_concept_mastery": round(avg_concept_mastery, 4),
        "weak_concept_ratio": round(weak_concept_ratio, 4),
        "course_progress_avg": round(course_progress_avg, 4),
        "resource_completion_count": float(completed_resources_count),
    }


def extract_cohort_dataframe(db: Session) -> Tuple[pd.DataFrame, List[StudentProfile]]:
    profiles = (
        db.query(StudentProfile)
        .options(
            selectinload(StudentProfile.weekly_telemetry),
            selectinload(StudentProfile.concept_masteries),
            selectinload(StudentProfile.enrollments),
            selectinload(StudentProfile.submissions),
            selectinload(StudentProfile.resource_interactions),
        )
        .order_by(StudentProfile.id)
        .all()
    )

    rows: List[Dict[str, float]] = []
    for p in profiles:
        completed_count = sum(1 for r in p.resource_interactions if r.status == "completed")
        feat = compute_student_features(
            profile=p,
            telemetry=p.weekly_telemetry,
            masteries=p.concept_masteries,
            enrollments=p.enrollments,
            submissions=p.submissions,
            completed_resources_count=completed_count,
        )
        # Observed composite academic outcome derived from actual enrollment course grades
        grade_vals = [e.current_grade for e in p.enrollments]
        if grade_vals:
            observed_outcome = float(np.mean(grade_vals))
        elif p.submissions:
            observed_outcome = float(np.mean([s.score_pct for s in p.submissions]))
        else:
            observed_outcome = 70.0

        feat["observed_outcome"] = round(observed_outcome, 4)
        feat["at_risk_target"] = 1 if observed_outcome < 68.0 else 0
        rows.append(feat)

    df = pd.DataFrame(rows)
    return df, profiles


def extract_single_student_features(db: Session, student_id: int) -> Dict[str, float]:
    profile = (
        db.query(StudentProfile)
        .options(
            selectinload(StudentProfile.weekly_telemetry),
            selectinload(StudentProfile.concept_masteries),
            selectinload(StudentProfile.enrollments),
            selectinload(StudentProfile.submissions),
            selectinload(StudentProfile.resource_interactions),
        )
        .filter(StudentProfile.id == student_id)
        .first()
    )
    if not profile:
        raise ValueError(f"Student profile {student_id} not found.")
    completed_count = sum(1 for r in profile.resource_interactions if r.status == "completed")
    return compute_student_features(
        profile=profile,
        telemetry=profile.weekly_telemetry,
        masteries=profile.concept_masteries,
        enrollments=profile.enrollments,
        submissions=profile.submissions,
        completed_resources_count=completed_count,
    )
