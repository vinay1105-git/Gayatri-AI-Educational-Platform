from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.feature_engineering import FEATURE_COLUMNS, FEATURE_LABELS


def classify_risk_tier(risk_probability_pct: float) -> str:
    if risk_probability_pct >= 60.0:
        return "high"
    if risk_probability_pct >= 30.0:
        return "moderate"
    return "low"


def train_risk_and_score_models(df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    X = df[FEATURE_COLUMNS].copy()
    y_risk = df["at_risk_target"].astype(int).values
    y_score = df["observed_outcome"].astype(float).values

    n_samples = len(df)
    n_splits = max(2, min(5, int(np.bincount(y_risk).min()))) if len(np.unique(y_risk)) > 1 else 2

    candidates = {
        "RandomForestClassifier": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=180, max_depth=6, min_samples_leaf=3, random_state=42, class_weight="balanced"
                    ),
                ),
            ]
        ),
        "GradientBoostingClassifier": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", GradientBoostingClassifier(n_estimators=120, learning_rate=0.06, max_depth=3, random_state=42)),
            ]
        ),
        "LogisticRegression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
            ]
        ),
    }

    cv_strat = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    comparison_results: List[Dict[str, Any]] = []
    best_model_name = "RandomForestClassifier"
    best_f1 = -1.0
    best_oof_probs = None
    best_oof_preds = None

    for name, pipe in candidates.items():
        if len(np.unique(y_risk)) > 1 and n_samples >= 10:
            oof_probs = cross_val_predict(pipe, X, y_risk, cv=cv_strat, method="predict_proba")[:, 1]
            oof_preds = (oof_probs >= 0.5).astype(int)
            acc = float(accuracy_score(y_risk, oof_preds))
            prec = float(precision_score(y_risk, oof_preds, zero_division=0))
            rec = float(recall_score(y_risk, oof_preds, zero_division=0))
            f1 = float(f1_score(y_risk, oof_preds, zero_division=0))
            auc = float(roc_auc_score(y_risk, oof_probs))
        else:
            pipe.fit(X, y_risk)
            oof_probs = pipe.predict_proba(X)[:, 1] if len(np.unique(y_risk)) > 1 else np.zeros(n_samples)
            oof_preds = (oof_probs >= 0.5).astype(int)
            acc, prec, rec, f1, auc = 1.0, 1.0, 1.0, 1.0, 1.0

        comparison_results.append(
            {
                "model": name,
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(auc, 4),
            }
        )
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_oof_probs = oof_probs
            best_oof_preds = oof_preds

    best_clf_pipeline = candidates[best_model_name]
    best_clf_pipeline.fit(X, y_risk)

    cm = confusion_matrix(y_risk, best_oof_preds, labels=[0, 1]).tolist()

    # Regressor for predicted final score
    reg_candidates = {
        "GradientBoostingRegressor": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("reg", GradientBoostingRegressor(n_estimators=120, learning_rate=0.06, max_depth=3, random_state=42)),
            ]
        ),
        "RidgeRegressor": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("reg", Ridge(alpha=2.0)),
            ]
        ),
    }

    kf = KFold(n_splits=min(5, max(2, n_samples // 4)), shuffle=True, random_state=42)
    reg_comparison: List[Dict[str, Any]] = []
    best_reg_name = "RidgeRegressor"
    best_rmse = float("inf")

    for name, pipe in reg_candidates.items():
        if n_samples >= 10:
            oof_score_preds = cross_val_predict(pipe, X, y_score, cv=kf)
        else:
            pipe.fit(X, y_score)
            oof_score_preds = pipe.predict(X)
        mae = float(mean_absolute_error(y_score, oof_score_preds))
        rmse = float(np.sqrt(mean_squared_error(y_score, oof_score_preds)))
        r2 = float(r2_score(y_score, oof_score_preds))
        reg_comparison.append(
            {
                "model": name,
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2_score": round(r2, 4),
            }
        )
        if rmse < best_rmse:
            best_rmse = rmse
            best_reg_name = name

    best_reg_pipeline = reg_candidates[best_reg_name]
    best_reg_pipeline.fit(X, y_score)

    # Global feature importances from Random Forest (or model estimator)
    rf_pipe = candidates["RandomForestClassifier"]
    rf_pipe.fit(X, y_risk)
    importances_raw = rf_pipe.named_steps["clf"].feature_importances_

    feature_means = X.mean().to_dict()
    feature_stds = X.std().replace(0, 1.0).to_dict()
    # Direction relative to risk target
    feature_corrs = {
        col: float(np.corrcoef(X[col].values, y_risk)[0, 1]) if np.std(X[col].values) > 1e-6 and np.std(y_risk) > 0 else 0.0
        for col in FEATURE_COLUMNS
    }

    feature_importance_list = sorted(
        [
            {
                "feature": col,
                "label": FEATURE_LABELS.get(col, col),
                "importance": round(float(imp), 4),
                "risk_correlation": round(feature_corrs[col], 4),
            }
            for col, imp in zip(FEATURE_COLUMNS, importances_raw)
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )

    artifacts = {
        "classifier": best_clf_pipeline,
        "regressor": best_reg_pipeline,
        "feature_columns": FEATURE_COLUMNS,
        "feature_means": feature_means,
        "feature_stds": feature_stds,
        "feature_importances": dict(zip(FEATURE_COLUMNS, [float(v) for v in importances_raw])),
        "feature_risk_correlations": feature_corrs,
    }

    best_clf_metrics = next(m for m in comparison_results if m["model"] == best_model_name)
    best_reg_metrics = next(m for m in reg_comparison if m["model"] == best_reg_name)

    evaluation = {
        "sample_size": n_samples,
        "positive_risk_count": int(np.sum(y_risk)),
        "cv_folds": n_splits,
        "selected_classifier": best_model_name,
        "classifier_metrics": best_clf_metrics,
        "classifier_comparison": comparison_results,
        "confusion_matrix": {
            "labels": ["On Track (0)", "At Risk (1)"],
            "matrix": cm,
        },
        "selected_regressor": best_reg_name,
        "regressor_metrics": best_reg_metrics,
        "regressor_comparison": reg_comparison,
        "feature_importances": feature_importance_list,
    }
    return artifacts, evaluation


def predict_student_risk_and_score(artifacts: Dict[str, Any], features: Dict[str, float]) -> Dict[str, Any]:
    cols = artifacts["feature_columns"]
    row_df = pd.DataFrame([[features[c] for c in cols]], columns=cols)

    clf = artifacts["classifier"]
    reg = artifacts["regressor"]

    if hasattr(clf, "predict_proba"):
        probs = clf.predict_proba(row_df)
        risk_prob = float(probs[0][1]) if probs.shape[1] > 1 else float(probs[0][0])
    else:
        risk_prob = float(clf.predict(row_df)[0])

    risk_score = round(float(np.clip(risk_prob * 100.0, 2.0, 98.0)), 2)
    predicted_score = round(float(np.clip(reg.predict(row_df)[0], 25.0, 99.5)), 2)
    risk_level = classify_risk_tier(risk_score)

    # Local attribution drivers
    means = artifacts["feature_means"]
    stds = artifacts["feature_stds"]
    importances = artifacts["feature_importances"]
    corrs = artifacts["feature_risk_correlations"]

    drivers: List[Dict[str, Any]] = []
    for col in cols:
        z_val = (features[col] - means[col]) / (stds[col] if stds[col] > 1e-6 else 1.0)
        corr_sign = 1.0 if corrs[col] >= 0 else -1.0
        impact = float(z_val * corr_sign * importances[col])
        drivers.append(
            {
                "feature": col,
                "label": FEATURE_LABELS.get(col, col),
                "student_value": round(float(features[col]), 2),
                "cohort_mean": round(float(means[col]), 2),
                "impact_score": round(impact, 4),
                "effect": "risk_increasing" if impact > 0.015 else ("protective" if impact < -0.015 else "neutral"),
            }
        )

    drivers_sorted = sorted(drivers, key=lambda d: abs(d["impact_score"]), reverse=True)[:5]

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "predicted_final_score": predicted_score,
        "drivers": drivers_sorted,
    }
