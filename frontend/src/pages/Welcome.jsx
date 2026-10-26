import React from 'react';
import {ArrowRight, Compass, Sparkles, Globe2, RefreshCw} from 'lucide-react';
import {studentExperience} from '../studentExperience';
import {welcomeHero} from '../welcomeHero';
import {welcomeMode} from '../welcomeMode';
import {Button} from '../components/Shared';
import StudentTrail from '../components/StudentTrail';
import ExplorerSetup from '../components/ExplorerSetup';
import './welcome.css';

export default function Welcome({state, createdProfileId='', loading=false, error='', onRetry, onNavigate, onCreate, busy=false, questTotal=3, experience=null, explorers=[], onExplorerChoice}) {
  if (loading) return <section className="welcome-page welcome-state" role="status"><Compass size={42} aria-hidden="true"/><h1>Welcome to CareerQuest AI.</h1><p>Getting your adventure ready…</p></section>;
  if (error) return <section className="welcome-page welcome-state"><div role="alert"><h1>Let’s get you started.</h1><p>{error}</p></div><Button onClick={onRetry}><RefreshCw size={19} aria-hidden="true"/>Try again</Button></section>;
  const mode = welcomeMode(state,createdProfileId,explorers);
  const progress = experience || studentExperience(state,null,questTotal);
  const journey = progress.journey;
  const hero = welcomeHero(state,questTotal,progress);
  const savedNickname = state?.profile?.alias?.trim() || 'explorer';
  if(mode==='setup'||mode==='choose')return <div className={`welcome-page onboarding-welcome onboarding-${mode}`}><div className="onboarding-grid"><section className="onboarding-introduction" aria-labelledby="welcome-title"><span className="welcome-eyebrow">WELCOME TO CAREERQUEST AI</span><h1 id="welcome-title">Your next chapter starts with curiosity.</h1><p>Play three discovery quests, explore career possibilities, and create a personal map of what interests you. You don’t need to have your future figured out.</p><div className="onboarding-art" aria-hidden="true"><span className="onboarding-orbit"/><Compass size={94} strokeWidth={1.3}/><span className="onboarding-spark">✦</span></div><ol className="onboarding-preview" aria-label="What your adventure includes"><li>Discover your interests</li><li>Explore careers</li><li>Create your portfolio</li></ol><p className="onboarding-local">For Grades 9–12 · Demo profiles using test data</p></section>{mode==='setup'?<ExplorerSetup onCreate={onCreate} busy={busy}/>:<section className="explorer-setup-card returning-choice"><span className="welcome-eyebrow">PICK UP WHERE YOU LEFT OFF</span><h2>Your adventure is waiting.</h2><p>This browser remembers saved demo explorers. Choose whose journey to continue, or start a new one.</p><Button onClick={()=>onExplorerChoice('saved')} busy={busy}>Continue My Adventure<ArrowRight size={20} aria-hidden="true"/></Button><Button className="secondary" onClick={()=>onExplorerChoice('create')} busy={busy}>Create a New Explorer</Button><p className="setup-local-note">These are local demo profiles, not authenticated student accounts.</p></section>}</div></div>;
  const title = mode==='aboard'?`Welcome aboard, ${savedNickname}!`:hero.title;
  const message = mode==='aboard'?'Your first quest is ready. There are no right or wrong answers.':hero.message;
  return <div className={`welcome-page welcome-mode-${mode}`}>
    <section className="welcome-intro" aria-labelledby="welcome-title">
      <div className="welcome-copy"><span className="welcome-eyebrow">{mode==='aboard'?'YOUR ADVENTURE STARTS HERE':'YOUR ADVENTURE HOME'}</span><h1 id="welcome-title">{title}</h1><p className="welcome-instruction">{message}</p>
        {(hero.grade!==null||hero.points!==null)&&<ul className="welcome-saved-facts" aria-label="Your saved explorer details">{hero.grade!==null&&<li>Grade {hero.grade}</li>}{hero.points!==null&&<li><Sparkles size={19} aria-hidden="true"/>{hero.points} Explorer Points earned</li>}</ul>}
        <p className="welcome-reassurance">For curious minds in Grades 9–12. You can change direction as you grow.</p></div>
      <div className="welcome-illustration" aria-hidden="true"><div className="welcome-orbit orbit-outer"/><div className="welcome-orbit orbit-inner"/><span className="welcome-compass"><Compass size={110} strokeWidth={1.2}/></span><span className="welcome-sticker sticker-discover"><Sparkles size={25}/>A spark of curiosity</span><span className="welcome-sticker sticker-explore"><Globe2 size={25}/>A world to explore</span><span className="welcome-art-star">✦</span><span className="welcome-art-dot"/></div>
    </section>
    {mode==='aboard'&&<section className="welcome-first-mission" aria-labelledby="first-mission-title"><span className="first-mission-icon" aria-hidden="true"><Sparkles size={38}/></span><div><span className="welcome-eyebrow">FIRST MISSION</span><h2 id="first-mission-title">Discover Your Spark</h2><p>What would you choose on a free afternoon? Collect your first clue in Quest 1.</p><p className="first-mission-note">Creating an explorer earns no points. Your discoveries earn Explorer Points as you go.</p><Button onClick={()=>onNavigate('quests')} busy={busy}>Start My First Quest<ArrowRight size={20} aria-hidden="true"/></Button></div></section>}
    {mode==='returning'&&<StudentTrail journey={journey} onNavigate={onNavigate} busy={busy}/>}
    <p className="welcome-demo-note">A alias-only educational demo. Career guidance uses curated offline sources and makes no admissions predictions.</p>
  </div>;
}
