import React,{useEffect,useState} from 'react';
import {Button} from './Shared';
const names={ask_clarifying_question:'Ask a clarifying question',revise_discovery_story:'Revise the Discovery Story',suggest_career_worlds:'Suggest Career Worlds',request_profile_review:'Request Explorer Profile review'};

export function discoveryAgentView(result) {
 const source=result.guide;const agent=result.agent;
 if(!source?.latest)return source;
 const latest={...source.latest,content:source.latest.content?{...source.latest.content}:null};
 if(agent&&!agent.is_stale&&agent.story_id===latest.id&&latest.content){
  if(agent.recommendations.length){latest.content.career_worlds=agent.recommendations;latest.recommendation_source=agent.recommendation_method==='groq'?'groq_tool_selection':'catalogue_fallback';}
  if(agent.changes)latest.changes=agent.changes;
 }
 return {...source,latest};
}

export default function DiscoveryAgentPanel({agent,busy,onAnswer,onReview,readOnly=false,hideManualAction=false}) {
 const question=readOnly?null:agent?.question;
 const [selected,setSelected]=useState(question?.selected_interests||[]);
 const [custom,setCustom]=useState('');
 const [correction,setCorrection]=useState('');
 useEffect(()=>{setSelected(question?.selected_interests||[]);setCustom('');setCorrection('');},[agent?.session_id,question?.id,agent?.trace?.length]);
 if(!agent)return null;
 const toggle=value=>setSelected(selected.includes(value)?selected.filter(i=>i!==value):[...selected,value]);
 const submit=event=>{event.preventDefault();onAnswer({event:'clarify',session_id:agent.session_id,question_id:question.id,preferred_interests:selected,correction});};
 const add=()=>{const value=custom.trim().toLowerCase();if(value&&!selected.includes(value)&&selected.length<3){setSelected([...selected,value]);setCustom('');}};
 return <div className="discovery-agent-panel">
  {readOnly&&agent.question&&<p role="status">Your guide has a saved question. Continue to Explorer Profile to answer it.</p>}
  {agent.fallback_used&&<p className="guide-source-label" role="status">Some agent steps used a bounded fallback or stopped safely. Discovery Agent Activity identifies which decisions came from Groq.</p>}
  {agent.engine==='bounded_service_fallback'&&<p role="status">LangGraph is unavailable. The bounded service fallback is running.</p>}
  {agent.is_stale?<p role="status">The previous agent session is archived because your saved answers or profile changed.</p>:question?<section className="guide-agent-question" aria-label="Discovery Agent question"><h3>A quick question before we continue</h3><p>{question.text}</p><form onSubmit={submit}><fieldset disabled={busy}><legend className="sr-only">Answer the saved discovery question</legend>{question.id==='correction'?<><label htmlFor="agent-correction">My correction · aliases and test data only</label><textarea id="agent-correction" value={correction} onChange={e=>setCorrection(e.target.value)} required minLength={3} maxLength={500} rows={3}/></>:<><div className="guide-interest-picker">{[...new Set([...question.options,...selected])].map(value=><button key={value} type="button" aria-pressed={selected.includes(value)} disabled={!selected.includes(value)&&selected.length>=3} onClick={()=>toggle(value)}>{value}</button>)}</div><label htmlFor="agent-interest">Add a preferred interest</label><div className="guide-custom-interest"><input id="agent-interest" value={custom} onChange={e=>setCustom(e.target.value)} maxLength={40}/><Button className="secondary" type="button" disabled={!custom.trim()||selected.length>=3} onClick={add}>Add interest</Button></div><p>Your selected interests replace guesses you don’t agree with. Choose up to three.</p></>}
   <Button type="submit" busy={busy} disabled={question.id==='correction'?correction.trim().length<3:!selected.length||Boolean(custom.trim())}>Continue with My Answer</Button></fieldset></form><p>{agent.clarifications_remaining} clarifying question{agent.clarifications_remaining===1?'':'s'} remaining. You can edit interests manually at any time.</p></section>:null}
  {!question&&!agent.is_stale&&agent.message&&<p>{agent.message}</p>}
  {!readOnly&&!hideManualAction&&!question&&!agent.is_stale&&agent.status==='manual_edit'&&<Button className="secondary" disabled={busy} onClick={()=>onReview(true)}>Open Manual Profile Review</Button>}
  <details className="discovery-agent-activity"><summary>Discovery Agent Activity</summary><p>Engine: {agent.engine}. Profile confirmation: {agent.pending_confirmation?'Still required':'Already saved by the student'}.</p><ol>{agent.trace.map(step=><li key={step.sequence}><strong>{names[step.action]||'Rejected action'}</strong><p>{step.method==='groq'?'Groq selected this tool':step.method==='bounded_policy_fallback'?'Bounded fallback selected this tool':'Deterministic policy selected this tool'} · {step.status} · {step.model}</p>{step.error&&<p>Safe failure detail: {step.error.error_type}{step.error.http_status&&` (HTTP ${step.error.http_status})`}. No secrets or hidden reasoning are shown.</p>}{step.output?.generation_status&&<p>Story generation: {step.output.generation_status==='groq'?'Groq':'Labeled deterministic fallback'}.</p>}{step.output?.recommendations?.map(world=><p key={world.world_id}>{world.title} · {world.source} · Not live verified</p>)}</li>)}</ol><p>Only four allowlisted tools can run. The agent cannot confirm a profile or create a personalized roadmap. SQLite saves questions and tool receipts for resume; native LangGraph checkpointing is not claimed.</p></details>
 </div>;
}
