from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import extract_client_ip, require_role
from app.db.models import AuditLog, Intervention, StudentProfile, User
from app.db.session import get_db
from app.schemas.domain import InterventionCreateRequest, InterventionUpdateRequest

router = APIRouter(prefix="/admin", tags=["Administration & Interventions"])


@router.get("/students")
def list_students(
    search: str = Query(default="", max_length=100),
    cohort: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    cluster_label: Optional[str] = Query(default=None),
    sort_by: str = Query(default="risk_score"),
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(StudentProfile).join(User).options(joinedload(StudentProfile.user))

    if search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            (User.full_name.ilike(term))
            | (User.email.ilike(term))
            | (StudentProfile.student_code.ilike(term))
        )
    if cohort:
        query = query.filter(StudentProfile.cohort == cohort)
    if risk_level:
        query = query.filter(StudentProfile.risk_level == risk_level)
    if cluster_label:
        query = query.filter(StudentProfile.cluster_label == cluster_label)

    sort_map = {
        "risk_score": StudentProfile.risk_score.desc(),
        "predicted_final_score": StudentProfile.predicted_final_score.desc(),
        "attendance_rate": StudentProfile.attendance_rate.asc(),
        "gpa": StudentProfile.current_gpa.desc(),
        "student_code": StudentProfile.student_code.asc(),
    }
    query = query.order_by(sort_map.get(sort_by, StudentProfile.risk_score.desc()))

    total = query.count()
    students = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "students": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "student_code": s.student_code,
                "full_name": s.user.full_name,
                "email": s.user.email,
                "avatar_initials": s.user.avatar_initials,
                "cohort": s.cohort,
                "program_track": s.program_track,
                "semester": s.semester,
                "attendance_rate": round(s.attendance_rate, 1),
                "engagement_index": round(s.engagement_index, 1),
                "assignment_timeliness": round(s.assignment_timeliness, 1),
                "current_gpa": round(s.current_gpa, 2),
                "predicted_final_score": round(s.predicted_final_score, 1),
                "risk_score": round(s.risk_score, 1),
                "risk_level": s.risk_level,
                "cluster_label": s.cluster_label,
            }
            for s in students
        ],
    }


@router.get("/interventions")
def list_interventions(
    status_filter: Optional[str] = Query(default=None),
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Intervention)
        .options(joinedload(Intervention.student).joinedload(StudentProfile.user), joinedload(Intervention.created_by))
        .order_by(Intervention.created_at.desc())
    )
    if status_filter:
        query = query.filter(Intervention.status == status_filter)

    rows = query.all()
    return {
        "interventions": [
            {
                "id": iv.id,
                "student_id": iv.student_id,
                "student_code": iv.student.student_code if iv.student else "",
                "student_name": iv.student.user.full_name if iv.student and iv.student.user else "",
                "student_risk_level": iv.student.risk_level if iv.student else "unknown",
                "intervention_type": iv.intervention_type,
                "priority": iv.priority,
                "notes": iv.notes,
                "status": iv.status,
                "created_by_name": iv.created_by.full_name if iv.created_by else "Advisor",
                "created_at": iv.created_at.isoformat(),
            }
            for iv in rows
        ]
    }


@router.post("/interventions", status_code=status.HTTP_201_CREATED)
def create_intervention(
    payload: InterventionCreateRequest,
    request: Request,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    student = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.user))
        .filter(StudentProfile.id == payload.student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    iv = Intervention(
        student_id=student.id,
        created_by_id=admin_user.id,
        intervention_type=payload.intervention_type.strip(),
        priority=payload.priority,
        notes=payload.notes.strip(),
        status="open",
    )
    db.add(iv)
    db.flush()

    db.add(
        AuditLog(
            user_id=admin_user.id,
            action="INTERVENTION_CREATED",
            resource_type="intervention",
            resource_id=str(iv.id),
            details=f"Logged {iv.priority}-priority {iv.intervention_type} for {student.student_code}",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    db.refresh(iv)

    return {
        "id": iv.id,
        "student_id": iv.student_id,
        "student_name": student.user.full_name,
        "intervention_type": iv.intervention_type,
        "priority": iv.priority,
        "notes": iv.notes,
        "status": iv.status,
        "created_at": iv.created_at.isoformat(),
    }


@router.patch("/interventions/{intervention_id}")
def update_intervention(
    intervention_id: int,
    payload: InterventionUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    iv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not iv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found.")

    iv.status = payload.status
    if payload.notes:
        iv.notes = payload.notes.strip()

    db.add(
        AuditLog(
            user_id=admin_user.id,
            action="INTERVENTION_UPDATED",
            resource_type="intervention",
            resource_id=str(iv.id),
            details=f"Updated intervention status to '{iv.status}'",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    return {"id": iv.id, "status": iv.status, "notes": iv.notes}


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(default=40, ge=1, le=200),
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit).all()
    user_ids = {l.user_id for l in logs if l.user_id is not None}
    users_map = {u.id: u.email for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return {
        "logs": [
            {
                "id": l.id,
                "user_email": users_map.get(l.user_id, "system"),
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "details": l.details,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]
    }
