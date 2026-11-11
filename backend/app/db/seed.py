from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Dict, List
import numpy as np
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.curriculum_data import ASSESSMENT_QUESTIONS_BY_COURSE, COURSES_CATALOG
from app.db.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentSubmission,
    AuditLog,
    Concept,
    ConceptMastery,
    Course,
    Enrollment,
    Intervention,
    LearningResource,
    QuestionResponse,
    ResourceInteraction,
    StudentProfile,
    User,
    WeeklyTelemetry,
)
from app.ml.model_registry import retrain_all_models

logger = logging.getLogger("gayatri_ai.seed")

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Diya", "Saanvi", "Aanya", "Aadhya", "Pari", "Anika", "Navya", "Myra", "Sara", "Ira",
    "Kabir", "Rohan", "Nikhil", "Siddharth", "Pranav", "Karthik", "Dev", "Harsh", "Tanvi", "Meera",
    "Neha", "Pooja", "Riya", "Sneha", "Shreya", "Kriti", "Nandini", "Tara", "Maya", "Zoya",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Iyer", "Nair", "Kulkarni", "Deshmukh", "Reddy", "Mehta", "Kapoor",
    "Gupta", "Joshi", "Rao", "Bhat", "Menon", "Choudhary", "Malhotra", "Sinha", "Banerjee", "Das",
    "Agarwal", "Saxena", "Bansal", "Chopra", "Bhattacharya", "Sen", "Bose", "Krishnan", "Mishra", "Tiwari",
]

COHORTS = [
    "Fall 2026 - AI Engineering",
    "Spring 2026 - Applied ML",
    "Summer 2026 - Data Systems",
    "Fall 2026 - MLOps Track",
]

TRACKS = [
    "Applied Artificial Intelligence",
    "Machine Learning Systems",
    "Data Engineering & Analytics",
    "Production MLOps",
]

RESOURCE_TYPES = ["Interactive Lab", "Deep Dive Article", "Video Lecture", "Guided Drill", "Case Study"]


