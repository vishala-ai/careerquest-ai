import React from 'react';
import {ArrowRight, ArrowUpRight, LockKeyhole, LoaderCircle, Check, Sparkles, Map, Compass, BookOpen} from 'lucide-react';
export function Button({children, busy = false, className = '', disabled, ...props}) {
  return <button className={`button ${className}`} disabled={busy || disabled} {...props}>{busy && <LoaderCircle className="spin" size={17}/>} {children}</button>;
}
export {default as PageHeading} from './PageHero';
export {default as NextAction} from './NextAction';
export function Gate({state, onNavigate}) {
  const page = !state ? 'profiles' : !state.quest_complete ? 'quests' : 'confirm';
  const title = !state ? 'First, meet your explorer.' : !state.quest_complete ? 'Find your spark first.' : 'Your profile. Your say.';
  const text = !state ? 'Create a demo profile to start your own exploration journey.' : !state.quest_complete ? 'Complete the three discovery quests, then review the clues in your profile.' : 'Review and confirm your interests before exploring your next steps.';
  return <div className="empty-state panel"><span className="empty-icon"><LockKeyhole size={30}/></span><h2>{title}</h2><p>{text}</p><Button onClick={() => onNavigate(page)}>{!state ? 'Create my explorer' : !state.quest_complete ? 'Start discovery' : 'Review my profile'}<ArrowRight size={17}/></Button></div>;
}
export function Sources({sources = []}) {
  return <div className="source-list">{sources.map(source => <div className="source-item" key={source.id}>{source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.source}<ArrowUpRight size={13}/></a> : <span>{source.source}</span>}<small>{source.title} · Not live verified</small></div>)}</div>;
}
const eventMeta = {
  quest_completed: {icon: Sparkles, title: 'A new clue discovered', color: 'lilac'},
  quest_revised: {icon: Sparkles, title: 'A discovery clue updated', color: 'lilac'},
  profile_drafted: {icon: Compass, title: 'Profile draft saved', color: 'green'},
  profile_confirmed: {icon: Compass, title: 'Your profile, confirmed', color: 'green'},
  reflection: {icon: BookOpen, title: 'A moment to reflect', color: 'peach'},
  roadmap_saved: {icon: Map, title: 'Next steps saved', color: 'blue'},
  interests_updated: {icon: Compass, title: 'A new direction', color: 'green'},
};
export function ActivityTimeline({events}) {
  if (!events.length) return <p className="muted">Your first discovery is just ahead. Start a quest to add to your story.</p>;
  return <ol className="activity-list">{[...events].reverse().map(event => {
    const meta = eventMeta[event.kind] || {icon: Check, title: 'Progress saved', color: 'green'};
    const Icon = meta.icon; const payload = event.payload;
    const text = ['quest_completed','quest_revised'].includes(event.kind) ? payload.choice : event.kind === 'reflection' ? payload.text.replace(/^Reflection:\s*/i, '') : event.kind === 'roadmap_saved' ? `Roadmap version ${payload.version}, ready to revisit.` : `Exploring ${(payload.interests || []).join(', ') || 'new possibilities'}.`;
    return <li key={event.id}><span className={`activity-icon ${meta.color}`}><Icon size={18}/></span><div><h3>{meta.title}</h3><p>{text}</p><time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString(undefined, {month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'})}</time></div></li>;
  })}</ol>;
}
