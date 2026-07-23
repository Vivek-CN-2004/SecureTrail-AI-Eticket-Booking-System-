/* App root + routing */

function App(){
  const [page,setPage]=React.useState("home");
  const [user,setUser]=React.useState(null);
  const [userData,setUserData]=React.useState(null);
  const [authReady,setAuthReady]=React.useState(false);
  const [shareToken,setShareToken]=React.useState(null);

  React.useEffect(()=>{
    const unsub=auth.onAuthStateChanged(async u=>{
      if(u){
        setUser(u);
        const snap=await db.collection("users").doc(u.uid).get();
        if(snap.exists){
          const d=snap.data();setUserData(d);
          // increment login count
          db.collection("users").doc(u.uid).update({login_count:firebase.firestore.FieldValue.increment(1)});
          if(d.role==="admin")setPage("admin");
          else if(d.role==="checker")setPage("checker");
        }
      }else{setUser(null);setUserData(null);}
      setAuthReady(true);
    });
    return()=>unsub();
  },[]);

  React.useEffect(()=>{
    const params=new URLSearchParams(window.location.search);
    const token=params.get("share");
    if(token){
      setShareToken(token);
      setPage("share-view");
    }
  },[]);

  function handleAuth(u,ud){setUser(u);setUserData(ud);setPage(ud?.role==="checker"?"checker":"home");}
  async function handleLogout(){await auth.signOut();setUser(null);setUserData(null);setPage("home");}

  if(!authReady)return(
    <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",flexDirection:"column",gap:16}}>
      <div style={{fontSize:"3rem"}}>🛡️</div>
      <div className="loader" style={{width:32,height:32}}/>
      <p className="text-muted">Loading SecureTrail…</p>
    </div>
  );

  return(
    <div>
      <Navbar page={page} setPage={setPage} user={user} userData={userData} onLogout={handleLogout}/>
      <main className="main">
        {page==="home"&&<HomePage setPage={setPage} user={user}/>}
        {page==="login"&&<div style={{display:"flex",justifyContent:"center",paddingTop:40}}><AuthPage mode="login" setPage={setPage} onAuth={handleAuth}/></div>}
        {page==="signup"&&<div style={{display:"flex",justifyContent:"center",paddingTop:40}}><AuthPage mode="signup" setPage={setPage} onAuth={handleAuth}/></div>}
        {page==="booking"&&(user?<BookingPage user={user} userData={userData} setPage={setPage}/>:<div style={{display:"flex",justifyContent:"center",paddingTop:40}}><AuthPage mode="login" setPage={setPage} onAuth={handleAuth}/></div>)}
        {page==="tickets"&&(user?<MyTicketsPage user={user} setPage={setPage}/>:<div style={{display:"flex",justifyContent:"center",paddingTop:40}}><AuthPage mode="login" setPage={setPage} onAuth={handleAuth}/></div>)}
        {page==="profile"&&(user?<ProfilePage user={user} userData={userData} onLogout={handleLogout}/>:<div style={{display:"flex",justifyContent:"center",paddingTop:40}}><AuthPage mode="login" setPage={setPage} onAuth={handleAuth}/></div>)}
        {page==="scanner"&&<ScannerPage user={user} userData={userData}/>}
        {page==="scanner-history"&&<ScannerPage user={user} userData={userData} initialTab="history"/>}
        {page==="admin"&&(userData?.role==="admin"?<AdminPage user={user}/>:<div className="page"><div className="alert alert-err">⛔ Admin access only.</div></div>)}
        {page==="checker"&&(userData?.role==="checker"||userData?.role==="admin"?<CheckerDashboard user={user}/>:<div className="page"><div className="alert alert-err">⛔ Checker access only.</div></div>)}
        {page==="share-view"&&<ShareViewPage token={shareToken} setPage={setPage}/>}
      </main>
    </div>
  );
}

const root=ReactDOM.createRoot(document.getElementById("root"));
root.render(<App/>);
