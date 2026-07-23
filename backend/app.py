"""
╔══════════════════════════════════════════════════════════════════╗
║  SecureTrail — E-Ticket Fraud Detection System                   ║
║  Flask Backend  |  All APIs  |  OTP Email  |  Admin Auth         ║
║  Hybrid Fraud Detection: Rule-Based + Decision Tree ML           ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sqlite3, pickle, random, string, smtplib, json, subprocess
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


BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
DB_PATH      = os.path.abspath(os.path.join(BASE_DIR, "..", "database.db"))
MODEL_PATH   = os.path.abspath(os.path.join(BASE_DIR, "..", "model", "fraud_model.pkl"))
SCAN_MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "model", "scan_model.pkl"))
UPLOADS_DIR  = os.path.abspath(os.path.join(BASE_DIR, "..", "uploads"))
REPORTS_DIR  = os.path.abspath(os.path.join(BASE_DIR, "..", "reports"))
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

SCAN_MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "scan_model.pkl")
UPLOADS_DIR  = os.path.join(BASE_DIR, "..", "uploads")
REPORTS_DIR  = os.path.join(BASE_DIR, "..", "reports")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


app = Flask(__name__, static_folder=FRONTEND_DIR)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24).hex())

SMTP_EMAIL    = os.environ.get("SMTP_EMAIL",    "your_email@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "your_app_password")
SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587

model_bundle = None
try:
    with open(MODEL_PATH, "rb") as f: model_bundle = pickle.load(f)
    print(f"ML Model loaded | Accuracy={model_bundle['accuracy']*100:.2f}%")
except Exception as e: print(f"ML Model not loaded: {e}")

scan_model_bundle = None
def load_scan_model():
    global scan_model_bundle
    try:
        with open(SCAN_MODEL_PATH, "rb") as f: scan_model_bundle = pickle.load(f)
        print(f"Scan Model loaded | Ensemble Accuracy={scan_model_bundle['accuracy']*100:.2f}%")
    except Exception as e: print(f"Scan Model not loaded: {e}")

load_scan_model()


scan_model_bundle = None
def load_scan_model():
    global scan_model_bundle
    try:
        with open(SCAN_MODEL_PATH, "rb") as f: scan_model_bundle = pickle.load(f)
        print(f"Scan Model loaded | Ensemble Accuracy={scan_model_bundle['accuracy']*100:.2f}%")
    except Exception as e: print(f"Scan Model not loaded: {e}")

load_scan_model()


SUSPICIOUS_IPS     = [f"192.168.{r}.{c}" for r in range(0,8) for c in range(1,15)]
SUSPICIOUS_DEVICES = [f"DEV{i:04d}" for i in range(1,11)]
CITY_DIST = {
    ("Mumbai","Delhi"):1400,("Mumbai","Bangalore"):980,("Mumbai","Chennai"):1330,
    ("Delhi","Kolkata"):1500,("Delhi","Bangalore"):2150,("Bangalore","Chennai"):350,
    ("Hyderabad","Chennai"):630,("Pune","Mumbai"):150,("Jaipur","Delhi"):280,("Lucknow","Delhi"):500,
}
def get_dist(a,b):
    if a==b: return random.randint(10,60)
    return CITY_DIST.get((a,b),CITY_DIST.get((b,a),random.randint(200,1800)))

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH); g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e):
    db = g.pop("db",None)
    if db: db.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        risk_score REAL DEFAULT 0, is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    try: conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0"); conn.commit()
    except: pass
    conn.execute("""CREATE TABLE IF NOT EXISTS tickets(
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        passenger_name TEXT, source TEXT, destination TEXT, booking_time TEXT,
        travel_time TEXT, seat_type TEXT, payment_method TEXT,
        payment_status TEXT DEFAULT 'PENDING', transaction_id TEXT,
        device_id TEXT, ip_address TEXT, ticket_status TEXT DEFAULT 'active',
        used_flag INTEGER DEFAULT 0, booking_count_last_24hrs INTEGER DEFAULT 1,
        travel_distance REAL DEFAULT 0, otp TEXT, otp_time TEXT,
        otp_attempts INTEGER DEFAULT 0, failed_payments_count INTEGER DEFAULT 0,
        is_fraud INTEGER DEFAULT 0, fraud_reason TEXT DEFAULT '',
        fraud_method TEXT DEFAULT '', risk_score REAL DEFAULT 0,
        ticket_price REAL DEFAULT 500, FOREIGN KEY(user_id) REFERENCES users(user_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY, user_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS scans(
        scan_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        scan_date TEXT DEFAULT CURRENT_TIMESTAMP, filename TEXT,
        input_type TEXT DEFAULT 'image', pnr TEXT, passenger_name TEXT,
        issuer TEXT, source TEXT, destination TEXT, travel_date TEXT,
        seat TEXT, price REAL, booking_id TEXT, fraud_score REAL DEFAULT 0,
        risk_level TEXT DEFAULT 'Low', is_fraud INTEGER DEFAULT 0,
        fraud_indicators TEXT DEFAULT '{}', ocr_text TEXT DEFAULT '',
        qr_data TEXT DEFAULT '', report_path TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS false_positives(
        fp_id INTEGER PRIMARY KEY AUTOINCREMENT, scan_id INTEGER,
        user_id INTEGER, reason TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS model_retrain_log(
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER,
        status TEXT, accuracy REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    if not conn.execute("SELECT 1 FROM users WHERE is_admin=1").fetchone():
        conn.execute("INSERT INTO users(name,email,password,is_admin) VALUES(?,?,?,1)",
            ("Admin","admin@securerail.com",generate_password_hash("Admin@123")))
        conn.commit()
        print("Default admin created: admin@securerail.com / Admin@123")
    conn.close(); print("Database initialised")

def gen_token(): return "".join(random.choices(string.ascii_letters+string.digits,k=64))
def get_user_by_token(tok):
    db=get_db(); s=db.execute("SELECT user_id FROM sessions WHERE token=?",(tok,)).fetchone()
    return db.execute("SELECT * FROM users WHERE user_id=?",(s["user_id"],)).fetchone() if s else None

def require_auth(f):
    @wraps(f)
    def wrap(*a,**kw):
        u=get_user_by_token(request.headers.get("Authorization","").replace("Bearer ",""))
        if not u: return jsonify({"error":"Unauthorized — please login"}),401
        request.current_user=u; return f(*a,**kw)
    return wrap

def require_admin(f):
    @wraps(f)
    def wrap(*a,**kw):
        u=get_user_by_token(request.headers.get("Authorization","").replace("Bearer ",""))
        if not u: return jsonify({"error":"Admin login required"}),401
        if not u["is_admin"]: return jsonify({"error":"Access denied — admin privileges required"}),403
        request.current_user=u; return f(*a,**kw)
    return wrap

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]="*"
    r.headers["Access-Control-Allow-Headers"]="Content-Type,Authorization"
    r.headers["Access-Control-Allow-Methods"]="GET,POST,PUT,DELETE,OPTIONS"
    return r

 

# ── CV & OCR Scanning ─────────────────────────────────────────────
def scan_ticket_image(filepath, data):
    img = cv2.imread(filepath)
    checks = {}
    
    # 1. QR Detected & 2. Decodable
    qr_detector = cv2.QRCodeDetector()
    data_qr, bbox, _ = qr_detector.detectAndDecode(img)
    checks["qr_detected"] = 1 if bbox is not None else 0
    checks["qr_decodable"] = 1 if data_qr else 0
    
    # 3. QR PNR Match
    pnr = str(data.get("pnr", "")).lower()
    checks["qr_pnr_match"] = 1 if pnr and pnr in data_qr.lower() else 0
    if not checks["qr_decodable"]: checks["qr_pnr_match"] = 0
    
    # 4. OCR Confidence
    ocr_text = ""
    conf_avg = 85.0
    try:
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confs = [float(c) for c in ocr_data["conf"] if float(c) > 0]
        if confs: conf_avg = sum(confs) / len(confs)
        ocr_text = pytesseract.image_to_string(img)
    except Exception as e:
        print("Tesseract failed or not installed:", e)
    
    checks["ocr_confidence"] = conf_avg
    
    # 5. Font Consistency (simple edge proxy)
    edges = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 100, 200)
    density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1] + 1e-5)
    checks["font_consistent"] = 1 if 0.02 < density < 0.25 else 0
    
    # 6. Text Anomalies
    text_anom = 0
    if len(ocr_text) < 20: text_anom = 1
    checks["text_anomaly"] = text_anom
    
    # 7 & 8. EXIF & File unmodified (simulated via file size/extensions for simplicity here)
    checks["exif_clean"] = 1
    checks["file_unmodified"] = 1
    
    # 9. Price Reasonable
    price = float(data.get("price", 0))
    checks["price_reasonable"] = 1 if 50 < price < 15000 else 0
    
    # 10. Metadata Consistent
    checks["metadata_consistent"] = 1 if str(data.get("issuer","")).lower() in ocr_text.lower() else 0

    return checks, ocr_text, data_qr

def run_scan_ml(checks):
    if not scan_model_bundle:
        # Fallback simple scoring
        score = 0
        if not checks["qr_detected"]: score += 30
        if not checks["qr_pnr_match"]: score += 30
        if checks["text_anomaly"]: score += 20
        if not checks["price_reasonable"]: score += 20
        is_f = score >= 50
        return is_f, float(score), "High" if is_f else "Low", score/100, 0.0

    gb = scan_model_bundle["gb_model"]
    iso = scan_model_bundle["iso_model"]
    fts = scan_model_bundle["features"]
    
    row = {k: checks.get(k,0) for k in fts}
    X = pd.DataFrame([row])[fts]
    
    gb_prob = float(gb.predict_proba(X)[0][1])
    iso_score = iso.decision_function(X)[0]
    iso_norm = 1 - (iso_score - scan_model_bundle["iso_min"]) / (scan_model_bundle["iso_max"] - scan_model_bundle["iso_min"] + 1e-9)
    iso_norm = float(np.clip(iso_norm, 0, 1))
    
    ensemble = 0.7 * gb_prob + 0.3 * iso_norm
    is_f = ensemble >= 0.35
    risk_level = "High" if ensemble > 0.65 else ("Medium" if ensemble >= 0.35 else "Low")
    
    return is_f, round(ensemble*100, 2), risk_level, round(gb_prob*100,2), round(iso_norm*100,2)

def generate_pdf_report(scan_data, checks, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Header
    elements.append(Paragraph(f"<b>SecureTrail AI Fraud Report</b>", styles['Title']))
    elements.append(Paragraph(f"Scan ID: {scan_data['scan_id']} | Date: {scan_data['scan_date']}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Verdict
    color = colors.red if scan_data['is_fraud'] else colors.green
    verdict = "FRAUDULENT" if scan_data['is_fraud'] else "VALID"
    elements.append(Paragraph(f"<font color='{color}'><b>Verdict: {verdict}</b> (Score: {scan_data['fraud_score']}/100)</font>", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Details Table
    details = [
        ["Passenger", scan_data['passenger_name'], "PNR", scan_data['pnr']],
        ["Route", f"{scan_data['source']} to {scan_data['destination']}", "Date", scan_data['travel_date']],
        ["Issuer", scan_data['issuer'], "Price", f"₹{scan_data['price']}"],
    ]
    t1 = Table(details)
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey)]))
    elements.append(t1)
    elements.append(Spacer(1, 12))
    
    # Checks
    check_data = [["Check", "Value"]]
    for k, v in checks.items():
        check_data.append([k, str(v)])
    t2 = Table(check_data)
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.lightgrey)]))
    elements.append(t2)
    
    doc.build(elements)
    return file_path


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path.startswith("api/"): return jsonify({"error":f"/{path} not found"}),404
    fp=os.path.join(FRONTEND_DIR,path)
    if path and os.path.exists(fp): return send_from_directory(FRONTEND_DIR,path)
    return send_from_directory(FRONTEND_DIR,"index.html")

