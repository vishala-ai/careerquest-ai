import React,{useId,useState} from 'react';
import {ArrowRight} from 'lucide-react';
import {Button} from './Shared';
import {setupProblems} from '../explorerSetup';
import './explorer-setup.css';
const AVATARS=[['🧭','Compass'],['🚀','Rocket'],['🌱','Seedling'],['🎨','Palette'],['🔬','Microscope'],['🪐','Planet']];
export default function ExplorerSetup({onCreate,busy=false}) {
 const id=useId(),[nickname,setNickname]=useState(''),[grade,setGrade]=useState(''),[avatar,setAvatar]=useState('🧭'),[fictional,setFictional]=useState(false),[touched,setTouched]=useState(false);
 const values={nickname,grade,avatar,fictional},issues=setupProblems(values);
 const submit=event=>{event.preventDefault();setTouched(true);if(!issues.length&&!busy)onCreate(values);};
 return <section className="explorer-setup-card" aria-labelledby={`${id}-title`}><span className="welcome-eyebrow">YOUR STARTING POINT</span><h2 id={`${id}-title`}>Create your explorer</h2><p>A nickname, an avatar, and a little curiosity.</p><form className="explorer-setup-form" onSubmit={submit}><fieldset disabled={busy}><legend className="sr-only">Explorer setup</legend>
 <fieldset className="setup-avatars"><legend>Choose an avatar</legend><div>{AVATARS.map(([icon,label])=><label key={icon} className={avatar===icon?'setup-avatar selected':'setup-avatar'}><input type="radio" name={`${id}-avatar`} value={icon} checked={avatar===icon} onChange={()=>setAvatar(icon)}/><span aria-hidden="true">{icon}</span><span>{label}</span></label>)}</div></fieldset>
 <label htmlFor={`${id}-name`}>Explorer nickname</label><input id={`${id}-name`} value={nickname} onChange={e=>setNickname(e.target.value)} onBlur={()=>setTouched(true)} placeholder="e.g. Nova Explorer" minLength={2} maxLength={40} required autoComplete="off" aria-invalid={touched&&nickname.trim().length<2?true:undefined} aria-describedby={`${id}-name-help`}/><span className="setup-field-help" id={`${id}-name-help`}>{touched&&nickname.trim().length<2?'Enter at least two characters. ':''}Use a made-up name, never a real student’s name.</span>
 <label htmlFor={`${id}-grade`}>Grade</label><select id={`${id}-grade`} value={grade} onChange={e=>setGrade(e.target.value)} required><option value="" disabled>Choose your grade</option>{[9,10,11,12].map(value=><option key={value} value={value}>Grade {value}</option>)}</select>
 <label className="setup-ack"><input type="checkbox" checked={fictional} onChange={e=>setFictional(e.target.checked)} required/><span>This is a demo explorer. I won’t enter real student information.</span></label>
 <div id={`${id}-guidance`} className="setup-guidance" aria-live="polite">{issues.length?<><strong>Before you start:</strong><ul>{issues.map(issue=><li key={issue}>{issue}</li>)}</ul></>:<span>Ready for your first adventure. Creating an explorer earns no XP.</span>}</div>
 <Button type="submit" busy={busy} disabled={issues.length>0} aria-describedby={`${id}-guidance`} className="full">Create My Explorer<ArrowRight size={20} aria-hidden="true"/></Button>
 </fieldset></form></section>;
}
