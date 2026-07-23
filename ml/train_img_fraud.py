import os, pickle
import cv2
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "dataset")
LABELS_PATH = os.path.join(DATA_DIR, "labels.csv")

def extract_features(img_path):
    img = cv2.imread(img_path)
    if img is None: return None
    
    # 1. Resize for consistency
    img_res = cv2.resize(img, (200, 100))
    gray = cv2.cvtColor(img_res, cv2.COLOR_BGR2GRAY)
    
    # 2. Edge Density (Canny)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size
    
    # 3. Blurriness (Laplacian Variance)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # 4. Color Distribution (Mean/Std)
    hsv = cv2.cvtColor(img_res, cv2.COLOR_BGR2HSV)
    h_mean, h_std = np.mean(hsv[:,:,0]), np.std(hsv[:,:,0])
    s_mean, s_std = np.mean(hsv[:,:,1]), np.std(hsv[:,:,1])
    v_mean, v_std = np.mean(hsv[:,:,2]), np.std(hsv[:,:,2])
    
    # 5. HOG features (simplified - just take a few histogram bins)
    win_size = (200, 100)
    block_size = (20, 20)
    block_stride = (10, 10)
    cell_size = (10, 10)
    nbins = 9
    hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
    hog_feats = hog.compute(gray).flatten()
    
    # Combine
    basic_feats = [edge_density, blur_score, h_mean, h_std, s_mean, s_std, v_mean, v_std]
    # To keep it simple and fast, we'll use a subset of HOG or just basic feats
    # Let's use a subset of HOG (every 50th feature to keep dimensionality manageable)
    combined = basic_feats + hog_feats[::50].tolist()
    
    return combined

print("Extracting features from dataset...")
df = pd.read_csv(LABELS_PATH)
X = []
y = []

for idx, row in df.iterrows():
    f = extract_features(os.path.join(DATA_DIR, row["image"]))
    if f:
        X.append(f)
        y.append(1 if row["label"] == "fake" else 0)

X = np.array(X)
y = np.array(y)

print(f"Dataset size: {len(X)} samples, {len(X[0])} features each")

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model
print("Training Random Forest Classifier...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Accuracy
preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f"Model Accuracy: {acc*100:.2f}%")

# Save model
OUT_PATH = os.path.join(BASE_DIR, "img_fraud_model.pkl")
with open(OUT_PATH, "wb") as f:
    pickle.dump({
        "model": model,
        "accuracy": acc,
        "features": "custom_cv_hog_subset"
    }, f)

print(f"Model saved to {OUT_PATH}")
