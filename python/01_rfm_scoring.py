"""
01_rfm_scoring.py — RFM Scoring Pipeline
=========================================
EN: Reads customer transaction data and computes RFM scores (1-5 scale)
    using quantile-based ranking (NTILE logic).

ES: Lee datos de transacciones y calcula puntajes RFM en escala 1-5
    usando ranking por cuantiles (logica NTILE).

Input : data/customer_transactions.csv
Output: data/rfm_scores.csv

RFM Definitions:
  R (Recency)   — Days since last purchase. Lower = better. Score 5 = most recent.
  F (Frequency) — Number of distinct orders.  Higher = better. Score 5 = most frequent.
  M (Monetary)  — Total spend.                Higher = better. Score 5 = highest spend.

Usage / Uso:
  python python/01_rfm_scoring.py
"""

import pandas as pd
import os
from datetime import date

# ── Config ──────────────────────────────────────────────────────────────────
TODAY     = pd.Timestamp("2026-02-26")
DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT     = os.path.join(DATA_DIR, "customer_transactions.csv")
OUTPUT    = os.path.join(DATA_DIR, "rfm_scores.csv")
N_TILES   = 5

# ── Load data ────────────────────────────────────────────────────────────────
print("Loading transaction data...")
df = pd.read_csv(INPUT, parse_dates=["purchase_date"])
print(f"  {len(df):,} transactions | {df['customer_id'].nunique():,} customers")

# ── Compute raw RFM ───────────────────────────────────────────────────────────
print("\nComputing RFM metrics...")
rfm = df.groupby("customer_id").agg(
    recency   = ("purchase_date", lambda x: (TODAY - x.max()).days),
    frequency = ("order_id",       "nunique"),
    monetary  = ("order_value",    "sum")
).reset_index()
rfm["monetary"] = rfm["monetary"].round(2)

# ── NTILE scoring (1-5) ───────────────────────────────────────────────────────
# Recency: lower days = better = score 5
rfm["r_score"] = pd.qcut(rfm["recency"],   q=N_TILES, labels=[5,4,3,2,1], duplicates="drop").astype(int)
# Frequency & Monetary: higher = better = score 5
rfm["f_score"] = pd.qcut(rfm["frequency"], q=N_TILES, labels=[1,2,3,4,5], duplicates="drop").astype(int)
rfm["m_score"] = pd.qcut(rfm["monetary"],  q=N_TILES, labels=[1,2,3,4,5], duplicates="drop").astype(int)

# Combined score
rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
rfm["rf_score"]  = rfm["r_score"].astype(str) + rfm["f_score"].astype(str)

# ── Save ──────────────────────────────────────────────────────────────────────
rfm.to_csv(OUTPUT, index=False)
print(f"\n  Saved {len(rfm)} customer RFM records to {OUTPUT}")

# ── Preview ───────────────────────────────────────────────────────────────────
print("\n── RFM Score Distribution ──────────────────────────────")
print(rfm[["r_score","f_score","m_score","rfm_score"]].describe().round(2).to_string())
print("\n── Top 5 Customers by RFM Score ────────────────────────")
print(rfm.nlargest(5, "rfm_score")[["customer_id","recency","frequency","monetary","rfm_score"]].to_string(index=False))
