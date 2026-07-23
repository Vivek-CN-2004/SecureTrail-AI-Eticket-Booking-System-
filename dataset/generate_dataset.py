"""
E-Ticket Fraud Detection — Synthetic Dataset Generator
Generates 1200+ rows with realistic fraud patterns including:
  - OTP failures, payment failures, high booking counts,
    cancelled tickets, shared devices, suspicious IPs
"""

import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ── Config ────────────────────────────────────────────────────────
TOTAL = 1300
FRAUD_RATIO = 0.30

CITIES = ["Mumbai","Delhi","Bangalore","Chennai","Kolkata",
          "Hyderabad","Pune","Ahmedabad","Jaipur","Lucknow"]
SEAT_TYPES   = ["AC","Sleeper","General","Business","First Class"]
PAYMENTS     = ["UPI","Credit Card","Debit Card","Net Banking","Wallet"]
PAY_STATUSES = ["SUCCESS","FAILED","PENDING"]
STATUSES     = ["active","cancelled","completed"]
DEVICE_IDS   = [f"DEV{i:04d}" for i in range(1, 250)]
IP_POOL      = [f"192.168.{r}.{c}" for r in range(0,20) for c in range(1,15)]

SUSPICIOUS_IPS     = [ip for ip in IP_POOL if int(ip.split(".")[2]) < 8]
SUSPICIOUS_DEVICES = DEVICE_IDS[:10]

CITY_DIST = {
    ("Mumbai","Delhi"):1400,("Mumbai","Bangalore"):980,
    ("Mumbai","Chennai"):1330,("Delhi","Kolkata"):1500,
    ("Delhi","Bangalore"):2150,("Bangalore","Chennai"):350,
    ("Hyderabad","Chennai"):630,("Pune","Mumbai"):150,
    ("Jaipur","Delhi"):280,("Lucknow","Delhi"):500,
}

def get_dist(a, b):
    if a == b: return random.randint(10,60)
    return CITY_DIST.get((a,b), CITY_DIST.get((b,a), random.randint(200,1800)))

def rand_dt(days_back=90, days_ahead=30):
    d = timedelta(days=random.randint(-days_back, days_ahead),
                  hours=random.randint(0,23), minutes=random.randint(0,59))
    return datetime.now() + d

# ── Valid record ──────────────────────────────────────────────────
def valid_rec(uid):
    src = random.choice(CITIES)
    dst = random.choice([c for c in CITIES if c != src])
    bk  = rand_dt(90, 30)
    tv  = bk + timedelta(days=random.randint(1,25), hours=random.randint(0,12))
    return dict(
        user_id=uid,
        passenger_name=f"User_{uid}",
        source=src, destination=dst,
        booking_time=bk.strftime("%Y-%m-%d %H:%M"),
        travel_time=tv.strftime("%Y-%m-%d %H:%M"),
        seat_type=random.choice(SEAT_TYPES),
        payment_method=random.choice(PAYMENTS),
        payment_status="SUCCESS",
        booking_count_last_24hrs=random.randint(1,3),
        used_flag=0,
        ticket_status=random.choices(STATUSES, weights=[70,15,15])[0],
        device_id=random.choice(DEVICE_IDS[10:]),
        ip_address=random.choice(IP_POOL[80:]),
        travel_distance=get_dist(src,dst),
        otp_attempts=random.randint(0,1),
        failed_payments_count=0,
        is_fraud=0,
    )

# ── Fraud record ──────────────────────────────────────────────────
def fraud_rec(uid):
    src = random.choice(CITIES)
    dst = random.choice([c for c in CITIES if c != src])
    bk  = rand_dt(90, 30)
    tv  = bk + timedelta(hours=random.randint(0,5))
    ftype = random.choice(["high_booking","cancelled_used","payment_fail",
                           "otp_abuse","shared_device","dup_use"])
    rec = dict(
        user_id=uid,
        passenger_name=f"User_{uid}",
        source=src, destination=dst,
        booking_time=bk.strftime("%Y-%m-%d %H:%M"),
        travel_time=tv.strftime("%Y-%m-%d %H:%M"),
        seat_type=random.choice(SEAT_TYPES),
        payment_method=random.choice(PAYMENTS),
        payment_status="SUCCESS",
        booking_count_last_24hrs=random.randint(6,18),
        used_flag=0,
        ticket_status="active",
        device_id=random.choice(DEVICE_IDS[10:]),
        ip_address=random.choice(IP_POOL[80:]),
        travel_distance=get_dist(src,dst),
        otp_attempts=random.randint(0,2),
        failed_payments_count=random.randint(0,2),
        is_fraud=1,
    )
    if ftype == "high_booking":
        rec["booking_count_last_24hrs"] = random.randint(6,20)
    elif ftype == "cancelled_used":
        rec["ticket_status"] = "cancelled"
        rec["used_flag"] = 1
        rec["booking_count_last_24hrs"] = random.randint(1,4)
    elif ftype == "payment_fail":
        rec["payment_status"] = "FAILED"
        rec["failed_payments_count"] = random.randint(3,8)
        rec["booking_count_last_24hrs"] = random.randint(2,6)
    elif ftype == "otp_abuse":
        rec["otp_attempts"] = random.randint(3,6)
        rec["booking_count_last_24hrs"] = random.randint(2,7)
    elif ftype == "shared_device":
        rec["device_id"] = random.choice(SUSPICIOUS_DEVICES)
        rec["ip_address"] = random.choice(SUSPICIOUS_IPS)
        rec["booking_count_last_24hrs"] = random.randint(2,8)
    elif ftype == "dup_use":
        rec["used_flag"] = 1
        rec["ticket_status"] = "active"
        rec["booking_count_last_24hrs"] = random.randint(1,4)
    return rec

# ── Build dataset ─────────────────────────────────────────────────
n_fraud = int(TOTAL * FRAUD_RATIO)
n_valid = TOTAL - n_fraud
records = []
for uid in [random.randint(1000,9999) for _ in range(n_valid)]:
    records.append(valid_rec(uid))
for uid in [random.randint(1000,9999) for _ in range(n_fraud)]:
    records.append(fraud_rec(uid))
random.shuffle(records)

df = pd.DataFrame(records)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eticket_data.csv")
df.to_csv(out, index=False)
print(f"✅ Dataset: {len(df)} rows | Fraud={df.is_fraud.sum()} ({df.is_fraud.mean()*100:.1f}%) | Saved: {out}")
