import React,{useEffect,useRef} from 'react';
import {Compass,RefreshCw} from 'lucide-react';
import Navigation,{PRIMARY_PAGES} from './Navigation';
import XPBadge from './XPBadge';
import StudentIdentity from './StudentIdentity';
import {studentExperience,primaryDestination} from '../studentExperience';
export {PRIMARY_PAGES};

export default function AppShell({page,state,career,careerScreen='worlds',avatar,account,onLogout,onNavigate,children,busy=false}) {
 const experience=studentExperience(state,career),shell=useRef(null),header=useRef(null);
 useEffect(()=>{
  const measure=()=>shell.current?.style.setProperty('--header-offset',`${Math.ceil(header.current?.getBoundingClientRect().height||0)+16}px`);
  measure();
  if(typeof ResizeObserver!=='undefined'){const observer=new ResizeObserver(measure);observer.observe(header.current);return()=>observer.disconnect();}
  window.addEventListener('resize',measure);return()=>window.removeEventListener('resize',measure);
 },[]);
 const accent=page==='confirm'?'confirm':page==='quests'?'discover':['worlds','portfolio'].includes(page)?careerScreen==='worlds'?'explore':'celebrate':'home';
 return <div ref={shell} className={`app spec-shell global-ui accent-${accent}`}><a href="#main" className="skip-link">Skip to content</a><header ref={header} className="global-header"><div className="global-header-top"><button className="brand global-brand" onClick={()=>onNavigate('welcome')} aria-label="CareerQuest AI Home"><span className="brand-symbol"><Compass size={25} aria-hidden="true"/></span><span>CareerQuest <b>AI</b></span></button>{state&&<><XPBadge state={state}/><StudentIdentity state={state} avatar={avatar} onLogout={onLogout} onNavigate={onNavigate} busy={busy} needsReview={experience.needsReview}/></>}{!state&&account&&<div className="account-header"><span>{account.username}</span><button className="account-signout" disabled={busy} onClick={onLogout}>Sign Out</button></div>}</div>{state&&<Navigation current={primaryDestination(page,careerScreen)} onNavigate={onNavigate} busy={busy}/>} {experience.needsReview&&<button className="global-review-notice" onClick={()=>onNavigate('confirm')}><RefreshCw size={17} aria-hidden="true"/><span><strong>Profile Needs Review.</strong> Confirm your updated preferences before new personalized research.</span></button>}</header>{children}</div>;
}
