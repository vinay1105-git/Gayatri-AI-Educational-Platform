import re
from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models import (
    AssessmentSubmission,
    Concept,
    ConceptMastery,
    Intervention,
    LearningResource,
    StudentProfile,
    User,
)
from app.ml.recommender import generate_personalized_recommendations


def _detect_intent(query: str, role: str) -> str:
    q = query.lower()
    admin_keywords = [
        "cohort",
        "students",
        "at-risk",
        "at risk",
        "intervention",
        "cluster",
        "institution",
        "department",
        "model accuracy",
        "evaluation metric",
        "faculty",
    ]
    plan_keywords = [
        "study plan",
        "schedule",
        "what should i study",
        "next module",
        "recommend",
        "focus next",
        "prepare",
        "roadmap",
        "weekly plan",
    ]
    perf_keywords = [
        "my performance",
        "my progress",
        "my score",
        "my risk",
        "weak",
        "struggling",
        "how am i doing",
        "gpa",
        "forecast",
        "grade",
        "assessment result",
        "diagnosis",
    ]

    if role == "admin" and any(k in q for k in admin_keywords):
        return "cohort_admin"
    if any(k in q for k in plan_keywords):
        return "study_plan"
    if any(k in q for k in perf_keywords):
        return "performance_diagnosis"
    if role == "admin" and ("overview" in q or "summary" in q or "status" in q):
        return "cohort_admin"
    return "concept_explanation"


def _retrieve_curriculum_context(db: Session, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    concepts = db.query(Concept).options(joinedload(Concept.course)).all()
    resources = (
        db.query(LearningResource)
        .options(joinedload(LearningResource.course), joinedload(LearningResource.concept))
        .all()
    )

    docs: List[Dict[str, Any]] = []
    corpus: List[str] = []

    for c in concepts:
        text = f"{c.code} {c.name} {c.description} {c.key_notes} {c.course.title if c.course else ''}"
        corpus.append(text)
        docs.append(
            {
                "kind": "Concept Specification",
                "id": c.id,
                "course_code": c.course.code if c.course else "CORE",
                "title": c.name,
                "concept_id": c.id,
                "concept_name": c.name,
                "summary": c.description,
                "body": c.key_notes,
            }
        )

    for r in resources:
        text = f"{r.title} {r.summary} {r.content_body} {r.tags} {r.concept.name if r.concept else ''}"
        corpus.append(text)
        docs.append(
            {
                "kind": r.resource_type,
                "id": r.id,
                "course_code": r.course.code if r.course else "CORE",
                "title": r.title,
                "concept_id": r.concept_id,
                "concept_name": r.concept.name if r.concept else "",
                "summary": r.summary,
                "body": r.content_body,
            }
        )

    if not corpus:
        return []

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix).flatten()

    # Keyword boost for exact concept name substring match
    q_lower = query.lower()
    for i, doc in enumerate(docs):
        title_tokens = [t for t in re.split(r"\W+", doc["title"].lower()) if len(t) > 3]
        if any(tok in q_lower for tok in title_tokens):
            sims[i] += 0.18

    top_indices = np.argsort(sims)[::-1][:top_k]
    results: List[Dict[str, Any]] = []
    for idx in top_indices:
        score = float(sims[idx])
        if score > 0.04 or not results:
            doc = dict(docs[idx])
            doc["relevance_score"] = round(min(0.99, score), 3)
            results.append(doc)
    return results


