/* Navbar + Auth + Home + Booking pages */

function Navbar({page,setPage,user,userData,onLogout}){
  return(
    <nav className="navbar">
      <div className="nav-logo" onClick={()=>setPage("home")}>
        <div className="nav-logo-icon">🛡️</div> Secure Trail
      </div>
      <div className="nav-links">
        <button className={`nav-link${page==="home"?" active":""}`} onClick={()=>setPage("home")}>Home</button>
        {user&&userData?.role!=="checker"&&<button className={`nav-link${page==="booking"?" active":""}`} onClick={()=>setPage("booking")}>🎫 Book Ticket</button>}
        {user&&userData?.role==="checker"&&<button className={`nav-link${page==="checker"?" active":""}`} onClick={()=>setPage("checker")}>🚆 Dashboard</button>}
        {user&&<button className={`nav-link${page==="scanner"?" active":""}`} onClick={()=>setPage("scanner")}>🔍 AI Scanner</button>}
        {user&&userData?.role!=="checker"&&<button className={`nav-link${page==="tickets"?" active":""}`} onClick={()=>setPage("tickets")}>My Tickets</button>}
        {user&&<button className={`nav-link${page==="profile"?" active":""}`} onClick={()=>setPage("profile")}>👤 Profile</button>}
        {user&&userData?.role==="admin"&&<button className={`nav-link${page==="admin"?" active":""}`} onClick={()=>setPage("admin")}>Admin</button>}
      </div>
      <div className="nav-right">
        {user ? (
          <div className="nav-user" onClick={()=>setPage("profile")} style={{cursor:"pointer"}}>
            <div className="nav-avatar">{userData?.name ? userData.name.charAt(0).toUpperCase() : "U"}</div>
            <div className="nav-username">{userData?.name || "User"}</div>
            <button className="btn-logout" onClick={(e)=>{e.stopPropagation();onLogout();}}>Logout</button>
          </div>
        ) : (
          <div style={{display:"flex",gap:"12px"}}>
            <button className="nav-link" onClick={()=>setPage("login")}>Login</button>
            <button className="btn btn-primary btn-sm" onClick={()=>setPage("signup")}>Sign Up</button>
          </div>
        )}
      </div>
    </nav>
  );
}

function AuthPage({mode,setPage,onAuth}){
  const [form,setForm]=React.useState({name:"",email:"",password:""});
  const [err,setErr]=React.useState("");
  const [loading,setLoading]=React.useState(false);
  const isLogin=mode==="login";

  async function submit(e){
    e.preventDefault();setErr("");setLoading(true);
    try{
      if(isLogin){
        const r=await auth.signInWithEmailAndPassword(form.email,form.password);
        const snap=await db.collection("users").doc(r.user.uid).get();
        onAuth(r.user,snap.data());
      }else{
        const r=await auth.createUserWithEmailAndPassword(form.email,form.password);
        const role=(form.email==="admin_new@securetrail.in")?"admin":(form.email==="checker@securetrail.in")?"checker":"user";
        const udata={name:form.name,email:form.email,role:role,created_at:new Date().toISOString(),login_count:0};
        await db.collection("users").doc(r.user.uid).set(udata);
        onAuth(r.user,udata);
      }
    }catch(ex){setErr(ex.message);}
    setLoading(false);
  }

  return(
    <div className="page fade-in" style={{maxWidth:440,paddingTop:40}}>
      <div className="card">
        <div className="text-center mb-16">
          <div style={{fontSize:"2.5rem",marginBottom:8}}>{isLogin?"🔐":"🚀"}</div>
          <h2>{isLogin?"Welcome Back":"Create Account"}</h2>
          <p className="text-muted mt-8" style={{fontSize:".9rem"}}>{isLogin?"Sign in to book tickets":"Join SecureTrail today"}</p>
        </div>
        {err&&<div className="alert alert-err">⚠️ {err}</div>}
        <form onSubmit={submit}>
          {!isLogin&&<div className="form-group">
            <label className="form-label">Full Name</label>
            <input required placeholder="Rahul Sharma" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/>
          </div>}
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input type="email" required placeholder="you@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input type="password" required placeholder="Min 6 characters" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
          </div>
          <button type="submit" className="btn btn-primary w100" disabled={loading}>
            {loading?<><span className="loader"/>&nbsp;Please wait…</>:isLogin?"Sign In →":"Create Account →"}
          </button>
        </form>
        <div className="text-center mt-16" style={{fontSize:".88rem",color:"var(--muted)"}}>
          {isLogin?"Don't have an account? ":"Already have an account? "}
          <span className="text-cyan" style={{cursor:"pointer"}} onClick={()=>setPage(isLogin?"signup":"login")}>{isLogin?"Sign Up":"Log In"}</span>
        </div>
        {isLogin&&<div className="text-center mt-8" style={{fontSize:".8rem",color:"var(--muted)"}}>Admin: admin_new@securetrail.in / Admin@123</div>}
      </div>
    </div>
  );
}

