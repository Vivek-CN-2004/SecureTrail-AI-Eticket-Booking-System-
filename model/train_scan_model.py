"""
SecureTrail — CV/OCR Scan Fraud Model Trainer
GradientBoosting (supervised, 70%) + IsolationForest (anomaly, 30%)
Outputs: model/scan_model.pkl
"""
import os, pickle, warnings
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (accuracy_score, roc_auc_score,
                             confusion_matrix, classification_report)

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "dataset", "scan_data.csv")
OUT  = os.path.join(BASE, "scan_model.pkl")

# ── Load ──────────────────────────────────────────────────────────
df = pd.read_csv(DATA)
print(f"Loaded {len(df)} rows | Fraud={df.is_fraud.sum()} ({df.is_fraud.mean()*100:.1f}%)")

FEATURES = [
    "qr_detected", "qr_decodable", "qr_pnr_match",
    "ocr_confidence", "font_consistent", "text_anomaly",
    "exif_clean", "file_unmodified", "price_reasonable",
    "metadata_consistent",
]

X = df[FEATURES].copy()
y = df["is_fraud"]

# ── Train / test split ────────────────────────────────────────────
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                           random_state=42, stratify=y)

# ── GradientBoosting (supervised) ────────────────────────────────
gb = GradientBoostingClassifier(
    n_estimators=200, learning_rate=0.08, max_depth=4,
    subsample=0.85, min_samples_split=4, random_state=42
)
gb.fit(X_tr, y_tr)

y_pred_gb = gb.predict(X_te)
y_prob_gb = gb.predict_proba(X_te)[:, 1]
acc_gb = accuracy_score(y_te, y_pred_gb)
auc_gb = roc_auc_score(y_te, y_prob_gb)
cm_gb  = confusion_matrix(y_te, y_pred_gb).tolist()

print(f"\nGradientBoosting  Accuracy={acc_gb*100:.2f}%  AUC={auc_gb:.4f}")
print(classification_report(y_te, y_pred_gb, target_names=["Valid","Fraud"]))

# ── IsolationForest (anomaly detection) ───────────────────────────
iso = IsolationForest(n_estimators=150, contamination=0.32,
                      random_state=42, n_jobs=-1)
iso.fit(X_tr)
iso_scores_tr = iso.decision_function(X_tr)
iso_scores_te = iso.decision_function(X_te)

# Normalize to 0-1 (higher = more anomalous)
iso_min, iso_max = iso_scores_tr.min(), iso_scores_tr.max()
iso_norm_te = 1 - (iso_scores_te - iso_min) / (iso_max - iso_min + 1e-9)
iso_norm_te = np.clip(iso_norm_te, 0, 1)

# ── Ensemble score ────────────────────────────────────────────────
ensemble_prob = 0.70 * y_prob_gb + 0.30 * iso_norm_te
ensemble_pred = (ensemble_prob >= 0.35).astype(int)
acc_ens = accuracy_score(y_te, ensemble_pred)
auc_ens = roc_auc_score(y_te, ensemble_prob)
cm_ens  = confusion_matrix(y_te, ensemble_pred).tolist()

print(f"Ensemble          Accuracy={acc_ens*100:.2f}%  AUC={auc_ens:.4f}")

# ── RandomForest for feature importance ───────────────────────────
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_tr, y_tr)
fi = sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1])
print("\nFeature Importances (RandomForest):")
for name, imp in fi:
    bar = "#" * int(imp * 40)
    print(f"  {name:<25} {imp:.4f}  {bar}")

# ── Cross-val ─────────────────────────────────────────────────────
cv = cross_val_score(gb, X, y, cv=5, scoring="accuracy")
print(f"\nCV 5-fold GB: {cv.mean()*100:.2f}% ± {cv.std()*100:.2f}%")

# ── Save ──────────────────────────────────────────────────────────
bundle = {
    "gb_model":   gb,
    "iso_model":  iso,
    "features":   FEATURES,
    "iso_min":    iso_min,
    "iso_max":    iso_max,
    "accuracy":   acc_ens,
    "gb_accuracy": acc_gb,
    "auc":        auc_ens,
    "gb_auc":     auc_gb,
    "confusion_matrix": cm_ens,
    "feature_importance": fi,
}
with open(OUT, "wb") as f:
    pickle.dump(bundle, f)
print(f"\nSaved -> {OUT}")
