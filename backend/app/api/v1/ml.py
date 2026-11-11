from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.security import extract_client_ip, get_current_user, require_role
from app.db.models import AuditLog, User
from app.db.session import get_db
from app.ml.model_registry import get_loaded_models, retrain_all_models

router = APIRouter(prefix="/ml", tags=["ML Pipeline & Evaluation"])


@router.get("/metrics")
def get_ml_evaluation_metrics(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    loaded = get_loaded_models(db)
    return loaded["metrics"]


@router.post("/retrain")
def trigger_model_retraining(
    request: Request,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    metrics = retrain_all_models(db)
    db.add(
        AuditLog(
            user_id=admin_user.id,
            action="ML_RETRAIN",
            resource_type="ml_pipeline",
            resource_id="gayatri_models",
            details=(
                f"Retrained on {metrics['cohort_size']} students | "
                f"Classifier={metrics['risk_model']['selected_classifier']} "
                f"F1={metrics['risk_model']['classifier_metrics']['f1_score']}"
            ),
            ip_address=extract_client_ip(request),
        )
    )
    db.commit()
    return {"status": "retrained", "metrics": metrics}
