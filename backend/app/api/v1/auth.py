from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    extract_client_ip,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.models import (
    AuditLog,
    Concept,
    ConceptMastery,
    Course,
    Enrollment,
    StudentProfile,
    User,
    WeeklyTelemetry,
)
from app.db.session import get_db
from app.ml.model_registry import refresh_student_predictions
from app.schemas.domain import AuthResponse, LoginRequest, RegisterRequest, UserSummary

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_user_summary(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        avatar_initials=user.avatar_initials,
        department=user.department,
        student_profile_id=user.student_profile.id if user.student_profile else None,
        student_code=user.student_profile.student_code if user.student_profile else None,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            user_id=user.id,
            action="USER_LOGIN",
            resource_type="auth",
            resource_id=str(user.id),
            details=f"Authenticated {user.role} session for {user.email}",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id), role=user.role)
    return AuthResponse(access_token=token, user=_build_user_summary(user))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    parts = [p for p in payload.full_name.strip().split() if p]
    initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()[:4]

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role="student",
        avatar_initials=initials,
        department="AI & Data Sciences",
        is_active=True,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()

    next_seq = db.query(StudentProfile).count() + 101
    profile = StudentProfile(
        user_id=user.id,
        student_code=f"GAI-2026-{next_seq:04d}",
        cohort=payload.cohort,
        program_track=payload.program_track,
        semester=1,
        study_goal_hours_weekly=12.0,
        attendance_rate=88.0,
        engagement_index=74.0,
        assignment_timeliness=85.0,
        current_gpa=3.25,
    )
    db.add(profile)
    db.flush()

    # Enroll new student in initial foundational courses and baseline mastery
    courses = db.query(Course).order_by(Course.id).limit(4).all()
    for course in courses:
        db.add(
            Enrollment(
                student_id=profile.id,
                course_id=course.id,
                progress_pct=15.0,
                modules_completed=1,
                current_grade=75.0,
                status="active",
            )
        )
        concepts = db.query(Concept).filter(Concept.course_id == course.id).all()
        for c in concepts:
            db.add(
                ConceptMastery(
                    student_id=profile.id,
                    concept_id=c.id,
                    mastery_score=62.0,
                    confidence=0.5,
                    attempts_count=1,
                )
            )

    now = datetime.now(timezone.utc)
    for w in range(1, 5):
        db.add(
            WeeklyTelemetry(
                student_id=profile.id,
                week_number=w,
                week_label=f"W{w:02d}",
                study_hours=11.0 + (w * 0.5),
                sessions_count=4,
                avg_quiz_score=72.0 + (w * 1.2),
                assignments_completed=2,
                attendance_pct=88.0,
                recorded_at=now - timedelta(weeks=4 - w),
            )
        )

    db.add(
        AuditLog(
            user_id=user.id,
            action="USER_REGISTER",
            resource_type="student_profile",
            resource_id=str(profile.id),
            details=f"Registered student {profile.student_code} ({user.email})",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()

    refresh_student_predictions(db, profile.id)
    db.refresh(user)

    token = create_access_token(subject=str(user.id), role=user.role)
    return AuthResponse(access_token=token, user=_build_user_summary(user))


@router.get("/me", response_model=UserSummary)
def get_me(current_user: User = Depends(get_current_user)):
    return _build_user_summary(current_user)
