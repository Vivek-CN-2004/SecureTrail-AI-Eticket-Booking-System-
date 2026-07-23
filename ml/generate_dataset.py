#!/usr/bin/env python3
"""
Generate 10,000-row synthetic e-ticket fraud dataset.
Output: ml/data/train_tickets.csv
Seed: 42 — fully reproducible, no external data sources.
"""
import os, random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

random.seed(42)
fake = Faker("en_IN")
fake.seed_instance(42)

# ── Cities & Routes ──────────────────────────────────────────────────────────
CITIES = [
    "Bangalore","Mysore","Chennai","Hyderabad","Mumbai","Delhi","Kolkata",
    "Pune","Ahmedabad","Jaipur","Kochi","Goa","Bhopal","Lucknow","Patna",
    "Surat","Nagpur","Indore","Visakhapatnam","Coimbatore","Agra","Varanasi",
    "Chandigarh","Amritsar","Jodhpur","Udaipur","Ranchi","Bhubaneswar",
    "Mangalore","Thiruvananthapuram"
]

DISTANCES = {
    ("Bangalore","Mysore"):150,("Bangalore","Chennai"):350,("Bangalore","Hyderabad"):570,
    ("Bangalore","Mumbai"):980,("Bangalore","Delhi"):2150,("Bangalore","Kolkata"):1870,
    ("Bangalore","Pune"):840,("Bangalore","Ahmedabad"):1300,("Bangalore","Jaipur"):2050,
    ("Bangalore","Kochi"):590,("Bangalore","Goa"):560,("Bangalore","Bhopal"):1420,
    ("Bangalore","Lucknow"):2000,("Bangalore","Patna"):2100,("Bangalore","Surat"):1250,
    ("Bangalore","Nagpur"):1130,("Bangalore","Indore"):1380,("Bangalore","Visakhapatnam"):1070,
    ("Bangalore","Coimbatore"):360,("Bangalore","Agra"):2200,("Bangalore","Varanasi"):2150,
    ("Bangalore","Chandigarh"):2550,("Bangalore","Amritsar"):2700,("Bangalore","Jodhpur"):2050,
    ("Bangalore","Udaipur"):1750,("Bangalore","Ranchi"):1800,("Bangalore","Bhubaneswar"):1600,
    ("Bangalore","Mangalore"):350,("Bangalore","Thiruvananthapuram"):730,
    ("Mumbai","Delhi"):1400,("Mumbai","Chennai"):1330,("Mumbai","Hyderabad"):710,
    ("Mumbai","Kolkata"):2050,("Mumbai","Pune"):150,("Mumbai","Ahmedabad"):530,
    ("Mumbai","Jaipur"):1150,("Mumbai","Kochi"):1200,("Mumbai","Goa"):590,
    ("Mumbai","Bhopal"):780,("Mumbai","Lucknow"):1200,("Mumbai","Patna"):1600,
    ("Mumbai","Surat"):280,("Mumbai","Nagpur"):870,("Mumbai","Indore"):590,
    ("Mumbai","Visakhapatnam"):1500,("Mumbai","Coimbatore"):1150,("Mumbai","Agra"):1320,
    ("Mumbai","Varanasi"):1550,("Mumbai","Chandigarh"):1580,("Mumbai","Amritsar"):1780,
    ("Mumbai","Jodhpur"):900,("Mumbai","Udaipur"):650,("Mumbai","Ranchi"):1700,
    ("Mumbai","Bhubaneswar"):1850,("Mumbai","Mangalore"):1000,("Mumbai","Thiruvananthapuram"):1550,
    ("Mumbai","Mysore"):1050,
    ("Delhi","Jaipur"):280,("Delhi","Chandigarh"):260,("Delhi","Amritsar"):450,
    ("Delhi","Agra"):200,("Delhi","Lucknow"):555,("Delhi","Varanasi"):820,
    ("Delhi","Patna"):1050,("Delhi","Kolkata"):1480,("Delhi","Bhopal"):770,
    ("Delhi","Indore"):870,("Delhi","Jodhpur"):620,("Delhi","Udaipur"):670,
    ("Delhi","Nagpur"):1160,("Delhi","Ranchi"):1280,("Delhi","Bhubaneswar"):1700,
    ("Delhi","Hyderabad"):1570,("Delhi","Chennai"):2170,("Delhi","Kochi"):2700,
    ("Delhi","Goa"):1900,("Delhi","Visakhapatnam"):1730,("Delhi","Coimbatore"):2300,
    ("Delhi","Mangalore"):2100,("Delhi","Surat"):1150,("Delhi","Ahmedabad"):950,
    ("Delhi","Thiruvananthapuram"):2900,("Delhi","Mysore"):2300,("Delhi","Pune"):1450,
    ("Chennai","Hyderabad"):630,("Chennai","Kochi"):720,("Chennai","Coimbatore"):490,
    ("Chennai","Visakhapatnam"):800,("Chennai","Bhubaneswar"):1200,("Chennai","Kolkata"):1650,
    ("Chennai","Thiruvananthapuram"):750,("Chennai","Mangalore"):730,("Chennai","Mysore"):450,
    ("Chennai","Goa"):930,("Chennai","Pune"):1180,("Chennai","Nagpur"):1100,
    ("Chennai","Lucknow"):1700,("Chennai","Patna"):1900,("Chennai","Ranchi"):1700,
    ("Hyderabad","Kochi"):1150,("Hyderabad","Visakhapatnam"):620,("Hyderabad","Nagpur"):490,
    ("Hyderabad","Pune"):570,("Hyderabad","Goa"):690,("Hyderabad","Bhubaneswar"):1000,
    ("Hyderabad","Kolkata"):1490,("Hyderabad","Lucknow"):1400,("Hyderabad","Bhopal"):880,
    ("Kolkata","Patna"):600,("Kolkata","Ranchi"):410,("Kolkata","Bhubaneswar"):440,
    ("Kolkata","Varanasi"):680,("Kolkata","Lucknow"):1000,("Kolkata","Nagpur"):1320,
    ("Ahmedabad","Surat"):270,("Ahmedabad","Jaipur"):660,("Ahmedabad","Indore"):420,
    ("Ahmedabad","Jodhpur"):490,("Ahmedabad","Udaipur"):250,("Ahmedabad","Bhopal"):680,
    ("Jaipur","Agra"):240,("Jaipur","Jodhpur"):340,("Jaipur","Udaipur"):400,
    ("Jaipur","Chandigarh"):530,("Jaipur","Amritsar"):620,("Jaipur","Lucknow"):580,
    ("Lucknow","Varanasi"):320,("Lucknow","Patna"):415,("Lucknow","Agra"):370,
    ("Varanasi","Patna"):270,("Varanasi","Ranchi"):520,
    ("Chandigarh","Amritsar"):230,
    ("Goa","Mangalore"):330,("Goa","Kochi"):640,
    ("Kochi","Coimbatore"):210,("Kochi","Thiruvananthapuram"):220,("Kochi","Mangalore"):450,
    ("Coimbatore","Thiruvananthapuram"):340,("Coimbatore","Mangalore"):420,
    ("Nagpur","Bhopal"):360,("Nagpur","Indore"):460,("Nagpur","Ranchi"):680,
    ("Bhopal","Indore"):190,
    ("Ranchi","Bhubaneswar"):440,("Ranchi","Patna"):330,
    ("Mysore","Coimbatore"):200,("Mysore","Mangalore"):250,("Mysore","Kochi"):480,
}

