"""
SecureTrail — Booking Fraud Model Trainer
Decision Tree Classifier on synthetic e-ticket dataset
Outputs: model/fraud_model.pkl
"""
import os, pickle, warnings
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (accuracy_score, roc_auc_score,
                             confusion_matrix, classification_report)

warnings.filterwarnings("ignore")

BASE   = os.path.dirname(os.path.abspath(__file__))
DATA   = os.path.join(BASE, "..", "dataset", "eticket_data.csv")
OUT    = os.path.join(BASE, "fraud_model.pkl")

# ── Load ──────────────────────────────────────────────────────────
df = pd.read_csv(DATA)
print(f"Loaded {len(df)} rows | Fraud={df.is_fraud.sum()} ({df.is_fraud.mean()*100:.1f}%)")

FEATURES = [
    "booking_count_last_24hrs", "used_flag", "travel_distance",
    "otp_attempts", "failed_payments_count",
    "ticket_status", "payment_method", "seat_type",
    "payment_status", "is_suspicious_device", "is_suspicious_ip",
]

SUSPICIOUS_DEVICES = [f"DEV{i:04d}" for i in range(1, 11)]
IP_SUSPICIOUS_OCTETS = list(range(0, 8))

# Derived binary columns
df["is_suspicious_device"] = df["device_id"].apply(
    lambda x: 1 if str(x) in SUSPICIOUS_DEVICES else 0)
df["is_suspicious_ip"] = df["ip_address"].apply(
    lambda x: 1 if (
        x.startswith("192.168.") and
        int(x.split(".")[2]) in IP_SUSPICIOUS_OCTETS
    ) else 0)

# ── Encode categoricals ───────────────────────────────────────────
CATS = ["ticket_status", "payment_method", "seat_type", "payment_status"]
encoders = {}
for col in CATS:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

X = df[FEATURES]
y = df["is_fraud"]

# ── Train / test split ────────────────────────────────────────────
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                           random_state=42, stratify=y)

model = DecisionTreeClassifier(
    max_depth=10, min_samples_split=4, min_samples_leaf=2,
    class_weight="balanced", random_state=42
)
model.fit(X_tr, y_tr)

# ── Evaluate ──────────────────────────────────────────────────────
y_pred  = model.predict(X_te)
y_prob  = model.predict_proba(X_te)[:, 1]
acc     = accuracy_score(y_te, y_pred)
auc     = roc_auc_score(y_te, y_prob)
cm      = confusion_matrix(y_te, y_pred).tolist()

# Cross-val
cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")

print(f"\n{'='*50}")
print(f"  Accuracy  : {acc*100:.2f}%")
print(f"  AUC-ROC   : {auc:.4f}")
print(f"  CV 5-fold : {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")
print(f"  Conf Mat  : {cm}")
print(f"{'='*50}")
print(classification_report(y_te, y_pred, target_names=["Valid","Fraud"]))

# ── Feature importance ────────────────────────────────────────────
fi = sorted(zip(FEATURES, model.feature_importances_),
            key=lambda x: -x[1])
print("Feature Importances:")
for name, imp in fi:
    bar = "#" * int(imp * 40)
    print(f"  {name:<30} {imp:.4f}  {bar}")

# ── Save ──────────────────────────────────────────────────────────
bundle = {
    "model":    model,
    "encoders": encoders,
    "features": FEATURES,
    "accuracy": acc,
    "auc":      auc,
    "confusion_matrix": cm,
    "feature_importance": fi,
}
with open(OUT, "wb") as f:
    pickle.dump(bundle, f)
print(f"\nSaved -> {OUT}")