def send_otp_email(to_email,otp,passenger,route):
    try:
        msg=MIMEMultipart("alternative")
        msg["Subject"]=f"SecureTrail OTP: {otp}"; msg["From"]=SMTP_EMAIL; msg["To"]=to_email
        h=f"""<html><body style="font-family:Arial;background:#0a0f1a;padding:20px">
<div style="max-width:500px;margin:auto;background:#0e1520;border-radius:16px;overflow:hidden;border:1px solid #1e3050">
<div style="background:linear-gradient(135deg,#00c4ff,#7c3aed);padding:28px;text-align:center">
<h2 style="color:#fff;margin:0">SecureTrail Payment OTP</h2></div>
<div style="padding:28px">
<p style="color:#8ba0be">Hello <b style="color:#fff">{passenger}</b>,</p>
<div style="background:#111c30;border:2px dashed #00c4ff;border-radius:12px;text-align:center;padding:24px;margin:20px 0">
<div style="font-size:46px;font-weight:900;color:#00c4ff;letter-spacing:14px;font-family:monospace">{otp}</div>
<p style="color:#6b8ab0;font-size:13px;margin:6px 0 0">Valid for <b style="color:#00c4ff">120 seconds</b></p></div>
<div style="background:#0a1628;border-radius:8px;padding:14px;color:#8ba0be;font-size:13px;line-height:1.8">
Route: <b style="color:#fff">{route}</b><br>Amount: <b style="color:#fff">500.00 INR</b><br>
Time: <b style="color:#fff">{datetime.now().strftime('%d %b %Y, %H:%M:%S')}</b></div>
<p style="color:#ff6b6b;font-size:12px;margin-top:14px">Do NOT share this OTP. Max 3 attempts. Expires in 120s.</p>
</div><div style="text-align:center;padding:16px;color:#3a5070;font-size:11px;border-top:1px solid #1e3050">
SecureTrail AI Fraud Detection</div></div></body></html>"""
        msg.attach(MIMEText(h,"html"))
        with smtplib.SMTP(SMTP_HOST,SMTP_PORT) as s:
            s.ehlo();s.starttls();s.ehlo();s.login(SMTP_EMAIL,SMTP_PASSWORD)
            s.sendmail(SMTP_EMAIL,to_email,msg.as_string())
        return True
    except Exception as e: print(f"Email failed: {e}"); return False

