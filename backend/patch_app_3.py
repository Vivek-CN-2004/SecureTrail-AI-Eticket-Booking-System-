import os

app_path = r'c:\Users\MY PC\Desktop\e-ticket\backend\app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

endpoints = """
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
    db.execute(\"\"\"INSERT INTO scans(user_id, filename, pnr, passenger_name, issuer, 
        source, destination, travel_date, seat, price, fraud_score, risk_level, is_fraud, 
        fraud_indicators, ocr_text, qr_data) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)\"\"\",
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
"""

content = content.replace('@app.route("/api/admin_dashboard"', endpoints + '\n@app.route("/api/admin_dashboard"')

# Patch admin_dashboard to include scan data
admin_stats_old = """    for key,sql in [
        ("total_tickets","SELECT COUNT(*) FROM tickets"),
        ("fraud_tickets","SELECT COUNT(*) FROM tickets WHERE is_fraud=1"),
        ("valid_tickets","SELECT COUNT(*) FROM tickets WHERE is_fraud=0 AND payment_status='SUCCESS'"),
        ("pending","SELECT COUNT(*) FROM tickets WHERE payment_status='PENDING'"),
        ("pay_success","SELECT COUNT(*) FROM tickets WHERE payment_status='SUCCESS'"),
        ("pay_failed","SELECT COUNT(*) FROM tickets WHERE payment_status='FAILED'"),
        ("total_users","SELECT COUNT(*) FROM users WHERE is_admin=0"),
        ("total_admins","SELECT COUNT(*) FROM users WHERE is_admin=1"),
    ]: stats[key]=db.execute(sql).fetchone()[0]"""

admin_stats_new = """    for key,sql in [
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
"""
content = content.replace(admin_stats_old, admin_stats_new)

admin_daily_old = """    daily=[dict(r) for r in db.execute(\"\"\"SELECT DATE(booking_time) day,COUNT(*) total,SUM(is_fraud) fraud_count,
        SUM(CASE WHEN payment_status='SUCCESS' THEN 1 ELSE 0 END) pay_ok,
        SUM(CASE WHEN payment_status='FAILED' THEN 1 ELSE 0 END) pay_fail
        FROM tickets WHERE booking_time>=DATE('now','-7 days') GROUP BY DATE(booking_time) ORDER BY day\"\"\").fetchall()]"""

admin_daily_new = """    daily=[dict(r) for r in db.execute(\"\"\"SELECT DATE(booking_time) day,COUNT(*) total,SUM(is_fraud) fraud_count,
        SUM(CASE WHEN payment_status='SUCCESS' THEN 1 ELSE 0 END) pay_ok,
        SUM(CASE WHEN payment_status='FAILED' THEN 1 ELSE 0 END) pay_fail
        FROM tickets WHERE booking_time>=DATE('now','-7 days') GROUP BY DATE(booking_time) ORDER BY day\"\"\").fetchall()]
    
    scan_daily=[dict(r) for r in db.execute(\"\"\"SELECT DATE(scan_date) day, COUNT(*) total, SUM(is_fraud) fraud_count
        FROM scans WHERE scan_date>=DATE('now','-7 days') GROUP BY DATE(scan_date) ORDER BY day\"\"\").fetchall()]
        
    recent_scans=[dict(r) for r in db.execute("SELECT * FROM scans ORDER BY scan_date DESC LIMIT 10").fetchall()]
    false_positives=[dict(r) for r in db.execute("SELECT * FROM false_positives ORDER BY created_at DESC LIMIT 10").fetchall()]
"""
content = content.replace(admin_daily_old, admin_daily_new)

content = content.replace('"suspicious_users":sus_users,"recent_fraud":recent_fraud,"model_info":model_info}',
                          '"suspicious_users":sus_users,"recent_fraud":recent_fraud,"model_info":model_info, "scan_daily":scan_daily, "recent_scans":recent_scans, "false_positives":false_positives}')

# patch public_stats
content = content.replace('"valid_tickets":  db.execute("SELECT COUNT(*) FROM tickets WHERE is_fraud=0 AND payment_status=\'SUCCESS\'").fetchone()[0],',
                          '"valid_tickets":  db.execute("SELECT COUNT(*) FROM tickets WHERE is_fraud=0 AND payment_status=\'SUCCESS\'").fetchone()[0],\n        "total_scans": db.execute("SELECT COUNT(*) FROM scans").fetchone()[0],')

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated API endpoints.")
