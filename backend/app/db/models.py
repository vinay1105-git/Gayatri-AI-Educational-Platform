from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="student", index=True)
    avatar_initials: Mapped[str] = mapped_column(String(8), default="GA")
    department: Mapped[str] = mapped_column(String(120), default="AI & Data Sciences")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    cohort: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    program_track: Mapped[str] = mapped_column(String(100), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, default=1)
    study_goal_hours_weekly: Mapped[float] = mapped_column(Float, default=14.0)
    attendance_rate: Mapped[float] = mapped_column(Float, default=85.0)
    engagement_index: Mapped[float] = mapped_column(Float, default=75.0)
    assignment_timeliness: Mapped[float] = mapped_column(Float, default=82.0)
    current_gpa: Mapped[float] = mapped_column(Float, default=3.2)

    predicted_final_score: Mapped[float] = mapped_column(Float, default=76.0)
    risk_score: Mapped[float] = mapped_column(Float, default=22.0)
    risk_level: Mapped[str] = mapped_column(String(20), default="low", index=True)
    cluster_id: Mapped[int] = mapped_column(Integer, default=0)
    cluster_label: Mapped[str] = mapped_column(String(64), default="Consistent Builder")
    pca_x: Mapped[float] = mapped_column(Float, default=0.0)
    pca_y: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    concept_masteries: Mapped[list["ConceptMastery"]] = relationship(
        "ConceptMastery", back_populates="student", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["AssessmentSubmission"]] = relationship(
        "AssessmentSubmission", back_populates="student", cascade="all, delete-orphan"
    )
    weekly_telemetry: Mapped[list["WeeklyTelemetry"]] = relationship(
        "WeeklyTelemetry", back_populates="student", cascade="all, delete-orphan"
    )
    interventions: Mapped[list["Intervention"]] = relationship(
        "Intervention", back_populates="student", cascade="all, delete-orphan"
    )
    resource_interactions: Mapped[list["ResourceInteraction"]] = relationship(
        "ResourceInteraction", back_populates="student", cascade="all, delete-orphan"
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), default="Intermediate")
    credit_hours: Mapped[int] = mapped_column(Integer, default=4)
    instructor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    modules_count: Mapped[int] = mapped_column(Integer, default=8)

    concepts: Mapped[list["Concept"]] = relationship(
        "Concept", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment", back_populates="course", cascade="all, delete-orphan"
    )
    resources: Mapped[list["LearningResource"]] = relationship(
        "LearningResource", back_populates="course", cascade="all, delete-orphan"
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(48), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_weight: Mapped[float] = mapped_column(Float, default=0.5)
    prerequisite_concept_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True
    )
    key_notes: Mapped[str] = mapped_column(Text, default="")

    course: Mapped["Course"] = relationship("Course", back_populates="concepts")
    prerequisite: Mapped[Optional["Concept"]] = relationship("Concept", remote_side=[id])


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    modules_completed: Mapped[int] = mapped_column(Integer, default=0)
    current_grade: Mapped[float] = mapped_column(Float, default=75.0)
    status: Mapped[str] = mapped_column(String(32), default="active")
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")


class ConceptMastery(Base):
    __tablename__ = "concept_masteries"
    __table_args__ = (UniqueConstraint("student_id", "concept_id", name="uq_student_concept"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    mastery_score: Mapped[float] = mapped_column(Float, default=65.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.6)
    attempts_count: Mapped[int] = mapped_column(Integer, default=1)
    last_practiced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="concept_masteries")
    concept: Mapped["Concept"] = relationship("Concept")


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(48), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), default="Intermediate")
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=25)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str] = mapped_column(String(255), default="")

    course: Mapped["Course"] = relationship("Course", back_populates="resources")
    concept: Mapped["Concept"] = relationship("Concept")


class ResourceInteraction(Base):
    __tablename__ = "resource_interactions"
    __table_args__ = (UniqueConstraint("student_id", "resource_id", name="uq_student_resource"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    resource_id: Mapped[int] = mapped_column(ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="viewed")
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="resource_interactions")
    resource: Mapped["LearningResource"] = relationship("LearningResource")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(48), default="Module Exam")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=25)
    passing_score: Mapped[float] = mapped_column(Float, default=70.0)
    total_points: Mapped[float] = mapped_column(Float, default=100.0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    course: Mapped["Course"] = relationship("Course", back_populates="assessments")
    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        "AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["AssessmentSubmission"]] = relationship(
        "AssessmentSubmission", back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(24), default="medium")
    points: Mapped[float] = mapped_column(Float, default=20.0)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="questions")
    concept: Mapped["Concept"] = relationship("Concept")


class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    score_pct: Mapped[float] = mapped_column(Float, nullable=False)
    points_earned: Mapped[float] = mapped_column(Float, nullable=False)
    points_possible: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=600)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="submissions")
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="submissions")
    responses: Mapped[list["QuestionResponse"]] = relationship(
        "QuestionResponse", back_populates="submission", cascade="all, delete-orphan"
    )


class QuestionResponse(Base):
    __tablename__ = "question_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    submission: Mapped["AssessmentSubmission"] = relationship("AssessmentSubmission", back_populates="responses")
    question: Mapped["AssessmentQuestion"] = relationship("AssessmentQuestion")


class WeeklyTelemetry(Base):
    __tablename__ = "weekly_telemetry"
    __table_args__ = (UniqueConstraint("student_id", "week_number", name="uq_student_week"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    week_label: Mapped[str] = mapped_column(String(24), nullable=False)
    study_hours: Mapped[float] = mapped_column(Float, default=10.0)
    sessions_count: Mapped[int] = mapped_column(Integer, default=4)
    avg_quiz_score: Mapped[float] = mapped_column(Float, default=75.0)
    assignments_completed: Mapped[int] = mapped_column(Integer, default=2)
    attendance_pct: Mapped[float] = mapped_column(Float, default=85.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="weekly_telemetry")


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    intervention_type: Mapped[str] = mapped_column(String(80), nullable=False)
    priority: Mapped[str] = mapped_column(String(24), default="medium")
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="interventions")
    created_by: Mapped[Optional["User"]] = relationship("User")


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_actions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
