import React,{useEffect,useState} from 'react';
import {Button} from './Shared';
import DiscoveryAgentPanel from './DiscoveryAgentPanel';
import {compact,GuideChanges,GuideDetails,GuideHistory,StoryOrigin} from './DiscoveryGuide';
import useDiscoveryGuide from '../useDiscoveryGuide';
import {studentCorrection,manualProfileChanges} from '../profilePresentation';

const INTERESTS=['science','technology','art','helping','building','research','creative','people','biology','coding','design','math','engineering','nature'];
export function ProfileDetails({values,hideInterests=false}) {
 return <dl className="profile-details">{!hideInterests&&<div><dt>Interests to explore</dt><dd>{values.interests.length?values.interests.join(', '):'Still exploring — no career choice needed.'}</dd></div>}<div><dt>Preferred activities</dt><dd>{values.learning_style}</dd></div><div><dt>Exploration goal</dt><dd>{values.goal}</dd></div>{values.correction&&<div><dt>Your voice shapes this</dt><dd>{studentCorrection(values.correction)}</dd></div>}{values.not_sure&&<div><dt>Your starting point</dt><dd>I’m not sure yet, and that’s okay.</dd></div>}</dl>;
}

export default function ProfileDiscoveryReview({state,values,reconfirmation=false,dirty=false,busy=false,onConfirm,onUpdated,onSaveRevision,onCancelEditing,onPrepareManual=()=>{},renderEditor,renderInterestEditor}) {
 const guide=useDiscoveryGuide(state);
 const latest=guide.latest;
 const initial=state.discovery_guide?.latest;
 const initialFeedback=initial&&!initial.is_stale&&initial.response_version===state.discovery_guide?.response_version?initial.feedback:null;
 const [verdict,setVerdict]=useState(()=>initialFeedback?.verdict||'');
 const [correction,setCorrection]=useState(()=>initialFeedback?.correction||'');
 const [preferred,setPreferred]=useState([]);
 const [retained,setRetained]=useState([]);
 const [custom,setCustom]=useState('');
 const [manual,setManual]=useState(reconfirmation);
 const [working,setWorking]=useState(false);
 const [error,setError]=useState('');
 const [saved,setSaved]=useState(false);
 useEffect(()=>{
  setVerdict(guide.ready?latest?.feedback?.verdict||'':'');
  setCorrection(guide.ready?latest?.feedback?.correction||'':'');
  setPreferred([]);setRetained([]);setCustom('');
 },[latest?.id,guide.ready]);
 const waiting=busy||working||guide.loading;
 const question=guide.agent&&!guide.agent.is_stale?guide.agent.question:null;
 const remaining=guide.guide?.revisions_remaining??3;
 const clues=guide.ready?compact(latest).clues:[];
 const union=[...new Set([...(verdict==='Somewhat'?retained:[]),...preferred])];
 const canRevise=guide.ready&&union.length>0&&union.length<=3&&(verdict!=='Somewhat'||correction.trim().length>=3)&&!custom.trim()&&remaining>0;
 const manualProposal=Boolean(!guide.ready&&!question&&state.profile_draft&&!guide.loading&&(guide.error||guide.agent?.status==='manual_edit'));
 const canConfirm=(guide.ready||manualProposal)&&!question&&!dirty&&verdict==='Yes';
 const changes=guide.ready&&latest.changes||state.profile_draft?.review_feedback?.changes||manualProfileChanges(state,values);
 const choose=value=>{setVerdict(value);setCorrection('');setPreferred([]);setRetained([]);setCustom('');setSaved(false);setError('');};
 const toggle=(value,items,set)=>set(items.includes(value)?items.filter(i=>i!==value):[...items,value]);
 const openManual=()=>{onPrepareManual({...((correction.trim())?{correction}:{}),...(union.length?{interests:union,not_sure:false}:{})});setManual(true);setVerdict(value=>['Somewhat','Not really'].includes(value)?value:'Not really');setError('');};
 const revise=async event=>{
  event.preventDefault();setWorking(true);setError('');
  try {
   if(verdict==='Yes') {await onConfirm(guide.ready?latest.id:null);return;}
   await guide.request({event:'feedback',story_id:latest.id,verdict,correction,preferred_interests:preferred,retained_interest_ids:verdict==='Somewhat'?retained:[]});
   setSaved(true);await onUpdated();
  }catch(err){setError(err.message);}finally{setWorking(false);}
 };
 const clarify=async body=>{
  setWorking(true);setError('');
  try{await guide.request(body);await onUpdated();setSaved(true);}catch(err){setError(err.message);}finally{setWorking(false);}
 };
 const saveManual=async()=>{
  if(!dirty){setManual(false);setVerdict('');return;}
  setWorking(true);setError('');
  try{
   const result=await onSaveRevision({review_verdict:['Somewhat','Not really'].includes(verdict)?verdict:null,review_story_id:guide.ready?latest.id:null});
   if(result){setManual(false);setVerdict('');setSaved(true);}
  }catch(err){setError(err.message);}finally{setWorking(false);}
 };
 const retry=force=>guide.request({event:'discover',...(force?{retry:true,request_id:crypto.randomUUID()}:{})}).catch(()=>{});
 return <section className="profile-discovery-review" aria-labelledby="profile-interpretation-title" aria-busy={waiting}>
  <span className="eyebrow">WHAT CAREERQUEST SUGGESTS</span><h2 id="profile-interpretation-title">A starting point, shaped by you</h2>
  {guide.loading&&<p role="status">Preparing your interpretation…</p>}
  {(error||guide.error)&&<div role="alert" className="guide-error"><p>{error||guide.error}</p><Button className="secondary" disabled={waiting} onClick={()=>retry(false)}>Retry guide</Button></div>}
  {guide.ready?<><StoryOrigin guide={latest}/><p className="discovery-story-summary">{compact(latest).summary}</p></>:<p>Your saved choices and interests are below. {manualProposal?'This is a manual proposal, not an AI-generated revision. You can review and confirm it without waiting for AI.':'Your earlier story stays in history while this proposal is prepared.'}</p>}
  <GuideChanges changes={changes?{...changes,correction:studentCorrection(changes.correction)}:null}/>
  {saved&&<p role="status">Proposal saved. Review what changed, then choose Yes only if it feels right. Nothing has been confirmed.</p>}
  {manual?<><h3>{reconfirmation?'Update your saved preferences':'Edit your interests and preferences'}</h3><p>Your interpretation above uses saved information. Save your edits to refresh it, then review before confirming.</p>{renderEditor()}<p>Changes stay unconfirmed. Your earlier profile and roadmaps remain saved.</p><div className="button-row"><Button busy={waiting} onClick={saveManual}>{dirty?'Save Changes & Review Proposal':'Review Saved Profile'}</Button><Button className="secondary" disabled={waiting} onClick={()=>{onCancelEditing();setManual(false);}}>Cancel manual edits</Button></div></>:<>
   {renderInterestEditor&&<section className="profile-inline-interests" aria-label="Edit interests"><h3>Interests to explore</h3>{renderInterestEditor(()=>{setManual(true);setError('');},correction)}<p>Tap an interest to change it. You’ll save and review changes before confirming.</p></section>}
   <ProfileDetails values={values} hideInterests={Boolean(renderInterestEditor)}/>
   <DiscoveryAgentPanel agent={guide.agent} busy={waiting} onAnswer={clarify} onReview={openManual} hideManualAction/>
   {!question&&<form className="guide-feedback" onSubmit={revise}><fieldset disabled={waiting}><legend>Does this interpretation feel like you?</legend>{['Yes','Somewhat','Not really'].map(value=><label key={value}><input type="radio" name="profile-feedback" value={value} checked={verdict===value} onChange={()=>choose(value)} required/>{value}</label>)}
    {verdict==='Yes'&&<p>Ready to make this yours? Confirming saves this profile version and its validated Discovery handoff.</p>}
    {['Somewhat','Not really'].includes(verdict)&&<>
     {verdict==='Somewhat'&&<fieldset className="guide-retained"><legend>Which interests still feel right?</legend>{clues.map(clue=><label key={clue.interest_id}><input type="checkbox" checked={retained.includes(clue.interest_id)} onChange={()=>toggle(clue.interest_id,retained,setRetained)}/>{clue.label}</label>)}</fieldset>}
     <p>{verdict==='Not really'?'Let’s start with your interests instead. Your earlier choices stay saved.':'Keep what feels right and tell us what to change.'}</p>
     <fieldset className="guide-preferences"><legend>What would you prefer to explore?</legend><div className="guide-interest-picker">{[...new Set([...INTERESTS,...preferred])].map(interest=><button type="button" key={interest} aria-pressed={preferred.includes(interest)} disabled={!preferred.includes(interest)&&union.length>=3&&!union.includes(interest)} onClick={()=>toggle(interest,preferred,setPreferred)}>{interest}</button>)}</div><label htmlFor="guide-interest">Add a preferred interest</label><div className="guide-custom-interest"><input id="guide-interest" value={custom} maxLength={40} onChange={e=>setCustom(e.target.value)}/><Button type="button" className="secondary" disabled={!custom.trim()||union.length>=3} onClick={()=>{const value=custom.trim().toLowerCase();if(value&&!preferred.includes(value)){setPreferred([...preferred,value]);setCustom('');}}}>Add interest</Button></div><p>Choose up to three interests, including any you keep.</p></fieldset>
     <label htmlFor="guide-correction">{verdict==='Somewhat'?'What should we change? (required)':'Anything else to change? (optional)'}</label><textarea id="guide-correction" rows={3} maxLength={500} minLength={verdict==='Somewhat'?3:undefined} required={verdict==='Somewhat'} value={correction} onChange={e=>setCorrection(e.target.value)}/><p>{remaining} guided revisions remaining. Manual editing is always available.</p>{remaining===0&&<p role="status">You’ve tried three guided revisions. Edit interests manually to continue.</p>}
    </>}
    <Button type="submit" busy={waiting} disabled={verdict==='Yes'?!canConfirm:!canRevise}>{verdict==='Yes'?(reconfirmation?'Reconfirm My Explorer Profile':'Confirm My Explorer Profile'):verdict==='Not really'?'Create a New Proposal':verdict==='Somewhat'?'Revise My Proposal':'Choose a response to continue'}</Button>
   </fieldset><p>Revisions stay unconfirmed. Raw quest choices and earlier profiles are preserved.</p></form>}
   <Button className="secondary" disabled={waiting} onClick={openManual}>Edit Interests Manually</Button>
  </>}
  {guide.ready&&<GuideDetails guide={latest} busy={waiting||manual} onRetry={()=>retry(true)}/>}
  <GuideHistory guideState={guide.guide}/>
 </section>;
}