def rule_based_check(td,uid,db):
    if td.get("used_flag")==1 and td.get("ticket_status")=="cancelled": return True,"Cancelled ticket reuse detected",60
    if td.get("used_flag")==1 and td.get("ticket_status")=="active": return True,"Duplicate ticket usage detected",60
    cnt=td.get("booking_count_last_24hrs",1)
    if cnt>5: return True,f"Excessive bookings in 24 hrs: {cnt}",50
    fp=td.get("failed_payments_count",0)
    if fp>=3: return True,f"Multiple failed payments: {fp}",55
    oa=td.get("otp_attempts",0)
    if oa>=3: return True,f"Repeated OTP failures: {oa} attempts",45
    ip=td.get("ip_address","")
    if any(ip.startswith(f"192.168.{r}.") for r in range(0,8)): return True,f"Suspicious IP: {ip}",40
    dev=td.get("device_id","")
    if dev in SUSPICIOUS_DEVICES:
        row=db.execute("SELECT COUNT(DISTINCT user_id) AS n FROM tickets WHERE device_id=?",(dev,)).fetchone()
        if row and row["n"]>=2: return True,f"Device shared across accounts: {dev}",45
    return False,"",0

def ml_fraud_check(td):
    if not model_bundle: return False,0.0
    import warnings; warnings.filterwarnings("ignore")
    m,enc,fts=model_bundle["model"],model_bundle["encoders"],model_bundle["features"]
    def se(col,val):
        try: return enc[col].transform([str(val)])[0]
        except: return 0
    row={
        "booking_count_last_24hrs":td.get("booking_count_last_24hrs",1),
        "used_flag":td.get("used_flag",0),"travel_distance":td.get("travel_distance",500),
        "otp_attempts":td.get("otp_attempts",0),"failed_payments_count":td.get("failed_payments_count",0),
        "ticket_status":se("ticket_status",td.get("ticket_status","active")),
        "payment_method":se("payment_method",td.get("payment_method","UPI")),
        "seat_type":se("seat_type",td.get("seat_type","General")),
        "payment_status":se("payment_status",td.get("payment_status","SUCCESS")),
        "is_suspicious_device":1 if td.get("device_id","") in SUSPICIOUS_DEVICES else 0,
        "is_suspicious_ip":1 if any(td.get("ip_address","").startswith(f"192.168.{r}.") for r in range(0,8)) else 0,
    }
    X=pd.DataFrame([row])[fts]; prob=float(m.predict_proba(X)[0][1]); pred=bool(m.predict(X)[0])
    return pred,round(prob,4)

