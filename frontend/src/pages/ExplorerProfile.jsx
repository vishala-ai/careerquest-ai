import React,{useEffect,useState} from 'react';
import {Check,Plus,Pencil} from 'lucide-react';
import {Button,PageHeading,Gate} from '../components/Shared';
import ProfileDiscoveryReview from '../components/ProfileDiscoveryReview';
import ExplorerProfileSummary,{ProfileRecordDetails} from '../components/ExplorerProfileSummary';
import {isReconfirmation} from '../profilePresentation';
import './explorer-profile.css';
import {profileForm} from '../journey';
const INTERESTS=['science','technology','art','helping','building','research','creative','people','biology','coding','design'];
const STYLES=['Hands-on projects','Research and reading','Creative activities','Team collaboration','Still figuring it out'];
const GOALS=['Explore careers and college majors','Try a mini-project','Explore high-school preparation','Not sure yet'];

export function InterestChipEditor({values,onChange,busy,onPending}) {
  const [custom,setCustom]=useState('');
  useEffect(()=>{onPending(Boolean(custom.trim()));return()=>onPending(false);},[custom,onPending]);
  const toggle=interest=>onChange(values.includes(interest)?values.filter(item=>item!==interest):[...values,interest]);
  const add=event=>{event.preventDefault();const value=custom.trim().toLowerCase();if(value&&!values.includes(value)&&values.length<12){onChange([...values,value]);setCustom('');}};
  return <div className="interest-editor"><div className="interest-picker">{[...new Set([...INTERESTS,...values])].map(interest=><button type="button" key={interest} aria-pressed={values.includes(interest)} className={values.includes(interest)?'selected':''} disabled={busy||(!values.includes(interest)&&values.length>=12)} onClick={()=>toggle(interest)}>{values.includes(interest)?<Check size={15}/>:<Plus size={15}/>} {interest}</button>)}</div><form className="add-interest" onSubmit={add}><label htmlFor="custom-interest" className="sr-only">Add an interest</label><input id="custom-interest" value={custom} onChange={event=>setCustom(event.target.value)} maxLength={40} placeholder="Add your own interest" disabled={busy}/><Button className="secondary" type="submit" disabled={busy||!custom.trim()||values.length>=12}>Add<Plus size={15}/></Button></form><small>{values.length}/12 interests selected. You can remove any suggestion.</small></div>;
}
export function ProfileSummary({state,quests}) {
 const answers=state.quest_answers||[];
 return <section className="panel profile-summary"><span className="eyebrow">WHAT YOU CHOSE</span><h2>Your actual quest choices</h2><p>These answers stay saved, even when your interests change.</p>{answers.map(answer=><div className="clue" key={answer.id}><span>0{answer.payload.quest+1}</span><div><small>{answer.payload.quest===2?'Your Working Style':quests[answer.payload.quest]?.title||'Discovery quest'}</small><strong>{answer.payload.choice}</strong><time dateTime={answer.created_at}>{new Date(answer.created_at).toLocaleDateString(undefined,{month:'short',day:'numeric'})}</time></div></div>)}</section>;
}
export function ProfileEditor({values,onChange,busy,onPending,suggestions}) {
 const update=patch=>onChange({...values,...patch});
 return <div className="profile-manual-editor"><h3>Interests to explore</h3><InterestChipEditor values={values.interests} busy={busy} onPending={onPending} onChange={interests=>update({interests,not_sure:false})}/><div className="profile-choice-actions"><button className="text-button" disabled={busy} onClick={()=>update({interests:suggestions,not_sure:false})}>Use quest suggestions</button><button className="text-button" disabled={busy} onClick={()=>update({interests:[]})}>Clear suggestions</button></div><label className="checkbox-label unsure-choice"><input type="checkbox" disabled={busy} checked={values.not_sure} onChange={e=>update({not_sure:e.target.checked,...(e.target.checked?{interests:[],goal:'Not sure yet',learning_style:'Still figuring it out'}:{})})}/>I’m not sure yet. I want to keep my options open.</label><label htmlFor="review-learning">Preferred activities</label><select id="review-learning" value={values.learning_style} disabled={busy} onChange={e=>update({learning_style:e.target.value})}>{[...new Set([...STYLES,values.learning_style])].map(value=><option key={value}>{value}</option>)}</select><label htmlFor="review-goal">Exploration goal</label><select id="review-goal" value={values.goal} disabled={busy} onChange={e=>update({goal:e.target.value})}>{[...new Set([...GOALS,values.goal])].map(value=><option key={value}>{value}</option>)}</select><label htmlFor="profile-correction">Anything we missed? <small>Optional correction</small></label><textarea id="profile-correction" value={values.correction} maxLength={500} disabled={busy} onChange={e=>update({correction:e.target.value})} rows={3} placeholder="For this demo explorer, I’d rather explore…"/><p className="small-note">Aliases and test data only. Changes stay unconfirmed until you review and explicitly confirm them.</p></div>;
}
export default function ExplorerProfile({state,quests,values,onChange,onConfirm,onSaveRevision,onGuideUpdated,onBeginEdit,onNavigate,busy,dirty,onPending}) {
 if(!state?.quest_complete)return <div className="spec-page"><PageHeading eyebrow="EXPLORER PROFILE" title="Your profile. Your say.">Complete your three quests, then review what you want to explore.</PageHeading><Gate state={state} onNavigate={onNavigate}/></div>;
 const nickname=state.profile.alias?.trim()||'Explorer';
 const suggestions=[...new Set(state.quest_answers.map(event=>event.payload.interest))];
 const reconfirmation=isReconfirmation(state);
 const title=state.confirmed?`${nickname}, your Explorer Profile`:reconfirmation?`Make it feel like you, ${nickname}`:`Does This Feel Like You, ${nickname}?`;
 return <div className="spec-page explorer-profile-page"><PageHeading eyebrow={state.confirmed?'MY EXPLORER PROFILE':reconfirmation?'EXPLORER PROFILE · UPDATE & REVIEW':'EXPLORER PROFILE · REVIEW & CONFIRM'} title={title}>{state.confirmed?'Your interests today. Open possibilities for tomorrow.':reconfirmation?'Your saved values are here. Make your updates, then review and confirm before new personalized research.':'Your choices are the starting point. You decide what to carry forward.'}</PageHeading>
  {!state.confirmed&&<div className="profile-review-status"><span className="profile-status draft">{reconfirmation?<><Pencil size={17} aria-hidden="true"/>Updating your profile</>:'Review required'}</span><p>Personalized research and new roadmaps wait for your explicit {reconfirmation?'reconfirmation':'confirmation'}.</p></div>}
  <div className="review-layout"><section className={`panel review-panel ${state.confirmed?'confirmed-summary-panel':''}`}>
   {state.confirmed?<ExplorerProfileSummary state={state} values={values} busy={busy} onEdit={onBeginEdit} onExplore={()=>onNavigate('worlds')}/>:<ProfileDiscoveryReview state={state} values={values} reconfirmation={reconfirmation} busy={busy} dirty={dirty} onConfirm={onConfirm} onUpdated={onGuideUpdated} onSaveRevision={onSaveRevision} onPrepareManual={patch=>onChange({...values,...patch})} onCancelEditing={()=>onChange(profileForm(state))} renderInterestEditor={(begin,correction)=><InterestChipEditor values={values.interests} busy={busy} onPending={onPending} onChange={interests=>{onChange({...values,interests,not_sure:false,...(correction.trim()?{correction}:{})});begin();}}/>} renderEditor={()=><ProfileEditor values={values} onChange={onChange} busy={busy} onPending={onPending} suggestions={suggestions}/>}/>}
  </section><aside><ProfileSummary state={state} quests={quests}/><p className="profile-agency-note">You can change your mind. These are interests to explore, not labels about your abilities.</p><ProfileRecordDetails state={state}/></aside></div>
 </div>;
}
