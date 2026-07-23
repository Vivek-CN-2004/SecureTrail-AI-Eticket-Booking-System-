import os

frontend_path = r'c:\Users\MY PC\Desktop\e-ticket\frontend\index.html'
with open(frontend_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add nav links
nav_old = """      <button class="nav-btn" onclick="nav('home')">Home</button>
      <button class="nav-btn" onclick="nav('book')">Book Ticket</button>
      <button class="nav-btn" onclick="nav('tickets')">My Tickets</button>
      <button class="nav-btn" onclick="goAdmin()">Admin</button>"""

nav_new = """      <button class="nav-btn" onclick="nav('home')">Home</button>
      <button class="nav-btn" onclick="nav('book')">Book Ticket</button>
      <button class="nav-btn" onclick="nav('scan')">Scan Ticket</button>
      <button class="nav-btn" onclick="nav('history')">Scan History</button>
      <button class="nav-btn" onclick="nav('tickets')">My Tickets</button>
      <button class="nav-btn" onclick="goAdmin()">Admin</button>"""
content = content.replace(nav_old, nav_new)

# 2. Add Scan Pages before My Tickets
scan_pages = """
<!-- ═══════════════════════════════════════════════
     PAGE: SCAN TICKET
     ═══════════════════════════════════════════════ -->
<div class="page" id="page-scan">
  <div class="flow-wrap" style="max-width:800px">
    <div class="flow-header" style="text-align:center">
      <h2>🔍 AI Ticket Scanner</h2>
      <p>Upload your e-ticket image to detect forgery, tampering, and anomalies</p>
    </div>
    
    <div style="display:flex;gap:2rem;flex-wrap:wrap">
      <!-- Left: Upload Area -->
      <div style="flex:1;min-width:300px">
        <div id="drop-area" style="border:2px dashed var(--line);border-radius:var(--r);padding:3rem 2rem;text-align:center;cursor:pointer;transition:all 0.3s;height:100%;display:flex;flex-direction:column;justify-content:center;background:var(--card)">
          <div style="font-size:3rem;margin-bottom:1rem">📄</div>
          <h3 style="font-family:var(--font-head);margin-bottom:0.5rem">Drop ticket image here</h3>
          <p style="color:var(--muted);font-size:0.85rem">or click to browse (JPG, PNG, PDF)</p>
          <input type="file" id="scan-file" accept="image/*,.pdf" style="display:none">
          
          <div id="scan-preview" style="display:none;margin-top:1.5rem">
            <img id="scan-img-preview" src="" style="max-width:100%;max-height:200px;border-radius:8px;border:1px solid var(--line)">
            <p id="scan-filename" style="font-size:0.8rem;color:var(--cyan);margin-top:0.5rem;word-break:break-all"></p>
            <button class="btn btn-ghost btn-sm" onclick="clearScanFile()" style="margin-top:0.5rem">Remove File</button>
          </div>
        </div>
      </div>
      
      <!-- Right: Form -->
      <div style="flex:1;min-width:300px">
        <div class="card card-sm">
          <div class="fdiv">Ticket Details (for verification)</div>
          <div class="field">
            <label>Issuer (e.g. IRCTC, MakeMyTrip)</label>
            <input type="text" id="scan-issuer" placeholder="IRCTC">
          </div>
          <div class="form-row">
            <div class="field">
              <label>PNR Number</label>
              <input type="text" id="scan-pnr" placeholder="1234567890">
            </div>
            <div class="field">
              <label>Passenger Name</label>
              <input type="text" id="scan-passenger" placeholder="John Doe">
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>Source</label>
              <input type="text" id="scan-src" placeholder="Mumbai">
            </div>
            <div class="field">
              <label>Destination</label>
              <input type="text" id="scan-dst" placeholder="Delhi">
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label>Travel Date</label>
              <input type="date" id="scan-date">
            </div>
            <div class="field">
              <label>Price (₹)</label>
              <input type="number" id="scan-price" placeholder="1500">
            </div>
          </div>
          
          <button class="btn btn-violet btn-full" onclick="runScan()" style="margin-top:1rem;padding:1rem">
            <span id="scan-btn-txt">Run AI Analysis</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════
     PAGE: SCAN RESULT
     ═══════════════════════════════════════════════ -->
<div class="page" id="page-scan-res">
  <div class="flow-wrap" style="max-width:900px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem">
      <h2 style="font-family:var(--font-head);font-size:1.8rem">Scan Report</h2>
      <button class="btn btn-ghost btn-sm" onclick="nav('history')">View History</button>
    </div>
    
    <div style="display:grid;grid-template-columns:1fr 2fr;gap:1.5rem">
      <!-- Left: Score Ring -->
      <div class="card" style="text-align:center;display:flex;flex-direction:column;justify-content:center;align-items:center">
        <div style="position:relative;width:150px;height:150px;margin-bottom:1.5rem">
          <svg viewBox="0 0 100 100" style="transform:rotate(-90deg);width:100%;height:100%">
            <circle cx="50" cy="50" r="45" fill="none" stroke="var(--line)" stroke-width="8" />
            <circle id="scan-score-ring" cx="50" cy="50" r="45" fill="none" stroke="var(--green)" stroke-width="8" stroke-dasharray="283" stroke-dashoffset="0" style="transition:stroke-dashoffset 1.5s ease-out, stroke 0.5s" />
          </svg>
          <div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center">
            <div id="scan-score-val" style="font-family:var(--font-head);font-size:2.5rem;font-weight:700;line-height:1">0</div>
            <div style="font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px">Score</div>
          </div>
        </div>
        <div id="scan-risk-badge" class="result-badge badge-valid" style="font-size:1rem;padding:0.5rem 1.5rem">LOW RISK</div>
        <p id="scan-verdict-txt" style="color:var(--muted);font-size:0.9rem;margin-top:1rem"></p>
        
        <a id="scan-pdf-btn" href="#" class="btn btn-ghost btn-full" style="margin-top:1.5rem" target="_blank">📄 Download PDF Report</a>
      </div>
      
      <!-- Right: ML & Checks -->
      <div style="display:flex;flex-direction:column;gap:1.5rem">
        <!-- ML Ensemble -->
        <div class="card card-sm" style="background:rgba(124,58,237,.05);border-color:rgba(124,58,237,.2)">
          <h3 style="font-family:var(--font-head);font-size:1rem;color:#a78bfa;margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem">
            🤖 ML Ensemble Output
          </h3>
          <div style="display:flex;gap:1rem">
            <div style="flex:1">
              <div style="font-size:0.75rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.25rem">GradientBoosting (70%)</div>
              <div style="height:6px;background:var(--card2);border-radius:3px;overflow:hidden">
                <div id="bar-gb" style="height:100%;background:#a78bfa;width:0%;transition:width 1s"></div>
              </div>
              <div id="val-gb" style="font-size:0.85rem;font-weight:700;text-align:right;margin-top:0.25rem">0%</div>
            </div>
            <div style="flex:1">
              <div style="font-size:0.75rem;color:var(--muted);text-transform:uppercase;margin-bottom:0.25rem">IsolationForest (30%)</div>
              <div style="height:6px;background:var(--card2);border-radius:3px;overflow:hidden">
                <div id="bar-iso" style="height:100%;background:var(--cyan);width:0%;transition:width 1s"></div>
              </div>
              <div id="val-iso" style="font-size:0.85rem;font-weight:700;text-align:right;margin-top:0.25rem">0%</div>
            </div>
          </div>
        </div>
        
        <!-- Checks Grid -->
        <div class="card card-sm">
          <h3 style="font-family:var(--font-head);font-size:1rem;margin-bottom:1rem">CV & Metadata Checks</h3>
          <div id="scan-checks-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem">
            <!-- Populated by JS -->
          </div>
        </div>
        
        <!-- OCR Text -->
        <div class="card card-sm">
          <h3 style="font-family:var(--font-head);font-size:1rem;margin-bottom:0.5rem">Extracted Text (OCR)</h3>
          <div id="scan-ocr-text" style="font-family:monospace;font-size:0.75rem;color:var(--muted);background:var(--card2);padding:0.75rem;border-radius:6px;max-height:120px;overflow-y:auto;white-space:pre-wrap"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════
     PAGE: SCAN HISTORY
     ═══════════════════════════════════════════════ -->
<div class="page" id="page-history">
  <div class="tickets-wrap">
    <h2 style="font-family:var(--font-head);font-size:2rem;margin-bottom:1.5rem">My Scan History</h2>
    <div id="history-list"></div>
  </div>
</div>
"""

content = content.replace('<!-- ═══════════════════════════════════════════════\n     PAGE: MY TICKETS', scan_pages + '\n<!-- ═══════════════════════════════════════════════\n     PAGE: MY TICKETS')

# 3. Add JS functions
js_code = """
/* ── SCANNER LOGIC ── */
let scanFile = null;

document.addEventListener("DOMContentLoaded", () => {
  const drop = document.getElementById("drop-area");
  if(drop) {
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.style.borderColor = "var(--cyan)"; });
    drop.addEventListener("dragleave", () => { drop.style.borderColor = "var(--line)"; });
    drop.addEventListener("drop", (e) => {
      e.preventDefault(); drop.style.borderColor = "var(--line)";
      if(e.dataTransfer.files.length) handleScanFile(e.dataTransfer.files[0]);
    });
    drop.addEventListener("click", () => document.getElementById("scan-file").click());
    document.getElementById("scan-file").addEventListener("change", (e) => {
      if(e.target.files.length) handleScanFile(e.target.files[0]);
    });
  }
});

function handleScanFile(f) {
  scanFile = f;
  document.getElementById("scan-filename").innerText = f.name;
  if(f.type.startsWith("image/")) {
    const r = new FileReader();
    r.onload = e => document.getElementById("scan-img-preview").src = e.target.result;
    r.readAsDataURL(f);
  } else {
    document.getElementById("scan-img-preview").src = "https://via.placeholder.com/150?text=PDF";
  }
  document.getElementById("scan-preview").style.display = "block";
}
function clearScanFile() {
  scanFile = null;
  document.getElementById("scan-file").value = "";
  document.getElementById("scan-preview").style.display = "none";
}

async function runScan() {
  if(!scanFile) return showToast("Please upload an image or PDF", "warn");
  const fd = new FormData();
  fd.append("file", scanFile);
  fd.append("issuer", document.getElementById("scan-issuer").value);
  fd.append("pnr", document.getElementById("scan-pnr").value);
  fd.append("passenger_name", document.getElementById("scan-passenger").value);
  fd.append("source", document.getElementById("scan-src").value);
  fd.append("destination", document.getElementById("scan-dst").value);
  fd.append("travel_date", document.getElementById("scan-date").value);
  fd.append("price", document.getElementById("scan-price").value);
  
  const btn = document.getElementById("scan-btn-txt");
  btn.innerHTML = "<div class='loader'></div> Analyzing...";
  document.querySelector("#page-scan .btn-violet").disabled = true;
  
  try {
    const r = await fetch(API+"/scan", {
      method:"POST", headers:{"Authorization":"Bearer "+getToken()}, body:fd
    });
    const data = await r.json();
    if(r.ok) {
      showScanResult(data);
    } else {
      showToast(data.error||"Scan failed","err");
    }
  } catch(e) {
    showToast("Network error","err");
  } finally {
    btn.innerHTML = "Run AI Analysis";
    document.querySelector("#page-scan .btn-violet").disabled = false;
  }
}

function showScanResult(data) {
  nav("scan-res");
  
  // Score Ring
  const ring = document.getElementById("scan-score-ring");
  const val = document.getElementById("scan-score-val");
  const badge = document.getElementById("scan-risk-badge");
  const verdict = document.getElementById("scan-verdict-txt");
  
  const pct = Math.min(Math.round(data.fraud_score), 100);
  setTimeout(() => {
    val.innerText = pct;
    const offset = 283 - (283 * pct / 100);
    ring.style.strokeDashoffset = offset;
    
    if(pct >= 65) {
      ring.style.stroke = "var(--coral)";
      badge.className = "result-badge badge-fraud";
      badge.innerText = "HIGH RISK - FRAUD";
      verdict.innerText = "This ticket exhibits significant signs of tampering or anomaly.";
    } else if(pct >= 35) {
      ring.style.stroke = "var(--gold)";
      badge.className = "result-badge badge-suspicious";
      badge.innerText = "MEDIUM RISK";
      verdict.innerText = "Some irregularities detected. Manual verification recommended.";
    } else {
      ring.style.stroke = "var(--green)";
      badge.className = "result-badge badge-valid";
      badge.innerText = "LOW RISK - VALID";
      verdict.innerText = "Ticket appears authentic and consistent.";
    }
  }, 100);
  
  // ML
  document.getElementById("val-gb").innerText = data.gb_probability + "%";
  document.getElementById("bar-gb").style.width = data.gb_probability + "%";
  document.getElementById("val-iso").innerText = data.isolation_score + "%";
  document.getElementById("bar-iso").style.width = data.isolation_score + "%";
  
  // OCR
  document.getElementById("scan-ocr-text").innerText = data.ocr_text || "No text detected";
  document.getElementById("scan-pdf-btn").href = API.replace("/api","") + data.report_url;
  
  // Checks Grid
  const grid = document.getElementById("scan-checks-grid");
  grid.innerHTML = "";
  const checksMap = {
    qr_detected: "QR Detected", qr_decodable: "QR Decodable", qr_pnr_match: "QR-PNR Match",
    ocr_confidence: "OCR Confidence", font_consistent: "Font Consistent", text_anomaly: "Text Anomalies",
    exif_clean: "EXIF Clean", file_unmodified: "File Unmodified", price_reasonable: "Price Reasonable",
    metadata_consistent: "Metadata Consistent"
  };
  
  for(let k in data.checks) {
    let v = data.checks[k];
    let isGood = true;
    let txt = "PASS";
    
    if(k === "ocr_confidence") {
      isGood = v > 70;
      txt = Math.round(v) + "%";
    } else if(k === "text_anomaly") {
      isGood = v === 0;
      txt = isGood ? "PASS" : "FAIL";
    } else {
      isGood = v === 1;
      txt = isGood ? "PASS" : "FAIL";
    }
    
    const color = isGood ? "var(--green)" : "var(--coral)";
    const icon = isGood ? "✓" : "✗";
    
    grid.innerHTML += `
      <div style="display:flex;justify-content:space-between;padding:0.4rem;border-bottom:1px solid var(--line);font-size:0.8rem">
        <span style="color:var(--muted)">${checksMap[k] || k}</span>
        <span style="color:${color};font-weight:700">${icon} ${txt}</span>
      </div>
    `;
  }
}

async function loadScanHistory() {
  const container = document.getElementById("history-list");
  container.innerHTML = "<div class='sk-loader'><div class='spinner-ring'></div>Loading scans...</div>";
  try {
    const r = await fetch(API+"/scan_history", {headers:{"Authorization":"Bearer "+getToken()}});
    const data = await r.json();
    if(data.scans.length===0) {
      container.innerHTML = "<div class='empty'><div class='empty-icon'>📂</div><h3>No scans yet</h3></div>";
      return;
    }
    let html = "";
    data.scans.forEach(s => {
      let cls = "valid-t", chip = "chip-valid", txt = "VALID";
      if(s.fraud_score >= 65) { cls="fraud-t"; chip="chip-fraud"; txt="FRAUD"; }
      else if(s.fraud_score >= 35) { cls="sus-t"; chip="chip-sus"; txt="SUSPICIOUS"; }
      
      const pUrl = API.replace("/api","") + "/api/report/" + s.scan_id;
      
      html += `
        <div class="ticket-card ${cls}">
          <div>
            <div class="ticket-route">${s.filename}</div>
            <div class="ticket-meta">
              <span>📅 ${s.scan_date.split('T')[0]}</span>
              <span>🎫 ${s.issuer || 'N/A'}</span>
              <span>👤 ${s.passenger_name || 'N/A'}</span>
            </div>
            <div style="margin-top:0.75rem">
              <span class="status-chip ${chip}">${txt} (${Math.round(s.fraud_score)})</span>
            </div>
          </div>
          <div class="ticket-actions">
            <a href="${pUrl}" target="_blank" class="btn btn-ghost btn-sm">PDF Report</a>
            <button onclick="reportFP(${s.scan_id})" class="btn btn-ghost btn-sm" style="font-size:0.7rem;margin-top:0.5rem;color:var(--muted)">Report False Positive</button>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = "<div class='empty'>Failed to load</div>";
  }
}

async function reportFP(id) {
  const reason = prompt("Why is this a false positive?");
  if(!reason) return;
  try {
    const r = await fetch(API+"/report_false_positive", {
      method:"POST", headers:{"Content-Type":"application/json", "Authorization":"Bearer "+getToken()},
      body:JSON.stringify({scan_id:id, reason:reason})
    });
    if(r.ok) showToast("False positive reported. Thank you!","ok");
  } catch(e) {}
}

async function adminRetrain() {
  if(!confirm("This will spin up a background process to retrain the Scan ML model. Proceed?")) return;
  showToast("Retraining started. This may take a minute...", "ok");
  try {
    const r = await fetch(API+"/admin/retrain", {
      method:"POST", headers:{"Authorization":"Bearer "+localStorage.getItem("st_admin_token")}
    });
    const d = await r.json();
    if(r.ok) showToast(`Retraining Complete! New Accuracy: ${d.accuracy}%`, "ok");
    else showToast(d.error||"Failed", "err");
  } catch(e) { showToast("Error connecting", "err"); }
}
"""

content = content.replace('/* ── API CALLS ── */', js_code + '\n/* ── API CALLS ── */')

# 4. Update the nav routing map
content = content.replace("if(p==='tickets') loadTickets();", "if(p==='tickets') loadTickets();\n  if(p==='history') loadScanHistory();")

with open(frontend_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Frontend updated with Scan features.")
