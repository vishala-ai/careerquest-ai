import React, {useId} from 'react';
import {Sparkles, UserRound, Globe2, Map, BookOpen, Check, LockKeyhole, LockOpen, ArrowRight, Flag, Leaf, Compass} from 'lucide-react';
import {trailMilestones} from '../studentTrail';
import './student-trail.css';

const icons = {quests:Sparkles, confirm:UserRound, worlds:Globe2, celebrate:Flag, roadmap:Map, reflect:BookOpen};

export default function StudentTrail({journey, onNavigate, busy=false, setupFormId='welcome-explorer-setup', setupReady=false}) {
  const id = useId();
  const milestones = trailMilestones(journey);
  const route=milestones.length===4?'M125 86 C250 86 250 150 375 150 S500 86 625 86 S750 150 875 150':'M100 86 C200 86 200 150 300 150 S400 86 500 86 S600 150 700 150 S800 86 900 86';
  return <section className={`student-trail${journey.complete?' is-finished':''}`} aria-labelledby={`${id}-title`}>
    <div className="trail-heading"><div><span className="welcome-eyebrow">YOUR STUDENT JOURNEY</span><h2 id={`${id}-title`}>Your Adventure Trail</h2><p>Follow your curiosity, one small adventure at a time.</p></div><span className="trail-heading-art" aria-hidden="true"><Compass size={37}/><Sparkles size={22}/></span></div>
    <p className="trail-guidance">{milestones.map(stage=>stage.title).join(' → ')}. Completed and available stops are yours to revisit.</p>
    <div className="trail-landscape">
      <svg className="trail-route" viewBox="0 0 1000 260" preserveAspectRatio="none" aria-hidden="true" focusable="false"><defs><linearGradient id={`${id}-route`}><stop stopColor="#6D28D9"/><stop offset=".35" stopColor="#0F766E"/><stop offset=".68" stopColor="#1D4ED8"/><stop offset="1" stopColor="#065F46"/></linearGradient></defs><path className="trail-route-shadow" d={route}/><path stroke={`url(#${id}-route)`} d={route}/></svg>
      <svg className="trail-route-mobile" viewBox="0 0 100 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="M50 20C20 120 80 200 50 300S20 450 50 500S80 650 50 700S20 850 50 980"/></svg>
      <div className="trail-scenery" aria-hidden="true"><Leaf className="trail-leaf" size={66} strokeWidth={1}/><Sparkles className="trail-spark" size={31}/><Flag className="trail-flag" size={40} strokeWidth={1.3}/></div>
      <ol className="trail-stops" style={{'--trail-count':milestones.length}} aria-label={`${milestones.map(stage=>stage.title).join(', ')} adventure trail`}>{milestones.map((stage,index)=>{
        const Icon = icons[stage.id];
        const target=stage.target;
        const StatusIcon = stage.locked?LockKeyhole:stage.done?Check:stage.active?Sparkles:LockOpen;
        const descriptionId = `${id}-${stage.id}-description`;
        return <li key={stage.id} className={`trail-stop trail-${stage.id} ${stage.active?'is-recommended':''} ${stage.done?'is-completed':''} ${journey.complete&&stage.primary?'is-portfolio-saved':''} ${stage.locked?'is-locked':'is-actionable'}`}>
          <div className="trail-node-wrap"><button className="trail-node" disabled={stage.locked||busy} onClick={()=>onNavigate(target)} aria-label={`${stage.title}: ${stage.status}. ${stage.actionLabel}`} aria-describedby={descriptionId} aria-current={stage.active?'step':undefined}><svg className="trail-icon-doodles" viewBox="0 0 100 100" aria-hidden="true" focusable="false"><circle cx="16" cy="22" r="5"/><path d="m80 15 2 7 7 2-7 2-2 7-2-7-7-2 7-2Z M17 76h12m-6-6v12 M74 79q9-11 12-5"/></svg><Icon size={49} aria-hidden="true"/><span className="trail-node-badge" aria-hidden="true"><StatusIcon size={18}/></span></button></div>
          <div className="trail-details">{stage.active&&<span className="trail-next-label">Your Next Adventure</span>}<h3>{String(index+1).padStart(2,'0')} · {stage.title}</h3><span className="trail-status"><StatusIcon size={16} aria-hidden="true"/>{stage.status}</span>{stage.historicalPortfolio&&stage.active&&<span className="trail-history-label">Earlier portfolio saved</span>}<p id={descriptionId}>{journey.complete&&stage.id==='celebrate'?'Portfolio saved.':stage.description}{stage.prerequisite&&<span className="trail-prerequisite">{stage.prerequisite}</span>}</p>
            {stage.primary ? journey.action.requiresSetup?<button className="trail-primary" type="submit" form={setupFormId} disabled={busy||!setupReady}>Start My First Quest<ArrowRight size={18} aria-hidden="true"/></button>:<button className="trail-primary" disabled={stage.locked||busy} onClick={()=>onNavigate(target)}>{stage.actionLabel}<ArrowRight size={18} aria-hidden="true"/></button>:!stage.locked&&<button className="trail-revisit" disabled={busy} onClick={()=>onNavigate(target)}>{stage.actionLabel}<ArrowRight size={16} aria-hidden="true"/></button>}
          </div>
        </li>;
      })}</ol>
    </div>
  </section>;
}
