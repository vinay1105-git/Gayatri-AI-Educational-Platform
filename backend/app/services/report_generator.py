import csv
from datetime import datetime, timezone
import io
from typing import Any, Dict, List
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models import (
    AssessmentSubmission,
    Concept,
    ConceptMastery,
    Intervention,
    StudentProfile,
)
from app.ml.knowledge_tracing import forecast_score_trajectory
from app.ml.model_registry import get_loaded_models, get_student_diagnostics
from app.ml.recommender import generate_personalized_recommendations


def _render_chart_to_buffer(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _build_student_trajectory_chart(trajectory: List[Dict[str, Any]]) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(6.8, 2.5), facecolor="#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    obs = [p for p in trajectory if not p["is_forecast"]]
    fc = [p for p in trajectory if p["is_forecast"] or p["projected_score"] is not None]

    if obs:
        ax.plot(
            [p["week_label"] for p in obs],
            [p["actual_score"] for p in obs],
            marker="o",
            linewidth=2.2,
            color="#0891B2",
            label="Observed Weekly Quiz Avg",
        )
    if len(fc) >= 2:
        x_fc = [p["week_label"] for p in fc]
        y_fc = [p["projected_score"] for p in fc]
        ax.plot(x_fc, y_fc, linestyle="--", marker="s", linewidth=2.0, color="#10B981", label="Ridge Forecast")
        lower = [p["lower_bound"] if p["lower_bound"] is not None else p["projected_score"] for p in fc]
        upper = [p["upper_bound"] if p["upper_bound"] is not None else p["projected_score"] for p in fc]
        ax.fill_between(x_fc, lower, upper, color="#10B981", alpha=0.14, label="Forecast Band")

    ax.set_ylim(30, 102)
    ax.set_ylabel("Score (%)", fontsize=8.5, color="#334155")
    ax.set_title("10-Week Performance Trajectory & 4-Week Projection", fontsize=10, fontweight="bold", color="#0F172A")
    ax.grid(True, linestyle=":", alpha=0.6, color="#CBD5E1")
    ax.tick_params(axis="both", labelsize=7.5, colors="#475569")
    ax.legend(fontsize=7.5, loc="lower right", frameon=True)
    return _render_chart_to_buffer(fig)


def _build_cohort_risk_and_cluster_chart(students: List[StudentProfile]) -> io.BytesIO:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.6), facecolor="#FFFFFF")

    # Left: Risk Tier distribution
    tiers = ["low", "moderate", "high"]
    counts = [sum(1 for s in students if s.risk_level == t) for t in tiers]
    bar_colors = ["#10B981", "#F59E0B", "#EF4444"]
    ax1.bar(["Low Risk", "Moderate Risk", "High Risk"], counts, color=bar_colors, width=0.55)
    ax1.set_title("Cohort Risk Tier Distribution", fontsize=9.5, fontweight="bold", color="#0F172A")
    ax1.set_ylabel("Students", fontsize=8, color="#334155")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.tick_params(labelsize=8, colors="#334155")

    # Right: PCA Cluster scatter
    palette = {
        "Accelerated Mastery": "#0891B2",
        "Consistent Builder": "#10B981",
        "Developing Momentum": "#F59E0B",
        "Targeted Support Needed": "#EF4444",
    }
    seen_labels = set()
    for s in students:
        lbl = s.cluster_label
        color = palette.get(lbl, "#64748B")
        ax2.scatter(
            s.pca_x,
            s.pca_y,
            c=color,
            s=24,
            alpha=0.82,
            label=lbl if lbl not in seen_labels else None,
        )
        seen_labels.add(lbl)
    ax2.set_title("K-Means Learner Personas (PCA 2D)", fontsize=9.5, fontweight="bold", color="#0F172A")
    ax2.set_xlabel("PC1", fontsize=8, color="#334155")
    ax2.set_ylabel("PC2", fontsize=8, color="#334155")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.tick_params(labelsize=7.5, colors="#334155")
    ax2.legend(fontsize=6.5, loc="best", frameon=True)

    plt.tight_layout()
    return _render_chart_to_buffer(fig)


def _pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BrandTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BrandSubtitle",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=11.5,
            textColor=colors.HexColor("#0E7490"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1E293B"),
        )
    )
    return styles


