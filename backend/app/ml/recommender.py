from typing import Any, Dict, List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session, joinedload

from app.db.models import ConceptMastery, LearningResource, ResourceInteraction


def generate_personalized_recommendations(
    db: Session,
    student_id: int,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    Hybrid recommendation engine combining:
    1. Concept mastery deficit urgency
    2. Prerequisite readiness gating
    3. Resource difficulty calibration
    4. TF-IDF semantic alignment with weak concepts
    """
    resources = (
        db.query(LearningResource)
        .options(joinedload(LearningResource.course), joinedload(LearningResource.concept))
        .all()
    )
    if not resources:
        return []

    masteries = (
        db.query(ConceptMastery)
        .options(joinedload(ConceptMastery.concept))
        .filter(ConceptMastery.student_id == student_id)
        .all()
    )
    mastery_by_concept: Dict[int, float] = {m.concept_id: float(m.mastery_score) for m in masteries}

    interactions = (
        db.query(ResourceInteraction)
        .filter(ResourceInteraction.student_id == student_id)
        .all()
    )
    interaction_map: Dict[int, str] = {i.resource_id: i.status for i in interactions}

    # Build TF-IDF corpus over learning resources
    docs = [
        f"{r.title} {r.summary} {r.tags} {r.concept.name if r.concept else ''} {r.course.title if r.course else ''}"
        for r in resources
    ]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(docs)

    # Construct learner deficit query from weakest concepts
    weak_masteries = sorted(masteries, key=lambda m: m.mastery_score)[:5]
    weak_query_text = " ".join(
        f"{m.concept.name} {m.concept.description}" for m in weak_masteries if m.concept
    ).strip() or "machine learning foundations neural networks evaluation metrics"

    query_vec = vectorizer.transform([weak_query_text])
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    scored_items: List[Dict[str, Any]] = []
    for idx, res in enumerate(resources):
        status = interaction_map.get(res.id, "unstarted")
        concept_mastery = mastery_by_concept.get(res.concept_id, 65.0)
        mastery_gap = max(0.0, 88.0 - concept_mastery)
        gap_urgency = np.clip(mastery_gap / 60.0, 0.05, 1.0)

        # Check prerequisite readiness
        prereq_id = res.concept.prerequisite_concept_id if res.concept else None
        prereq_mastery = mastery_by_concept.get(prereq_id, 78.0) if prereq_id else 85.0
        prereq_ready = prereq_mastery >= 55.0
        prereq_multiplier = 1.08 if prereq_ready else 0.72

        # Difficulty calibration relative to current mastery
        if concept_mastery < 58.0:
            diff_fit = {"Foundational": 1.0, "Intermediate": 0.78, "Advanced": 0.45}.get(res.difficulty, 0.75)
        elif concept_mastery < 78.0:
            diff_fit = {"Foundational": 0.72, "Intermediate": 1.0, "Advanced": 0.78}.get(res.difficulty, 0.85)
        else:
            diff_fit = {"Foundational": 0.45, "Intermediate": 0.82, "Advanced": 1.0}.get(res.difficulty, 0.85)

        completed_penalty = 0.25 if status == "completed" else 1.0
        tfidf_sim = float(sim_scores[idx])

        composite = (
            (0.48 * gap_urgency + 0.24 * diff_fit + 0.28 * min(1.0, tfidf_sim * 2.1 + 0.18))
            * prereq_multiplier
            * completed_penalty
        )
        match_score = round(float(np.clip(composite * 100.0, 28.0, 99.0)), 1)

        if not prereq_ready and res.concept and res.concept.prerequisite:
            rationale = (
                f"Current {res.concept.name} mastery is {concept_mastery:.0f}%. "
                f"Review prerequisite '{res.concept.prerequisite.name}' ({prereq_mastery:.0f}%) alongside this module."
            )
            prereq_status = "Review Prerequisite"
        elif concept_mastery < 65.0:
            rationale = (
                f"High-priority reinforcement for {res.concept.name} (mastery {concept_mastery:.0f}% vs 80% target)."
            )
            prereq_status = "Priority Gap"
        elif concept_mastery < 82.0:
            rationale = (
                f"Calibrated {res.difficulty.lower()} progression to elevate {res.concept.name} from {concept_mastery:.0f}% toward mastery."
            )
            prereq_status = "Ready"
        else:
            rationale = f"Advanced enrichment in {res.concept.name} (current mastery {concept_mastery:.0f}%)."
            prereq_status = "Enrichment"

        scored_items.append(
            {
                "resource_id": res.id,
                "title": res.title,
                "course_code": res.course.code if res.course else "",
                "course_title": res.course.title if res.course else "",
                "concept_id": res.concept_id,
                "concept_name": res.concept.name if res.concept else "",
                "resource_type": res.resource_type,
                "difficulty": res.difficulty,
                "estimated_minutes": res.estimated_minutes,
                "summary": res.summary,
                "content_body": res.content_body,
                "tags": [t.strip() for t in res.tags.split(",") if t.strip()],
                "match_score": match_score,
                "current_concept_mastery": round(concept_mastery, 1),
                "prerequisite_status": prereq_status,
                "interaction_status": status,
                "rationale": rationale,
            }
        )

    scored_items.sort(key=lambda item: (item["interaction_status"] == "completed", -item["match_score"]))
    return scored_items[:limit]