def seed_database(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    logger.info("Seeding Gayatri AI enterprise educational dataset...")
    rng = np.random.default_rng(42)
    now = datetime.now(timezone.utc)

    # 1. Create Admin Account
    admin_user = User(
        email="admin@gayatri-ai.edu",
        full_name="Dr. Kavita Rao",
        hashed_password=hash_password("Admin@Gayatri2026"),
        role="admin",
        avatar_initials="KR",
        department="Academic Intelligence & AI Curriculum",
        is_active=True,
        created_at=now - timedelta(days=90),
        last_login_at=now - timedelta(hours=2),
    )
    db.add(admin_user)
    db.flush()

    # 2. Create Courses, Concepts, Learning Resources, and Assessments
    concept_by_code: Dict[str, Concept] = {}
    courses_list: List[Course] = []
    resources_by_course: Dict[int, List[LearningResource]] = {}
    assessments_by_course: Dict[int, Assessment] = {}
    questions_by_assessment: Dict[int, List[AssessmentQuestion]] = {}

    for c_idx, c_data in enumerate(COURSES_CATALOG):
        course = Course(
            code=c_data["code"],
            title=c_data["title"],
            category=c_data["category"],
            difficulty=c_data["difficulty"],
            credit_hours=c_data["credit_hours"],
            instructor_name=c_data["instructor_name"],
            description=c_data["description"],
            modules_count=c_data["modules_count"],
        )
        db.add(course)
        db.flush()
        courses_list.append(course)
        resources_by_course[course.id] = []

        # First pass: create concepts
        for k_idx, k_data in enumerate(c_data["concepts"]):
            concept = Concept(
                course_id=course.id,
                code=k_data["code"],
                name=k_data["name"],
                description=k_data["description"],
                difficulty_weight=k_data["difficulty_weight"],
                prerequisite_concept_id=None,
                key_notes=k_data["key_notes"],
            )
            db.add(concept)
            db.flush()
            concept_by_code[k_data["code"]] = concept

            # Create 1 rich learning resource per concept
            res_type = RESOURCE_TYPES[(c_idx + k_idx) % len(RESOURCE_TYPES)]
            res_diff = "Foundational" if k_data["difficulty_weight"] < 0.55 else (
                "Intermediate" if k_data["difficulty_weight"] < 0.72 else "Advanced"
            )
            resource = LearningResource(
                course_id=course.id,
                concept_id=concept.id,
                title=f"{k_data['name']}: Applied {res_type}",
                resource_type=res_type,
                difficulty=res_diff,
                estimated_minutes=int(20 + k_data["difficulty_weight"] * 25),
                summary=f"Structured {res_type.lower()} mastering {k_data['name']} within {c_data['code']}.",
                content_body=(
                    f"Module Focus: {k_data['description']}\n\n"
                    f"Key Mathematical & Engineering Principles:\n{k_data['key_notes']}\n\n"
                    f"Practice Checklist:\n"
                    f"- Verify conceptual assumptions and edge cases on small synthetic inputs.\n"
                    f"- Trace parameter sensitivity and compare baseline vs regularized behavior.\n"
                    f"- Complete the associated diagnostic check in {c_data['code']} Assessment."
                ),
                tags=f"{c_data['code']}, {c_data['category']}, {k_data['name']}",
            )
            db.add(resource)
            db.flush()
            resources_by_course[course.id].append(resource)

        # Create Assessment for this course
        q_templates = ASSESSMENT_QUESTIONS_BY_COURSE[c_data["code"]]
        assessment = Assessment(
            course_id=course.id,
            title=f"{c_data['code']} Comprehensive Mastery Evaluation",
            assessment_type="Module Exam" if c_idx % 2 == 0 else "Diagnostic Quiz",
            description=f"Evaluates conceptual understanding and applied reasoning across {c_data['title']}.",
            duration_minutes=20,
            passing_score=70.0,
            total_points=float(len(q_templates) * 20),
            is_published=True,
            created_by_id=admin_user.id,
            created_at=now - timedelta(days=45),
        )
        db.add(assessment)
        db.flush()
        assessments_by_course[course.id] = assessment
        questions_by_assessment[assessment.id] = []

        for q_data in q_templates:
            q = AssessmentQuestion(
                assessment_id=assessment.id,
                concept_id=concept_by_code[q_data["concept_code"]].id,
                prompt=q_data["prompt"],
                options_json=json.dumps(q_data["options"]),
                correct_index=q_data["correct_index"],
                explanation=q_data["explanation"],
                difficulty=q_data["difficulty"],
                points=20.0,
            )
            db.add(q)
            db.flush()
            questions_by_assessment[assessment.id].append(q)

    # Link concept prerequisites after all concepts exist
    for c_data in COURSES_CATALOG:
        for k_data in c_data["concepts"]:
            if k_data["prereq_code"] and k_data["prereq_code"] in concept_by_code:
                concept_by_code[k_data["code"]].prerequisite_concept_id = concept_by_code[k_data["prereq_code"]].id
    db.flush()

    # 3. Create 100 Realistic Students (2 Featured Demo Profiles + 98 Cohort Learners)
    shared_student_hash = hash_password("Student@2026")

    featured_specs = [
        {
            "full_name": "Ananya Sharma",
            "email": "ananya.sharma@gayatri-ai.edu",
            "archetype": "consistent",
            "cohort": COHORTS[0],
            "track": TRACKS[0],
            "semester": 3,
        },
        {
            "full_name": "Rohan Verma",
            "email": "rohan.verma@gayatri-ai.edu",
            "archetype": "at_risk",
            "cohort": COHORTS[1],
            "track": TRACKS[1],
            "semester": 2,
        },
    ]

    archetype_choices = ["accelerated", "consistent", "developing", "at_risk"]
    archetype_probs = [0.24, 0.34, 0.24, 0.18]

    student_profiles: List[StudentProfile] = []
    used_emails = {spec["email"] for spec in featured_specs}

    for idx in range(100):
        if idx < len(featured_specs):
            spec = featured_specs[idx]
            full_name = spec["full_name"]
            email = spec["email"]
            archetype = spec["archetype"]
            cohort = spec["cohort"]
            track = spec["track"]
            semester = spec["semester"]
        else:
            fname = FIRST_NAMES[(idx * 7 + int(rng.integers(0, 10))) % len(FIRST_NAMES)]
            lname = LAST_NAMES[(idx * 11 + int(rng.integers(0, 10))) % len(LAST_NAMES)]
            full_name = f"{fname} {lname}"
            base_email = f"{fname.lower()}.{lname.lower()}.{idx + 1}@gayatri-ai.edu"
            while base_email in used_emails:
                base_email = f"{fname.lower()}.{lname.lower()}.{idx + 100}@gayatri-ai.edu"
            email = base_email
            used_emails.add(email)
            archetype = str(rng.choice(archetype_choices, p=archetype_probs))
            cohort = COHORTS[idx % len(COHORTS)]
            track = TRACKS[idx % len(TRACKS)]
            semester = int(rng.integers(1, 5))

        parts = full_name.split()
        initials = (parts[0][0] + parts[-1][0]).upper()

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=shared_student_hash,
            role="student",
            avatar_initials=initials,
            department="AI & Data Sciences",
            is_active=True,
            created_at=now - timedelta(days=75),
            last_login_at=now - timedelta(hours=int(rng.integers(1, 96))),
        )
        db.add(user)
        db.flush()

        # Archetype behavioral parameter centers with realistic stochastic spread
        if archetype == "accelerated":
            base_ability = float(np.clip(rng.normal(86.0, 4.5), 74, 96))
            att = float(np.clip(rng.normal(93.0, 3.5), 82, 99))
            eng = float(np.clip(rng.normal(88.0, 4.5), 76, 98))
            timely = float(np.clip(rng.normal(92.0, 4.0), 80, 99))
            hours_mean = float(np.clip(rng.normal(16.5, 2.2), 11, 22))
            hours_vol = 1.4
            slope = float(rng.normal(0.65, 0.35))
        elif archetype == "consistent":
            base_ability = float(np.clip(rng.normal(77.5, 5.2), 65, 89))
            att = float(np.clip(rng.normal(87.0, 4.5), 74, 96))
            eng = float(np.clip(rng.normal(76.5, 5.5), 62, 90))
            timely = float(np.clip(rng.normal(84.5, 5.0), 70, 95))
            hours_mean = float(np.clip(rng.normal(13.0, 2.0), 8, 18))
            hours_vol = 1.8
            slope = float(rng.normal(0.45, 0.45))
        elif archetype == "developing":
            base_ability = float(np.clip(rng.normal(69.5, 5.8), 55, 82))
            att = float(np.clip(rng.normal(79.0, 5.5), 64, 90))
            eng = float(np.clip(rng.normal(65.0, 6.5), 50, 80))
            timely = float(np.clip(rng.normal(73.0, 6.5), 55, 88))
            hours_mean = float(np.clip(rng.normal(9.5, 2.2), 5, 14))
            hours_vol = 2.9
            slope = float(rng.normal(0.55, 0.65))
        else:  # at_risk
            base_ability = float(np.clip(rng.normal(55.5, 6.5), 38, 70))
            att = float(np.clip(rng.normal(64.5, 7.5), 44, 80))
            eng = float(np.clip(rng.normal(49.0, 7.5), 30, 68))
            timely = float(np.clip(rng.normal(56.0, 8.5), 35, 76))
            hours_mean = float(np.clip(rng.normal(6.0, 1.9), 2.5, 10.5))
            hours_vol = 2.7
            slope = float(rng.normal(-0.85, 0.55))

        gpa = float(np.clip(1.6 + (base_ability / 100.0) * 2.35 + rng.normal(0, 0.12), 1.4, 3.98))
        profile = StudentProfile(
            user_id=user.id,
            student_code=f"GAI-2026-{101 + idx:04d}",
            cohort=cohort,
            program_track=track,
            semester=semester,
            study_goal_hours_weekly=14.0 if archetype != "accelerated" else 16.0,
            attendance_rate=round(att, 1),
            engagement_index=round(eng, 1),
            assignment_timeliness=round(timely, 1),
            current_gpa=round(gpa, 2),
        )
        db.add(profile)
        db.flush()
        student_profiles.append(profile)

        # 10-Week Longitudinal Telemetry
        for w in range(1, 11):
            w_hours = float(np.clip(hours_mean + rng.normal(0, hours_vol), 1.5, 26.0))
            w_score = float(np.clip(base_ability - 3.5 + slope * (w - 5) + rng.normal(0, 3.8), 30.0, 99.0))
            w_sessions = int(np.clip(round(w_hours / 2.4 + rng.normal(0, 1)), 1, 12))
            w_assign = int(np.clip(round((timely / 35.0) + rng.normal(0, 0.6)), 0, 4))
            w_att = float(np.clip(att + rng.normal(0, 4.0), 35.0, 100.0))
            db.add(
                WeeklyTelemetry(
                    student_id=profile.id,
                    week_number=w,
                    week_label=f"W{w:02d}",
                    study_hours=round(w_hours, 2),
                    sessions_count=w_sessions,
                    avg_quiz_score=round(w_score, 2),
                    assignments_completed=w_assign,
                    attendance_pct=round(w_att, 1),
                    recorded_at=now - timedelta(weeks=10 - w),
                )
            )

        # Enroll in 4 courses (featured students enrolled in all 6 for full exploration!)
        if idx < 2:
            enrolled_courses = courses_list
        else:
            chosen_indices = sorted(rng.choice(len(courses_list), size=4, replace=False))
            enrolled_courses = [courses_list[i] for i in chosen_indices]

        for course in enrolled_courses:
            # Determine realistic course progress & grade
            progress = float(np.clip(rng.normal(76 if archetype in ("accelerated", "consistent") else 54, 14), 20, 100))
            modules_done = int(round((progress / 100.0) * course.modules_count))
            grade = float(np.clip(base_ability + rng.normal(0, 4.8), 35, 98))
            status = "completed" if progress >= 98 else ("at_risk" if grade < 64 else "active")
            db.add(
                Enrollment(
                    student_id=profile.id,
                    course_id=course.id,
                    progress_pct=round(progress, 1),
                    modules_completed=modules_done,
                    current_grade=round(grade, 1),
                    status=status,
                    last_accessed_at=now - timedelta(hours=int(rng.integers(2, 120))),
                )
            )

            # Concept Masteries for each concept in this course
            course_concepts = [c for c in concept_by_code.values() if c.course_id == course.id]
            for concept in course_concepts:
                difficulty_penalty = (concept.difficulty_weight - 0.55) * 18.0
                # For featured student Ananya (idx=0), introduce authentic targeted gaps in Backprop & Attention
                if idx == 0 and concept.code in ("DL-BP", "NLP-ATT", "ML-BIAS"):
                    m_score = float(np.clip(rng.normal(56.0, 3.0), 48, 63))
                else:
                    m_score = float(np.clip(base_ability - difficulty_penalty + rng.normal(0, 6.0), 28.0, 97.5))

                db.add(
                    ConceptMastery(
                        student_id=profile.id,
                        concept_id=concept.id,
                        mastery_score=round(m_score, 1),
                        confidence=round(float(np.clip(0.45 + (m_score / 200.0), 0.35, 0.96)), 2),
                        attempts_count=int(rng.integers(2, 8)),
                        last_practiced_at=now - timedelta(days=int(rng.integers(1, 21))),
                    )
                )

            # Resource interactions
            for res in resources_by_course[course.id]:
                if archetype == "accelerated" and rng.random() < 0.65:
                    r_status = "completed"
                elif archetype == "consistent" and rng.random() < 0.42:
                    r_status = "completed"
                elif rng.random() < 0.22:
                    r_status = "viewed"
                else:
                    continue
                db.add(
                    ResourceInteraction(
                        student_id=profile.id,
                        resource_id=res.id,
                        status=r_status,
                        rating=int(rng.integers(4, 6)) if r_status == "completed" else None,
                        updated_at=now - timedelta(days=int(rng.integers(1, 25))),
                    )
                )

            # Historical Assessment Submissions (leave last 2 assessments open for featured student Ananya so she can take new ones immediately, while still having 4 completed!)
            should_submit = not (idx == 0 and course.code in ("DL-301", "NLP-305"))
            if should_submit and rng.random() < (0.95 if idx < 2 else 0.85):
                assessment = assessments_by_course[course.id]
                qs = questions_by_assessment[assessment.id]
                sub = AssessmentSubmission(
                    assessment_id=assessment.id,
                    student_id=profile.id,
                    score_pct=0.0,
                    points_earned=0.0,
                    points_possible=assessment.total_points,
                    passed=False,
                    time_spent_seconds=int(rng.integers(420, 1140)),
                    submitted_at=now - timedelta(days=int(rng.integers(3, 35))),
                )
                db.add(sub)
                db.flush()

                earned = 0.0
                for q in qs:
                    # Probability of answering correctly depends on latent ability minus item difficulty
                    diff_shift = {"easy": 10.0, "medium": 0.0, "hard": -12.0}.get(q.difficulty, 0.0)
                    p_correct = float(np.clip((base_ability + diff_shift) / 100.0, 0.18, 0.96))
                    is_correct = bool(rng.random() < p_correct)
                    if is_correct:
                        earned += q.points
                        sel = q.correct_index
                    else:
                        wrong_opts = [opt_i for opt_i in range(4) if opt_i != q.correct_index]
                        sel = int(rng.choice(wrong_opts))

                    db.add(
                        QuestionResponse(
                            submission_id=sub.id,
                            question_id=q.id,
                            selected_index=sel,
                            is_correct=is_correct,
                        )
                    )
                sub.points_earned = earned
                sub.score_pct = round((earned / assessment.total_points) * 100.0, 2)
                sub.passed = sub.score_pct >= assessment.passing_score

    db.flush()

    # 4. Train all ML Models cleanly on the populated cohort dataset
    retrain_all_models(db)

    # 5. Create realistic academic interventions for highest-risk students
    high_risk_students = (
        db.query(StudentProfile)
        .filter(StudentProfile.risk_level == "high")
        .order_by(StudentProfile.risk_score.desc())
        .limit(6)
        .all()
    )
    intervention_templates = [
        ("Prerequisite Review Plan", "high", "Assigned targeted Linear Algebra & Gradient Descent reinforcement before DL-301 midterm."),
        ("Academic Coaching", "high", "Scheduled 1:1 advisor check-in to address declining weekly session cadence and attendance friction."),
        ("Workload Calibration", "medium", "Recommended structured 12-hour weekly study blocks and milestone reminders."),
    ]
    for i_idx, stu in enumerate(high_risk_students):
        i_type, prio, note = intervention_templates[i_idx % len(intervention_templates)]
        db.add(
            Intervention(
                student_id=stu.id,
                created_by_id=admin_user.id,
                intervention_type=i_type,
                priority=prio,
                notes=note,
                status="in_progress" if i_idx % 2 == 0 else "open",
                created_at=now - timedelta(days=int(rng.integers(1, 10))),
            )
        )

    db.add(
        AuditLog(
            user_id=admin_user.id,
            action="SYSTEM_INITIALIZATION",
            resource_type="platform",
            resource_id="gayatri_ai",
            details="Initial cohort telemetry seeded and ML pipelines trained (100 learners, 6 courses, 24 concepts).",
            ip_address="127.0.0.1",
            created_at=now,
        )
    )
    db.commit()
    logger.info("Seed completed successfully.")
