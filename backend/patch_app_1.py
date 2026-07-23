import os
import re

app_path = r'c:\Users\MY PC\Desktop\e-ticket\backend\app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
imports_old = """import os, sqlite3, pickle, random, string, smtplib
from datetime import datetime, timedelta
from functools import wraps
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash"""

imports_new = """import os, sqlite3, pickle, random, string, smtplib, json, subprocess
from datetime import datetime, timedelta
from functools import wraps
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, g, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import cv2
import pytesseract
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
"""

content = content.replace(imports_old, imports_new)

# 2. Add UPLOADS_DIR and REPORTS_DIR
dirs_old = """BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
DB_PATH      = os.path.join(BASE_DIR, "..", "database.db")
MODEL_PATH   = os.path.join(BASE_DIR, "..", "model", "fraud_model.pkl")"""

dirs_new = """BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
DB_PATH      = os.path.join(BASE_DIR, "..", "database.db")
MODEL_PATH   = os.path.join(BASE_DIR, "..", "model", "fraud_model.pkl")
SCAN_MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "scan_model.pkl")
UPLOADS_DIR  = os.path.join(BASE_DIR, "..", "uploads")
REPORTS_DIR  = os.path.join(BASE_DIR, "..", "reports")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
"""

content = content.replace(dirs_old, dirs_new)

# 3. Add scan model loading
scan_model_loading = """
scan_model_bundle = None
def load_scan_model():
    global scan_model_bundle
    try:
        with open(SCAN_MODEL_PATH, "rb") as f: scan_model_bundle = pickle.load(f)
        print(f"Scan Model loaded | Ensemble Accuracy={scan_model_bundle['accuracy']*100:.2f}%")
    except Exception as e: print(f"Scan Model not loaded: {e}")

load_scan_model()
"""
content = content.replace("except Exception as e: print(f\"ML Model not loaded: {e}\")", "except Exception as e: print(f\"ML Model not loaded: {e}\")\n" + scan_model_loading)


with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated basic app.py configuration.")