def generate_student_report_pdf(db: Session, student_id: int) -> bytes:
    student = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.user),
            selectinload(StudentProfile.enrollments),
            selectinload(StudentProfile.concept_masteries).joinedload(ConceptMastery.concept),
            selectinload(StudentProfile.submissions).joinedload(AssessmentSubmission.assessment),
            selectinload(StudentProfile.weekly_telemetry),
        )
        .filter(StudentProfile.id == student_id)
        .first()
    )
    if not student:
        raise ValueError("Student profile not found.")

    diag = get_student_diagnostics(db, student.id)
    trajectory = forecast_score_trajectory(student.weekly_telemetry, horizon_weeks=4)
    recs = generate_personalized_recommendations(db, student.id, limit=4)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = _pdf_styles()
    story: List[Any] = []

    generated_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph("Gayatri AI — Student Performance Intelligence Report", styles["BrandTitle"]))
    story.append(
        Paragraph(
            f"Learner: <b>{student.user.full_name}</b> ({student.student_code}) &nbsp;|&nbsp; "
            f"Cohort: {student.cohort} &nbsp;|&nbsp; Generated: {generated_ts}",
            styles["BrandSubtitle"],
        )
    )

    # Executive Summary KPI Table
    kpi_data = [
        ["Metric", "Value", "Metric", "Value"],
        [
            "Projected Final Score",
            f"{diag['prediction']['predicted_final_score']:.1f}%",
            "Risk Classification",
            f"{diag['prediction']['risk_level'].upper()} ({diag['prediction']['risk_score']:.1f}%)",
        ],
        [
            "Learner Persona Cluster",
            diag["cluster"]["cluster_label"],
            "Current Cumulative GPA",
            f"{student.current_gpa:.2f} / 4.00",
        ],
        [
            "Attendance Rate",
            f"{student.attendance_rate:.1f}%",
            "Engagement Index",
            f"{student.engagement_index:.1f} / 100",
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[1.65 * inch, 1.95 * inch, 1.65 * inch, 1.95 * inch])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (2, 1), (2, -1), colors.HexColor("#F1F5F9")),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # Trajectory Chart
    if trajectory:
        chart_buf = _build_student_trajectory_chart(trajectory)
        story.append(Image(chart_buf, width=6.9 * inch, height=2.45 * inch))
        story.append(Spacer(1, 8))

    # Predictive Drivers
    story.append(Paragraph("1. Predictive Risk & Outcome Drivers", styles["SectionHeading"]))
    driver_rows = [["Factor", "Learner Value", "Cohort Mean", "Directional Effect"]]
    for d in diag["prediction"]["drivers"]:
        effect_label = (
            "Risk Increasing" if d["effect"] == "risk_increasing" else ("Protective" if d["effect"] == "protective" else "Neutral")
        )
        driver_rows.append([d["label"], f"{d['student_value']}", f"{d['cohort_mean']}", effect_label])
    driver_table = Table(driver_rows, colWidths=[2.5 * inch, 1.4 * inch, 1.4 * inch, 1.9 * inch])
    driver_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(driver_table)

    # Concept Mastery Highlights
    story.append(Paragraph("2. Lowest Concept Masteries & Targeted Recommendations", styles["SectionHeading"]))
    rec_rows = [["Recommended Module", "Concept", "Current Mastery", "Action Rationale"]]
    for r in recs:
        rec_rows.append(
            [
                Paragraph(r["title"], styles["BodySmall"]),
                Paragraph(r["concept_name"], styles["BodySmall"]),
                f"{r['current_concept_mastery']:.1f}%",
                Paragraph(r["rationale"], styles["BodySmall"]),
            ]
        )
    rec_table = Table(rec_rows, colWidths=[1.9 * inch, 1.5 * inch, 1.0 * inch, 2.8 * inch])
    rec_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E7490")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(rec_table)

    # Recent Assessment Submissions
    story.append(Paragraph("3. Recent Assessment Transcript", styles["SectionHeading"]))
    subs = sorted(student.submissions, key=lambda s: s.submitted_at, reverse=True)[:6]
    sub_rows = [["Assessment", "Score (%)", "Status", "Submitted"]]
    for s in subs:
        sub_rows.append(
            [
                s.assessment.title if s.assessment else "Assessment",
                f"{s.score_pct:.1f}%",
                "Passed" if s.passed else "Needs Review",
                s.submitted_at.strftime("%Y-%m-%d"),
            ]
        )
    if len(sub_rows) == 1:
        sub_rows.append(["No submissions recorded", "-", "-", "-"])
    sub_table = Table(sub_rows, colWidths=[3.3 * inch, 1.1 * inch, 1.4 * inch, 1.4 * inch])
    sub_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(sub_table)

    doc.build(story)
    return buf.getvalue()


