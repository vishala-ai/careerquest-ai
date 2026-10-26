import React,{useEffect,useState} from 'react';
import {api} from '../api';
import {Button} from './Shared';

export function ProposedExplorer({outcome,onEdit,busy=false}) {
 if(!outcome?.proposed_profile)return null;
 const values=outcome.proposed_profile;
 return <section className="discovery-profile-proposal" aria-labelledby="proposed-explorer-title">
  <h3 id="proposed-explorer-title">Your proposed Explorer Profile</h3>
  <p>{outcome.profile_origin==='quest_clues_to_review'?'These quest clues are suggestions you can edit.':'These are your saved interests and preferences.'} Your agreement with a story does not confirm this profile.</p>
  <dl className="profile-details"><div><dt>Interests to explore</dt><dd>{values.interests.length?values.interests.join(', '):'Still exploring — no career selection needed.'}</dd></div><div><dt>How I like to explore</dt><dd>{values.learning_style}</dd></div><div><dt>My next goal</dt><dd>{values.goal}</dd></div>{values.correction&&<div><dt>My correction</dt><dd>{values.correction}</dd></div>}</dl>
  <Button className="secondary" disabled={busy} onClick={onEdit}>Edit & Review My Explorer Profile</Button>
  <p className="small-note">You can keep your options open. Explicit confirmation is a separate step.</p>
 </section>;
}

export function WorldCards({worlds}) {
 return <div className="guide-worlds">{worlds.map(world=><article key={world.world_id} data-world-id={world.world_id}><h3>{world.title}</h3>{world.explanation&&<p>{world.explanation}</p>}{world.description&&<p>{world.description}</p>}{world.url?<a href={world.url} target="_blank" rel="noreferrer">{world.source} ↗</a>:<span>{world.source}</span>}<p className="small-note">Curated catalogue · Not live verified</p></article>)}</div>;
}

export default function ConfirmedCareerWorlds({state,onReview,initialCatalogue}) {
 const [worlds,setWorlds]=useState(initialCatalogue??null);
 const [error,setError]=useState('');
 const [retry,setRetry]=useState(0);
 useEffect(()=>{
  if(initialCatalogue)return;
  let active=true;setError('');
  api('/career-worlds').then(data=>{if(active)setWorlds(data);}).catch(err=>{if(active)setError(err.message);});
  return()=>{active=false;};
 },[retry,initialCatalogue]);
 const handoff=state?.confirmed?state.discovery_handoff?.active:null;
 return <section className="discovery-world-handoff">
  <section className="panel" aria-labelledby="confirmed-worlds-title"><span className="eyebrow">YOUR CHOICES LEAD THE WAY</span><h2 id="confirmed-worlds-title">Worlds from your confirmed profile</h2>
   {handoff?<><p>Saved with Explorer Profile version {handoff.profile_version}. {handoff.exploratory?'You are keeping your options open. No career choice is required.':'These catalogue connections follow the interests you explicitly confirmed.'}</p>
    {handoff.career_worlds.length?<WorldCards worlds={handoff.career_worlds}/>:<p>No personalized world is selected. Browse any world below, or add interests whenever you’re ready.</p>}
    <p className="small-note">Suggestions are catalogue connections, not career rankings or predictions.</p>
    <details><summary>Your saved Discovery handoff</summary><p>Handoff version {handoff.version} · Profile version {handoff.profile_version}</p><p>Confirmed interests: {handoff.selected_interests.join(', ')||'Still exploring'}.</p>{handoff.story&&<p>{handoff.story.summary}</p>}{handoff.next_mission&&<p>Optional next mission: {handoff.next_mission.text}</p>}<p><time dateTime={handoff.timestamp}>{new Date(handoff.timestamp).toLocaleString()}</time></p></details>
   </>:<><p>{state?.confirmed?'Review and explicitly confirm your saved profile to create its Discovery handoff.':'Personalized suggestions need your explicit profile confirmation. Earlier versions stay in history while you review changes.'}</p><Button className="secondary" onClick={onReview}>Review My Explorer Profile</Button></>}
  </section>
  <section className="panel" aria-labelledby="all-worlds-title"><h2 id="all-worlds-title">All Career Worlds</h2><p>Follow any curiosity. These worlds stay open, whether or not they match your profile.</p>
   {error?<div role="alert"><p>Couldn’t load the catalogue. {error}</p><Button className="secondary" onClick={()=>setRetry(retry+1)}>Retry catalogue</Button></div>:worlds===null?<p role="status">Loading Career Worlds…</p>:worlds.length?<WorldCards worlds={worlds}/>:<p role="status">The catalogue is unavailable right now. Your saved profile and history are safe.</p>}
  </section>
 </section>;
}