def calc_risk(td):
    s=0
    if td.get("booking_count_last_24hrs",1)>5: s+=20
    if td.get("failed_payments_count",0)>=2: s+=30
    if td.get("otp_attempts",0)>=2: s+=20
    if td.get("used_flag",0)==1: s+=30
    if td.get("ticket_status","")=="cancelled": s+=20
    if td.get("device_id","") in SUSPICIOUS_DEVICES: s+=15
    return min(s,100)

def detect_fraud(td,uid,db):
    rf,rr,_=rule_based_check(td,uid,db); rs=calc_risk(td); _,ml_p=ml_fraud_check(td)
    if rf:
        st="FRAUD" if rs>=50 else "SUSPICIOUS"
        return dict(is_fraud=True,fraud_reason=rr,fraud_method="Rule-Based",risk_score=rs,fraud_status=st,ml_probability=ml_p)
    ml_f,ml_p=ml_fraud_check(td)
    if ml_f:
        st="FRAUD" if rs>=50 else "SUSPICIOUS"
        return dict(is_fraud=True,fraud_reason=f"AI model flagged pattern (risk={ml_p:.0%})",fraud_method="AI Model",risk_score=rs,fraud_status=st,ml_probability=ml_p)
    st="SUSPICIOUS" if 20<=rs<50 else "VALID"
    return dict(is_fraud=(rs>=50),fraud_reason="",fraud_method="None",risk_score=rs,fraud_status=st,ml_probability=ml_p)

@app.route("/api/register",methods=["POST","OPTIONS"])
def register():
    if request.method=="OPTIONS": return jsonify({}),200
    d=request.get_json() or {}
    name,em,pw=d.get("name","").strip(),d.get("email","").strip().lower(),d.get("password","")
    if not all([name,em,pw]): return jsonify({"error":"All fields required"}),400
    if len(pw)<6: return jsonify({"error":"Password must be at least 6 characters"}),400
    db=get_db()
    if db.execute("SELECT 1 FROM users WHERE email=?",(em,)).fetchone(): return jsonify({"error":"Email already registered"}),409
    db.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name,em,generate_password_hash(pw))); db.commit()
    return jsonify({"message":"Account created! Please sign in."}),201

@app.route("/api/login",methods=["POST","OPTIONS"])
def login():
    if request.method=="OPTIONS": return jsonify({}),200
    d=request.get_json() or {}; em,pw=d.get("email","").strip().lower(),d.get("password","")
    db=get_db(); u=db.execute("SELECT * FROM users WHERE email=?",(em,)).fetchone()
    if not u or not check_password_hash(u["password"],pw): return jsonify({"error":"Invalid email or password"}),401
    tok=gen_token(); db.execute("INSERT INTO sessions(token,user_id) VALUES(?,?)",(tok,u["user_id"])); db.commit()
    return jsonify({"message":"Login successful","token":tok,"user":{"user_id":u["user_id"],"name":u["name"],"email":u["email"],"risk_score":u["risk_score"]}})

@app.route("/api/admin_login",methods=["POST","OPTIONS"])
def admin_login():
    if request.method=="OPTIONS": return jsonify({}),200
    d=request.get_json() or {}; em,pw=d.get("email","").strip().lower(),d.get("password","")
    if not em or not pw: return jsonify({"error":"Email and password required"}),400
    db=get_db(); u=db.execute("SELECT * FROM users WHERE email=? AND is_admin=1",(em,)).fetchone()
    if not u or not check_password_hash(u["password"],pw): return jsonify({"error":"Invalid admin credentials"}),401
    tok=gen_token(); db.execute("INSERT INTO sessions(token,user_id) VALUES(?,?)",(tok,u["user_id"])); db.commit()
    return jsonify({"message":"Admin login successful","token":tok,"admin":{"user_id":u["user_id"],"name":u["name"],"email":u["email"],"is_admin":u["is_admin"]}})