def generate_cohort_executive_pdf(db: Session) -> bytes:
    students = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .order_by(StudentProfile.risk_score.desc())
        .all()
    )
    models_data = get_loaded_models(db)
    metrics = models_data["metrics"]
    risk_m = metrics["risk_model"]
    cluster_m = metrics["clustering_model"]

    total = len(students)
    high_cnt = sum(1 for s in students if s.risk_level == "high")
    mod_cnt = sum(1 for s in students if s.risk_level == "moderate")
    avg_pred = float(np.mean([s.predicted_final_score for s in students])) if students else 0.0
    avg_att = float(np.mean([s.attendance_rate for s in students])) if students else 0.0
    open_interv = db.query(Intervention).filter(Intervention.status != "resolved").count()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = _pdf_styles()
    story: List[Any] = []

    generated_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph("Gayatri AI — Executive Cohort Intelligence Report", styles["BrandTitle"]))
    story.append(
        Paragraph(
            f"Institutional Analytics Summary &nbsp;|&nbsp; Active Learners: <b>{total}</b> &nbsp;|&nbsp; Generated: {generated_ts}",
            styles["BrandSubtitle"],
        )
    )

    kpi_rows = [
        ["Institutional KPI", "Measured Value", "ML Model Telemetry", "Measured Value"],
        [
            "Mean Projected Score",
            f"{avg_pred:.1f}%",
            "Active Risk Classifier",
            risk_m["selected_classifier"],
        ],
        [
            "High Risk / Moderate Risk",
            f"{high_cnt} High / {mod_cnt} Moderate",
            "CV Accuracy / F1 / ROC-AUC",
            f"{risk_m['classifier_metrics']['accuracy']*100:.1f}% / {risk_m['classifier_metrics']['f1_score']:.3f} / {risk_m['classifier_metrics']['roc_auc']:.3f}",
        ],
        [
            "Mean Attendance Rate",
            f"{avg_att:.1f}%",
            "K-Means Silhouette Score",
            f"{cluster_m['silhouette_score']:.3f} (k={cluster_m['n_clusters']})",
        ],
        [
            "Open Interventions",
            str(open_interv),
            "Score Regressor RMSE / R2",
            f"{risk_m['regressor_metrics']['rmse']:.2f} / {risk_m['regressor_metrics']['r2_score']:.3f}",
        ],
    ]
    kpi_table = Table(kpi_rows, colWidths=[1.65 * inch, 1.85 * inch, 1.85 * inch, 1.85 * inch])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (2, 1), (2, -1), colors.HexColor("#F1F5F9")),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 5.5),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    if students:
        chart_buf = _build_cohort_risk_and_cluster_chart(students)
        story.append(Image(chart_buf, width=7.0 * inch, height=2.55 * inch))
        story.append(Spacer(1, 8))

    story.append(Paragraph("1. Priority At-Risk Intervention Roster (Top 10)", styles["SectionHeading"]))
    roster_rows = [["Student Code", "Full Name", "Cohort", "Persona", "Pred Score", "Risk Score"]]
    for s in students[:10]:
        roster_rows.append(
            [
                s.student_code,
                s.user.full_name,
                s.cohort.split(" - ")[0],
                s.cluster_label,
                f"{s.predicted_final_score:.1f}%",
                f"{s.risk_score:.1f}% ({s.risk_level.upper()})",
            ]
        )
    roster_table = Table(roster_rows, colWidths=[1.1 * inch, 1.5 * inch, 1.0 * inch, 1.45 * inch, 0.9 * inch, 1.25 * inch])
    roster_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E7490")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 4.5),
            ]
        )
    )
    story.append(roster_table)

    # Concept mastery summary
    concepts = db.query(Concept).all()
    concept_avgs = []
    for c in concepts:
        ms = db.query(ConceptMastery).filter(ConceptMastery.concept_id == c.id).all()
        if ms:
            concept_avgs.append((c.code, c.name, float(np.mean([m.mastery_score for m in ms]))))
    concept_avgs.sort(key=lambda x: x[2])

    story.append(Paragraph("2. Lowest Cohort Mastery Concepts Requiring Curriculum Calibration", styles["SectionHeading"]))
    c_rows = [["Code", "Concept Name", "Cohort Mean Mastery"]]
    for code, cname, avg_m in concept_avgs[:6]:
        c_rows.append([code, cname, f"{avg_m:.1f}%"])
    c_table = Table(c_rows, colWidths=[1.4 * inch, 4.3 * inch, 1.5 * inch])
    c_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(c_table)

    doc.build(story)
    return buf.getvalue()


def generate_cohort_csv(db: Session) -> str:
    students = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .order_by(StudentProfile.student_code)
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "student_code",
            "full_name",
            "email",
            "cohort",
            "program_track",
            "semester",
            "gpa",
            "attendance_rate",
            "engagement_index",
            "assignment_timeliness",
            "predicted_final_score",
            "risk_score",
            "risk_level",
            "cluster_label",
        ]
    )
    for s in students:
        writer.writerow(
            [
                s.student_code,
                s.user.full_name,
                s.user.email,
                s.cohort,
                s.program_track,
                s.semester,
                round(s.current_gpa, 2),
                round(s.attendance_rate, 1),
                round(s.engagement_index, 1),
                round(s.assignment_timeliness, 1),
                round(s.predicted_final_score, 1),
                round(s.risk_score, 1),
                s.risk_level,
                s.cluster_label,
            ]
        )
    return output.getvalue()


def generate_student_csv(db: Session, student_id: int) -> str:
    student = (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.user),
            selectinload(StudentProfile.concept_masteries)
            .joinedload(ConceptMastery.concept)
            .joinedload(Concept.course),
        )
        .filter(StudentProfile.id == student_id)
        .first()
    )
    if not student:
        raise ValueError("Student not found.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["student_code", "full_name", "course_code", "concept_code", "concept_name", "mastery_score", "confidence", "attempts"])
    for m in sorted(student.concept_masteries, key=lambda x: x.mastery_score):
        writer.writerow(
            [
                student.student_code,
                student.user.full_name,
                m.concept.course.code if m.concept and m.concept.course else "",
                m.concept.code if m.concept else "",
                m.concept.name if m.concept else "",
                round(m.mastery_score, 2),
                round(m.confidence, 3),
                m.attempts_count,
            ]
        )
    return output.getvalue()
