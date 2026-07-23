import os, random, json, csv
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import qrcode
from datetime import datetime, timedelta

# Settings
OUT_DIR = os.path.join(os.path.dirname(__file__), "dataset")
REAL_DIR = os.path.join(OUT_DIR, "real")
FAKE_DIR = os.path.join(OUT_DIR, "fake")
os.makedirs(REAL_DIR, exist_ok=True)
os.makedirs(FAKE_DIR, exist_ok=True)

NUM_BASE = 100  # 100 base real tickets
AUG_PER_BASE = 5 # 5 augmentations per real = 500
# Another 500 fake tickets

# Try to find a font
FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = None # Default font

def gen_pnr():
    return "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3)) + "".join(random.choices("0123456789", k=7))

def create_base_ticket(pnr, price, date_str, passenger):
    # Create white canvas
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        font_h = ImageFont.truetype(FONT_PATH, 24) if FONT_PATH else ImageFont.load_default()
        font_n = ImageFont.truetype(FONT_PATH, 18) if FONT_PATH else ImageFont.load_default()
    except:
        font_h = ImageFont.load_default()
        font_n = ImageFont.load_default()

    # Layout
    draw.rectangle([10, 10, 590, 290], outline=(0, 0, 0), width=2)
    draw.text((20, 20), "INDIAN RAILWAYS - E-TICKET", fill=(0, 0, 0), font=font_h)
    draw.line([20, 50, 580, 50], fill=(100, 100, 100), width=1)
    
    draw.text((20, 70), f"PNR: {pnr}", fill=(0, 0, 0), font=font_n)
    draw.text((20, 100), f"Passenger: {passenger}", fill=(0, 0, 0), font=font_n)
    draw.text((20, 130), f"Price: INR {price}", fill=(0, 0, 0), font=font_n)
    draw.text((20, 160), f"Date: {date_str}", fill=(0, 0, 0), font=font_n)
    draw.text((20, 190), "Status: CONFIRMED", fill=(0, 150, 0), font=font_n)
    
    # QR Code
    qr = qrcode.QRCode(box_size=4)
    qr.add_data(pnr)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img.paste(qr_img, (450, 70))
    
    return img

def augment(img):
    # Convert to cv2
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # Random Rotation
    angle = random.uniform(-5, 5)
    h, w = cv_img.shape[:2]
    M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
    cv_img = cv2.warpAffine(cv_img, M, (w, h), borderValue=(255,255,255))
    
    # Random Brightness/Contrast
    alpha = random.uniform(0.8, 1.2) # Contrast
    beta = random.randint(-20, 20)   # Brightness
    cv_img = cv2.convertScaleAbs(cv_img, alpha=alpha, beta=beta)
    
    # Random Blur
    if random.random() > 0.7:
        cv_img = cv2.GaussianBlur(cv_img, (3, 3), 0)
        
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

def create_fake(img):
    # Tamper with the image
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # 1. Sloppy Price change
    if random.random() > 0.5:
        # Draw a white box over price
        cv2.rectangle(cv_img, (110, 130), (250, 155), (255, 255, 255), -1)
        # Put new price with slightly different font or alignment
        cv2.putText(cv_img, str(random.randint(5000, 9999)), (115, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        # Add some "tamper noise" around it
        noise = np.random.randint(0, 50, (25, 140, 3), dtype='uint8')
        cv_img[130:155, 110:250] = cv2.addWeighted(cv_img[130:155, 110:250], 0.8, noise, 0.2, 0)

    # 2. Localized Blur (simulating bad editing)
    if random.random() > 0.5:
        x, y = random.randint(20, 300), random.randint(20, 200)
        cv_img[y:y+40, x:x+100] = cv2.GaussianBlur(cv_img[y:y+40, x:x+100], (15, 15), 0)

    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

labels = []

print("Generating dataset...")
for i in range(NUM_BASE):
    pnr = gen_pnr()
    price = random.randint(200, 2000)
    date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
    passenger = random.choice(["Amit Kumar", "Sita Devi", "Rahul Singh", "Priya Sharma", "Vivek Gupta"])
    
    base = create_base_ticket(pnr, price, date, passenger)
    
    # Save Real & Augmentations
    for a in range(AUG_PER_BASE):
        aug_img = augment(base)
        fname = f"real_{i}_{a}.jpg"
        aug_img.save(os.path.join(REAL_DIR, fname))
        labels.append({"image": f"real/{fname}", "label": "real"})
        
    # Save Fake & Augmentations
    for f in range(AUG_PER_BASE):
        fake_img = create_fake(base)
        fake_img = augment(fake_img)
        fname = f"fake_{i}_{f}.jpg"
        fake_img.save(os.path.join(FAKE_DIR, fname))
        labels.append({"image": f"fake/{fname}", "label": "fake"})

# Save labels.csv
with open(os.path.join(OUT_DIR, "labels.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["image", "label"])
    writer.writeheader()
    writer.writerows(labels)

print(f"Total images generated: {len(labels)}")
print(f"Labels saved to {os.path.join(OUT_DIR, 'labels.csv')}")