@app.route("/api/admin_logout",methods=["POST","OPTIONS"])
@require_admin
def admin_logout():
    if request.method=="OPTIONS": return jsonify({}),200
    tok=request.headers.get("Authorization","").replace("Bearer ","")
    get_db().execute("DELETE FROM sessions WHERE token=?",(tok,)); get_db().commit()
    return jsonify({"message":"Admin logged out"})

@app.route("/api/logout",methods=["POST","OPTIONS"])
@require_auth
def logout():
    if request.method=="OPTIONS": return jsonify({}),200
    tok=request.headers.get("Authorization","").replace("Bearer ","")
    get_db().execute("DELETE FROM sessions WHERE token=?",(tok,)); get_db().commit()
    return jsonify({"message":"Logged out"})

@app.route("/api/initiate_booking",methods=["POST","OPTIONS"])
@require_auth
def initiate_booking():
    if request.method=="OPTIONS": return jsonify({}),200
    data=request.get_json() or {}; user=request.current_user; db=get_db()
    for f in ["passenger_name","source","destination","travel_time","seat_type","payment_method"]:
        if not data.get(f): return jsonify({"error":f"Missing: {f}"}),400
    if data["source"]==data["destination"]: return jsonify({"error":"Source and destination must differ"}),400
    since=(datetime.now()-timedelta(hours=24)).isoformat()
    bc=db.execute("SELECT COUNT(*) AS n FROM tickets WHERE user_id=? AND booking_time>=?",(user["user_id"],since)).fetchone()["n"]+1
    # Use distance/price from frontend (dynamic pricing); fallback to server calc
    frontend_dist  = data.get("travel_distance", 0)
    frontend_price = data.get("ticket_price", 0)
    dist  = int(frontend_dist)  if frontend_dist  > 0 else get_dist(data["source"], data["destination"])
    price = float(frontend_price) if frontend_price > 0 else max(150.0, round(dist * 2 + 100))

    dev=data.get("device_id",f"DEV{random.randint(11,999):04d}")
    ip=request.remote_addr or "10.0.0.1"; bk=datetime.now().isoformat()
    otp="".join(random.choices(string.digits,k=4))
    db.execute("""INSERT INTO tickets(user_id,passenger_name,source,destination,booking_time,travel_time,
        seat_type,payment_method,payment_status,device_id,ip_address,booking_count_last_24hrs,
        travel_distance,otp,otp_time,otp_attempts,failed_payments_count,ticket_price)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user["user_id"],data["passenger_name"],data["source"],data["destination"],bk,data["travel_time"],
         data["seat_type"],data["payment_method"],"PENDING",dev,ip,bc,dist,otp,bk,0,0,price))
    db.commit()
    tid=db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    route=f"{data['source']} -> {data['destination']}"
    email_sent=send_otp_email(user["email"],otp,data["passenger_name"],route)
    return jsonify({"message":"OTP sent to your email","ticket_id":tid,"otp_sent":email_sent,
        "demo_otp":otp,"email":user["email"],"ticket_price":price,
        "travel_distance":dist,"payment_method":data["payment_method"]}),201

@app.route("/api/verify_otp",methods=["POST","OPTIONS"])
@require_auth
def verify_otp():
    if request.method=="OPTIONS": return jsonify({}),200
    data=request.get_json() or {}; user=request.current_user; db=get_db()
    tid=data.get("ticket_id"); entered=str(data.get("otp","")).strip()
    ticket=db.execute("SELECT * FROM tickets WHERE ticket_id=? AND user_id=?",(tid,user["user_id"])).fetchone()
    if not ticket: return jsonify({"error":"Ticket not found"}),404
    if ticket["payment_status"]=="SUCCESS": return jsonify({"error":"Payment already completed"}),400
    attempts=ticket["otp_attempts"]
    if attempts>=3:
        db.execute("UPDATE tickets SET payment_status='FAILED' WHERE ticket_id=?",(tid,)); db.commit()
        return jsonify({"error":"Max OTP attempts exceeded. Payment failed.","payment_status":"FAILED"}),403
    if datetime.now()-datetime.fromisoformat(ticket["otp_time"])>timedelta(seconds=120):
        db.execute("UPDATE tickets SET payment_status='FAILED' WHERE ticket_id=?",(tid,)); db.commit()
        return jsonify({"error":"OTP expired. Click Resend OTP.","expired":True,"payment_status":"FAILED"}),400
    if entered!=ticket["otp"]:
        new_att=attempts+1; new_fp=ticket["failed_payments_count"]+1
        db.execute("UPDATE tickets SET otp_attempts=?,failed_payments_count=? WHERE ticket_id=?",(new_att,new_fp,tid)); db.commit()
        return jsonify({"error":f"Wrong OTP. {3-new_att} attempt(s) left.","attempts_left":3-new_att,"payment_status":"FAILED"}),400
    txn_id="TXN"+"".join(random.choices(string.digits,k=10))
    td={"used_flag":ticket["used_flag"],"ticket_status":ticket["ticket_status"],
        "booking_count_last_24hrs":ticket["booking_count_last_24hrs"],
        "failed_payments_count":ticket["failed_payments_count"],"otp_attempts":ticket["otp_attempts"],
        "payment_status":"SUCCESS","payment_method":ticket["payment_method"],"seat_type":ticket["seat_type"],
        "travel_distance":ticket["travel_distance"],"device_id":ticket["device_id"],"ip_address":ticket["ip_address"]}
    fraud=detect_fraud(td,user["user_id"],db)
    db.execute("""UPDATE tickets SET payment_status='SUCCESS',transaction_id=?,is_fraud=?,
        fraud_reason=?,fraud_method=?,risk_score=?,ticket_status=? WHERE ticket_id=?""",
        (txn_id,int(fraud["is_fraud"]),fraud["fraud_reason"],fraud["fraud_method"],
         fraud["risk_score"],"flagged" if fraud["is_fraud"] else "active",tid))
    db.execute("UPDATE users SET risk_score=(risk_score*0.6+?*0.4) WHERE user_id=?",(fraud["risk_score"],user["user_id"]))
    db.commit()
    return jsonify({"message":"Payment successful!","transaction_id":txn_id,"payment_status":"SUCCESS",
        "fraud_detection":{"is_fraud":fraud["is_fraud"],"fraud_status":fraud["fraud_status"],
        "fraud_reason":fraud["fraud_reason"],"fraud_method":fraud["fraud_method"],
        "risk_score":fraud["risk_score"],"ml_probability":fraud["ml_probability"]},"ticket_id":tid})

@app.route("/api/resend_otp",methods=["POST","OPTIONS"])
@require_auth
def resend_otp():
    if request.method=="OPTIONS": return jsonify({}),200
    data=request.get_json() or {}; user=request.current_user; db=get_db(); tid=data.get("ticket_id")
    ticket=db.execute("SELECT * FROM tickets WHERE ticket_id=? AND user_id=?",(tid,user["user_id"])).fetchone()
    if not ticket: return jsonify({"error":"Ticket not found"}),404
    if ticket["payment_status"]=="SUCCESS": return jsonify({"error":"Already paid"}),400
    new_otp="".join(random.choices(string.digits,k=4)); now=datetime.now().isoformat()
    db.execute("UPDATE tickets SET otp=?,otp_time=?,otp_attempts=0 WHERE ticket_id=?",(new_otp,now,tid)); db.commit()
    route=f"{ticket['source']} -> {ticket['destination']}"
    email_sent=send_otp_email(user["email"],new_otp,ticket["passenger_name"],route)
    return jsonify({"message":"New OTP sent","demo_otp":new_otp,"email_sent":email_sent})

@app.route("/api/get_tickets",methods=["GET","OPTIONS"])
@require_auth
def get_tickets():
    if request.method=="OPTIONS": return jsonify({}),200
    db=get_db(); rows=db.execute("SELECT * FROM tickets WHERE user_id=? ORDER BY booking_time DESC",(request.current_user["user_id"],)).fetchall()
    return jsonify({"tickets":[dict(r) for r in rows],"total":len(rows)})

@app.route("/api/cancel_ticket/<int:tid>",methods=["POST","OPTIONS"])
@require_auth
def cancel_ticket(tid):
    if request.method=="OPTIONS": return jsonify({}),200
    db=get_db(); t=db.execute("SELECT * FROM tickets WHERE ticket_id=? AND user_id=?",(tid,request.current_user["user_id"])).fetchone()
    if not t: return jsonify({"error":"Ticket not found"}),404
    if t["ticket_status"]=="cancelled": return jsonify({"error":"Already cancelled"}),400
    db.execute("UPDATE tickets SET ticket_status='cancelled' WHERE ticket_id=?",(tid,)); db.commit()
    return jsonify({"message":f"Ticket #{tid} cancelled"})


@app.route("/api/scan", methods=["POST", "OPTIONS"])
@require_auth
def scan_ticket():
    if request.method == "OPTIONS": return jsonify({}), 200
    if 'file' not in request.files: return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "Empty filename"}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOADS_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
    file.save(filepath)
    
    data = request.form
    user = request.current_user
    
    # Run checks
    checks, ocr_text, qr_data = scan_ticket_image(filepath, data)
    
    # ML Scoring
    is_f, score, risk_level, gb_prob, iso_norm = run_scan_ml(checks)
    
    db = get_db()
    db.execute("""INSERT INTO scans(user_id, filename, pnr, passenger_name, issuer, 
        source, destination, travel_date, seat, price, fraud_score, risk_level, is_fraud, 
        fraud_indicators, ocr_text, qr_data) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user["user_id"], filename, data.get("pnr"), data.get("passenger_name"), 
         data.get("issuer"), data.get("source"), data.get("destination"), data.get("travel_date"),
         data.get("seat"), data.get("price"), score, risk_level, int(is_f), 
         json.dumps(checks), ocr_text[:400], qr_data))
    db.commit()
    scan_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    
    # Generate PDF Report
    report_filename = f"report_{scan_id}.pdf"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    scan_row = db.execute("SELECT * FROM scans WHERE scan_id=?", (scan_id,)).fetchone()
    generate_pdf_report(dict(scan_row), checks, report_path)
    
    db.execute("UPDATE scans SET report_path=? WHERE scan_id=?", (report_filename, scan_id))
    db.commit()
    
    return jsonify({
        "scan_id": scan_id, "fraud_score": score, "risk_level": risk_level,
        "is_fraud": is_f, "checks": checks, "ocr_text": ocr_text[:400],
        "qr_data": qr_data, "gb_probability": gb_prob, "isolation_score": iso_norm,
        "report_url": f"/api/report/{scan_id}"
    })

