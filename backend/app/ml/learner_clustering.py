from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, silhouette_score
from sklearn.preprocessing import StandardScaler

CLUSTER_FEATURES: List[str] = [
    "avg_concept_mastery",
    "avg_study_hours",
    "study_consistency",
    "attendance_rate",
    "quiz_score_trend",
    "engagement_index",
]


def _derive_cluster_labels(centroids_unscaled: np.ndarray) -> Dict[int, Dict[str, str]]:
    # Score each centroid along mastery+engagement vs momentum
    mastery_idx = CLUSTER_FEATURES.index("avg_concept_mastery")
    trend_idx = CLUSTER_FEATURES.index("quiz_score_trend")
    consistency_idx = CLUSTER_FEATURES.index("study_consistency")

    ranked_by_mastery = np.argsort(centroids_unscaled[:, mastery_idx])[::-1]

    labels: Dict[int, Dict[str, str]] = {}
    if len(ranked_by_mastery) >= 4:
        c_top = int(ranked_by_mastery[0])
        c_low = int(ranked_by_mastery[-1])
        mid_indices = [int(ranked_by_mastery[1]), int(ranked_by_mastery[2])]
        # Distinguish Consistent Builder vs Developing Momentum by consistency & trend
        if centroids_unscaled[mid_indices[0], consistency_idx] >= centroids_unscaled[mid_indices[1], consistency_idx]:
            c_consistent, c_momentum = mid_indices[0], mid_indices[1]
        else:
            c_consistent, c_momentum = mid_indices[1], mid_indices[0]

        labels[c_top] = {
            "name": "Accelerated Mastery",
            "description": "High concept mastery, strong attendance, and sustained independent study cadence.",
        }
        labels[c_consistent] = {
            "name": "Consistent Builder",
            "description": "Steady weekly habits and balanced assessment outcomes across core modules.",
        }
        labels[c_momentum] = {
            "name": "Developing Momentum",
            "description": "Variable study cadence or emerging upward trend; benefits from structured milestones.",
        }
        labels[c_low] = {
            "name": "Targeted Support Needed",
            "description": "Lower mastery density or attendance friction; prioritized for prerequisite reinforcement.",
        }
    else:
        for i in range(len(centroids_unscaled)):
            labels[i] = {
                "name": f"Learner Cohort {i + 1}",
                "description": "Behavioral and academic segmentation group.",
            }
    return labels


def train_learner_clustering(df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    X = df[CLUSTER_FEATURES].copy()
    n_samples = len(df)
    n_clusters = min(4, max(2, n_samples // 6)) if n_samples >= 8 else 2

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    cluster_ids = kmeans.fit_predict(X_scaled)

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)

    centroids_unscaled = scaler.inverse_transform(kmeans.cluster_centers_)
    label_map = _derive_cluster_labels(centroids_unscaled)

    sil_score = float(silhouette_score(X_scaled, cluster_ids)) if len(set(cluster_ids)) > 1 and n_samples > n_clusters else 0.0
    ch_score = float(calinski_harabasz_score(X_scaled, cluster_ids)) if len(set(cluster_ids)) > 1 and n_samples > n_clusters else 0.0

    cluster_summaries: List[Dict[str, Any]] = []
    for cid in range(n_clusters):
        mask = cluster_ids == cid
        centroid = centroids_unscaled[cid]
        cluster_summaries.append(
            {
                "cluster_id": int(cid),
                "label": label_map[cid]["name"],
                "description": label_map[cid]["description"],
                "student_count": int(np.sum(mask)),
                "centroid": {
                    feat: round(float(centroid[idx]), 2) for idx, feat in enumerate(CLUSTER_FEATURES)
                },
            }
        )

    artifacts = {
        "scaler": scaler,
        "kmeans": kmeans,
        "pca": pca,
        "features": CLUSTER_FEATURES,
        "label_map": label_map,
    }

    evaluation = {
        "algorithm": f"KMeans (k={n_clusters}) + PCA (2D)",
        "n_clusters": n_clusters,
        "silhouette_score": round(sil_score, 4),
        "calinski_harabasz_score": round(ch_score, 2),
        "pca_explained_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "clusters": cluster_summaries,
    }
    return artifacts, evaluation


def assign_student_cluster(artifacts: Dict[str, Any], features: Dict[str, float]) -> Dict[str, Any]:
    cols = artifacts["features"]
    row_df = pd.DataFrame([[features[c] for c in cols]], columns=cols)
    X_scaled = artifacts["scaler"].transform(row_df)
    cid = int(artifacts["kmeans"].predict(X_scaled)[0])
    pca_xy = artifacts["pca"].transform(X_scaled)[0]
    info = artifacts["label_map"].get(cid, {"name": "Consistent Builder", "description": ""})
    return {
        "cluster_id": cid,
        "cluster_label": info["name"],
        "cluster_description": info["description"],
        "pca_x": round(float(pca_xy[0]), 4),
        "pca_y": round(float(pca_xy[1]), 4),
    }
