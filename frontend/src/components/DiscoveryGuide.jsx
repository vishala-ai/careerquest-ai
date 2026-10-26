import React from 'react';
import {Button} from './Shared';
import DiscoveryAgentPanel from './DiscoveryAgentPanel';
import useDiscoveryGuide from '../useDiscoveryGuide';

const legacySummary='Your choices are a starting point for curiosity, not a final answer about your future. You can use the clues below to choose something you would like to explore. Try one small idea and notice what feels interesting, what you would change, and what questions come next. You do not need to choose a career today. Keep the clues that feel right, replace those that do not, or begin with interests of your own. Your next step is to review this proposal and make it yours.';
export const compact=guide=>({
  summary:guide.content.summary||legacySummary,
  clues:guide.content.interest_clues||guide.content.what_this_might_suggest.map((item,index)=>({interest_id:item.interest_id||`clue-${index}`,label:item.interest_id||item.text,choice_ids:item.choice_ids})),
  mission:guide.content.mini_mission??guide.content.what_you_could_try_next?.[0],
});
const sourceLabel=(guide,id)=>{
 const preference=guide.preferences?.evidence?.find(item=>item.choice_id===id);
 if(preference)return preference.choice;
 const choice=guide.source_answers.find(item=>item.choice_id===id);
 return choice?`Quest ${(choice.quest??guide.source_answers.indexOf(choice))+1}`:'Saved evidence';
};
export function GuideContent({guide}) {
 const content=compact(guide);
 return <><p className="discovery-story-summary">{content.summary}</p>
  <h3>Interest clues</h3><ul className="guide-clues">{content.clues.slice(0,3).map(clue=><li key={clue.interest_id}><strong>{clue.label}</strong><small>{clue.stated?'Your stated preference':'A possibility to explore'}</small></li>)}</ul>
  {content.mission&&<div className="guide-mini-mission"><h3>Optional mini-mission</h3><p>{content.mission.text}</p></div>}
  <h3>Career Worlds to get curious about</h3>
  {guide.recommendation_source==='catalogue_fallback'&&<p className="guide-source-label">Catalogue-based suggestions · Not Groq-generated</p>}
  {guide.content.career_worlds.length?<div className="guide-worlds">{guide.content.career_worlds.map(world=><article key={world.world_id}><h4>{world.title}</h4><p>{world.explanation||'A catalogue connection supported by the saved evidence below.'}</p><small className="guide-evidence">From: {world.choice_ids.map(id=>sourceLabel(guide,id)).join('; ')}</small>{world.url?<a href={world.url} target="_blank" rel="noreferrer">{world.source} ↗</a>:<span>{world.source}</span>}<small>Curated catalogue · Not live verified</small></article>)}</div>:<p role="status">No supported match is available in this small catalogue. Your preferences are still valid. Edit interests manually or review your profile without a recommendation.</p>}
 </>;
}

export function GuideChanges({changes}) {
 if(!changes)return null;
 return <section className="guide-changes" aria-label="What changed"><h3>What changed</h3><p>{changes.mode==='Not really'?'This proposal follows your preferred interests. Earlier guesses have been set aside.':'This proposal keeps your agreed interests and follows your correction.'}</p>{changes.kept.length>0&&<p>Kept: {changes.kept.join(', ')}.</p>}{changes.added.length>0&&<p>Added: {changes.added.join(', ')}.</p>}{changes.removed.length>0&&<p>Set aside: {changes.removed.join(', ')}.</p>}{changes.details?.map(item=><p key={item.field}>{item.field}: {String(item.before)} → {String(item.after)}.</p>)}{changes.correction&&<p>Your correction: “{changes.correction}”</p>}</section>;
}
export function StoryOrigin({guide}) {return <p className="guide-source-label">{guide.status==='groq'?'AI Discovery Story':'Deterministic Discovery Summary · Not AI-generated'}</p>;}
export function GuideDetails({guide,onRetry,busy}) {
 return <details className="guide-generation"><summary>How this was generated</summary><p><strong>{guide.status==='groq'?'Groq-generated Discovery Story':'Deterministic Discovery Summary · Not AI-generated'}</strong></p><p>Model: {guide.model}. Generation status: {guide.status}. Version {guide.version}.</p><p>Recommendation source: {guide.recommendation_source||'legacy output'}. Validation: {guide.diagnostics?.reason||'legacy output'}.</p><p>Aliases and test data only. Your saved choices and grade, plus stated corrections, guide generation. Your nickname is used here, not sent. This story cannot confirm a profile.</p><h4>What You Chose</h4><ul>{guide.source_answers.map(item=><li key={item.choice_id}>{item.choice}</li>)}</ul><h4>What This Might Suggest</h4><p>Interest clues are tentative or labeled as stated preferences.</p><h4>What You Could Try Next</h4><p>The mini-mission is optional.</p>{guide.status==='fallback'&&<Button className="secondary" disabled={busy} onClick={onRetry}>Retry with Groq</Button>}</details>;
}
export function GuideHistory({guideState}) {
 if(!guideState?.history?.length)return null;
 return <details className="guide-versions"><summary>Discovery Guide history ({guideState.history.length})</summary>{[...guideState.history].reverse().map(item=><div className="guide-history" key={item.id}><h3>Version {item.version} · {item.is_stale||item.response_version!==guideState.response_version?'Stale':item.recommendations_stale?'Previous proposal':'Current answers'}</h3><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time>{item.content&&<p>{compact(item).summary}</p>}{item.preferences?.interests?.length>0&&<p>Stated interests: {item.preferences.interests.join(', ')}.</p>}{item.feedback&&<p>Saved feedback: {item.feedback.verdict}{item.feedback.correction&&` — ${item.feedback.correction}`}</p>}</div>)}</details>;
}
export default function DiscoveryGuide({state}) {
 const guide=useDiscoveryGuide(state);
 const retry=force=>guide.request({event:'discover',...(force?{retry:true,request_id:crypto.randomUUID()}:{})}).catch(()=>{});
 return <section className="panel discovery-guide" aria-labelledby="discovery-guide-title" aria-busy={guide.loading}>
  <span className="eyebrow">YOUR DISCOVERY GUIDE</span><h2 id="discovery-guide-title">{state.profile.alias?.trim()||'Explorer'}, your Discovery Story</h2><p>A few clues to take into your profile review.</p>
  {guide.loading&&<p role="status">Preparing your story…</p>}
  {guide.error&&<div className="guide-error" role="alert"><p>{guide.error}</p><Button className="secondary" disabled={guide.loading} onClick={()=>retry(false)}>Try again</Button></div>}
  {guide.latest&&!guide.ready&&<p role="status">Your earlier guide is stale. Your saved choices and history are safe. Continue to Explorer Profile to review your updated interests.</p>}
  {guide.ready&&<><StoryOrigin guide={guide.latest}/><GuideContent guide={guide.latest}/><GuideDetails guide={guide.latest} busy={guide.loading} onRetry={()=>retry(true)}/></>}
  <DiscoveryAgentPanel agent={guide.agent} readOnly/>
  <GuideHistory guideState={guide.guide}/>
 </section>;
}