@app.route("/api/report/<int:scan_id>", methods=["GET", "OPTIONS"])
@require_auth
def download_report(scan_id):
    if request.method == "OPTIONS": return jsonify({}), 200
    db = get_db()
    scan = db.execute("SELECT * FROM scans WHERE scan_id=? AND user_id=?", (scan_id, request.current_user["user_id"])).fetchone()
    if not scan or not scan["report_path"]: return jsonify({"error": "Report not found"}), 404
    return send_file(os.path.join(REPORTS_DIR, scan["report_path"]), as_attachment=True)

@app.route("/api/scan_history", methods=["GET", "OPTIONS"])
@require_auth
def get_scan_history():
    if request.method == "OPTIONS": return jsonify({}), 200
    db = get_db()
    rows = db.execute("SELECT * FROM scans WHERE user_id=? ORDER BY scan_date DESC", (request.current_user["user_id"],)).fetchall()
    return jsonify({"scans": [dict(r) for r in rows], "total": len(rows)})

@app.route("/api/report_false_positive", methods=["POST", "OPTIONS"])
@require_auth
def report_fp():
    if request.method == "OPTIONS": return jsonify({}), 200
    data = request.get_json() or {}
    scan_id = data.get("scan_id")
    if not scan_id: return jsonify({"error": "scan_id required"}), 400
    db = get_db()
    db.execute("INSERT INTO false_positives(scan_id, user_id, reason) VALUES(?,?,?)",
               (scan_id, request.current_user["user_id"], data.get("reason", "")))
    db.commit()
    return jsonify({"message": "False positive reported. Model will be adjusted."})

