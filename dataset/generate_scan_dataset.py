"""
SecureTrail — CV/OCR Scan Fraud Dataset Generator
1500 rows: 68% valid, 32% fraud across 8 fraud types
Outputs: dataset/scan_data.csv
"""
import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

random.seed(99)
np.random.seed(99)

TOTAL       = 1500
FRAUD_RATIO = 0.32

ISSUERS = ["IRCTC","RedBus","MakeMyTrip","Yatra","Paytm","GoIbibo","Cleartrip","AbhiBus"]
CITIES  = ["Mumbai","Delhi","Bangalore","Chennai","Kolkata","Hyderabad","Pune",
           "Ahmedabad","Jaipur","Lucknow","Surat","Kanpur","Nagpur","Indore","Bhopal"]
SEATS   = ["AC","Sleeper","General","Business","First Class","2A","3A","CC"]
CLASSES = ["Economy","Business","First","Sleeper","AC Chair"]

FRAUD_TYPES = [
    "ocr_tamper","qr_invalid","price_mismatch",
    "metadata_tamper","behavioral","duplicate","font_mismatch","no_qr"
]

def rand_price(src, dst):
    base = random.randint(150, 3500)
    return round(base, 2)

def rand_date(days_back=180, days_ahead=60):
    d = timedelta(days=random.randint(-days_back, days_ahead))
    return (datetime.now() + d).strftime("%Y-%m-%d")

def valid_rec(uid):
    src = random.choice(CITIES)
    dst = random.choice([c for c in CITIES if c != src])
    price = rand_price(src, dst)
    return dict(
        user_id=uid,
        issuer=random.choice(ISSUERS),
        source=src, destination=dst,
        travel_date=rand_date(180, 60),
        seat=random.choice(SEATS),
        travel_class=random.choice(CLASSES),
        price=price,
        qr_detected=1,
        qr_decodable=1,
        qr_pnr_match=random.choices([1,0],[95,5])[0],
        ocr_confidence=random.uniform(72, 98),
        font_consistent=random.choices([1,0],[90,10])[0],
        text_anomaly=0,
        exif_clean=random.choices([1,0],[88,12])[0],
        file_unmodified=random.choices([1,0],[85,15])[0],
        price_reasonable=1,
        metadata_consistent=random.choices([1,0],[90,10])[0],
        fraud_type="none",
        is_fraud=0,
    )

def fraud_rec(uid):
    src = random.choice(CITIES)
    dst = random.choice([c for c in CITIES if c != src])
    price = rand_price(src, dst)
    ftype = random.choice(FRAUD_TYPES)
    rec = dict(
        user_id=uid,
        issuer=random.choice(ISSUERS),
        source=src, destination=dst,
        travel_date=rand_date(180, 60),
        seat=random.choice(SEATS),
        travel_class=random.choice(CLASSES),
        price=price,
        qr_detected=1,
        qr_decodable=1,
        qr_pnr_match=0,
        ocr_confidence=random.uniform(50, 70),
        font_consistent=0,
        text_anomaly=1,
        exif_clean=0,
        file_unmodified=0,
        price_reasonable=1,
        metadata_consistent=0,
        fraud_type=ftype,
        is_fraud=1,
    )
    if ftype == "ocr_tamper":
        rec["ocr_confidence"]    = random.uniform(20, 55)
        rec["text_anomaly"]      = 1
        rec["font_consistent"]   = 0
    elif ftype == "qr_invalid":
        rec["qr_detected"]       = random.choices([0,1],[60,40])[0]
        rec["qr_decodable"]      = 0
        rec["qr_pnr_match"]      = 0
    elif ftype == "price_mismatch":
        rec["price_reasonable"]  = 0
        rec["price"]             = random.choice([5.0, 10.0, 9999.0, 0.5])
    elif ftype == "metadata_tamper":
        rec["exif_clean"]        = 0
        rec["file_unmodified"]   = 0
        rec["metadata_consistent"] = 0
    elif ftype == "behavioral":
        rec["qr_pnr_match"]      = 0
        rec["text_anomaly"]      = 1
        rec["ocr_confidence"]    = random.uniform(30, 60)
    elif ftype == "duplicate":
        rec["qr_pnr_match"]      = 1
        rec["qr_decodable"]      = 1
        rec["file_unmodified"]   = 0
        rec["exif_clean"]        = 0
    elif ftype == "font_mismatch":
        rec["font_consistent"]   = 0
        rec["text_anomaly"]      = 1
        rec["ocr_confidence"]    = random.uniform(55, 75)
    elif ftype == "no_qr":
        rec["qr_detected"]       = 0
        rec["qr_decodable"]      = 0
        rec["qr_pnr_match"]      = 0
    return rec

# ── Build ──────────────────────────────────────────────────────────
n_fraud = int(TOTAL * FRAUD_RATIO)
n_valid = TOTAL - n_fraud
records = []
for uid in [random.randint(1000, 9999) for _ in range(n_valid)]:
    records.append(valid_rec(uid))
for uid in [random.randint(1000, 9999) for _ in range(n_fraud)]:
    records.append(fraud_rec(uid))
random.shuffle(records)

df = pd.DataFrame(records)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_data.csv")
df.to_csv(out, index=False)
print(f"Scan dataset: {len(df)} rows | Fraud={df.is_fraud.sum()} "
      f"({df.is_fraud.mean()*100:.1f}%) | Saved: {out}")