def get_dist(a, b):
    d = DISTANCES.get((a,b)) or DISTANCES.get((b,a))
    if not d:
        d = random.randint(200, 1500)
    return d

TRAIN_CLASSES = ["General","Sleeper","AC 3 Tier","AC 2 Tier","First Class"]
BUS_CLASSES   = ["General","Sleeper","AC Seater","AC Sleeper"]
FLIGHT_CLASSES= ["Economy","Business"]
TICKET_TYPES  = ["train","bus","flight"]
CHANNELS      = ["official_website","official_website","official_website",
                  "official_app","official_app","reseller","reseller","dark_web"]

PRICE_RATES = {
    "train":  {"General":0.5,"Sleeper":1.0,"AC 3 Tier":1.8,"AC 2 Tier":2.5,"First Class":3.5},
    "bus":    {"General":1.2,"Sleeper":2.0,"AC Seater":2.5,"AC Sleeper":3.0},
    "flight": {"Economy":5.0,"Business":9.0}
}
FLIGHT_BASE = {"Economy":800,"Business":2000}

def base_price(ticket_type, cls, dist):
    rate = PRICE_RATES.get(ticket_type,{}).get(cls,1.5)
    base = FLIGHT_BASE.get(cls, 0) if ticket_type == "flight" else 0
    price = round(rate * dist + base + random.gauss(0, 50), 2)
    return max(price, 50.0)

