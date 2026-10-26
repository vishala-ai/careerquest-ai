import React,{useEffect,useRef,useState} from 'react';
import {Compass,LockKeyhole,ArrowRight} from 'lucide-react';
import {api,setCsrfToken} from '../api';
import './auth.css';

export default function AuthGate({children}){
 const [session,setSession]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[mode,setMode]=useState('login'),[busy,setBusy]=useState(false);
 const [username,setUsername]=useState(''),[password,setPassword]=useState(''),[confirm,setConfirm]=useState(''),[ack,setAck]=useState(false),pending=useRef(false);
 const adopt=value=>{setCsrfToken(value.csrf_token);setSession(value.authenticated?value:null);};
 const load=async()=>{setLoading(true);setError('');try{adopt(await api('/auth/session'));}catch(err){setError(err.message);}finally{setLoading(false);}};
 useEffect(()=>{load();const expired=()=>{adopt({authenticated:false});setError('Your session ended. Sign in to continue your saved adventure.');};window.addEventListener('cq-session-expired',expired);return()=>window.removeEventListener('cq-session-expired',expired);},[]);
 const register=mode==='register';
 const valid=/^[a-zA-Z0-9][a-zA-Z0-9_-]{2,29}$/.test(username.trim())&&password.length>0&&(!register||(password.length>=15&&password===confirm&&ack));
 async function submit(event){
  event.preventDefault();if(pending.current||!valid)return;pending.current=true;setBusy(true);setError('');
  try{adopt(await api(`/auth/${register?'register':'login'}`,'POST',{username:username.trim(),password,...(register?{demo_ack:ack}:{})}));setPassword('');setConfirm('');}
  catch(err){setError(err.message);}finally{pending.current=false;setBusy(false);}
 }
 async function logout(){if(pending.current)return;pending.current=true;setBusy(true);try{await api('/auth/logout','POST',{});adopt({authenticated:false});setUsername('');setMode('login');setError('');}catch(err){if(err.status===401)adopt({authenticated:false});else setError(err.message);}finally{pending.current=false;setBusy(false);}}
 if(session)return <>{error&&<div className="auth-session-error" role="alert">{error}<button onClick={logout} disabled={busy}>Retry sign out</button></div>}{children(session.account,logout)}</>;
 return <div className="auth-page"><header><Compass size={30} aria-hidden="true"/><strong>CareerQuest <span>AI</span></strong></header><main id="main" className="auth-layout"><section className="auth-intro"><span className="welcome-eyebrow">YOUR ADVENTURE STARTS WITH CURIOSITY</span><h1>Your next chapter is yours to explore.</h1><p>Discover your interests, explore career possibilities and create a personal map. You don’t need your future figured out.</p><Compass className="auth-compass" size={138} strokeWidth={1.2} aria-hidden="true"/><p className="auth-demo-note">Educational demo · Grades 9–12<br/>Use aliases and test data only. Don’t enter real student information.</p></section><section className="auth-card" aria-labelledby="auth-title">
 {loading?<p role="status">Checking your saved session…</p>:<><LockKeyhole size={28} aria-hidden="true"/><h2 id="auth-title">{register?'Start your adventure':'Welcome back'}</h2><p>{register?'Create a login to keep your Explorer and discoveries together.':'Sign in to continue your saved adventure.'}</p>
 {error&&<p className="auth-error" role="alert">{error}</p>}
 <form onSubmit={submit}><fieldset disabled={busy}><legend className="sr-only">{register?'Create account':'Sign in'}</legend><label htmlFor="auth-username">Username</label><input id="auth-username" name="username" value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" required minLength={3} maxLength={30} aria-describedby="username-help"/><small id="username-help">3–30 letters, numbers, hyphens or underscores. Use an alias, not your real name.</small><label htmlFor="auth-password">Password</label><input id="auth-password" name="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete={register?'new-password':'current-password'} required maxLength={128} minLength={register?15:1} aria-describedby={register?'password-help':undefined}/>{register&&<><small id="password-help">Use a passphrase of 15–128 characters. Keep it somewhere safe.</small><label htmlFor="auth-confirm">Confirm password</label><input id="auth-confirm" type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} autoComplete="new-password" required maxLength={128}/>{confirm&&confirm!==password&&<span role="status">Passwords must match.</span>}<label className="auth-ack"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)} required/><span>I’ll use aliases and test data only. I won’t enter real student information.</span></label></>}
 <button className="auth-primary" type="submit" disabled={!valid||busy}>{busy?'Please wait…':register?'Create My Account':'Sign In'}<ArrowRight size={20} aria-hidden="true"/></button></fieldset></form>
 <button className="auth-switch" disabled={busy} onClick={()=>{setMode(register?'login':'register');setError('');setPassword('');setConfirm('');setAck(false);}}>{register?'Already have an account? Sign in':'New here? Create an account'}</button><button className="auth-retry" onClick={load} disabled={busy}>Retry connection</button><p className="auth-help">No email address is collected. If you forget your password, ask the demo host for a reset.</p></>}
 </section></main></div>;
}