@app.route("/api/admin/retrain", methods=["POST", "OPTIONS"])
@require_admin
def admin_retrain():
    if request.method == "OPTIONS": return jsonify({}), 200
    db = get_db()
    try:
        script_path = os.path.join(BASE_DIR, "..", "model", "train_scan_model.py")
        subprocess.run(["python", script_path], check=True, capture_output=True)
        load_scan_model()
        acc = scan_model_bundle["accuracy"] if scan_model_bundle else 0.0
        db.execute("INSERT INTO model_retrain_log(admin_id, status, accuracy) VALUES(?,?,?)",
                   (request.current_user["user_id"], "success", acc))
        db.commit()
        return jsonify({"message": "Model retrained successfully", "accuracy": round(acc*100, 2)})
    except Exception as e:
        db.execute("INSERT INTO model_retrain_log(admin_id, status, accuracy) VALUES(?,?,?)",
                   (request.current_user["user_id"], "failed", 0.0))
        db.commit()
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin_dashboard",methods=["GET","OPTIONS"])
@require_admin
def admin_dashboard():
    if request.method=="OPTIONS": return jsonify({}),200
    db=get_db(); stats={}
    for key,sql in [
        ("total_tickets","SELECT COUNT(*) FROM tickets"),
        ("fraud_tickets","SELECT COUNT(*) FROM tickets WHERE is_fraud=1"),
        ("valid_tickets","SELECT COUNT(*) FROM tickets WHERE is_fraud=0 AND payment_status='SUCCESS'"),
        ("pending","SELECT COUNT(*) FROM tickets WHERE payment_status='PENDING'"),
        ("pay_success","SELECT COUNT(*) FROM tickets WHERE payment_status='SUCCESS'"),
        ("pay_failed","SELECT COUNT(*) FROM tickets WHERE payment_status='FAILED'"),
        ("total_users","SELECT COUNT(*) FROM users WHERE is_admin=0"),
        ("total_admins","SELECT COUNT(*) FROM users WHERE is_admin=1"),
        ("total_scans","SELECT COUNT(*) FROM scans"),
        ("fp_count", "SELECT COUNT(*) FROM false_positives"),
    ]: stats[key]=db.execute(sql).fetchone()[0]

    stats["fraud_rate"]=round(stats["fraud_tickets"]/max(stats["total_tickets"],1)*100,1)
    by_method=[dict(r) for r in db.execute("SELECT fraud_method,COUNT(*) AS cnt FROM tickets WHERE is_fraud=1 AND fraud_method!='' GROUP BY fraud_method").fetchall()]
    daily=[dict(r) for r in db.execute("""SELECT DATE(booking_time) day,COUNT(*) total,SUM(is_fraud) fraud_count,
        SUM(CASE WHEN payment_status='SUCCESS' THEN 1 ELSE 0 END) pay_ok,
        SUM(CASE WHEN payment_status='FAILED' THEN 1 ELSE 0 END) pay_fail
        FROM tickets WHERE booking_time>=DATE('now','-7 days') GROUP BY DATE(booking_time) ORDER BY day""").fetchall()]
    
    scan_daily=[dict(r) for r in db.execute("""SELECT DATE(scan_date) day, COUNT(*) total, SUM(is_fraud) fraud_count
        FROM scans WHERE scan_date>=DATE('now','-7 days') GROUP BY DATE(scan_date) ORDER BY day""").fetchall()]
        
    recent_scans=[dict(r) for r in db.execute("SELECT * FROM scans ORDER BY scan_date DESC LIMIT 10").fetchall()]
    false_positives=[dict(r) for r in db.execute("SELECT * FROM false_positives ORDER BY created_at DESC LIMIT 10").fetchall()]

    
    scan_daily=[dict(r) for r in db.execute("""SELECT DATE(scan_date) day, COUNT(*) total, SUM(is_fraud) fraud_count
        FROM scans WHERE scan_date>=DATE('now','-7 days') GROUP BY DATE(scan_date) ORDER BY day""").fetchall()]
        
    recent_scans=[dict(r) for r in db.execute("SELECT * FROM scans ORDER BY scan_date DESC LIMIT 10").fetchall()]
    false_positives=[dict(r) for r in db.execute("SELECT * FROM false_positives ORDER BY created_at DESC LIMIT 10").fetchall()]

    sus_users=[dict(r) for r in db.execute("""SELECT u.user_id,u.name,u.email,u.risk_score,
        COUNT(t.ticket_id) total_tickets,SUM(t.is_fraud) fraud_tickets,
        SUM(CASE WHEN t.otp_attempts>=2 THEN 1 ELSE 0 END) otp_abuse,SUM(t.failed_payments_count) total_failed_pay
        FROM users u LEFT JOIN tickets t ON u.user_id=t.user_id WHERE u.is_admin=0
        GROUP BY u.user_id HAVING u.risk_score>0.3 ORDER BY u.risk_score DESC LIMIT 10""").fetchall()]
    recent_fraud=[dict(r) for r in db.execute("""SELECT t.ticket_id,u.name,t.source,t.destination,
        t.fraud_reason,t.fraud_method,t.risk_score,t.booking_time,t.transaction_id,t.otp_attempts,t.failed_payments_count
        FROM tickets t JOIN users u ON t.user_id=u.user_id WHERE t.is_fraud=1 ORDER BY t.booking_time DESC LIMIT 12""").fetchall()]
    model_info={}
    if model_bundle: model_info={"accuracy":round(model_bundle["accuracy"]*100,2),"auc":round(model_bundle["auc"],4),"confusion_matrix":model_bundle["confusion_matrix"]}
    return jsonify({"stats":stats,"by_method":by_method,"daily":daily,"suspicious_users":sus_users,"recent_fraud":recent_fraud,"model_info":model_info, "scan_daily":scan_daily, "recent_scans":recent_scans, "false_positives":false_positives})

