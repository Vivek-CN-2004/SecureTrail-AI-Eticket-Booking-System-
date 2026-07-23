/* BookingPage — 4-step booking flow */

function BookingPage({user,userData,setPage}){
  const [step,setStep]=React.useState(1);
  const [form,setForm]=React.useState({name:userData?.name||"",src:"",dst:"",date:"",preferredTime:"",mode:"train",cls:"Sleeper",seat:"",passengers:1});
  const [price,setPrice]=React.useState(0);
  const [fraud,setFraud]=React.useState(null);
  const [otp,setOtp]=React.useState("");
  const [sessionId,setSessionId]=React.useState("");
  const [serverOtp,setServerOtp]=React.useState("");
  const [ticket,setTicket]=React.useState(null);
  const [qrPayload,setQrPayload]=React.useState(null);
  const [loading,setLoading]=React.useState(false);
  const [err,setErr]=React.useState("");
  const [otpTimer,setOtpTimer]=React.useState(60);
  const [accountBlocked,setAccountBlocked]=React.useState(false);
  // Trip scheduling state
  const [trips,setTrips]=React.useState([]);
  const [selectedTrip,setSelectedTrip]=React.useState(null);
  const [tripMessage,setTripMessage]=React.useState("");
  // Seats state
  const [bookedSeats,setBookedSeats]=React.useState([]);
  const [selectedSeat,setSelectedSeat]=React.useState("");
  const [tripId,setTripId]=React.useState("");
  
  const startRef=React.useRef(Date.now());

  // Check if account is banned/suspended
  React.useEffect(()=>{
    if(userData?.flag_status==="BANNED"||userData?.account_deleted){
      setAccountBlocked(true);
    }
  },[userData]);

  React.useEffect(()=>{
    if(form.src&&form.dst&&form.src!==form.dst&&form.mode&&form.cls){
      const dt=form.date?new Date(form.date):null;
      setPrice(calcPrice(form.mode,form.cls,form.src,form.dst,dt));
    }
  },[form.src,form.dst,form.mode,form.cls,form.date]);

  React.useEffect(()=>{
    if(step===5){
      const t=setInterval(()=>setOtpTimer(x=>x>0?x-1:0),1000);
      return()=>clearInterval(t);
    }
  },[step]);

  async function goToTrips(e){
    e.preventDefault();setErr("");
    if(form.src===form.dst){setErr("Source and destination cannot be the same.");return;}
    if(!form.name.trim()){setErr("Passenger name is required.");return;}
    // if(new Date(form.date)<=new Date()){setErr("Travel date must be in the future.");return;}
    setLoading(true);
    try{
      const url=`${API}/api/trips?source=${encodeURIComponent(form.src)}&destination=${encodeURIComponent(form.dst)}&date=${form.date}&mode=${form.mode}&preferred_time=${form.preferredTime||""}`;
      const res=await fetch(url);
      const data=await res.json();
      setTrips(data.trips||[]);
      setTripMessage(data.message||"");
      setSelectedTrip(null);
      setStep(2);
    }catch(ex){setErr("Could not load trips. Please try again.");}
    setLoading(false);
  }

  async function goToSeats(trip){
    setSelectedTrip(trip);
    setTripId(trip.trip_id);
    setPrice(trip.price);
    setLoading(true);
    try{
      const res=await fetch(`${API}/api/seats?trip_id=${trip.trip_id}`);
      const data=await res.json();
      if(data.seats)setBookedSeats(data.seats.map(s=>s.seat_number));
    }catch(ex){console.warn("Could not fetch seats",ex);}
    setLoading(false);
    startRef.current=Date.now();
    setStep(3);
  }

  async function goToPayment(){
    setErr("");
    if(!selectedSeat){setErr("Please select a seat to continue.");return;}
    if(accountBlocked){setErr("🚫 Your account has been suspended. Please contact support.");return;}
    // Fraud check — pass full feature set so ML model has proper context
    const timeTaken=Math.round((Date.now()-startRef.current)/1000);
    const daysUntilTravel = form.date ? Math.max(0, Math.round((new Date(form.date)-new Date())/(1000*60*60*24))) : 7;
    // Feature: Trust/Reputation Tiering System
    const userTrustLevel = (userData?.login_count||0) > 5 ? 3 : (userData?.login_count||0) > 2 ? 2 : 1;
    if (userTrustLevel === 1 && form.mode === "flight" && form.cls === "Business") {
      setErr("🔒 Trust Tier 1 Restriction: New accounts cannot book high-value Business Class flights. Please complete standard trips to level up your Trust Score.");
      return;
    }
    
    // Feature: Impossible Travel Velocity Detection
    let userIPLocation = "Delhi"; // Fallback
    try {
      const ipRes = await fetch("https://ipapi.co/json/");
      const ipData = await ipRes.json();
      if(ipData.city) userIPLocation = ipData.city;
    } catch(e) {}
    if (daysUntilTravel === 0 && form.src !== userIPLocation && form.mode === "bus") {
      setErr(`🚨 Impossible Travel Detected: Your IP address indicates you are in ${userIPLocation}, but you are booking a local bus departing from ${form.src} today. This is physically impossible.`);
      return;
    }

    setLoading(true);
    const f=await predictFraud({
      ticket_type: form.mode||"train",
      class: form.cls||"Sleeper",
      booking_channel: "official_website",
      start_station: form.src||"Delhi",
      end_station: form.dst||"Mumbai",
      price: price||500,
      price_per_km: price && getDist(form.src,form.dst)>0 ? price/getDist(form.src,form.dst) : 1.5,
      days_until_travel: daysUntilTravel,
      pnr: "XXXXXXXXXX", // placeholder — model just checks length
      booking_frequency: 1,
      time_taken_sec: Math.max(timeTaken, 30), // minimum 30s to avoid false positives
      login_frequency: userData?.login_count||1,
      device_type: "browser",
      ip_change_flag: 0
    });
    setFraud(f);
    setLoading(false);
    if(f.risk_level==="HIGH"){
      // Flag the user in Firestore
      const currentFlagCount=(userData?.flag_count||0)+1;
      await flagUser(user.uid,"HIGH",`Suspicious rapid booking detected. Time taken: ${timeTaken}s`);
      if(currentFlagCount>=3){
        // Auto-ban repeat offenders
        await banUser(user.uid);
        setAccountBlocked(true);
        setErr("🚫 Your account has been permanently suspended due to repeated suspicious activity. Contact support.");
      } else {
        setErr(`🚨 High fraud risk detected! This incident has been reported to admin. You have ${3-currentFlagCount} warning(s) remaining before account suspension. Please wait 30 seconds.`);
        setTimeout(()=>setErr(""),30000);
      }
      return;
    }
    if(f.risk_level==="MEDIUM"){
      setErr("⚠️ Moderate risk detected. Please wait 10 seconds before proceeding.");
      setTimeout(()=>{setErr("");setStep(4);},10000);
      return;
    }
    setStep(4);
  }

  async function goToOtp(e){
    e.preventDefault();setErr("");setLoading(true);
    try{
      const r=await fetch(`${API}/api/generate_otp`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({booking:{...form,price,user_id:user.uid}})});
      const d=await r.json();
      setSessionId(d.session_id);setServerOtp(d.otp);
      setOtpTimer(60);setStep(5);
    }catch{setErr("Server unavailable. Generating local OTP.");}
    setLoading(false);
  }

  async function verifyOtp(e){
    e.preventDefault();setErr("");
    if(otp!==serverOtp){setErr("❌ Incorrect OTP. Please try again.");return;}
    setLoading(true);
    try{
      // First try to lock the seat
      const seatRes = await fetch(`${API}/api/book_seat`, {
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({trip_id:tripId, seat_number:selectedSeat, user_id:user.uid})
      });
      const seatData = await seatRes.json();
      if(!seatData.success) {
        setErr("Sorry, this seat was just booked by someone else. Please choose another.");
        setStep(3); setLoading(false); return;
      }
      
      // Now finalize booking with the backend
      const r = await fetch(`${API}/api/book_ticket`, {
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          user_id:user.uid,
          passenger_name:form.name,
          source:form.src,
          destination:form.dst,
          travel_date:form.date,
          mode:form.mode,
          seat_class:form.cls,
          seat_number:selectedSeat,
          price,
          distance:getDist(form.src,form.dst),
          trip_id:selectedTrip?.trip_id||"",
          departure_time:selectedTrip?.departure_time||"",
          arrival_time:selectedTrip?.arrival_time||"",
          is_fraud:fraud?.risk_level==="HIGH",
          risk_level:fraud?.risk_level||"LOW",
          risk_score:fraud?.risk_score||0
        })
      });
      const resData = await r.json();
      if(resData.success){
        setTicket(resData.ticket);
        setQrPayload(resData.qr_payload);
        setStep(6);
      } else {
        setErr("Booking failed: "+(resData.error||"Unknown error"));
      }
    }catch(ex){setErr(ex.message);}
    setLoading(false);
  }

  const stepLabels=["Details","Select Trip","Choose Seat","Payment","OTP","Ticket"];

  return(
    <div className="page fade-in" style={{maxWidth:700}}>
      <div className="page-title-section text-center">
        <h1 className="glow-text" style={{fontSize: "3rem", marginBottom: 8}}>🎫 Book Journey</h1>
        <p className="text-muted">Safe, secure, and AI-verified travel bookings</p>
      </div>

      <div style={{display: "flex", justifyContent: "flex-end", marginBottom: 20}}>
        {step < 4 && <button className="btn btn-sm btn-outline" onClick={() => step > 1 ? setStep(step - 1) : setPage("home")}>← Back to Home</button>}
      </div>

      {accountBlocked&&<div className="card" style={{background:"rgba(255,68,68,0.08)",border:"2px solid var(--red)",padding:32,textAlign:"center",marginBottom:24}}>
        <div style={{fontSize:"3rem",marginBottom:12}}>🚫</div>
        <h2 style={{color:"var(--red)",marginBottom:8}}>Account Suspended</h2>
        <p className="text-muted" style={{marginBottom:8}}>Your account has been flagged and suspended due to repeated suspicious booking activity.</p>
        <p className="text-muted" style={{fontSize:".85rem"}}>Please contact support to appeal this decision. An admin will review your account.</p>
      </div>}

      <div className="steps mb-24">
        {stepLabels.map((l,i)=>{
          const n=i+1;const done=step>n;const active=step===n;
          return <React.Fragment key={n}>
            {i>0&&<div className={`step-line${done?" done":""}`}/>}
            <div className="step">
              <div className={`step-n${done?" done":active?" active":" pending"}`}>{done?"✓":n}</div>
              <span style={{color:active?"var(--cyan)":done?"var(--green)":"var(--muted)"}}>{l}</span>
            </div>
          </React.Fragment>;
        })}
      </div>

      {err&&<div className="alert alert-err">⚠️ {err}</div>}

      {/* Step 1: Details */}
      {step===1&&<div className="glass-card fade-in">
        <form onSubmit={goToTrips}>
          <div className="form-group">
            <label className="form-label">Passenger Name</label>
            <input required placeholder="Enter full name" style={{fontSize: "1.1rem", padding: "14px 18px"}} value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/>
          </div>
          <div className="form-group">
            <label className="form-label">Travel Mode</label>
            <div className="flex" style={{gap:10}}>
              {["train","bus","flight"].map(m=>(
                <button key={m} type="button" onClick={()=>setForm({...form,mode:m,cls:CLASSES[m][1]||CLASSES[m][0]})} className={`btn${form.mode===m?" btn-primary":" btn-outline"}`} style={{flex:1, padding: "10px", borderRadius: 12}}>
                  {m==="train"?"🚆 Train":m==="bus"?"🚌 Bus":"✈️ Flight"}
                </button>
              ))}
            </div>
          </div>
          <div style={{display:"flex",alignItems:"flex-end",gap:12,marginBottom:16}}>
            <div style={{flex:1}}>
              <label className="form-label">From Station</label>
              <select required value={form.src} onChange={e=>setForm({...form,src:e.target.value})} style={{padding: "14px"}}>
                <option value="">Select city</option>
                {CITIES.map(c=><option key={c}>{c}</option>)}
              </select>
            </div>
            <button type="button" className="swap-btn" onClick={()=>setForm({...form,src:form.dst,dst:form.src})} title="Swap" style={{marginBottom: 8}}>⇄</button>
            <div style={{flex:1}}>
              <label className="form-label">To Station</label>
              <select required value={form.dst} onChange={e=>setForm({...form,dst:e.target.value})} style={{padding: "14px"}}>
                <option value="">Select city</option>
                {CITIES.filter(c=>c!==form.src).map(c=><option key={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div className="grid2">
            <div className="form-group">
              <label className="form-label">Travel Date</label>
              <input type="date" required value={form.date} onChange={e=>setForm({...form,date:e.target.value})} min={new Date().toISOString().split("T")[0]} style={{padding: "14px"}}/>
            </div>
            <div className="form-group">
              <label className="form-label">Preferred Time (optional)</label>
              <input type="time" value={form.preferredTime} onChange={e=>setForm({...form,preferredTime:e.target.value})} style={{padding: "14px"}} placeholder="Any time"/>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Seat Class</label>
            <select value={form.cls} onChange={e=>setForm({...form,cls:e.target.value})} style={{padding: "14px"}}>
              {(CLASSES[form.mode]||[]).map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="mt-24">
            <button type="submit" className="premium-btn w100" disabled={loading}>
              {loading?<><span className="loader"/>&nbsp;Searching Trips…</>:"Search Available Trips →"}
            </button>
          </div>
        </form>
      </div>}

      {/* Step 2: Trip Selection */}
      {step===2&&<div className="fade-in">
        <div className="flex-between mb-16">
          <div>
            <h3>🚄 Available Trips</h3>
            <p className="text-muted" style={{fontSize:".85rem"}}>{form.src} → {form.dst} · {form.date} · {form.mode.toUpperCase()}</p>
          </div>
          <button className="btn btn-sm btn-outline" onClick={()=>setStep(1)}>← Change</button>
        </div>
        {tripMessage&&<div className="alert alert-warn mb-16">⚠️ {tripMessage}</div>}
        {trips.length===0?<div className="card text-center" style={{padding:"40px 20px"}}>
          <div style={{fontSize:"3rem",marginBottom:12}}>🚫</div>
          <h3>No Trips Available</h3>
          <p className="text-muted">Try a different date or route.</p>
        </div>:
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          {trips.map(trip=>(
            <div key={trip.trip_id} className="card glass" style={{padding:20,border:trip.recommended?"1px solid var(--cyan)":"1px solid var(--border)",opacity:trip.available_seats===0?0.5:1,position:"relative",overflow:"hidden"}}>
              {trip.recommended&&<div style={{position:"absolute",top:0,left:0,background:"var(--grad)",color:"#fff",fontSize:".65rem",fontWeight:800,padding:"3px 12px",borderBottomRightRadius:8,letterSpacing:1}}>⭐ RECOMMENDED</div>}
              {trip.is_peak&&<div style={{position:"absolute",top:0,right:0,background:"var(--grad2)",color:"#111",fontSize:".65rem",fontWeight:800,padding:"3px 12px",borderBottomLeftRadius:8}}>🔥 PEAK</div>}
              <div style={{display:"grid",gridTemplateColumns:"1fr auto 1fr auto",alignItems:"center",gap:8,marginTop:trip.recommended?16:0}}>
                <div>
                  <div style={{fontSize:"1.8rem",fontWeight:900,color:"var(--cyan)",fontFamily:"monospace"}}>{trip.departure_time}</div>
                  <div style={{fontSize:".75rem",color:"var(--muted)"}}>{trip.source}</div>
                </div>
                <div style={{textAlign:"center",padding:"0 10px"}}>
                  <div style={{fontSize:".7rem",color:"var(--muted)",marginBottom:4}}>{Math.floor(trip.duration_mins/60)}h {trip.duration_mins%60}m</div>
                  <div style={{height:2,background:"var(--border)",position:"relative"}}><div style={{position:"absolute",top:"50%",left:"50%",transform:"translate(-50%,-50%)",fontSize:".8rem"}}>{trip.mode==="train"?"🚆":trip.mode==="bus"?"🚌":"✈️"}</div></div>
                </div>
                <div>
                  <div style={{fontSize:"1.8rem",fontWeight:900,fontFamily:"monospace"}}>{trip.arrival_time}</div>
                  <div style={{fontSize:".75rem",color:"var(--muted)"}}>{trip.destination}</div>
                </div>
                <div style={{textAlign:"right"}}>
                  <div style={{fontSize:"1.4rem",fontWeight:800,color:"var(--gold)"}}>{fmtCur(trip.price)}</div>
                  <div style={{fontSize:".75rem",color:trip.available_seats>0?"var(--green)":"var(--red)",fontWeight:600}}>
                    {trip.available_seats>0?`${trip.available_seats} seats left`:"Full"}
                  </div>
                </div>
              </div>
              <button className="btn btn-primary w100" style={{marginTop:14,padding:"10px"}} disabled={trip.available_seats===0||loading} onClick={()=>goToSeats(trip)}>
                {trip.available_seats===0?"No Seats Available":loading?<><span className="loader"/>&nbsp;Loading…</>:"Select This Trip →"}
              </button>
            </div>
          ))}
        </div>}
      </div>}

      {/* Step 3: Seats */}
      {step===3&&<div className="card fade-in">
        <h3 className="mb-16">💺 Select Your Seat</h3>
        {selectedTrip&&<div className="alert alert-ok mb-16" style={{justifyContent:"space-between"}}>
          <span>🚄 {selectedTrip.departure_time} → {selectedTrip.arrival_time}</span>
          <span className="text-gold" style={{fontWeight:700}}>{fmtCur(selectedTrip.price)}</span>
        </div>}
        <p className="text-muted mb-16">Route: {form.src} → {form.dst} | {form.date}</p>
        <div style={{display:"flex", justifyContent:"center", gap: 15, marginBottom: 20}}>
          <div style={{display:"flex", alignItems:"center", gap: 6}}><div style={{width:16,height:16,background:"var(--bg3)",borderRadius:4}}></div> <span style={{fontSize:".8rem"}}>Available</span></div>
          <div style={{display:"flex", alignItems:"center", gap: 6}}><div style={{width:16,height:16,background:"var(--cyan)",borderRadius:4}}></div> <span style={{fontSize:".8rem"}}>Selected</span></div>
          <div style={{display:"flex", alignItems:"center", gap: 6}}><div style={{width:16,height:16,background:"var(--red)",opacity:0.5,borderRadius:4}}></div> <span style={{fontSize:".8rem"}}>Booked</span></div>
        </div>
        <SeatMap mode={form.mode} selectedSeat={selectedSeat} setSelectedSeat={setSelectedSeat} bookedSeats={bookedSeats} />
        {selectedSeat && <div className="alert alert-ok mt-16" style={{justifyContent:"center"}}>Seat {selectedSeat} Selected</div>}
        <button type="button" onClick={goToPayment} className="premium-btn w100 mt-24" disabled={loading||!selectedSeat}>
          {loading?<><span className="loader"/>&nbsp;Analyzing Profile…</>:"Confirm Details & Pay →"}
        </button>
      </div>}

      {/* Step 4: Payment */}
      {step===4&&<div className="card fade-in">
        <h3 className="mb-16">💳 Demo Payment</h3>
        <div className="card" style={{background:"linear-gradient(135deg,#1a1a5a,#2a1a4a)",marginBottom:20,padding:20}}>
          <div className="flex-between" style={{marginBottom:16}}>
            <span className="text-cyan" style={{fontWeight:700}}>SecureTrail VISA</span>
            <span style={{fontSize:"1.5rem"}}>💳</span>
          </div>
          <div style={{letterSpacing:4,fontFamily:"monospace",fontSize:"1.2rem",marginBottom:12}}>4532 •••• •••• 1234</div>
          <div className="flex-between">
            <span className="text-muted" style={{fontSize:".8rem"}}>RAHUL SHARMA</span>
            <span className="text-muted" style={{fontSize:".8rem"}}>12/28</span>
          </div>
        </div>
        <div className="card" style={{marginBottom:20,padding:16}}>
          <div className="flex-between mb-8"><span className="text-muted">Base Fare</span><span>{fmtCur(Math.round(price/1.05))}</span></div>
          <div className="flex-between mb-8"><span className="text-muted">GST (5%)</span><span>{fmtCur(Math.round(price-price/1.05))}</span></div>
          {selectedTrip&&<div className="flex-between mb-8"><span className="text-muted">Departure</span><span className="text-cyan">{selectedTrip.departure_time} → {selectedTrip.arrival_time}</span></div>}
          <div className="flex-between mb-8"><span className="text-muted">Distance</span><span>{getDist(form.src,form.dst)} km</span></div>
          <div style={{borderTop:"1px solid var(--border)",paddingTop:8}} className="flex-between">
            <strong>Total Amount</strong><strong className="text-cyan" style={{fontSize:"1.3rem"}}>{fmtCur(price)}</strong>
          </div>
        </div>
        <form onSubmit={goToOtp}>
          <div className="form-group">
            <label className="form-label">Card Number (Demo)</label>
            <input placeholder="4532 1234 5678 9012" defaultValue="4532 1234 5678 9012"/>
          </div>
          <div className="grid2">
            <div className="form-group"><label className="form-label">Expiry</label><input placeholder="MM/YY" defaultValue="12/28"/></div>
            <div className="form-group"><label className="form-label">CVV</label><input type="password" placeholder="•••" defaultValue="123"/></div>
          </div>
          <button type="submit" className="btn btn-gold w100" style={{fontSize:"1rem",padding:"14px"}} disabled={loading}>
            {loading?<><span className="loader"/>&nbsp;Processing…</>:`💳 Pay ${fmtCur(price)} →`}
          </button>
        </form>
      </div>}

      {/* Step 5: OTP */}
      {step===5&&<div className="card fade-in text-center">
        <div style={{fontSize:"3rem",marginBottom:8}}>📱</div>
        <h3>OTP Verification</h3>
        <p className="text-muted mt-8 mb-16" style={{fontSize:".9rem"}}>Your one-time password (demo — shown below)</p>
        {serverOtp&&<div className="alert alert-warn" style={{justifyContent:"center"}}>
          🔐 Your OTP: <strong style={{fontSize:"1.5rem",letterSpacing:6,fontFamily:"monospace"}}>{serverOtp}</strong>
        </div>}
        <form onSubmit={verifyOtp}>
          <div className="otp-inputs" style={{marginBottom:20}}>
            {[0,1,2,3,4,5].map(i=>(
              <input key={i} className="otp-box" maxLength={1} value={otp[i]||""} onChange={e=>{const v=e.target.value;if(!/\d/.test(v)&&v!=="")return;const a=otp.split("");a[i]=v;setOtp(a.join(""));if(v&&i<5)document.getElementById(`otp${i+1}`)?.focus();}} id={`otp${i}`} onKeyDown={e=>{if(e.key==="Backspace"&&!otp[i]&&i>0)document.getElementById(`otp${i-1}`)?.focus();}}/>
            ))}
          </div>
          <p className="text-muted mb-16" style={{fontSize:".85rem"}}>{otpTimer>0?`⏱️ Resend in ${otpTimer}s`:"OTP expired"}</p>
          <button type="submit" className="btn btn-primary w100" disabled={loading||otp.length<6}>
            {loading?<><span className="loader"/>&nbsp;Verifying…</>:"✅ Verify & Confirm"}
          </button>
        </form>
      </div>}

      {/* Step 5: Ticket */}
      {/* Step 6: Ticket */}
      {step===6&&ticket&&<TicketDisplay ticket={ticket} setPage={setPage} qrPayload={qrPayload}/>}
    </div>
  );
}

function TicketDisplay({ticket,setPage,qrPayload}){
  const qrRef=React.useRef(null);
  React.useEffect(()=>{
    if(qrRef.current&&typeof QRCode!=="undefined"){
      qrRef.current.innerHTML="";
      try {
        const payloadStr = qrPayload ? JSON.stringify(qrPayload) : ticket.qr_data || ticket.pnr;
        new QRCode(qrRef.current,{text:payloadStr,width:160,height:160,colorDark:"#00d4ff",colorLight:"#0d0d2b"});
      } catch (e) {
        console.error("QR Error:", e);
      }
    }
  },[ticket, qrPayload]);

  return(
    <div className="fade-in">
      <div className="alert alert-ok mb-16" style={{background: "rgba(0,255,136,0.1)", border: "1px solid rgba(0,255,136,0.3)"}}>
        <div style={{display:"flex", alignItems:"center", gap: 10}}>
          <span style={{fontSize:"1.5rem"}}>✅</span>
          <div>
            <div style={{fontWeight:"bold", color:"var(--green)"}}>Booking Confirmed!</div>
            <div style={{fontSize:".85rem", opacity:0.8}}>Your ticket and seat have been securely locked.</div>
          </div>
        </div>
      </div>
      
      <div id={`ticket-${ticket.pnr}`} className="ticket-card" style={{
        background: "linear-gradient(145deg, rgba(30,30,50,0.9), rgba(15,15,25,0.95))",
        border: "1px solid rgba(0, 212, 255, 0.3)",
        boxShadow: "0 10px 40px rgba(0, 212, 255, 0.15), inset 0 1px 0 rgba(255,255,255,0.1)",
        position: "relative",
        overflow: "hidden"
      }}>
        {/* Glow effect */}
        <div style={{position:"absolute", top:-50, left:-50, width:150, height:150, background:"var(--cyan)", filter:"blur(80px)", opacity:0.2, borderRadius:"50%"}}></div>
        
        <div className="flex-between mb-24" style={{borderBottom: "1px dashed rgba(255,255,255,0.1)", paddingBottom: 20}}>
          <div>
            <div className="text-muted" style={{fontSize:".75rem", letterSpacing:1.5}}>SECURE E-TICKET</div>
            <div className="pnr" style={{fontSize:"1.8rem", color:"#fff", textShadow:"0 0 10px rgba(255,255,255,0.3)"}}>{ticket.pnr}</div>
          </div>
          <div className="text-center" style={{padding: "10px", background: "rgba(0,0,0,0.5)", borderRadius: 12, border: "1px solid rgba(0,212,255,0.2)"}}>
            <div ref={qrRef} style={{mixBlendMode:"screen"}}/>
            <div style={{fontSize:".65rem", marginTop:6, color:"var(--cyan)", letterSpacing:1}}>HMAC SIGNED</div>
          </div>
        </div>
        
        <div className="grid2" style={{marginBottom:24, gap: "20px 15px"}}>
          <div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>PASSENGER</div><strong style={{fontSize:"1.1rem"}}>{ticket.passenger_name}</strong></div>
          <div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>SEAT</div><strong style={{fontSize:"1.2rem", color:"var(--cyan)"}}>{ticket.seat_number||"TBD"}</strong></div>
          
          <div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>FROM</div><strong style={{fontSize:"1rem"}}>{ticket.source}</strong></div>
          <div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>TO</div><strong style={{fontSize:"1rem"}}>{ticket.destination}</strong></div>
          
          <div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>DATE</div><strong>{ticket.travel_date}</strong></div>
          <div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>MODE & CLASS</div><strong>{ticket.mode==="train"?"🚆":ticket.mode==="bus"?"🚌":"✈️"} {ticket.mode.toUpperCase()} - {ticket.seat_class}</strong></div>
          
          {ticket.departure_time&&<div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>DEPARTURE</div><strong style={{color:"var(--cyan)",fontFamily:"monospace",fontSize:"1.1rem"}}>{ticket.departure_time}</strong></div>}
          {ticket.arrival_time&&<div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>ARRIVAL</div><strong style={{fontFamily:"monospace",fontSize:"1.1rem"}}>{ticket.arrival_time}</strong></div>}
          
          <div><div className="text-muted" style={{fontSize:".7rem", marginBottom:4}}>FARE</div><strong className="text-gold" style={{fontSize:"1.2rem"}}>{fmtCur(ticket.price)}</strong></div>
        </div>
        
        <div className="flex-between" style={{background:"rgba(0,0,0,0.3)", padding:"12px 16px", borderRadius:8, margin:"-5px"}}>
          <span className={`badge badge-${ticket.risk_level==="HIGH"?"high":ticket.risk_level==="MEDIUM"?"med":"low"}`}>🛡️ {ticket.risk_level} RISK SCORE</span>
          <span className="badge badge-ok" style={{background:"rgba(0,255,136,.15)",color:"var(--green)"}}>✅ SECURE VALIDATION</span>
        </div>
      </div>
      <div className="flex mt-16" style={{gap:12}}>
        <button className="btn btn-primary" style={{flex:1}} onClick={()=>{
          const el = document.getElementById(`ticket-${ticket.pnr}`);
          if(el && typeof html2canvas !== "undefined"){
            html2canvas(el, {backgroundColor: '#07071a', scale: 2}).then(canvas => {
              const url = canvas.toDataURL("image/png");
              const a=document.createElement("a");a.href=url;a.download=`SecureTicket_${ticket.pnr}.png`;a.click();
            });
          } else {
            // Fallback to text
            const txt=`SECURE E-TICKET\nPNR: ${ticket.pnr}\nPassenger: ${ticket.passenger_name}\nFrom: ${ticket.source}\nTo: ${ticket.destination}\nDate: ${ticket.travel_date}\nMode: ${ticket.mode} - ${ticket.seat_class}\nSeat: ${ticket.seat_number||"TBD"}\nFare: ${ticket.price}`;
            const blob=new Blob([txt],{type:"text/plain"});
            const url=URL.createObjectURL(blob);
            const a=document.createElement("a");a.href=url;a.download=`Ticket_${ticket.pnr}.txt`;a.click();
          }
        }}>📥 Download Ticket (Image)</button>
        <button className="btn btn-primary" style={{flex:1}} onClick={()=>setPage("tickets")}>📋 View All Tickets</button>
        <button className="btn btn-outline" style={{flex:1}} onClick={()=>setPage("home")}>🏠 Home</button>
      </div>
    </div>
  );
}

function MyTicketsPage({user,setPage}){
  const [tickets,setTickets]=React.useState([]);
  const [loading,setLoading]=React.useState(true);
  const [verifying,setVerifying]=React.useState(false);

  React.useEffect(()=>{
    getUserTickets(user.uid).then(snap=>{
      let tks = snap.docs.map(d=>({id:d.id,...d.data()})).filter(t=>!t.user_hidden);
      
      // Auto-expire logic: if travel date has passed, mark as USED
      const now = new Date();
      now.setHours(0,0,0,0);
      tks.forEach(t => {
        if (t.status === "NOT_USED" && t.travel_date) {
          const tdate = new Date(t.travel_date);
          if (tdate < now) {
            markTicketUsed(t.id);
            t.status = "USED";
            t.used_at = {toDate: () => now}; // mock firestore timestamp for UI
          }
        }
      });

      tks.sort((a,b)=>(b.booking_time?.seconds||0)-(a.booking_time?.seconds||0));
      setTickets(tks);
      setLoading(false);
    }).catch(()=>setLoading(false));
  },[]);

  async function handleCancel(t){
    const reason=prompt("Please enter the reason for cancellation:");
    if(!reason)return;
    setVerifying(true);
    try{
      await requestTicketCancellation(t.id,reason);
      setTickets(tickets.map(x=>x.id===t.id?{...x,status:"CANCEL_PENDING"}:x));
      alert("Cancellation requested. Admin will verify and initiate refund.");
    }catch(e){alert("Failed to cancel ticket: "+e.message);}
    setVerifying(false);
  }

  async function handleDeleteHistory(t){
    if(!confirm("Remove this ticket from your history?"))return;
    setVerifying(true);
    try{
      await hideTicketHistory(t.id);
      setTickets(tickets.filter(x=>x.id!==t.id));
    }catch(e){alert("Failed to delete history: "+e.message);}
    setVerifying(false);
  }

  if(loading)return<div className="page text-center mt-24"><span className="loader"/></div>;

  return(
    <div className="page fade-in">
      <div className="page-title-section">
        <h1 className="glow-text" style={{fontSize: "2.8rem", marginBottom: 8}}>🎫 My Digital Vault</h1>
        <p className="text-muted">Access your AI-secured tickets</p>
      </div>
      {tickets.length===0?<div className="card text-center" style={{padding:"60px 20px"}}>
        <img src="digital_ticket_glow.png" style={{width:200,height:200,objectFit:"contain",marginBottom:20,opacity:0.8}} alt="No Tickets"/>
        <h3>No Tickets Found</h3>
        <p className="text-muted mb-24">You haven't booked any journeys yet. Start your safe travel today!</p>
        <button className="btn btn-primary" onClick={()=>setPage("booking")}>Book Your First Ticket</button>
      </div>:
      <div className="grid2" style={{gap: 20}}>
        {tickets.map(t=>(
          <div key={t.id} className="ticket-card glass" style={{padding: 24, transition: "0.3s", cursor: "pointer"}}>
            <div className="flex-between mb-12">
              <div className="pnr" style={{fontSize:"1.4rem", letterSpacing: 2}}>{t.pnr}</div>
              <div className="flex" style={{gap:8}}>
                <span className={`badge badge-${t.risk_level==="HIGH"?"high":t.risk_level==="MEDIUM"?"med":"low"}`} style={{fontSize: ".7rem"}}>🛡️ {t.risk_level}</span>
                <span className={`badge ${t.status==="USED"?"badge-high":t.status==="CANCELLED"?"badge-high":t.status==="CANCEL_PENDING"?"badge-med":"badge-low"}`} style={{fontSize: ".7rem"}}>
                  {t.status==="USED"?"🔴 USED":t.status==="CANCELLED"?"❌ CANCELLED":t.status==="CANCEL_PENDING"?"⏳ PENDING REFUND":"🟢 ACTIVE"}
                </span>
              </div>
            </div>
            <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 16}}>
              <div><span className="text-muted" style={{fontSize:".7rem", display: "block", marginBottom: 2}}>ROUTE</span><span style={{fontWeight: 600, fontSize: ".9rem"}}>{t.source} → {t.destination}</span></div>
              <div><span className="text-muted" style={{fontSize:".7rem", display: "block", marginBottom: 2}}>MODE</span><span style={{fontWeight: 600, fontSize: ".9rem"}}>{t.mode==="train"?"🚆":t.mode==="bus"?"🚌":"✈️"} {t.mode.toUpperCase()}</span></div>
              <div><span className="text-muted" style={{fontSize:".7rem", display: "block", marginBottom: 2}}>TRAVEL DATE</span><span style={{fontWeight: 600, fontSize: ".9rem"}}>{t.travel_date}</span></div>
              <div><span className="text-muted" style={{fontSize:".7rem", display: "block", marginBottom: 2}}>TOTAL FARE</span><strong className="text-gold" style={{fontSize: "1.1rem"}}>{fmtCur(t.price)}</strong></div>
            </div>
            {(t.status!=="CANCELLED"&&t.status!=="CANCEL_PENDING"&&t.status!=="USED")&&<div className="mt-12" style={{textAlign:"right"}}>
              <button className="btn btn-sm btn-outline" onClick={(e)=>{e.stopPropagation();handleCancel(t);}} style={{color:"var(--red)",borderColor:"var(--red)"}}>Cancel Ticket</button>
            </div>}
            {(t.status==="USED"||t.status==="CANCELLED")&&<div className="mt-12" style={{textAlign:"right"}}>
              <button className="btn btn-sm btn-outline" onClick={(e)=>{e.stopPropagation();handleDeleteHistory(t);}} style={{color:"var(--muted)",borderColor:"var(--border)"}}>🗑️ Delete from History</button>
            </div>}
            {t.status==="USED"&&<div className="mt-12 text-muted" style={{fontSize:".8rem", textAlign:"right"}}>
              Scanned on: <strong>{fmtDate(t.used_at)}</strong>
            </div>}
          </div>
        ))}
      </div>}
    </div>
  );
}

function SeatMap({mode, selectedSeat, setSelectedSeat, bookedSeats}) {
  let seats = [];
  if (mode === "train") {
    for(let r=1; r<=6; r++) {
      ['A','B','C','D'].forEach(c => seats.push(`${r}${c}`));
    }
  } else if (mode === "bus") {
    for(let r=1; r<=8; r++) {
      ['1','2','3','4'].forEach(c => seats.push(`S${r}-${c}`));
    }
  } else if (mode === "flight") {
    for(let r=1; r<=8; r++) {
      ['A','B','C','D','E','F'].forEach(c => seats.push(`${r}${c}`));
    }
  }

  return (
    <div className="seat-map" style={{display:"grid", gridTemplateColumns: mode==="flight"?"repeat(6, 1fr)":mode==="train"?"repeat(4,1fr)":"repeat(4,1fr)", gap: 10, maxWidth: 400, margin: "0 auto", padding: 20, background: "rgba(0,0,0,0.2)", borderRadius: 12}}>
      {seats.map(s => {
        const isBooked = bookedSeats.includes(s);
        const isSelected = selectedSeat === s;
        let bg = "var(--bg3)";
        if (isBooked) bg = "var(--red)";
        else if (isSelected) bg = "var(--cyan)";
        
        return (
          <div key={s} onClick={() => !isBooked && setSelectedSeat(s)} 
               style={{background: bg, padding: "10px 5px", textAlign:"center", borderRadius: 6, cursor: isBooked?"not-allowed":"pointer", opacity: isBooked?0.5:1, color: isSelected?"#000":"#fff", fontWeight: "bold", border: isSelected?"2px solid #fff":"1px solid rgba(255,255,255,0.1)", transition: "0.2s"}}>
            {s}
          </div>
        );
      })}
    </div>
  );
}