def make_pnr(valid=True):
    if valid:
        return ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ",k=2)) + \
               ''.join(random.choices("0123456789",k=8))
    patterns = [
        lambda: ''.join(random.choices("0123456789",k=10)),          # all digits
        lambda: "1111111111",                                          # all same
        lambda: "XXXXXXXXXX",                                          # all letters
        lambda: ''.join(random.choices("AB",k=4)),                    # too short
        lambda: '#' + ''.join(random.choices("ABCD1234",k=6)),        # invalid char
    ]
    return random.choice(patterns)()

def random_date_pair(future=True, impossible=False):
    base = datetime(2025, 1, 1)
    end  = datetime(2027, 1, 1)
    booking_dt = base + timedelta(days=random.randint(0, (end - base).days))
    if impossible:
        travel_dt = booking_dt - timedelta(days=random.randint(1, 30))
    elif not future:
        travel_dt = datetime(2030, 1, 1) + timedelta(days=random.randint(0, 365))
    else:
        travel_dt = booking_dt + timedelta(days=random.randint(1, 90))
    return booking_dt.date().isoformat(), travel_dt.date().isoformat()

def gen_seat(ticket_type):
    if ticket_type == "train":
        return f"{random.randint(1,72)}{random.choice('ABCD')}"
    if ticket_type == "bus":
        return f"S{random.randint(1,50)}"
    return f"{random.randint(1,30)}{random.choice('ABCDEF')}"

# ── Generate Normal Tickets ───────────────────────────────────────────────────
def gen_normal():
    tt   = random.choice(TICKET_TYPES)
    src, dst = random.sample(CITIES, 2)
    dist = get_dist(src, dst)
    cls  = random.choice(TRAIN_CLASSES if tt=="train" else BUS_CLASSES if tt=="bus" else FLIGHT_CLASSES)
    price= base_price(tt, cls, dist)
    book_d, trav_d = random_date_pair()
    days = (datetime.fromisoformat(trav_d) - datetime.fromisoformat(book_d)).days
    
    device = random.choice(["mobile", "desktop", "tablet"])
    ip_change = 0 if random.random() > 0.1 else 1
    
    return {
        "ticket_id":      None,
        "pnr":            make_pnr(valid=True),
        "passenger_name": fake.name(),
        "route":          f"{src} → {dst}",
        "start_station":  src,
        "end_station":    dst,
        "travel_date":    trav_d,
        "booking_date":   book_d,
        "class":          cls,
        "seat":           gen_seat(tt),
        "price":          price,
        "currency":       "INR",
        "ticket_type":    tt,
        "booking_channel":random.choice(["official_website","official_website","official_app"]),
        "days_until_travel": days,
        "price_per_km":   round(price/dist,4) if dist else 0,
        "booking_frequency": random.randint(1, 5),
        "time_taken_sec": random.randint(30, 120),
        "login_frequency": random.randint(1, 10),
        "device_type":    device,
        "ip_change_flag": ip_change,
        "is_fraud":       0
    }

