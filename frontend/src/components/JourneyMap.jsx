import React from 'react';
import {UserRound, Sparkles, Compass, Globe2, Map, BookOpen, Check, LockKeyhole, ArrowUpRight} from 'lucide-react';
import {journeyStages} from '../journey';
const icons = {profile: UserRound, spark: Sparkles, compass: Compass, world: Globe2, map: Map, journal: BookOpen};
const positions = [[1, 1], [1, 2], [2, 2], [2, 1], [3, 1], [3, 2]];
export default function JourneyMap({state, onNavigate, preview = false}) {
  return <div className={`journey-map ${preview ? 'preview-map' : ''}`}>
    <svg className="route-line" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path d="M24 17 H76 Q96 17 96 33 Q96 50 76 50 H24 Q4 50 4 67 Q4 83 24 83 H76"/></svg>
    <ol className="route-stops" aria-label="Your exploration journey">{journeyStages(state).map((stage, index) => {const Icon = icons[stage.icon]; return <li key={stage.id} style={{gridRow: positions[index][0], gridColumn: positions[index][1]}}>
      <button className={`route-stop stop-${index} ${stage.done ? 'is-done' : ''} ${stage.current ? 'is-current' : ''}`} disabled={stage.locked || preview} onClick={() => onNavigate(stage.id)} aria-current={stage.current ? 'step' : undefined}>
        <span className="stop-top"><span className="stop-icon"><Icon size={24}/></span><span className="stop-status">{stage.done ? <><Check size={13}/> Complete</> : stage.locked ? <><LockKeyhole size={12}/> Up ahead</> : stage.current ? 'You are here' : `Stop 0${index + 1}`}</span></span>
        <span className="stop-number">0{index + 1}</span><h3>{stage.title}</h3><p>{stage.description}</p><span className="stop-link">{stage.done ? 'Revisit' : stage.locked ? (index === 2 ? 'Finish discovery first' : index > 2 ? 'Confirm your profile first' : 'Create an explorer first') : 'Let’s go'}{!stage.locked && <ArrowUpRight size={16}/>}</span>
      </button></li>;})}</ol>
  </div>;
}
