#!/usr/bin/env python3
"""
Train fraud detection models on synthetic e-ticket dataset.
Saves ml/fraud_model.pkl with Logistic Regression + Decision Tree ensemble.
"""
import os, pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

# ── Load Dataset ──────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "train_tickets.csv")

if not os.path.exists(DATA_PATH):
    print("Dataset not found. Running generate_dataset.py first...")
    import subprocess
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "generate_dataset.py")], check=True)

df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} rows | Fraud: {df['is_fraud'].sum()} | Normal: {(df['is_fraud']==0).sum()}")

# ── Feature Engineering ───────────────────────────────────────────────────────
# Encode categoricals
le_tt   = LabelEncoder().fit(df["ticket_type"])
le_cls  = LabelEncoder().fit(df["class"])
le_ch   = LabelEncoder().fit(df["booking_channel"])
le_src  = LabelEncoder().fit(df["start_station"])
le_dst  = LabelEncoder().fit(df["end_station"])

df["ticket_type_enc"]      = le_tt.transform(df["ticket_type"])
df["class_enc"]            = le_cls.transform(df["class"])
df["booking_channel_enc"]  = le_ch.transform(df["booking_channel"])
df["start_station_enc"]    = le_src.transform(df["start_station"])
df["end_station_enc"]      = le_dst.transform(df["end_station"])

# Price z-score anomaly (per ticket_type)
df["price_z"] = df.groupby("ticket_type")["price"].transform(
    lambda x: (x - x.mean()) / (x.std() + 1e-6)
)

# Days until travel (negative = impossible)
df["days_clipped"] = df["days_until_travel"].clip(-30, 365)

# PNR validity: alphanumeric, length 10
import re
df["pnr_valid"] = df["pnr"].apply(
    lambda p: 1 if re.match(r'^[A-Z]{2}[0-9]{8}$', str(p)) else 0
)

# New Device Encoder
le_dev = LabelEncoder().fit(df["device_type"].astype(str))
df["device_type_enc"] = le_dev.transform(df["device_type"].astype(str))

FEATURES = [
    "ticket_type_enc", "class_enc", "booking_channel_enc",
    "start_station_enc", "end_station_enc",
    "price", "price_z", "price_per_km",
    "days_clipped", "pnr_valid",
    "booking_frequency", "time_taken_sec", "login_frequency",
    "device_type_enc", "ip_change_flag"
]

X = df[FEATURES].fillna(0).values
y = df["is_fraud"].values

# ── Train / Test Split ────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

scaler  = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ── Random Forest Classifier ──────────────────────────────────────────────────
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, class_weight="balanced")
rf.fit(X_train_s, y_train)
rf_pred = rf.predict(X_test_s)
rf_prob = rf.predict_proba(X_test_s)[:, 1]

acc = accuracy_score(y_test, rf_pred)
print("\n-- Random Forest Results --------------------------------------------------")
print(f"Accuracy : {acc*100:.2f}%")
print(f"Precision: {precision_score(y_test, rf_pred)*100:.2f}%")
print(f"Recall   : {recall_score(y_test, rf_pred)*100:.2f}%")
print(f"F1 Score : {f1_score(y_test, rf_pred)*100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, rf_pred, target_names=["Normal","Fraud"]))

# ── Save Model Bundle ──────────────────────────────────────────────────────────
model_bundle = {
    "rf":        rf,
    "scaler":    scaler,
    "features":  FEATURES,
    "encoders": {
        "ticket_type": le_tt, "class": le_cls, "booking_channel": le_ch,
        "start_station": le_src, "end_station": le_dst, "device_type": le_dev
    },
    "accuracy": acc,
    "trained_at": pd.Timestamp.now().isoformat()
}

out_path = os.path.join(os.path.dirname(__file__), "fraud_model.pkl")
with open(out_path, "wb") as f:
    pickle.dump(model_bundle, f)

print(f"\n[OK] Model saved to {out_path}")
