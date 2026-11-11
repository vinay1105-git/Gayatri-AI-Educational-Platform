from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import joblib
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import StudentProfile
from app.ml.feature_engineering import extract_cohort_dataframe, extract_single_student_features
from app.ml.learner_clustering import assign_student_cluster, train_learner_clustering
from app.ml.risk_predictor import predict_student_risk_and_score, train_risk_and_score_models

logger = logging.getLogger("gayatri_ai.ml")

_MODEL_CACHE: Optional[Dict[str, Any]] = None


def _artifact_paths() -> Dict[str, Path]:
    base = get_settings().ml_artifacts_path
    return {
        "bundle": base / "gayatri_models.joblib",
        "metrics": base / "evaluation_metrics.json",
    }


def retrain_all_models(db: Session) -> Dict[str, Any]:
    global _MODEL_CACHE
    df, profiles = extract_cohort_dataframe(db)
    if df.empty or len(df) < 6:
        raise ValueError("At least 6 student telemetry profiles are required to train ML pipelines.")

    risk_artifacts, risk_eval = train_risk_and_score_models(df)
    cluster_artifacts, cluster_eval = train_learner_clustering(df)

    bundle = {
        "risk": risk_artifacts,
        "cluster": cluster_artifacts,
    }
    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "cohort_size": len(df),
        "risk_model": risk_eval,
        "clustering_model": cluster_eval,
    }

    paths = _artifact_paths()
    joblib.dump(bundle, paths["bundle"])
    paths["metrics"].write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _MODEL_CACHE = {"bundle": bundle, "metrics": metrics}

    # Update persisted predictions and cluster assignments for every student
    for idx, profile in enumerate(profiles):
        feat_row = df.iloc[idx].to_dict()
        pred = predict_student_risk_and_score(risk_artifacts, feat_row)
        clust = assign_student_cluster(cluster_artifacts, feat_row)
        profile.risk_score = pred["risk_score"]
        profile.risk_level = pred["risk_level"]
        profile.predicted_final_score = pred["predicted_final_score"]
        profile.cluster_id = clust["cluster_id"]
        profile.cluster_label = clust["cluster_label"]
        profile.pca_x = clust["pca_x"]
        profile.pca_y = clust["pca_y"]

    db.commit()
    logger.info(
        "Trained ML models on %d students | Classifier=%s F1=%.3f AUC=%.3f | Silhouette=%.3f",
        len(df),
        risk_eval["selected_classifier"],
        risk_eval["classifier_metrics"]["f1_score"],
        risk_eval["classifier_metrics"]["roc_auc"],
        cluster_eval["silhouette_score"],
    )
    return metrics


def get_loaded_models(db: Session) -> Dict[str, Any]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    paths = _artifact_paths()
    if paths["bundle"].exists() and paths["metrics"].exists():
        bundle = joblib.load(paths["bundle"])
        metrics = json.loads(paths["metrics"].read_text(encoding="utf-8"))
        _MODEL_CACHE = {"bundle": bundle, "metrics": metrics}
        return _MODEL_CACHE

    metrics = retrain_all_models(db)
    return {"bundle": _MODEL_CACHE["bundle"], "metrics": metrics}


def refresh_student_predictions(db: Session, student_id: int) -> Dict[str, Any]:
    loaded = get_loaded_models(db)
    bundle = loaded["bundle"]

    features = extract_single_student_features(db, student_id)
    pred = predict_student_risk_and_score(bundle["risk"], features)
    clust = assign_student_cluster(bundle["cluster"], features)

    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if profile:
        profile.risk_score = pred["risk_score"]
        profile.risk_level = pred["risk_level"]
        profile.predicted_final_score = pred["predicted_final_score"]
        profile.cluster_id = clust["cluster_id"]
        profile.cluster_label = clust["cluster_label"]
        profile.pca_x = clust["pca_x"]
        profile.pca_y = clust["pca_y"]
        db.commit()

    return {
        "features": features,
        "prediction": pred,
        "cluster": clust,
    }


def get_student_diagnostics(db: Session, student_id: int) -> Dict[str, Any]:
    loaded = get_loaded_models(db)
    bundle = loaded["bundle"]
    features = extract_single_student_features(db, student_id)
    pred = predict_student_risk_and_score(bundle["risk"], features)
    clust = assign_student_cluster(bundle["cluster"], features)
    return {
        "features": features,
        "prediction": pred,
        "cluster": clust,
    }
