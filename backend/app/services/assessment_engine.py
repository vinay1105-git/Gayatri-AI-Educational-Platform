import json
from datetime import datetime, timezone
from typing import Any, Dict, List
import numpy as np
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentSubmission,
    Enrollment,
    QuestionResponse,
    StudentProfile,
)
from app.ml.knowledge_tracing import update_mastery_from_assessment_item
from app.ml.model_registry import refresh_student_predictions


def grade_assessment_submission(
    db: Session,
    student: StudentProfile,
    assessment: Assessment,
    answers: Dict[int, int],
    time_spent_seconds: int,
) -> Dict[str, Any]:
    questions = (
        db.query(AssessmentQuestion)
        .options(joinedload(AssessmentQuestion.concept))
        .filter(AssessmentQuestion.assessment_id == assessment.id)
        .order_by(AssessmentQuestion.id)
        .all()
    )
    if not questions:
        raise ValueError("This assessment has no configured questions.")

    points_possible = sum(q.points for q in questions)
    points_earned = 0.0
    correct_count = 0
    item_results: List[Dict[str, Any]] = []

    submission = AssessmentSubmission(
        assessment_id=assessment.id,
        student_id=student.id,
        score_pct=0.0,
        points_earned=0.0,
        points_possible=points_possible,
        passed=False,
        time_spent_seconds=max(10, time_spent_seconds),
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.flush()

    for q in questions:
        selected = answers.get(q.id, -1)
        is_correct = selected == q.correct_index
        if is_correct:
            points_earned += q.points
            correct_count += 1

        db.add(
            QuestionResponse(
                submission_id=submission.id,
                question_id=q.id,
                selected_index=selected,
                is_correct=is_correct,
            )
        )

        updated_mastery = update_mastery_from_assessment_item(
            db=db,
            student_id=student.id,
            concept_id=q.concept_id,
            is_correct=is_correct,
            item_difficulty=q.difficulty,
        )

        options = json.loads(q.options_json)
        item_results.append(
            {
                "question_id": q.id,
                "prompt": q.prompt,
                "concept_name": q.concept.name if q.concept else "",
                "selected_index": selected,
                "correct_index": q.correct_index,
                "options": options,
                "is_correct": is_correct,
                "points_earned": q.points if is_correct else 0.0,
                "points_possible": q.points,
                "explanation": q.explanation,
                "updated_concept_mastery": updated_mastery.mastery_score,
            }
        )

    score_pct = round((points_earned / points_possible) * 100.0, 2) if points_possible > 0 else 0.0
    passed = score_pct >= assessment.passing_score

    submission.score_pct = score_pct
    submission.points_earned = round(points_earned, 2)
    submission.passed = passed

    # Update course enrollment grade smoothly
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student.id, Enrollment.course_id == assessment.course_id)
        .first()
    )
    if enrollment:
        enrollment.current_grade = round(0.65 * enrollment.current_grade + 0.35 * score_pct, 2)
        enrollment.last_accessed_at = datetime.now(timezone.utc)
        if enrollment.progress_pct < 100.0:
            enrollment.progress_pct = round(min(100.0, enrollment.progress_pct + 4.5), 1)

    db.commit()

    # Recompute ML risk score, predicted final score, and persona cluster
    ml_refresh = refresh_student_predictions(db, student.id)

    return {
        "submission_id": submission.id,
        "assessment_id": assessment.id,
        "assessment_title": assessment.title,
        "score_pct": score_pct,
        "points_earned": round(points_earned, 2),
        "points_possible": round(points_possible, 2),
        "correct_count": correct_count,
        "total_questions": len(questions),
        "passed": passed,
        "passing_score": assessment.passing_score,
        "time_spent_seconds": submission.time_spent_seconds,
        "submitted_at": submission.submitted_at.isoformat(),
        "updated_prediction": ml_refresh["prediction"],
        "items": item_results,
    }


def compute_assessment_psychometrics(db: Session, assessment_id: int) -> Dict[str, Any]:
    assessment = (
        db.query(Assessment)
        .options(
            selectinload(Assessment.questions).joinedload(AssessmentQuestion.concept),
            selectinload(Assessment.submissions).selectinload(AssessmentSubmission.responses),
        )
        .filter(Assessment.id == assessment_id)
        .first()
    )
    if not assessment:
        raise ValueError("Assessment not found.")

    subs = sorted(assessment.submissions, key=lambda s: s.score_pct)
    n_subs = len(subs)
    scores = [s.score_pct for s in subs]

    # Top/Bottom 27% groups for Item Discrimination Index (Kelley 1939 standard)
    k = max(1, int(round(0.27 * n_subs))) if n_subs >= 4 else max(1, n_subs // 2)
    low_sub_ids = {s.id for s in subs[:k]}
    high_sub_ids = {s.id for s in subs[-k:]}

    item_stats: List[Dict[str, Any]] = []
    for q in assessment.questions:
        total_attempts = 0
        total_correct = 0
        high_correct = 0
        high_total = 0
        low_correct = 0
        low_total = 0

        for sub in subs:
            resp = next((r for r in sub.responses if r.question_id == q.id), None)
            if not resp:
                continue
            total_attempts += 1
            if resp.is_correct:
                total_correct += 1
            if sub.id in high_sub_ids:
                high_total += 1
                if resp.is_correct:
                    high_correct += 1
            if sub.id in low_sub_ids:
                low_total += 1
                if resp.is_correct:
                    low_correct += 1

        p_val = (total_correct / total_attempts) if total_attempts > 0 else 0.0
        p_high = (high_correct / high_total) if high_total > 0 else p_val
        p_low = (low_correct / low_total) if low_total > 0 else p_val
        disc_idx = p_high - p_low

        if disc_idx >= 0.35:
            quality = "Strong Discriminator"
        elif disc_idx >= 0.15:
            quality = "Acceptable"
        else:
            quality = "Review Calibration"

        item_stats.append(
            {
                "question_id": q.id,
                "prompt": q.prompt,
                "concept_name": q.concept.name if q.concept else "",
                "difficulty_tag": q.difficulty,
                "attempts": total_attempts,
                "difficulty_p_value": round(p_val, 3),
                "discrimination_index": round(disc_idx, 3),
                "calibration_status": quality,
            }
        )

    return {
        "assessment_id": assessment.id,
        "title": assessment.title,
        "submissions_count": n_subs,
        "mean_score": round(float(np.mean(scores)), 2) if scores else 0.0,
        "median_score": round(float(np.median(scores)), 2) if scores else 0.0,
        "std_dev": round(float(np.std(scores)), 2) if scores else 0.0,
        "pass_rate": round(float(np.mean([1.0 if s.passed else 0.0 for s in subs]) * 100.0), 1) if subs else 0.0,
        "items": item_stats,
    }