# ── Generate Fraud Tickets ────────────────────────────────────────────────────
FRAUD_PATTERNS = ["price_low","price_high","invalid_pnr","impossible_date",
                  "future_date","dup_pnr","dark_web","cross_class"]

def gen_fraud(existing_pnrs):
    pattern = random.choice(FRAUD_PATTERNS)
    tt   = random.choice(TICKET_TYPES)
    src, dst = random.sample(CITIES, 2)
    dist = get_dist(src, dst)
    cls  = random.choice(TRAIN_CLASSES if tt=="train" else BUS_CLASSES if tt=="bus" else FLIGHT_CLASSES)
    normal_price = base_price(tt, cls, dist)
    book_d, trav_d = random_date_pair()

    price = normal_price
    pnr   = make_pnr(valid=True)
    channel = random.choice(["official_website","official_app","reseller"])

    if pattern == "price_low":
        price = round(normal_price * random.uniform(0.05, 0.15), 2)
    elif pattern == "price_high":
        price = round(normal_price * random.uniform(5, 15), 2)
    elif pattern == "invalid_pnr":
        pnr = make_pnr(valid=False)
    elif pattern == "impossible_date":
        book_d, trav_d = random_date_pair(impossible=True)
    elif pattern == "future_date":
        book_d, trav_d = random_date_pair(future=False)
    elif pattern == "dup_pnr" and existing_pnrs:
        pnr = random.choice(existing_pnrs)
        src2, dst2 = random.sample(CITIES, 2)
        src, dst = src2, dst2
    elif pattern == "dark_web":
        channel = "dark_web"
        price   = round(normal_price * random.uniform(0.1, 0.3), 2)
    elif pattern == "cross_class":
        # bus ticket but with train class
        if tt == "bus":
            cls = random.choice(TRAIN_CLASSES)
        else:
            cls = random.choice(BUS_CLASSES)

    days = (datetime.fromisoformat(trav_d) - datetime.fromisoformat(book_d)).days
    
    device = random.choice(["mobile", "desktop", "tablet", "unknown"])
    ip_change = 1 if random.random() > 0.4 else 0
    bfreq = random.randint(10, 25) if pattern == "dark_web" else random.randint(1, 10)
    ttsec = random.randint(2, 15) if pattern == "dark_web" else random.randint(5, 120)
    
    return {
        "ticket_id":      None,
        "pnr":            pnr,
        "passenger_name": fake.name(),
        "route":          f"{src} → {dst}",
        "start_station":  src,
        "end_station":    dst,
        "travel_date":    trav_d,
        "booking_date":   book_d,
        "class":          cls,
        "seat":           gen_seat(tt),
        "price":          price,
        "currency":       "INR",
        "ticket_type":    tt,
        "booking_channel": channel,
        "days_until_travel": days,
        "price_per_km":   round(price/dist, 4) if dist else 0,
        "booking_frequency": bfreq,
        "time_taken_sec": ttsec,
        "login_frequency": random.randint(1, 5),
        "device_type":    "unknown" if pattern == "dark_web" else device,
        "ip_change_flag": ip_change,
        "is_fraud":       1
    }

# ── Build Dataset ─────────────────────────────────────────────────────────────
records   = []
pnr_pool  = []

# 5000 normal
for _ in range(5000):
    rec = gen_normal()
    pnr_pool.append(rec["pnr"])
    records.append(rec)

# 5000 fraud
for _ in range(5000):
    rec = gen_fraud(pnr_pool)
    records.append(rec)

random.shuffle(records)
df = pd.DataFrame(records)
df["ticket_id"] = range(1, len(df)+1)

# ── Save ──────────────────────────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "train_tickets.csv")
df.to_csv(out_path, index=False)

print(f"Dataset shape:    {df.shape}")
print(f"Normal tickets:   {(df['is_fraud']==0).sum()}")
print(f"Fraud tickets:    {(df['is_fraud']==1).sum()}")
print(f"Saved -> {out_path}")
