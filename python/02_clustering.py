"""
02_clustering.py — K-Means Customer Segmentation
==================================================
EN: Applies K-Means clustering (k=5) on normalized RFM scores
    and assigns business-readable segment labels.

ES: Aplica clustering K-Means (k=5) sobre puntajes RFM normalizados
    y asigna etiquetas de segmento legibles para el negocio.

Input : data/rfm_scores.csv
Output: data/customer_segments.csv

Segment Labels / Etiquetas de Segmentos:
  Champions    — High R, F, M. Best customers. / Mejores clientes.
  Loyal        — High F, M. Frequent buyers. / Compradores frecuentes.
  At Risk      — High F, M but low R. Were good, going cold. / Eran buenos, se estan enfriando.
  Potential    — Medium scores. Promising. / Prometedores.
  Lost         — Low R, F, M. Need win-back. / Necesitan recuperacion.

Usage / Uso:
  python python/02_clustering.py
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT    = os.path.join(DATA_DIR, "rfm_scores.csv")
OUTPUT   = os.path.join(DATA_DIR, "customer_segments.csv")
K        = 5
SEED     = 42

# ── Load RFM ─────────────────────────────────────────────────────────────────
print("Loading RFM scores...")
rfm = pd.read_csv(INPUT)
features = rfm[["r_score", "f_score", "m_score"]]

# ── Normalize ─────────────────────────────────────────────────────────────────
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(features)

# ── K-Means ───────────────────────────────────────────────────────────────────
print(f"Running K-Means (k={K})...")
km = KMeans(n_clusters=K, init="k-means++", n_init=20, random_state=SEED)
rfm["cluster"] = km.fit_predict(X_scaled)

sil = silhouette_score(X_scaled, rfm["cluster"])
print(f"  Silhouette Score: {sil:.4f}  (0=bad, 1=perfect)")

# ── Segment labeling ──────────────────────────────────────────────────────────
# Rank clusters by combined RFM centroid score to assign consistent labels
centers_df = pd.DataFrame(km.cluster_centers_, columns=["r","f","m"])
centers_df["total"] = centers_df.sum(axis=1)

# Build label map: highest total → Champions, lowest → Lost
sorted_clusters = centers_df["total"].sort_values(ascending=False).index.tolist()
label_map = {
    sorted_clusters[0]: "Champions",
    sorted_clusters[1]: "Loyal",
    sorted_clusters[2]: "At Risk",
    sorted_clusters[3]: "Potential",
    sorted_clusters[4]: "Lost",
}
rfm["segment"] = rfm["cluster"].map(label_map)

# ── Retention recommendations ──────────────────────────────────────────────────
ACTION = {
    "Champions": "Reward them. Ask for reviews. Make them brand ambassadors.",
    "Loyal":     "Upsell higher-value products. Engage with loyalty program.",
    "At Risk":   "Send win-back emails. Offer a limited discount.",
    "Potential": "Nurture with onboarding emails and product recommendations.",
    "Lost":      "Re-engage with a strong discount offer or survey to learn why.",
}
ACTION_ES = {
    "Champions": "Recompensalos. Pídeles reseñas. Convírtelos en embajadores.",
    "Loyal":     "Ofrece productos premium. Enróllalos en programa de lealtad.",
    "At Risk":   "Envía emails de recuperación. Ofrece descuento limitado.",
    "Potential": "Nutre con emails de onboarding y recomendaciones.",
    "Lost":      "Re-engancha con descuento fuerte o encuesta de salida.",
}
rfm["action_en"] = rfm["segment"].map(ACTION)
rfm["action_es"] = rfm["segment"].map(ACTION_ES)

# ── Save ──────────────────────────────────────────────────────────────────────
rfm.to_csv(OUTPUT, index=False)

# ── Summary Table ─────────────────────────────────────────────────────────────
print("\n── Segment Summary ─────────────────────────────────────────────────")
summary = rfm.groupby("segment").agg(
    customers  = ("customer_id",  "count"),
    avg_recency    = ("recency",      "mean"),
    avg_frequency  = ("frequency",    "mean"),
    avg_monetary   = ("monetary",     "mean"),
    total_revenue  = ("monetary",     "sum"),
).round(1).reset_index()
summary["pct_customers"] = (summary["customers"] / summary["customers"].sum() * 100).round(1)
summary["pct_revenue"]   = (summary["total_revenue"] / summary["total_revenue"].sum() * 100).round(1)
print(summary[["segment","customers","pct_customers","avg_recency","avg_frequency","avg_monetary","pct_revenue"]].to_string(index=False))
print(f"\nSilhouette Score: {sil:.4f}")
print(f"Saved → {OUTPUT}")
