#!/usr/bin/env python3
"""
Train a Document Classifier (Ticket vs Non-Ticket) for the Scanner.
Uses synthetic OCR data based on ticket keywords.
Output: ml/scanner_model.pkl
"""
import os, pickle, random
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ── Keywords ──────────────────────────────────────────────────────────────────
TICKET_WORDS = [
    "PNR", "Passenger", "Train No", "Coach", "Seat", "Fare", "IRCTC", 
    "Indian Railways", "Bus", "Flight", "Boarding Pass", "Gate", "Station", 
    "Class", "Sleeper", "Quota", "Confirmed", "Waiting List", "RAC", 
    "Berth", "Departure", "Arrival", "Travel Date", "Adult", "Child",
    "Ticket ID", "Transaction ID", "Total Fare", "GST", "Payment Success",
    "Coach Number", "Seat Number", "Source", "Destination", "Via", "Platform"
]

NOISE_WORDS = [
    "Menu", "Invoice", "Bill", "Order", "Recipe", "Ingredients", "Selfie", 
    "Profile", "Status", "Chat", "Message", "Email", "Subject", "Regards",
    "Discount", "Promo", "Sale", "Limited Time", "Buy Now", "Add to Cart",
    "Meeting", "Zoom", "Calendar", "Notes", "Project", "Tasks", "Done",
    "Weather", "News", "Sports", "Score", "Match", "Entertainment", "Movie",
    "Cast", "Rating", "Review", "Comments", "Like", "Share", "Subscribe",
    "Database", "Schema", "Table", "Query", "Primary Key", "Foreign Key",
    "String", "Integer", "Boolean", "Float", "Array", "Object", "Null",
    "Listing", "Contract", "User", "Farmer", "Company", "Seller", "Product",
    "Type", "ID", "PK", "FK", "Relationship", "Diagram", "Entity", "Attribute"
]

def generate_ticket_text():
    # Pick 5-15 random ticket words
    words = random.sample(TICKET_WORDS, k=random.randint(5, 15))
    # Add some random names/numbers
    words.append(str(random.randint(10000, 99999)))
    words.append(random.choice(["RAHUL", "VIVEK", "AMIT", "PRIYA", "SNEHA"]))
    random.shuffle(words)
    return " ".join(words)

def generate_noise_text():
    # Pick 5-15 random noise words
    words = random.sample(NOISE_WORDS, k=random.randint(5, 15))
    # Add some random filler
    words.append(random.choice(["The", "A", "Is", "And", "Or", "But"]))
    random.shuffle(words)
    return " ".join(words)

# ── Build Dataset ─────────────────────────────────────────────────────────────
records = []
for _ in range(5000):
    records.append({"text": generate_ticket_text(), "is_ticket": 1})
for _ in range(5000):
    records.append({"text": generate_noise_text(), "is_ticket": 0})

df = pd.DataFrame(records)
random_indices = np.random.permutation(len(df))
df = df.iloc[random_indices]

# ── Train Model ───────────────────────────────────────────────────────────────
print("Training Scanner Document Classifier...")
X_train, X_test, y_train, y_test = train_test_split(df["text"], df["is_ticket"], test_size=0.2, random_state=42)

vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec  = vectorizer.transform(X_test)

model = LogisticRegression(random_state=42)
model.fit(X_train_vec, y_train)

preds = model.predict(X_test_vec)
acc = accuracy_score(y_test, preds)
print(f"Accuracy: {acc*100:.2f}%")

# ── Save Model ────────────────────────────────────────────────────────────────
ml_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(ml_dir, "scanner_model.pkl")

bundle = {
    "vectorizer": vectorizer,
    "model":      model,
    "accuracy":   acc,
    "trained_at": pd.Timestamp.now().isoformat()
}

with open(out_path, "wb") as f:
    pickle.dump(bundle, f)

print(f"Scanner model saved -> {out_path}")
