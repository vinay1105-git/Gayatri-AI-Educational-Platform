from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.security import extract_client_ip, get_current_user, require_role
from app.db.models import AuditLog, StudentProfile, User
from app.db.session import get_db
from app.services.report_generator import (
    generate_cohort_csv,
    generate_cohort_executive_pdf,
    generate_student_csv,
    generate_student_report_pdf,
)

router = APIRouter(prefix="/reports", tags=["Exportable Reports"])


@router.get("/student/{student_id}/pdf")
def export_student_pdf(
    student_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_self = current_user.student_profile and current_user.student_profile.id == student_id
    if current_user.role != "admin" and not is_self:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    pdf_bytes = generate_student_report_pdf(db, student_id)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="REPORT_EXPORT_STUDENT_PDF",
            resource_type="student_report",
            resource_id=student.student_code,
            details=f"Exported PDF performance report for {student.student_code}",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Gayatri_AI_Report_{student.student_code}.pdf"'},
    )


@router.get("/student/{student_id}/csv")
def export_student_csv(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_self = current_user.student_profile and current_user.student_profile.id == student_id
    if current_user.role != "admin" and not is_self:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    csv_text = generate_student_csv(db, student_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="Gayatri_AI_Mastery_{student.student_code}.csv"'},
    )


@router.get("/cohort/pdf")
def export_cohort_pdf(
    request: Request,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    pdf_bytes = generate_cohort_executive_pdf(db)
    db.add(
        AuditLog(
            user_id=admin_user.id,
            action="REPORT_EXPORT_COHORT_PDF",
            resource_type="cohort_report",
            resource_id="institutional",
            details="Exported Executive Cohort Intelligence PDF",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="Gayatri_AI_Executive_Cohort_Report.pdf"'},
    )


@router.get("/cohort/csv")
def export_cohort_csv(
    request: Request,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    csv_text = generate_cohort_csv(db)
    db.add(
        AuditLog(
            user_id=admin_user.id,
            action="REPORT_EXPORT_COHORT_CSV",
            resource_type="cohort_report",
            resource_id="institutional",
            details="Exported Cohort Telemetry CSV",
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="Gayatri_AI_Cohort_Telemetry.csv"'},
    )
