/* ScannerPage + AdminPage */

function ScannerPage({user,userData,initialTab}){
  const [tab,setTab]=React.useState(initialTab||"public");
  const [file,setFile]=React.useState(null);
  const [meta,setMeta]=React.useState({pnr:"",passenger_name:"",price:"",source:"",destination:"",travel_date:""});
  const [result,setResult]=React.useState(null);
  const [loading,setLoading]=React.useState(false);
  const [history,setHistory]=React.useState([]);
  const [hLoading,setHLoading]=React.useState(false);
  const [feedback,setFeedback]=React.useState({});
  const [batchFiles,setBatchFiles]=React.useState([]);
  const [batchResults,setBatchResults]=React.useState([]);
  const [batchLoading,setBatchLoading]=React.useState(false);
  const [shareUrl,setShareUrl]=React.useState("");
  const [drag,setDrag]=React.useState(false);

  React.useEffect(()=>{
    if(tab==="history"&&user){loadHistory();}
  },[tab]);

  async function loadHistory(){
    setHLoading(true);
    try{
      const r=await fetch(`${API}/api/scan/history/${user?.uid||"anon"}`);
      const d=await r.json();
      setHistory(d.scans||[]);
    }catch{setHistory([]);}
    setHLoading(false);
  }

  async function doScan(e){
    e&&e.preventDefault();
    if(!file){alert("Please select a ticket image.");return;}
    setLoading(true);setResult(null);setShareUrl("");
    const fd=new FormData();
    fd.append("file",file);
    Object.keys(meta).forEach(k=>fd.append(k,meta[k]));
    const endpoint=user&&tab==="pro"?"/api/scan/pro":"/api/scan";
    if(user&&tab==="pro")fd.append("user_id",user.uid);
    try{
      const r=await fetch(`${API}${endpoint}`,{method:"POST",body:fd});
      const d=await r.json();
      setResult(d);
    }catch{setResult({fraud_score:0,risk_level:"LOW",is_fraud:false,checks:{},error:"Backend offline – CV analysis unavailable"});}
    setLoading(false);
  }

  async function doBatch(){
    if(!batchFiles.length){alert("Select up to 10 files.");return;}
    setBatchLoading(true);setBatchResults([]);
    const fd=new FormData();
    batchFiles.forEach(f=>fd.append("files",f));
    fd.append("user_id",user?.uid||"anon");
    try{
      const r=await fetch(`${API}/api/scan/batch`,{method:"POST",body:fd});
      const d=await r.json();
      setBatchResults(d.results||[]);
    }catch{alert("Backend offline.");}
    setBatchLoading(false);
  }

  async function createShare(scanId){
    try{
      const r=await fetch(`${API}/api/share/${scanId}`,{method:"POST"});
      const d=await r.json();
      if(d.share_url){
        setShareUrl(d.share_url);
        navigator.clipboard.writeText(d.share_url);
        alert("Share link copied to clipboard!");
      }
    }catch{alert("Could not generate share link.");}
  }

  async function sendFeedback(scanId,fb){
    setFeedback(prev=>({...prev,[scanId]:fb}));
    try{
      await fetch(`${API}/api/feedback`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scan_id:scanId,user_id:user?.uid,feedback:fb,reason:"User correction"})});
    }catch{}
  }

  function DropZone({onFile,multiple}){
    return(
      <div className={`drop-zone${drag?" drag":""}`}
        onDragOver={e=>{e.preventDefault();setDrag(true)}}
        onDragLeave={()=>setDrag(false)}
        onDrop={e=>{e.preventDefault();setDrag(false);const files=Array.from(e.dataTransfer.files).filter(f=>f.type.startsWith("image/"));multiple?setBatchFiles(files.slice(0,10)):onFile(files[0]);}}
        onClick={()=>document.getElementById(multiple?"batch-inp":"file-inp").click()}>
        <div style={{fontSize:"2.5rem",marginBottom:8}}>📁</div>
        <p className="text-muted" style={{fontSize:".9rem"}}>{multiple?"Drop up to 10 ticket images":"Drop ticket image here or click to browse"}</p>
        <p className="text-muted" style={{fontSize:".8rem",marginTop:4}}>JPG, PNG, WEBP supported</p>
        <input id={multiple?"batch-inp":"file-inp"} type="file" accept="image/*" multiple={multiple} style={{display:"none"}} onChange={e=>{multiple?setBatchFiles(Array.from(e.target.files).slice(0,10)):onFile(e.target.files[0]);}}/>
      </div>
    );
  }

  function ResultCard({r}){
    const status = r.status || "UNKNOWN";
    const msg = r.message || "";
    const pnr = r.ticket_id || "N/A";
    
    const statusColors = {
      "VALID": "var(--green)",
      "FRAUD": "var(--red)",
      "FAKE": "var(--red)",
      "INVALID": "var(--orange)",
      "SUSPICIOUS": "var(--orange)",
      "DUPLICATE": "var(--orange)",
      "USED": "var(--orange)"
    };

    const statusIcons = {
      "VALID": "✅",
      "FRAUD": "🚨",
      "FAKE": "❌",
      "INVALID": "⏰",
      "SUSPICIOUS": "⚠️",
      "DUPLICATE": "⚠️",
      "USED": "🔴"
    };

    return(
      <div className="glass-card fade-in mt-24" style={{borderWidth: 2, borderColor: "rgba(0,212,255,0.1)"}}>
        <div className="flex-between mb-24">
          <h3 className="glow-text">🤖 Scanner Verdict</h3>
          <span className="badge" style={{background: statusColors[status] || "var(--card2)", padding: "6px 14px", fontSize: ".8rem"}}>
            {statusIcons[status] || "❓"} {status}
          </span>
        </div>
        <div style={{textAlign:"center",marginBottom:24}}>
          <div style={{fontSize:"4.5rem", marginBottom:15, filter: "drop-shadow(0 0 15px rgba(255,255,255,0.2))"}}>{statusIcons[status] || "❓"}</div>
          <h2 style={{color: statusColors[status] || "var(--muted)", textTransform: "uppercase", letterSpacing: 3, fontSize: "2.2rem"}}>{status}</h2>
          <p className="mt-12" style={{fontSize: "1.2rem", fontWeight: 600, color: "var(--text)"}}>{msg}</p>
          <p className="text-muted mt-8" style={{fontSize:".9rem"}}>PNR ID: <strong className="text-cyan" style={{fontFamily: "monospace"}}>{pnr}</strong></p>
        </div>
        
        {r.checks && (
          <div className="mt-24">
            <h3 className="mb-16" style={{fontSize: "0.9rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: 1}}>🔍 Deep Scan Analysis</h3>
            <div className="grid2" style={{gap:10}}>
              {Object.entries(r.checks).map(([k,v])=>(
                <div key={k} className="scanner-grid-detail glass" style={{padding: "12px 16px", borderRadius: 12}}>
                  <span style={{fontSize:".7rem",color:"var(--muted)",textTransform:"uppercase", fontWeight: 700}}>{k.replace(/_/g," ")}</span>
                  <span style={{color:v?"var(--green)":"var(--red)",fontWeight:800,fontSize:".85rem"}}>{v?"PASS":"FAIL"}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {user && r.scan_id && <div className="flex mt-24" style={{gap:12}}>
          <a href={`${API}/api/report/${r.scan_id}`} target="_blank" className="premium-btn" style={{flex:1, textAlign: "center", textDecoration: "none"}}>📄 Full Report</a>
          <button onClick={()=>createShare(r.scan_id)} className="btn btn-outline" style={{flex:1, borderRadius: "var(--r)"}}>{shareUrl?"✅ Link Copied":"🔗 Share Results"}</button>
        </div>}
        {shareUrl && <div className="mt-16 alert alert-ok" style={{flexDirection:"column",alignItems:"flex-start",gap:8}}>
          <div style={{fontSize:".8rem",fontWeight:700,textTransform:"uppercase",letterSpacing:1,opacity:0.8}}>Shareable Link:</div>
          <div style={{width:"100%",display:"flex",gap:8}}>
            <input readOnly value={shareUrl} style={{flex:1,background:"rgba(255,255,255,0.05)",border:"1px solid var(--border)",borderRadius:8,padding:"8px 12px",fontSize:".85rem",color:"var(--cyan)"}}/>
            <button className="btn btn-sm btn-primary" onClick={()=>{navigator.clipboard.writeText(shareUrl);alert("Copied!");}}>Copy</button>
          </div>
        </div>}
      </div>
    );
  }

  const tabs=["public","pro","batch","history"].filter(t=>t==="public"||user);
  const tabLabels={"public":"🔍 Quick Scan","pro":"⚡ Pro Scan","batch":"📦 Batch","history":"📋 History"};

  return(
    <div className="page fade-in">
      <div className="scanner-hero">
        <div className="scanner-beam"></div>
        <div style={{position:"relative",zIndex:20}}>
          <h1 style={{fontSize:"2.5rem",marginBottom:8}}>Secure Scanner</h1>
          <p className="text-muted" style={{maxWidth:500,margin:"0 auto"}}>Advanced AI scanning with OCR & biometric verification</p>
          {!user&&<div className="badge badge-low mt-16">Guest Access Active</div>}
        </div>
      </div>
      <div className="tabs">{tabs.map(t=><button key={t} className={`tab${tab===t?" active":""}`} onClick={()=>setTab(t)}>{tabLabels[t]}</button>)}</div>

      {(tab==="public"||tab==="pro")&&<div>
        <div className="card">
          <DropZone onFile={setFile} multiple={false}/>
          {file&&<div className="alert alert-ok mt-8">📎 {file.name} selected</div>}
          <div className="mt-16">
            <h3 className="mb-8">📋 Ticket Details (Optional)</h3>
            <div className="grid2">
              <div className="form-group"><label className="form-label">PNR</label><input placeholder="AB12345678" value={meta.pnr} onChange={e=>setMeta({...meta,pnr:e.target.value})}/></div>
              <div className="form-group"><label className="form-label">Passenger Name</label><input placeholder="Name on ticket" value={meta.passenger_name} onChange={e=>setMeta({...meta,passenger_name:e.target.value})}/></div>
              <div className="form-group"><label className="form-label">Price (₹)</label><input type="number" placeholder="e.g. 850" value={meta.price} onChange={e=>setMeta({...meta,price:e.target.value})}/></div>
              <div className="form-group"><label className="form-label">Travel Date</label><input type="date" value={meta.travel_date} onChange={e=>setMeta({...meta,travel_date:e.target.value})}/></div>
            </div>
          </div>
          <button onClick={doScan} disabled={loading||!file} className="btn btn-primary w100 mt-8">
            {loading?<><span className="loader"/>&nbsp;Analyzing…</>:"🤖 Analyze for Fraud"}
          </button>
        </div>
        {result&&<ResultCard r={result}/>}
      </div>}

      {tab==="batch"&&<div>
        <div className="card">
          <DropZone onFile={null} multiple={true}/>
          {batchFiles.length>0&&<div className="alert alert-ok mt-8">📎 {batchFiles.length} file(s) selected</div>}
          <button onClick={doBatch} disabled={batchLoading||!batchFiles.length} className="btn btn-primary w100 mt-8">
            {batchLoading?<><span className="loader"/>&nbsp;Scanning all…</>:`📦 Scan ${batchFiles.length} Ticket(s)`}
          </button>
        </div>
        {batchResults.length>0&&<div className="card mt-16">
          <h3 className="mb-8">Batch Results ({batchResults.length} tickets)</h3>
          <table className="table">
            <thead><tr><th>File</th><th>Score</th><th>Risk</th><th>Verdict</th></tr></thead>
            <tbody>{batchResults.map((r,i)=>(
              <tr key={i}>
                <td style={{fontSize:".85rem"}}>{r.filename}</td>
                <td><strong>{r.fraud_score}/100</strong></td>
                <td><span className={`badge badge-${r.risk_level==="HIGH"?"high":r.risk_level==="MEDIUM"?"med":"low"}`}>{r.risk_level}</span></td>
                <td style={{color:r.is_fraud?"var(--red)":"var(--green)",fontWeight:700}}>{r.is_fraud?"❌ FRAUD":"✅ VALID"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>}
      </div>}

      {tab==="history"&&<div>
        {hLoading?<div className="text-center mt-24"><span className="loader"/></div>:
        history.length===0?<div className="card text-center"><p className="text-muted">No scan history yet.</p></div>:
        <div style={{display:"flex",flexDirection:"column",gap:12}}>
          {history.map((s,i)=>(
            <div key={i} className="card" style={{padding:16}}>
              <div className="flex-between mb-8">
                <span style={{fontSize:".85rem",color:"var(--muted)"}}>{s.scan_date?.slice(0,16)||"—"}</span>
                <span className={`badge badge-${s.risk_level==="HIGH"?"high":s.risk_level==="MEDIUM"?"med":"low"}`}>{s.risk_level}</span>
              </div>
              <div className="flex-between">
                <div><span className="text-muted" style={{fontSize:".8rem"}}>FILE: </span>{s.filename}</div>
                <div><span className="text-muted" style={{fontSize:".8rem"}}>SCORE: </span><strong>{s.fraud_score}/100</strong></div>
                <div style={{color:s.is_fraud?"var(--red)":"var(--green)",fontWeight:700}}>{s.is_fraud?"❌ FRAUD":"✅ VALID"}</div>
              </div>
              {s._id&&<div className="flex mt-8" style={{gap:8}}>
                <button onClick={()=>sendFeedback(s._id,"false_positive")} disabled={!!feedback[s._id]} className="btn btn-sm btn-outline" style={{flex:1}}>👎 False Positive?</button>
                <button onClick={()=>createShare(s._id)} className="btn btn-sm btn-outline" style={{flex:1}}>🔗 Share</button>
              </div>}
              {feedback[s._id]&&<div className="alert alert-ok mt-8" style={{padding:"6px 10px",fontSize:".8rem"}}>✅ Feedback sent</div>}
            </div>
          ))}
        </div>}
      </div>}
    </div>
  );
}

function AdminPage({user}){
  const [stats,setStats]=React.useState(null);
  const [tickets,setTickets]=React.useState([]);
  const [tab,setTab]=React.useState("overview");
  const [cancellations,setCancellations]=React.useState([]);
  const [flaggedUsers,setFlaggedUsers]=React.useState([]);
  const [alerts,setAlerts]=React.useState([]);
  const [loading,setLoading]=React.useState(true);
  const [retraining,setRetraining]=React.useState(false);
  const [retMsg,setRetMsg]=React.useState("");
  const chartRef=React.useRef(null);
  const chartInst=React.useRef(null);

  React.useEffect(()=>{loadData();},[]);

  async function loadData(){
    setLoading(true);
    try{
      const r=await fetch(`${API}/api/stats`);
      const d=await r.json();setStats(d);
    }catch{setStats({total_tickets:0,total_scans:0,fraud_tickets:0,fraud_scans:0,model_loaded:false});}
    const snap=await db.collection("tickets").orderBy("booking_time","desc").limit(20).get();
    setTickets(snap.docs.map(d=>({id:d.id,...d.data()})));
    const cSnap=await db.collection("tickets").where("status","==","CANCEL_PENDING").get();
    setCancellations(cSnap.docs.map(d=>({id:d.id,...d.data()})));
    try{
      const fSnap=await getFlaggedUsers();
      setFlaggedUsers(fSnap.docs.map(d=>({id:d.id,...d.data()})));
    }catch{}
    try{
      const aSnap=await getScanAlerts();
      setAlerts(aSnap.docs.map(d=>({id:d.id,...d.data()})));
    }catch{}
    setLoading(false);
  }

  async function handleApproveRefund(id){
    if(!confirm("Approve cancellation and initiate refund?"))return;
    setLoading(true);
    try{
      await approveCancellation(id);
      setCancellations(cancellations.filter(c=>c.id!==id));
      alert("Refund approved and processed successfully!");
    }catch(e){alert("Failed to approve refund: "+e.message);}
    setLoading(false);
  }

  React.useEffect(()=>{
    if(tab==="charts"&&stats&&chartRef.current){
      if(chartInst.current)chartInst.current.destroy();
      chartInst.current=new Chart(chartRef.current,{
        type:"doughnut",
        data:{labels:["Valid Tickets","Fraud Tickets","Valid Scans","Fraud Scans"],
          datasets:[{data:[stats.total_tickets-stats.fraud_tickets,stats.fraud_tickets,stats.total_scans-stats.fraud_scans,stats.fraud_scans],backgroundColor:["#00ff88","#ff4444","#00d4ff","#ff8c00"],borderColor:"#0d0d2b",borderWidth:2}]},
        options:{responsive:true,plugins:{legend:{labels:{color:"#e8e8ff",font:{size:12}}}}}
      });
    }
  },[tab,stats]);

  async function retrain(){
    setRetraining(true);setRetMsg("");
    try{
      const r=await fetch(`${API}/api/retrain`,{method:"POST"});
      const d=await r.json();
      setRetMsg(d.message?`✅ ${d.message} | Accuracy: ${d.accuracy}%`:`❌ ${d.error}`);
    }catch{setRetMsg("❌ Backend offline");}
    setRetraining(false);
  }

  if(loading)return<div className="page text-center mt-24"><span className="loader"/></div>;

  return(
    <div className="page fade-in">
      <div className="flex-between mb-16">
        <div><h2>📊 Admin Dashboard</h2><p className="text-muted" style={{fontSize:".9rem"}}>Platform overview & fraud analytics</p></div>
        <button onClick={loadData} className="btn btn-sm btn-outline">🔄 Refresh</button>
      </div>

      <div className="tabs">
        {["overview","tickets","flagged","cancellations","alerts","charts","model"].map(t=>(
          <button key={t} className={`tab${tab===t?" active":""}`} onClick={()=>setTab(t)}>
            {t==="overview"?"📈 Overview":t==="tickets"?"🎫 Bookings":t==="flagged"?`🚨 Flagged (${flaggedUsers.length})`:t==="cancellations"?"💰 Refunds":t==="alerts"?"⚠️ Alerts":t==="charts"?"📊 Charts":"🤖 Model"}
          </button>
        ))}
      </div>

      {tab==="overview"&&stats&&<div>
        <div className="grid4 mb-24">
          {[
            {icon:"🎫",label:"Total Tickets",val:stats.total_tickets,color:"var(--cyan)"},
            {icon:"🔍",label:"Total Scans",val:stats.total_scans,color:"var(--cyan)"},
            {icon:"🚨",label:"Fraud Tickets",val:stats.fraud_tickets,color:"var(--red)"},
            {icon:"⚠️",label:"Fraud Scans",val:stats.fraud_scans,color:"var(--orange)"},
          ].map(s=>(
            <div key={s.label} className="stat-card glass" style={{padding: 24, textAlign: "center"}}>
              <div style={{fontSize:"2.2rem",marginBottom:10, filter: "drop-shadow(0 0 10px rgba(255,255,255,0.1))"}}>{s.icon}</div>
              <div className="stat-num" style={{fontSize: "2.4rem", marginBottom: 4}}>{s.val||0}</div>
              <div className="text-muted" style={{fontSize:".75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: 1}}>{s.label}</div>
              <div style={{position: "absolute", bottom: 0, left: 0, right: 0, height: 3, background: s.color, opacity: 0.5}}></div>
            </div>
          ))}
        </div>
        <div className="grid2">
          <div className="glass-card" style={{padding: 30, textAlign: "center"}}>
            <h3 className="mb-12" style={{color: "var(--muted)", fontSize: ".9rem", textTransform: "uppercase"}}>🛡️ System Fraud Rate</h3>
            <div style={{fontSize:"3.5rem",fontWeight:900, color: "var(--text)", textShadow: "0 0 30px rgba(255,68,68,0.2)"}}>
              {stats.total_tickets>0?Math.round(stats.fraud_tickets/stats.total_tickets*100):0}<span style={{fontSize: "1.5rem", color: "var(--muted)"}}>%</span>
            </div>
            <p className="text-muted mt-12" style={{fontSize:".85rem"}}>AI-detected anomalies in total transactions</p>
          </div>
          <div className="glass-card" style={{padding: 30, textAlign: "center"}}>
            <h3 className="mb-12" style={{color: "var(--muted)", fontSize: ".9rem", textTransform: "uppercase"}}>🤖 Network Status</h3>
            <div className={`badge ${stats.model_loaded?"badge-low":"badge-high"}`} style={{fontSize:"1.1rem",padding:"10px 24px", borderRadius: 12}}>
              {stats.model_loaded?"✅ AI MODELS ACTIVE":"❌ SYSTEM OFFLINE"}
            </div>
            <p className="text-muted mt-16" style={{fontSize:".85rem"}}>Neural network core is operational</p>
          </div>
        </div>
      </div>}

      {tab==="flagged"&&<div>
        <div className="flex-between mb-16">
          <h3>🚨 Flagged & Suspicious Accounts</h3>
          <span className="badge badge-high">{flaggedUsers.length} Users Flagged</span>
        </div>
        {flaggedUsers.length===0?<div className="card text-center"><p className="text-muted">✅ No flagged users at this time.</p></div>:
        <div style={{display:"flex",flexDirection:"column",gap:16}}>
          {flaggedUsers.map(u=>(
            <div key={u.id} className="card glass" style={{borderColor:u.flag_status==="BANNED"?"var(--red)":"var(--orange)"}}>
              <div className="flex-between mb-12">
                <div>
                  <div style={{fontWeight:700,fontSize:"1.1rem"}}>{u.name||"Unknown User"}</div>
                  <div className="text-muted" style={{fontSize:".8rem"}}>{u.email}</div>
                </div>
                <div style={{textAlign:"right"}}>
                  <span className={`badge ${u.flag_status==="BANNED"?"badge-high":"badge-med"}`} style={{display:"block",marginBottom:4}}>
                    {u.flag_status==="BANNED"?"🔴 BANNED":"🟡 SUSPICIOUS"}
                  </span>
                  <span className="text-muted" style={{fontSize:".75rem"}}>Strikes: {u.flag_count||1}/3</span>
                </div>
              </div>
              <div className="alert alert-warn mb-12" style={{flexDirection:"column",alignItems:"flex-start",padding:"10px 14px"}}>
                <strong style={{fontSize:".8rem"}}>REASON:</strong>
                <span style={{fontSize:".85rem",fontStyle:"italic"}}>{u.flag_reason||"Suspicious activity detected."}</span>
              </div>
              <div style={{display:"flex",gap:10}}>
                <button className="btn btn-sm btn-outline" style={{flex:1,color:"var(--green)",borderColor:"var(--green)"}} onClick={async()=>{
                  if(!confirm(`Clear flag for ${u.name}? They will be allowed to book tickets again.`))return;
                  await clearUserFlag(u.id);
                  setFlaggedUsers(flaggedUsers.filter(x=>x.id!==u.id));
                  alert("User flag cleared. They can now book tickets.");
                }}>✅ Clear & Allow Booking</button>
                <button className="btn btn-sm btn-outline" style={{flex:1,color:"var(--red)",borderColor:"var(--red)"}} onClick={async()=>{
                  if(!confirm(`PERMANENTLY BAN ${u.name}? This will block all future bookings.`))return;
                  await banUser(u.id);
                  setFlaggedUsers(flaggedUsers.map(x=>x.id===u.id?{...x,flag_status:"BANNED"}:x));
                  alert("User has been permanently banned.");
                }}>🔴 Ban Account</button>
                <button className="btn btn-sm btn-danger" style={{flex:1}} onClick={async()=>{
                  if(!confirm(`DELETE account for ${u.name}? This action marks their account as deleted.`))return;
                  await deleteUserAccount(u.id);
                  setFlaggedUsers(flaggedUsers.filter(x=>x.id!==u.id));
                  alert("Account has been deleted.");
                }}>🗑️ Delete Account</button>
              </div>
            </div>
          ))}
        </div>}
      </div>}

      {tab==="tickets"&&<div>
        {tickets.length===0?<div className="card text-center"><p className="text-muted">No bookings yet.</p></div>:
        <div className="card" style={{padding:0,overflow:"hidden"}}>
          <table className="table">
            <thead><tr><th>PNR</th><th>Passenger</th><th>Route</th><th>Mode</th><th>Fare</th><th>Risk</th><th>Status</th></tr></thead>
            <tbody>{tickets.map(t=>(
              <tr key={t.id}>
                <td><span className="text-cyan" style={{fontFamily:"monospace",fontWeight:700}}>{t.pnr}</span></td>
                <td>{t.passenger_name}</td>
                <td style={{fontSize:".83rem"}}>{t.source} → {t.destination}</td>
                <td>{t.mode==="train"?"🚆":t.mode==="bus"?"🚌":"✈️"}</td>
                <td className="text-gold">{fmtCur(t.price)}</td>
                <td><span className={`badge badge-${t.risk_level==="HIGH"?"high":t.risk_level==="MEDIUM"?"med":"low"}`}>{t.risk_level}</span></td>
                <td><span style={{color:t.status==="USED"?"var(--orange)":"var(--green)",fontWeight:700}}>{t.status}</span></td>
              </tr>
            ))}</tbody>
          </table>
        </div>}
      </div>}

      {tab==="cancellations"&&<div>
        <h3 className="mb-16">💰 Pending Refunds & Cancellations</h3>
        {cancellations.length===0?<div className="card text-center"><p className="text-muted">No pending cancellation requests.</p></div>:
        <div style={{display:"flex",flexDirection:"column",gap:16}}>
          {cancellations.map(c=>(
            <div key={c.id} className="card glass">
              <div className="flex-between mb-12">
                <div style={{fontSize:"1.2rem", fontWeight:700}}>{c.pnr}</div>
                <div className="text-gold" style={{fontSize:"1.2rem", fontWeight:700}}>{fmtCur(c.price)}</div>
              </div>
              <div className="grid2 mb-12" style={{gap:10}}>
                <div><span className="text-muted" style={{fontSize:".8rem", display:"block"}}>PASSENGER</span>{c.passenger_name}</div>
                <div><span className="text-muted" style={{fontSize:".8rem", display:"block"}}>ROUTE</span>{c.source} → {c.destination}</div>
              </div>
              <div className="alert alert-warn mb-16" style={{flexDirection:"column", alignItems:"flex-start", padding:"12px 16px"}}>
                <strong style={{fontSize:".85rem", marginBottom:4}}>REASON FOR CANCELLATION:</strong>
                <span style={{fontStyle:"italic"}}>{c.cancel_reason||"No reason provided."}</span>
              </div>
              <button className="btn btn-primary w100" onClick={()=>handleApproveRefund(c.id)}>✅ Verify & Resend Money</button>
            </div>
          ))}
      </div>}
      </div>}

      {tab==="alerts"&&<div>
        <div className="flex-between mb-16">
          <h3>🚨 Fraud Scan Alerts</h3>
          <span className="badge badge-high">{alerts.filter(a=>a.verdict!=="VALID").length} Fraud Events</span>
        </div>
        {alerts.length===0?<div className="card text-center"><p className="text-muted">No scan alerts yet.</p></div>:
        <div className="card" style={{padding:0,overflow:"hidden"}}>
          <table className="table">
            <thead><tr><th>Time</th><th>PNR</th><th>Checker</th><th>Mode</th><th>Verdict</th><th>Fraud Flags</th></tr></thead>
            <tbody>{alerts.map((a,i)=>(
              <tr key={i}>
                <td className="text-muted" style={{fontSize:".8rem"}}>{a.logged_at?.toDate?a.logged_at.toDate().toLocaleString("en-IN"):"—"}</td>
                <td><span className="text-cyan" style={{fontFamily:"monospace",fontWeight:700}}>{a.pnr||"—"}</span></td>
                <td style={{fontSize:".85rem"}}>{a.checker_id||"—"}</td>
                <td>{a.mode==="train"?"🚆":a.mode==="bus"?"🚌":a.mode==="flight"?"✈️":"—"} {(a.mode||"").toUpperCase()}</td>
                <td><span className={`badge ${a.verdict==="VALID"?"badge-low":"badge-high"}`}>{a.verdict}</span></td>
                <td style={{fontSize:".8rem",color:"var(--orange)"}}>{(a.flags||[]).join(", ")||"—"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>}
      </div>}

      {tab==="charts"&&<div className="card text-center">
        <h3 className="mb-16">Bookings & Scans — Fraud Distribution</h3>
        <canvas ref={chartRef} style={{maxHeight:340,maxWidth:480,margin:"0 auto"}}/>
      </div>}

      {tab==="model"&&<div className="card">
        <h3 className="mb-8">🤖 Retrain Fraud Detection Model</h3>
        <p className="text-muted mb-16" style={{fontSize:".9rem"}}>This triggers the Python training script using accumulated feedback data. May take 30–120 seconds.</p>
        {retMsg&&<div className={`alert ${retMsg.startsWith("✅")?"alert-ok":"alert-err"} mb-8`}>{retMsg}</div>}
        <button onClick={retrain} disabled={retraining} className="btn btn-primary">
          {retraining?<><span className="loader"/>&nbsp;Training…</>:"🔄 Retrain Model Now"}
        </button>
      </div>}
    </div>
  );
}

function CheckerDashboard({user}){
  const [mode,setMode]=React.useState("manual"); // manual | image | camera
  const [travelMode,setTravelMode]=React.useState("train");
  const [pnr,setPnr]=React.useState("");
  const [result,setResult]=React.useState(null);
  const [loading,setLoading]=React.useState(false);
  const [recentScans,setRecentScans]=React.useState([]);
  const [camActive,setCamActive]=React.useState(false);
  const videoRef=React.useRef(null);
  const canvasRef=React.useRef(null);
  const streamRef=React.useRef(null);
  const scanLoopRef=React.useRef(null);

  // Camera cleanup on mode change
  React.useEffect(()=>{
    if(mode!=="camera"){stopCamera();}
    return()=>stopCamera();
  },[mode]);

  function stopCamera(){
    if(scanLoopRef.current){cancelAnimationFrame(scanLoopRef.current);scanLoopRef.current=null;}
    if(streamRef.current){streamRef.current.getTracks().forEach(t=>t.stop());streamRef.current=null;}
    setCamActive(false);
  }

  async function startCamera(){
    try{
      const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"},audio:false});
      streamRef.current=stream;
      if(videoRef.current){videoRef.current.srcObject=stream;videoRef.current.play();}
      setCamActive(true);
      scanFrame();
    }catch(e){alert("Camera access denied or not available: "+e.message);}
  }

  function scanFrame(){
    const video=videoRef.current;const canvas=canvasRef.current;
    if(!video||!canvas||!streamRef.current){return;}
    const ctx=canvas.getContext("2d");
    canvas.width=video.videoWidth||320;canvas.height=video.videoHeight||240;
    ctx.drawImage(video,0,0,canvas.width,canvas.height);
    const imageData=ctx.getImageData(0,0,canvas.width,canvas.height);
    if(typeof jsQR!=="undefined"){
      const code=jsQR(imageData.data,imageData.width,imageData.height);
      if(code&&code.data){
        stopCamera();
        const decoded=extractPNRFromQR(code.data);
        if(decoded){runVerification(decoded);return;}
      }
    }
    scanLoopRef.current=requestAnimationFrame(scanFrame);
  }

  function extractPNRFromQR(raw){
    try{
      const obj=JSON.parse(raw);
      return obj.ticket_id||obj.pnr||null;
    }catch{
      const m=raw.match(/[A-Z]{2}\d{8}/);
      return m?m[0]:raw.trim().toUpperCase()||null;
    }
  }

  function handleImageUpload(e){
    const file=e.target.files[0];if(!file)return;
    const img=new Image();const url=URL.createObjectURL(file);
    img.onload=()=>{
      const canvas=document.createElement("canvas");
      canvas.width=img.width;canvas.height=img.height;
      const ctx=canvas.getContext("2d");ctx.drawImage(img,0,0);
      const imageData=ctx.getImageData(0,0,canvas.width,canvas.height);
      if(typeof jsQR!=="undefined"){
        const code=jsQR(imageData.data,imageData.width,imageData.height);
        if(code&&code.data){
          const decoded=extractPNRFromQR(code.data);
          if(decoded){runVerification(decoded);return;}
        }
      }
      alert("No QR code found in image. Please enter PNR manually.");
    };
    img.src=url;
  }

  async function runVerification(pnrVal){
    if(!pnrVal)return;
    setLoading(true);setResult(null);
    const pnrUpper=pnrVal.trim().toUpperCase();
    const flags=[];
    let verdict="VALID";let color="var(--green)";let icon="✅";let msg="Ticket is VALID — Passenger cleared for boarding!";
    let tktData=null;

    try{
      const snap=await getTicketByPNR(pnrUpper);

      // FRAUD CHECK 1: Fake / Not in DB
      if(snap.empty){
        flags.push("NOT_IN_DB");verdict="FAKE";color="var(--red)";icon="🚨";
        msg="❌ Ticket NOT found in database — Possible FAKE or INVALID ticket!";
      } else {
        tktData=snap.docs[0].data();
        const id=snap.docs[0].id;

        // FRAUD CHECK 2: Expired Ticket
        if(tktData.travel_date){
          const travelDate=new Date(tktData.travel_date);
          const today=new Date();today.setHours(0,0,0,0);
          if(travelDate<today){
            flags.push("EXPIRED");
            const daysAgo=Math.floor((today-travelDate)/(1000*60*60*24));
            verdict="EXPIRED";color="var(--red)";icon="⏰";
            msg=`⏰ Ticket EXPIRED — Travel date was ${daysAgo} day(s) ago. Do NOT allow boarding!`;
          }
        }

        // FRAUD CHECK 3: Already Used / Duplicate
        if(tktData.status==="USED"){
          flags.push("DUPLICATE");
          const usedAt=tktData.used_at?.toDate?tktData.used_at.toDate().toLocaleString("en-IN"):"recently";
          verdict="DUPLICATE";color="var(--orange)";icon="⚠️";
          msg=`⚠️ Ticket already USED on ${usedAt} — DUPLICATE / FRAUD detected!`;
        }

        // FRAUD CHECK 4: Cancelled ticket boarding attempt
        if(tktData.status==="CANCELLED"||tktData.status==="CANCEL_PENDING"){
          flags.push("CANCELLED");verdict="CANCELLED";color="var(--red)";icon="🚫";
          msg="🚫 This ticket has been CANCELLED — Do NOT allow boarding!";
        }

        // FRAUD CHECK 5: Mode Mismatch
        if(verdict==="VALID"&&tktData.mode&&tktData.mode!==travelMode){
          flags.push("MODE_MISMATCH");verdict="MODE_MISMATCH";color="var(--red)";icon="⛔";
          msg=`⛔ MODE MISMATCH — Ticket is for ${tktData.mode.toUpperCase()} but you are scanning for ${travelMode.toUpperCase()}!`;
        }

        // Mark as USED only if fully valid
        if(verdict==="VALID"){
          await markTicketUsed(id);
          setRecentScans(prev=>[{pnr:pnrUpper,passenger:tktData.passenger_name,route:`${tktData.source} → ${tktData.destination}`,verdict:"VALID",time:new Date().toLocaleTimeString("en-IN")},...prev.slice(0,9)]);
        }
      }

      // Log every scan to audit trail
      await logScanAlert({
        pnr:pnrUpper,checker_id:user?.uid||"unknown",checker_email:user?.email||"unknown",
        mode:travelMode,verdict,flags,passenger:tktData?.passenger_name||null,
        route:tktData?`${tktData.source} → ${tktData.destination}`:null,
        risk_score:tktData?.risk_score||0,risk_level:tktData?.risk_level||null
      });

      const riskScore=tktData?.risk_score||0;
      const riskWarning=verdict==="VALID"&&riskScore>=65;
      setResult({status:verdict,pnr:pnrUpper,msg:riskWarning?msg+" ⚠️ HIGH RISK — Verify passenger ID manually!":msg,color,icon,tkt:tktData,riskScore,flags});

    }catch(err){
      setResult({status:"ERROR",pnr:pnrUpper,msg:"⚠️ Connection error: "+err.message,color:"var(--orange)",icon:"⚠️"});
    }
    setLoading(false);setPnr("");
  }

  function handleManualSubmit(e){e.preventDefault();runVerification(pnr);}

  const modeIcon=travelMode==="train"?"🚆":travelMode==="bus"?"🚌":"✈️";

  return(
    <div className="page fade-in">
      <div className="page-title-section text-center">
        <h1 className="glow-text" style={{fontSize:"2.8rem",marginBottom:8}}>🚆 Checker Dashboard</h1>
        <p className="text-muted">Official ticket verification portal for conductors, TTEs & boarding agents</p>
        <div className="flex mt-16" style={{justifyContent:"center",gap:12}}>
          <span className="badge badge-low">🟢 Live System</span>
          <span className="badge badge-low">🔐 6-Layer Fraud Detection</span>
        </div>
      </div>

      {/* Travel Mode Selector */}
      <div className="glass-card mb-16" style={{padding:"16px 24px"}}>
        <div className="flex-between">
          <strong style={{fontSize:".9rem",color:"var(--muted)"}}>CURRENT TRANSPORT MODE (select before scanning):</strong>
          <div className="flex" style={{gap:10}}>
            {["train","bus","flight"].map(m=>(
              <button key={m} onClick={()=>setTravelMode(m)}
                className={`btn btn-sm ${travelMode===m?"btn-primary":"btn-outline"}`}
                style={{borderRadius:10}}>
                {m==="train"?"🚆 Train":m==="bus"?"🚌 Bus":"✈️ Flight"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Scan Input Tabs */}
      <div className="glass-card mb-24" style={{padding:32,border:"1px solid rgba(0,212,255,0.3)",boxShadow:"0 0 40px rgba(0,212,255,0.1)"}}>
        <div className="tabs mb-24">
          {[["manual","🔢 Manual PNR"],["image","🖼️ Upload Image"],["camera","📷 Live Camera"]].map(([k,l])=>(
            <button key={k} className={`tab${mode===k?" active":""}`} onClick={()=>{setMode(k);setResult(null);}}>
              {l}
            </button>
          ))}
        </div>

        {/* Manual */}
        {mode==="manual"&&<form onSubmit={handleManualSubmit}>
          <div style={{display:"flex",gap:12,maxWidth:600,margin:"0 auto"}}>
            <input id="checker-pnr-input" value={pnr} onChange={e=>setPnr(e.target.value.toUpperCase())}
              placeholder="Enter PNR (e.g. AB12345678)"
              style={{flex:1,padding:"18px 22px",fontSize:"1.2rem",fontFamily:"monospace",letterSpacing:3,textAlign:"center",fontWeight:700}} autoFocus/>
            <button type="submit" className="premium-btn" disabled={loading||!pnr.trim()} style={{padding:"18px 32px"}}>
              {loading?<><span className="loader"/>&nbsp;Checking…</>:"Verify →"}
            </button>
          </div>
        </form>}

        {/* Image Upload */}
        {mode==="image"&&<div style={{textAlign:"center"}}>
          <div className="drop-zone" style={{maxWidth:500,margin:"0 auto"}} onClick={()=>document.getElementById("checker-img-input").click()}>
            <div style={{fontSize:"2.5rem",marginBottom:8}}>🖼️</div>
            <p className="text-muted">Click to upload ticket image or screenshot</p>
            <p className="text-muted" style={{fontSize:".8rem",marginTop:4}}>QR code will be scanned automatically</p>
            <input id="checker-img-input" type="file" accept="image/*" style={{display:"none"}} onChange={handleImageUpload}/>
          </div>
          {loading&&<div className="mt-16 text-center"><span className="loader"/>&nbsp;<span className="text-muted">Decoding QR…</span></div>}
        </div>}

        {/* Camera */}
        {mode==="camera"&&<div style={{textAlign:"center"}}>
          {!camActive?<button className="premium-btn" onClick={startCamera} style={{padding:"16px 32px",fontSize:"1rem"}}>
            📷 Start Camera
          </button>:
          <div>
            <div style={{position:"relative",display:"inline-block",border:"2px solid var(--cyan)",borderRadius:12,overflow:"hidden"}}>
              <video ref={videoRef} style={{width:"100%",maxWidth:480,display:"block"}} playsInline muted/>
              <div style={{position:"absolute",inset:0,border:"3px solid var(--cyan)",borderRadius:12,animation:"scan-pulse 1.5s ease-in-out infinite",pointerEvents:"none"}}/>
            </div>
            <canvas ref={canvasRef} style={{display:"none"}}/>
            <p className="text-muted mt-12" style={{fontSize:".9rem"}}>📡 Scanning for QR code… Point camera at the ticket's QR code</p>
            <button className="btn btn-outline mt-8" onClick={stopCamera}>⛔ Stop Camera</button>
          </div>}
          {loading&&<div className="mt-16 text-center"><span className="loader"/>&nbsp;<span className="text-muted">Verifying…</span></div>}
        </div>}

        {/* Result */}
        {result&&(
          <div className="fade-in mt-24" style={{maxWidth:620,margin:"24px auto 0"}}>
            <div style={{background:"rgba(0,0,0,0.5)",border:`2px solid ${result.color}`,borderRadius:16,padding:28,boxShadow:`0 0 30px ${result.color}33`}}>
              <div style={{fontSize:"3.5rem",marginBottom:8}}>{result.icon}</div>
              <h2 style={{color:result.color,fontSize:"1.8rem",letterSpacing:2,marginBottom:8,textTransform:"uppercase"}}>{result.status}</h2>
              <p style={{fontSize:"1rem",fontWeight:600,marginBottom:16}}>{result.msg}</p>
              <div style={{background:"rgba(0,0,0,0.3)",borderRadius:10,padding:"10px 16px",fontFamily:"monospace",fontSize:"1.3rem",color:"var(--cyan)",letterSpacing:3,marginBottom:16}}>
                PNR: {result.pnr}
              </div>

              {/* AI Risk Score Bar */}
              {result.tkt&&(
                <div style={{marginBottom:16,textAlign:"left"}}>
                  <div className="flex-between mb-8" style={{fontSize:".85rem"}}>
                    <span className="text-muted">AI BOOKING RISK SCORE</span>
                    <strong style={{color:result.riskScore>=65?"var(--red)":result.riskScore>=35?"var(--orange)":"var(--green)"}}>{result.riskScore}/100 — {result.riskScore>=65?"HIGH":result.riskScore>=35?"MEDIUM":"LOW"}</strong>
                  </div>
                  <div style={{height:8,background:"rgba(255,255,255,0.1)",borderRadius:4,overflow:"hidden"}}>
                    <div style={{height:"100%",width:`${result.riskScore}%`,background:result.riskScore>=65?"var(--red)":result.riskScore>=35?"var(--orange)":"var(--green)",borderRadius:4,transition:"width 0.6s ease"}}/>
                  </div>
                  {result.riskScore>=65&&<div className="alert alert-err mt-8" style={{fontSize:".85rem",padding:"8px 12px"}}>⚠️ HIGH RISK — Request passenger government ID before allowing boarding!</div>}
                </div>
              )}

              {/* Fraud Flags */}
              {result.flags&&result.flags.length>0&&(
                <div className="flex mb-12" style={{gap:8,flexWrap:"wrap"}}>
                  {result.flags.map(f=><span key={f} className="badge badge-high" style={{fontSize:".75rem"}}>🚨 {f.replace(/_/g," ")}</span>)}
                </div>
              )}

              {/* Passenger Details */}
              {result.tkt&&(
                <div className="grid2 mt-12" style={{gap:10,textAlign:"left"}}>
                  {[["PASSENGER",result.tkt.passenger_name],["SEAT",result.tkt.seat_number||"TBD"],["FROM",result.tkt.source],["TO",result.tkt.destination],["DATE",result.tkt.travel_date],["MODE & CLASS",`${result.tkt.mode==="train"?"🚆":result.tkt.mode==="bus"?"🚌":"✈️"} ${(result.tkt.mode||"").toUpperCase()} — ${result.tkt.seat_class}`]].map(([l,v])=>(
                    <div key={l} style={{background:"rgba(255,255,255,0.04)",borderRadius:10,padding:12}}>
                      <div className="text-muted" style={{fontSize:".65rem",marginBottom:3}}>{l}</div>
                      <strong style={{fontSize:".9rem"}}>{v}</strong>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button className="btn btn-outline mt-16 w100" onClick={()=>{setResult(null);setPnr("");}}>🔄 Scan Next Ticket</button>
          </div>
        )}
      </div>

      {/* Recent Scans */}
      {recentScans.length>0&&(
        <div className="card">
          <h3 className="mb-16">📋 Cleared Passengers (This Session)</h3>
          <table className="table">
            <thead><tr><th>PNR</th><th>Passenger</th><th>Route</th><th>Verdict</th><th>Time</th></tr></thead>
            <tbody>{recentScans.map((s,i)=>(
              <tr key={i}>
                <td><span className="text-cyan" style={{fontFamily:"monospace",fontWeight:700}}>{s.pnr}</span></td>
                <td>{s.passenger}</td>
                <td style={{fontSize:".85rem"}}>{s.route}</td>
                <td><span className="badge badge-low">✅ BOARDED</span></td>
                <td className="text-muted" style={{fontSize:".85rem"}}>{s.time}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ShareViewPage({token,setPage}){
  const [data,setData]=React.useState(null);
  const [loading,setLoading]=React.useState(true);
  const [error,setError]=React.useState("");

  React.useEffect(()=>{
    async function load(){
      try{
        const r=await fetch(`${API}/api/share/view/${token}`);
        const d=await r.json();
        if(d.error)setError(d.error);
        else setData(d);
      }catch{setError("Backend offline.");}
      setLoading(false);
    }
    load();
  },[token]);

  if(loading)return <div className="page text-center"><span className="loader"/></div>;
  if(error)return <div className="page text-center"><div className="alert alert-err">{error}</div><button className="btn btn-primary mt-16" onClick={()=>setPage("home")}>Go Home</button></div>;

  return(
    <div className="page fade-in" style={{maxWidth:700}}>
      <div className="text-center mb-24">
        <h1 className="glow-text">Shared Scan Result</h1>
        <p className="text-muted">This result was shared via SecureTrail Platform</p>
      </div>
      {data && <ScannerPage_ResultCard r={data} noUser={true}/>}
      <div className="mt-24 text-center">
        <button className="btn btn-outline" onClick={()=>setPage("home")}>Visit SecureTrail Home</button>
      </div>
    </div>
  );
}

function ScannerPage_ResultCard({r,noUser}){
    const status = r.status || "UNKNOWN";
    const msg = r.message || "";
    const pnr = r.ticket_id || "N/A";
    
    const statusColors = {
      "VALID": "var(--green)", "FRAUD": "var(--red)", "FAKE": "var(--red)", "INVALID": "var(--orange)", "SUSPICIOUS": "var(--orange)", "DUPLICATE": "var(--orange)", "USED": "var(--orange)"
    };
    const statusIcons = {
      "VALID": "✅", "FRAUD": "🚨", "FAKE": "❌", "INVALID": "⏰", "SUSPICIOUS": "⚠️", "DUPLICATE": "⚠️", "USED": "🔴"
    };

    return(
      <div className="glass-card fade-in mt-24" style={{borderWidth: 2, borderColor: "rgba(0,212,255,0.1)"}}>
        <div className="flex-between mb-24">
          <h3 className="glow-text">🤖 Scanner Verdict</h3>
          <span className="badge" style={{background: statusColors[status] || "var(--card2)", padding: "6px 14px", fontSize: ".8rem"}}>
            {statusIcons[status] || "❓"} {status}
          </span>
        </div>
        <div style={{textAlign:"center",marginBottom:24}}>
          <div style={{fontSize:"4.5rem", marginBottom:15, filter: "drop-shadow(0 0 15px rgba(255,255,255,0.2))"}}>{statusIcons[status] || "❓"}</div>
          <h2 style={{color: statusColors[status] || "var(--muted)", textTransform: "uppercase", letterSpacing: 3, fontSize: "2.2rem"}}>{status}</h2>
          <p className="mt-12" style={{fontSize: "1.2rem", fontWeight: 600, color: "var(--text)"}}>{msg}</p>
          <p className="text-muted mt-8" style={{fontSize:".9rem"}}>PNR ID: <strong className="text-cyan" style={{fontFamily: "monospace"}}>{pnr}</strong></p>
        </div>
        
        {r.checks && (
          <div className="mt-24">
            <h3 className="mb-16" style={{fontSize: "0.9rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: 1}}>🔍 Deep Scan Analysis</h3>
            <div className="grid2" style={{gap:10}}>
              {Object.entries(r.checks).map(([k,v])=>(
                <div key={k} className="scanner-grid-detail glass" style={{padding: "12px 16px", borderRadius: 12}}>
                  <span style={{fontSize:".7rem",color:"var(--muted)",textTransform:"uppercase", fontWeight: 700}}>{k.replace(/_/g," ")}</span>
                  <span style={{color:v?"var(--green)":"var(--red)",fontWeight:800,fontSize:".85rem"}}>{v?"PASS":"FAIL"}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
}