function HomePage({setPage,user}){
  const stats=[
    {icon:"🎫",label:"Tickets Booked",val:"12,400+"},
    {icon:"🛡️",label:"Frauds Detected",val:"3,200+"},
    {icon:"🏙️",label:"Indian Cities",val:"30"},
    {icon:"🤖",label:"AI Accuracy",val:"94.8%"},
  ];

  return(
    <div>
      <section className="hero">
        <div className="hero-grid">
          <div className="hero-left fade-in">
            <div className="hero-tag">🤖 AI · OTP · REAL-TIME FRAUD DETECTION</div>
            <h1>E-Tickets<br/>Protected by<br/><span>AI & Secure OTP</span></h1>
            <p>Book train, bus & flight e-tickets with real-time OTP payment verification and hybrid AI fraud detection. Every journey, secured.</p>
            <div className="hero-actions">
              <button className="btn btn-primary" onClick={()=>user?setPage("booking"):setPage("login")}>🎫 Book E-Ticket</button>
              <button className="btn btn-outline" onClick={()=>user?setPage("scanner"):setPage("login")}>🔍 Scan Ticket</button>
              <button className="btn btn-logout" style={{display:"flex",alignItems:"center",gap:6,border:"1px solid rgba(255,255,255,0.1)",background:"rgba(255,255,255,0.05)"}} onClick={()=>user?setPage("tickets"):setPage("login")}>📊 Dashboard</button>
            </div>
          </div>
          <div className="hero-right">
            <div className="hero-pill hero-pill-1">
              <div><span style={{fontSize:"1.1rem"}}>🤖</span> <span className="text-muted" style={{fontSize:".7rem",display:"block"}}>AI FRAUD CHECK</span><span className="text-green">✅ VALID — 0% Risk</span></div>
            </div>
            <div className="hero-pill hero-pill-2">
              <div><span style={{fontSize:"1.1rem"}}>🔒</span> <span className="text-muted" style={{fontSize:".7rem",display:"block"}}>OTP VERIFIED</span><span className="text-cyan">TXN9823041762</span></div>
            </div>
            <div className="hero-pill hero-pill-3">
              <div><span style={{fontSize:"1.1rem"}}>🚨</span> <span className="text-muted" style={{fontSize:".7rem",display:"block"}}>FRAUD BLOCKED</span><span className="text-red">Rule-Based · IP Suspicious</span></div>
            </div>
          </div>
        </div>
      </section>

      <div className="page">
        <div className="grid4 mt-24 mb-16">
          {stats.map(s=>(
            <div key={s.label} className="stat-card text-center">
              <div style={{fontSize:"2rem",marginBottom:8}}>{s.icon}</div>
              <div className="stat-num">{s.val}</div>
              <div className="text-muted" style={{fontSize:".85rem",marginTop:4}}>{s.label}</div>
            </div>
          ))}
        </div>

        <div className="card mt-24">
          <div className="grid2">
            <div>
              <h2 className="mb-16" style={{fontSize:"2rem"}}>🛡️ AI Fraud Detection Engine</h2>
              <p className="text-muted mb-16" style={{lineHeight:1.6,fontSize:"1.05rem"}}>Our proprietary hybrid machine learning system instantly scores every ticket using advanced behavior analytics and computer vision.</p>
              <img src="ai_security.png" alt="AI Security" className="feature-img"/>
              <button className="btn btn-primary mt-8" onClick={()=>user?setPage("scanner"):setPage("login")}>Try the Scanner</button>
            </div>
            <div className="grid2">
              {[
                {icon:"🤖",t:"Behavior Analysis",d:"ML model analyzes booking patterns, speed, and device changes in real-time."},
                {icon:"📷",t:"Image Scanning",d:"Upload ticket images for deep CV analysis—QR verification, OCR, edge detection."},
                {icon:"📊",t:"Risk Scoring",d:"Every ticket gets a 0–100 risk score with LOW/MEDIUM/HIGH classification."},
                {icon:"🔄",t:"Active Learning",d:"User feedback loops back to retrain the model, improving accuracy continuously."}
              ].map(f=>(
                <div key={f.t} className="card" style={{borderColor:"rgba(0,212,255,.2)",padding:"16px"}}>
                  <div style={{fontSize:"1.5rem",marginBottom:8}}>{f.icon}</div>
                  <h3 style={{fontSize:"1rem"}}>{f.t}</h3>
                  <p className="text-muted mt-8" style={{fontSize:".8rem",lineHeight:1.5}}>{f.d}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card mt-24 mb-24" style={{background:"transparent",border:"none",padding:0}}>
          <div className="grid2" style={{alignItems:"center"}}>
             <div className="card" style={{background:"rgba(0,212,255,0.02)",borderColor:"var(--cyan)"}}>
               <h2 className="mb-16 text-cyan" style={{fontSize:"2rem"}}>Seamless Nationwide Booking</h2>
               <p className="text-muted mb-16" style={{lineHeight:1.6,fontSize:"1.05rem"}}>Access tickets for trains, buses, and flights across 30 major Indian cities seamlessly within a single, secure interface.</p>
               <button className="btn btn-outline" onClick={()=>user?setPage("booking"):setPage("login")}>Explore Routes</button>
             </div>
             <img src="travel_train.png" alt="Travel" className="feature-img" style={{height:"300px",marginBottom:0}}/>
          </div>
        </div>
      </div>
    </div>
  );
}

function ProfilePage({user,userData,onLogout}){
  return(
    <div className="page fade-in" style={{maxWidth:600}}>
      <div className="card text-center" style={{padding:"40px 20px"}}>
        <div className="nav-avatar" style={{width:80,height:80,fontSize:"2.5rem",margin:"0 auto 16px",background:"linear-gradient(135deg,var(--cyan),var(--blue))"}}>
          {userData?.name ? userData.name.charAt(0).toUpperCase() : "U"}
        </div>
        <h2 style={{fontSize:"2rem"}}>{userData?.name || "User Account"}</h2>
        <p className="text-muted mb-24">{userData?.email || "No email provided"}</p>
        
        <div className="grid2 mb-24" style={{textAlign:"left"}}>
          <div className="card" style={{background:"rgba(255,255,255,0.03)",padding:16}}>
            <div className="text-muted" style={{fontSize:".8rem"}}>ROLE</div>
            <div style={{fontWeight:700,color:"var(--cyan)"}}>{userData?.role?.toUpperCase() || "USER"}</div>
          </div>
          <div className="card" style={{background:"rgba(255,255,255,0.03)",padding:16}}>
            <div className="text-muted" style={{fontSize:".8rem"}}>JOINED</div>
            <div style={{fontWeight:700}}>{userData?.created_at?.split("T")[0] || "N/A"}</div>
          </div>
        </div>

        <div className="card mb-24" style={{textAlign:"left",background:"rgba(0,212,255,0.05)",borderColor:"var(--cyan)"}}>
          <h3 className="mb-8">🛡️ Security Status</h3>
          <p className="text-muted" style={{fontSize:".85rem"}}>Your account is protected by 2FA and AI Behavior Analysis.</p>
          <div className="flex mt-12" style={{gap:12}}>
            <div className="badge badge-low">Verified</div>
            <div className="badge badge-low">SSL Active</div>
          </div>
        </div>

        <button className="btn btn-danger w100" onClick={onLogout}>Logout Securely</button>
      </div>
    </div>
  );
}
