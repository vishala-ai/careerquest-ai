import React from 'react';
import {Compass,ShieldCheck,Sparkles,Palette,Leaf,Code2,HeartHandshake,FlaskConical,Wrench,BookOpen,Users,Lightbulb,Target,Pencil,ArrowRight} from 'lucide-react';
import {Button} from './Shared';
import {studentCorrection} from '../profilePresentation';

const interestArt={art:[Palette,'Try a visual idea and see where it takes you.'],biology:[Leaf,'Keep getting curious about living things.'],coding:[Code2,'Try turning an idea into a small program.'],technology:[Code2,'Explore tools and ideas you could build.'],science:[FlaskConical,'Follow a question and explore the evidence.'],helping:[HeartHandshake,'Explore small ways to support a community.'],building:[Wrench,'Make a simple prototype and try it out.'],research:[BookOpen,'Keep asking questions and comparing ideas.'],people:[Users,'Explore ideas with other curious people.'],nature:[Leaf,'Notice patterns in the world around you.'],creative:[Palette,'Try making something in your own way.'],design:[Lightbulb,'Explore different ways an idea could work.']};

export function ProfileRecordDetails({state}) {
 const saved=state.profile_draft||state.profile_preferences;
 const handoff=state.discovery_handoff?.active;
 return <details className="profile-record-details"><summary>Saved profile details</summary><dl><div><dt>Profile version</dt><dd>{state.profile_version}</dd></div><div><dt>Status</dt><dd>{state.confirmed?'Confirmed by you':'Awaiting your confirmation'}</dd></div>{handoff&&<><div><dt>Discovery handoff version</dt><dd>{handoff.version}</dd></div>{handoff.timestamp&&<div><dt>Saved</dt><dd><time dateTime={handoff.timestamp}>{new Date(handoff.timestamp).toLocaleString()}</time></dd></div>}</>}</dl>{saved?.correction&&<div className="profile-original-note"><h3>Original saved note</h3><p>{saved.correction}</p><p className="profile-support">Your original wording stays in your saved history.</p></div>}</details>;
}

export default function ExplorerProfileSummary({state,values,onEdit,onExplore,busy=false}) {
 const nickname=state.profile.alias?.trim()||'Explorer';
 return <section className="profile-curiosity-summary" aria-labelledby="confirmed-profile-title">
  <div className="profile-curiosity-hero"><div><span className="profile-confirmed-badge"><ShieldCheck size={19} aria-hidden="true"/>Confirmed by you</span><h2 id="confirmed-profile-title">{nickname}, your curiosity in focus</h2><p>A snapshot of what you’d like to explore. There’s room to grow and change.</p></div><div className="profile-compass-art" aria-hidden="true"><Compass size={76} strokeWidth={1.3}/><Sparkles size={25}/></div></div>
  <div className="profile-summary-body"><h3 className="profile-section-title">Interests I’m exploring</h3>
   {values.interests.length?<div className="profile-interest-grid">{values.interests.map(interest=>{const [Icon,caption]=interestArt[interest]||[Sparkles,'Try one small idea that follows this interest.'];return <article className="profile-interest-card" key={interest}><span className="profile-interest-icon"><Icon size={27} aria-hidden="true"/></span><h4>{interest.charAt(0).toUpperCase()+interest.slice(1)}</h4><p>{caption}</p></article>;})}</div>:<div className="profile-open-options"><Compass size={30} aria-hidden="true"/><div><h4>Still exploring</h4><p>You don’t need to choose a career or a fixed interest. Follow any curiosity when you’re ready.</p></div></div>}
   <div className="profile-preference-grid"><article><span><Lightbulb size={24} aria-hidden="true"/></span><div><h3>How I like to explore</h3><p>{values.learning_style}</p></div></article><article><span><Target size={24} aria-hidden="true"/></span><div><h3>My next exploration goal</h3><p>{values.goal}</p></div></article></div>
   {values.correction&&<section className="profile-student-note"><h3>Your voice shapes this</h3><p>{studentCorrection(values.correction)}</p></section>}
   <div className="profile-summary-actions"><Button className="secondary" busy={busy} onClick={onEdit}><Pencil size={18} aria-hidden="true"/>Edit Profile</Button><Button busy={busy} onClick={onExplore}>Explore Career Worlds<ArrowRight size={18} aria-hidden="true"/></Button></div><p className="profile-support">Changing direction is part of exploring. Edits open a new draft; your earlier profiles and roadmaps stay saved.</p>
  </div>
 </section>;
}
