from datetime import datetime, timezone
from typing import Any, Dict, List
import numpy as np
from sklearn.linear_model import Ridge
from sqlalchemy.orm import Session

from app.db.models import Concept, ConceptMastery, WeeklyTelemetry

DIFFICULTY_WEIGHT = {
    "easy": 0.28,
    "medium": 0.38,
    "hard": 0.48,
}


def update_mastery_from_assessment_item(
    db: Session,
    student_id: int,
    concept_id: int,
    is_correct: bool,
    item_difficulty: str = "medium",
) -> ConceptMastery:
    """
    Bayesian/EWMA-inspired knowledge tracing update:
    Adjusts mastery score based on item difficulty, correctness, and prerequisite readiness.
    """
    mastery = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.student_id == student_id, ConceptMastery.concept_id == concept_id)
        .first()
    )
    concept = db.query(Concept).filter(Concept.id == concept_id).first()

    prereq_factor = 1.0
    if concept and concept.prerequisite_concept_id:
        prereq_m = (
            db.query(ConceptMastery)
            .filter(
                ConceptMastery.student_id == student_id,
                ConceptMastery.concept_id == concept.prerequisite_concept_id,
            )
            .first()
        )
        if prereq_m and prereq_m.mastery_score < 60.0:
            prereq_factor = 0.85

    alpha = DIFFICULTY_WEIGHT.get(item_difficulty.lower(), 0.35)
    observation = 96.0 if is_correct else 28.0

    if not mastery:
        initial = 72.0 if is_correct else 46.0
        mastery = ConceptMastery(
            student_id=student_id,
            concept_id=concept_id,
            mastery_score=round(initial * prereq_factor, 2),
            confidence=0.45,
            attempts_count=1,
            last_practiced_at=datetime.now(timezone.utc),
        )
        db.add(mastery)
    else:
        updated = (1.0 - alpha) * mastery.mastery_score + alpha * (observation * prereq_factor)
        mastery.mastery_score = round(float(np.clip(updated, 15.0, 99.0)), 2)
        mastery.attempts_count += 1
        mastery.confidence = round(float(min(0.98, mastery.confidence + 0.08)), 3)
        mastery.last_practiced_at = datetime.now(timezone.utc)

    db.flush()
    return mastery


def update_mastery_from_resource_completion(
    db: Session,
    student_id: int,
    concept_id: int,
    resource_difficulty: str = "Intermediate",
) -> ConceptMastery:
    mastery = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.student_id == student_id, ConceptMastery.concept_id == concept_id)
        .first()
    )
    boost = {"Foundational": 6.5, "Intermediate": 5.0, "Advanced": 4.0}.get(resource_difficulty, 5.0)

    if not mastery:
        mastery = ConceptMastery(
            student_id=student_id,
            concept_id=concept_id,
            mastery_score=round(60.0 + boost, 2),
            confidence=0.5,
            attempts_count=1,
            last_practiced_at=datetime.now(timezone.utc),
        )
        db.add(mastery)
    else:
        # Diminishing returns as mastery approaches 96
        headroom = max(0.0, (96.0 - mastery.mastery_score) / 96.0)
        gain = boost * (0.45 + 0.75 * headroom)
        mastery.mastery_score = round(float(np.clip(mastery.mastery_score + gain, 15.0, 98.5)), 2)
        mastery.attempts_count += 1
        mastery.confidence = round(float(min(0.98, mastery.confidence + 0.05)), 3)
        mastery.last_practiced_at = datetime.now(timezone.utc)

    db.flush()
    return mastery


def forecast_score_trajectory(telemetry: List[WeeklyTelemetry], horizon_weeks: int = 4) -> List[Dict[str, Any]]:
    ordered = sorted(telemetry, key=lambda t: t.week_number)
    if not ordered:
        return []

    weeks = np.array([t.week_number for t in ordered], dtype=float)
    scores = np.array([t.avg_quiz_score for t in ordered], dtype=float)
    hours = np.array([t.study_hours for t in ordered], dtype=float)

    history: List[Dict[str, Any]] = [
        {
            "week_label": t.week_label,
            "week_number": int(t.week_number),
            "actual_score": round(float(t.avg_quiz_score), 2),
            "projected_score": None,
            "lower_bound": None,
            "upper_bound": None,
            "study_hours": round(float(t.study_hours), 2),
            "is_forecast": False,
        }
        for t in ordered
    ]

    if len(ordered) >= 3:
        X_train = np.column_stack([weeks, hours])
        model = Ridge(alpha=4.0)
        model.fit(X_train, scores)
        in_sample = model.predict(X_train)
        residual_std = float(np.std(scores - in_sample))
        last_hours = float(np.mean(hours[-3:]))
        last_week = int(weeks[-1])

        # Bridge point on last observed week for seamless chart continuity
        history[-1]["projected_score"] = history[-1]["actual_score"]

        for step in range(1, horizon_weeks + 1):
            w_next = last_week + step
            pred_raw = float(model.predict(np.array([[w_next, last_hours]]))[0])
            # Damped blend toward last 3-week moving average to prevent runaway extrapolation
            recent_anchor = float(np.mean(scores[-3:]))
            damped = (0.72 ** step) * pred_raw + (1.0 - 0.72 ** step) * recent_anchor
            pred = float(np.clip(damped, 30.0, 99.0))
            band = max(2.2, residual_std * 1.35 * np.sqrt(step))
            history.append(
                {
                    "week_label": f"W{w_next:02d}",
                    "week_number": w_next,
                    "actual_score": None,
                    "projected_score": round(pred, 2),
                    "lower_bound": round(float(np.clip(pred - band, 20.0, 99.0)), 2),
                    "upper_bound": round(float(np.clip(pred + band, 25.0, 100.0)), 2),
                    "study_hours": round(last_hours, 2),
                    "is_forecast": True,
                }
            )

    return history
