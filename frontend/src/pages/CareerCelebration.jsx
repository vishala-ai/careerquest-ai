import React from 'react';
import {Sparkles,Compass,CheckCircle2} from 'lucide-react';
import {Button} from '../components/Shared';

export function celebrationMessage(event) {
 const name=event.nickname?.trim()||'Explorer',career=event.career_name;
 const messages={
  first_research:{title:`Curiosity in action, ${name}!`,text:`You explored ${career}. Noticing what interests you is a useful step. You can keep exploring and change direction as you learn.`,action:'explore',label:'Explore Another Career'},
  first_shortlist:{title:`Way to go, ${name}!`,text:`You saved ${career}. Exploring something interesting is a great first step—and you can always change direction.`,action:'shortlist',label:'View My Shortlist'},
  second_shortlist:{title:`More than one spark, ${name}!`,text:`You saved ${career}, too. You can be curious about more than one possibility. There’s room to explore both.`,action:'paths',label:'Choose My Paths'},
  primary_path:{title:`A next step, chosen by you, ${name}!`,text:`You chose ${career} as your Primary Exploration Path. It’s a starting point for curiosity, not a permanent career decision. A second path is optional.`,action:'portfolio',label:'Review My Portfolio'},
  secondary_path:{title:`Keep your options open, ${name}!`,text:`You added ${career} as a Secondary Exploration Path. Exploring different interests can help you notice what you enjoy. You can update either path later.`,action:'portfolio',label:'Review My Portfolio'},
  portfolio_completed:{title:`Look how far your curiosity has taken you, ${name}!`,text:'Your Career Discovery Portfolio snapshot is complete. You gathered ideas and saved possibilities to explore. This is a starting point, and your next chapter can change as you grow.',action:'portfolio',label:'Review My Portfolio'},
 };
 return messages[event.kind]||null;
}

export default function CareerCelebration({event,onFinish,busy=false,error='',confirmed=true}) {
 const message=celebrationMessage(event);if(!message)return null;
 const final=event.kind==='portfolio_completed',Icon=final?Sparkles:event.kind==='first_research'?Compass:CheckCircle2;
 return <section className={`career-celebration${final?' is-portfolio-complete':''}`} aria-labelledby={`celebration-${event.id}`}>
  <span className="career-celebration-icon" aria-hidden="true"><Icon size={final?36:26}/></span><div role="status" aria-live="polite" aria-atomic="true"><h2 id={`celebration-${event.id}`}>{message.title}</h2><p>{message.text}</p></div>
  {error&&<p role="alert">{error}</p>}<div className="career-celebration-actions"><Button disabled={busy} onClick={()=>onFinish(confirmed?message.action:'profile')}>{confirmed?message.label:'Review My Explorer Profile'}</Button><Button className="secondary" disabled={busy} onClick={()=>onFinish(null)} aria-label="Dismiss celebration">Keep exploring</Button></div>
 </section>;
}