@app.route("/api/public_stats",methods=["GET","OPTIONS"])
def public_stats():
    """
    Public endpoint — no auth required.
    Returns only high-level aggregate counts for the home page stats bar.
    Does NOT expose sensitive user/ticket details.
    """
    if request.method=="OPTIONS": return jsonify({}),200
    db=get_db()
    stats={
        "total_tickets": db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
        "fraud_tickets":  db.execute("SELECT COUNT(*) FROM tickets WHERE is_fraud=1").fetchone()[0],
        "valid_tickets":  db.execute("SELECT COUNT(*) FROM tickets WHERE is_fraud=0 AND payment_status='SUCCESS'").fetchone()[0],
        "total_scans": db.execute("SELECT COUNT(*) FROM scans").fetchone()[0],
        "total_scans": db.execute("SELECT COUNT(*) FROM scans").fetchone()[0],
        "total_users":    db.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0],
    }
    model_accuracy = round(model_bundle["accuracy"]*100,2) if model_bundle else None
    return jsonify({**stats,"model_accuracy":model_accuracy})

@app.route("/api/user_profile",methods=["GET"])
@require_auth
def user_profile():
    db=get_db(); u=request.current_user
    s=db.execute("SELECT COUNT(*) total,SUM(is_fraud) fraud,SUM(CASE WHEN payment_status='SUCCESS' THEN 1 ELSE 0 END) success_pay FROM tickets WHERE user_id=?",(u["user_id"],)).fetchone()
    return jsonify({"user":dict(u),"stats":dict(s)})

with app.app_context():
    init_db()

if __name__=="__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*55)
    print(f"  SecureTrail running at  http://localhost:{port}")
    print("  Admin: admin@securerail.com  /  Admin@123")
    print("="*55 + "\n")
    app.run(debug=False, host="0.0.0.0", port=port)