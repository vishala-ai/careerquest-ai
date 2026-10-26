import React,{useRef} from 'react';
import {UserRound,ChevronDown} from 'lucide-react';

export default function StudentIdentity({state,avatar,onNavigate,onLogout,busy=false,needsReview=false}) {
 const menu=useRef(null),nickname=state?.profile?.alias?.trim()||'Explorer';
 const go=page=>{if(menu.current)menu.current.open=false;onNavigate(page);};
 if(!state)return <button className="global-create-explorer" disabled={busy} onClick={()=>go('welcome')}><UserRound size={20} aria-hidden="true"/>Explorer setup</button>;
 return <details className="identity-menu" ref={menu} onKeyDown={event=>{if(event.key==='Escape'){menu.current.open=false;menu.current.querySelector('summary')?.focus();}}}><summary aria-label={`Student profile: ${nickname}, Grade ${state.profile.grade}`}><span className="identity-avatar" aria-hidden="true">{avatar||<UserRound size={24}/>}</span><span className="identity-copy"><strong>{nickname}</strong><span>Grade {state.profile.grade}</span></span><ChevronDown size={16} aria-hidden="true"/></summary><div className="identity-actions"><p>Explorer · Educational demo</p>{needsReview&&<p className="identity-review">Profile Needs Review</p>}<button disabled={busy} onClick={()=>go('confirm')}>Explorer Profile</button><button disabled={busy} onClick={()=>onLogout?onLogout():go('profiles')}>{onLogout?'Sign Out / Switch Account':'Switch Explorer'}</button><details><summary>Earlier saved activities</summary><button onClick={()=>go('roadmap')} disabled={busy}>My Roadmap</button><button onClick={()=>go('journey')} disabled={busy}>My Journey</button></details></div></details>;
}