def generate_assistant_reply(
    db: Session,
    user: User,
    query: str,
    model_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    intent = _detect_intent(query, user.role)
    retrieved = _retrieve_curriculum_context(db, query, top_k=3)

    citations = [
        {
            "title": doc["title"],
            "course_code": doc["course_code"],
            "kind": doc["kind"],
            "relevance": doc["relevance_score"],
        }
        for doc in retrieved
    ]

    profile = (
        db.query(StudentProfile)
        .options(
            selectinload(StudentProfile.concept_masteries).joinedload(ConceptMastery.concept),
            selectinload(StudentProfile.submissions).joinedload(AssessmentSubmission.assessment),
        )
        .filter(StudentProfile.user_id == user.id)
        .first()
    )

    if intent == "cohort_admin" and user.role == "admin":
        all_students = db.query(StudentProfile).options(joinedload(StudentProfile.user)).all()
        total = len(all_students)
        high_risk = [s for s in all_students if s.risk_level == "high"]
        mod_risk = [s for s in all_students if s.risk_level == "moderate"]
        avg_pred = float(np.mean([s.predicted_final_score for s in all_students])) if all_students else 0.0
        open_interventions = db.query(Intervention).filter(Intervention.status != "resolved").count()

        # Find lowest mastery concepts across cohort
        concepts = db.query(Concept).all()
        concept_avgs = []
        for c in concepts:
            ms = db.query(ConceptMastery).filter(ConceptMastery.concept_id == c.id).all()
            if ms:
                concept_avgs.append((c.name, float(np.mean([m.mastery_score for m in ms]))))
        concept_avgs.sort(key=lambda x: x[1])
        weakest_3 = concept_avgs[:3]

        high_risk_names = ", ".join(
            f"{s.user.full_name} ({s.risk_score:.0f}% risk)" for s in sorted(high_risk, key=lambda x: -x.risk_score)[:4]
        )
        weakest_str = "; ".join(f"{name} ({avg:.1f}%)" for name, avg in weakest_3)

        clf_info = ""
        if model_metrics and "risk_model" in model_metrics:
            cm = model_metrics["risk_model"].get("classifier_metrics", {})
            clf_info = (
                f"\n\n**Predictive Pipeline Telemetry:** {model_metrics['risk_model'].get('selected_classifier')} "
                f"is active with cross-validated Accuracy `{cm.get('accuracy', 0)*100:.1f}%`, "
                f"F1 `{cm.get('f1_score', 0):.3f}`, and ROC-AUC `{cm.get('roc_auc', 0):.3f}`."
            )

        answer = (
            f"### Institutional Cohort Diagnostics\n\n"
            f"Across **{total} active learners**, the projected mean final score is **{avg_pred:.1f}%**. "
            f"Currently **{len(high_risk)} learners** are in the **High Risk** tier and **{len(mod_risk)}** "
            f"are in **Moderate Risk**, with **{open_interventions} open academic interventions**.\n\n"
            f"**Priority Students for Immediate Outreach:**\n"
            f"- {high_risk_names or 'No high-risk students currently flagged.'}\n\n"
            f"**Lowest Cohort Concept Mastery:**\n"
            f"- {weakest_str or 'Insufficient mastery records.'}\n\n"
            f"**Recommended Administrative Actions:**\n"
            f"1. Schedule targeted prerequisite review sessions for the lowest-mastery concepts listed above.\n"
            f"2. Review learners in the *Targeted Support Needed* cluster and log advisor check-ins.\n"
            f"3. Export the Executive Cohort Intelligence PDF for department review."
            f"{clf_info}"
        )
        actions = [
            {"label": "Inspect High-Risk Learners", "route": "/admin/students"},
            {"label": "View ML Evaluation Console", "route": "/admin/ml-models"},
            {"label": "Export Executive Report", "route": "/reports"},
        ]
        return {"answer": answer, "intent": intent, "citations": citations, "suggested_actions": actions}

    if profile and intent == "performance_diagnosis":
        masteries_sorted = sorted(profile.concept_masteries, key=lambda m: m.mastery_score)
        weakest = masteries_sorted[:3]
        strongest = masteries_sorted[-2:][::-1]
        recent_subs = sorted(profile.submissions, key=lambda s: s.submitted_at, reverse=True)[:3]

        weak_bullets = "\n".join(
            f"- **{m.concept.name}** ({m.mastery_score:.1f}% mastery, {m.attempts_count} attempts)"
            for m in weakest
            if m.concept
        )
        strong_bullets = "\n".join(
            f"- **{m.concept.name}** ({m.mastery_score:.1f}% mastery)"
            for m in strongest
            if m.concept
        )
        sub_bullets = "\n".join(
            f"- {s.assessment.title if s.assessment else 'Assessment'}: **{s.score_pct:.1f}%** ({'Passed' if s.passed else 'Needs Review'})"
            for s in recent_subs
        )

        answer = (
            f"### Personal Performance Diagnostic — {user.full_name}\n\n"
            f"- **Learner Persona:** {profile.cluster_label}\n"
            f"- **Projected Final Score:** **{profile.predicted_final_score:.1f}%** | **Risk Tier:** `{profile.risk_level.upper()}` ({profile.risk_score:.1f}% risk index)\n"
            f"- **Attendance:** {profile.attendance_rate:.1f}% | **Engagement Index:** {profile.engagement_index:.1f}/100 | **GPA:** {profile.current_gpa:.2f}\n\n"
            f"**Highest-Impact Concept Gaps to Reinforce:**\n{weak_bullets or '- No concept gaps detected yet.'}\n\n"
            f"**Strongest Foundations:**\n{strong_bullets or '- Keep completing baseline diagnostics.'}\n\n"
            f"**Recent Assessments:**\n{sub_bullets or '- No recent submissions recorded.'}"
        )
        actions = [
            {"label": "Open Adaptive Recommendations", "route": "/courses"},
            {"label": "Take Diagnostic Assessment", "route": "/assessments"},
            {"label": "Download Progress Transcript PDF", "route": "/reports"},
        ]
        return {"answer": answer, "intent": intent, "citations": citations, "suggested_actions": actions}

    if profile and intent == "study_plan":
        recs = generate_personalized_recommendations(db, profile.id, limit=3)
        plan_lines = []
        total_mins = 0
        for idx, rec in enumerate(recs, start=1):
            total_mins += rec["estimated_minutes"]
            plan_lines.append(
                f"{idx}. **{rec['title']}** ({rec['course_code']} · {rec['resource_type']}, ~{rec['estimated_minutes']} min)\n"
                f"   - *Why:* {rec['rationale']}"
            )
        plan_block = "\n".join(plan_lines) if plan_lines else "All core modules are currently completed."
        answer = (
            f"### Personalized Adaptive Study Plan ({total_mins} min total)\n\n"
            f"Calibrated for your **{profile.cluster_label}** profile (weekly goal: {profile.study_goal_hours_weekly:.0f} hrs):\n\n"
            f"{plan_block}\n\n"
            f"**Execution Strategy:** Complete items in order so prerequisite mastery propagates before your next module assessment, "
            f"then run a targeted practice evaluation in the Assessment Center to verify mastery gain."
        )
        actions = [
            {"label": "Launch Recommended Modules", "route": "/courses"},
            {"label": "Verify Mastery in Assessment Center", "route": "/assessments"},
        ]
        return {"answer": answer, "intent": intent, "citations": citations, "suggested_actions": actions}

    # Concept Explanation / Technical Tutoring Mode
    primary = retrieved[0] if retrieved else None
    secondary = retrieved[1] if len(retrieved) > 1 else None

    student_mastery_note = ""
    if profile and primary and primary.get("concept_id"):
        cm = next((m for m in profile.concept_masteries if m.concept_id == primary["concept_id"]), None)
        if cm:
            gap_tip = (
                "Focus on worked numerical examples and check prerequisite foundations."
                if cm.mastery_score < 70.0
                else "You have solid mastery here—challenge yourself with an applied lab or hard assessment item."
            )
            student_mastery_note = (
                f"\n\n**Your Mastery Telemetry for {primary['concept_name']}:** "
                f"**{cm.mastery_score:.1f}%** ({cm.attempts_count} recorded interactions). {gap_tip}"
            )

    if primary:
        extra_block = (
            f"\n\n**Related Curriculum Resource:** *{secondary['title']}* ({secondary['course_code']}) — {secondary['summary']}"
            if secondary
            else ""
        )
        answer = (
            f"### {primary['title']} ({primary['course_code']})\n\n"
            f"{primary['summary']}\n\n"
            f"**Core Technical Principles & Notes:**\n"
            f"{primary['body']}"
            f"{student_mastery_note}"
            f"{extra_block}"
        )
    else:
        answer = (
            "I searched the Gayatri AI curriculum corpus for your query. Try asking about specific topics like "
            "*Backpropagation*, *Gradient Descent*, *Regularization & Bias-Variance*, *Transformers & Attention*, "
            "*Precision-Recall & ROC-AUC*, *K-Means Clustering*, or ask for your *Performance Diagnostic* or *Weekly Study Plan*."
        )

    actions = [
        {"label": "Explore Course Curriculum", "route": "/courses"},
        {"label": "Practice Concept Assessments", "route": "/assessments"},
    ]
    return {"answer": answer, "intent": intent, "citations": citations, "suggested_actions": actions}
