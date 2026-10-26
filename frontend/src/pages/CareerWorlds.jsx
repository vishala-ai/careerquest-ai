import React,{useEffect,useRef,useState} from 'react';
import {Globe2,Code2,FlaskConical,Palette,Leaf,ArrowRight,Bookmark,Check,ArrowLeft} from 'lucide-react';
import {api} from '../api';
import {Button,PageHeading,Gate,Sources,NextAction} from '../components/Shared';
import CareerPortfolioPaths from './CareerPortfolioPaths';
import CareerComparison from './CareerComparison';
import CareerCelebration from './CareerCelebration';
import CareerPortfolio from './CareerPortfolio';
import CareerDiscoveryMilestone from './CareerDiscoveryMilestone';

import './career-worlds.css';

const icons={bioengineering:FlaskConical,software:Code2,design:Palette,environment:Leaf};
export function CareerWorldCard({world,onExplore,busy,explored=false,saved=false}) {
 const Icon=icons[world.world_id]||Globe2;
 return <article className={`career-world-card world-${world.world_id}`}><span className="career-world-icon"><Icon size={32} aria-hidden="true"/></span>{world.recommended&&<span className="career-world-label">From your confirmed interests</span>}<h3>{world.title}</h3><p>{world.description}</p>{world.recommended&&world.reason&&<p className="career-world-reason"><strong>Why suggested?</strong><br/>{world.reason}</p>}<p className="career-world-history">{saved?'In your shortlist':explored?'Previously explored':'A possibility to discover'}</p><Button className="full" disabled={busy} onClick={()=>onExplore(world.world_id)} aria-label={`Explore Career: ${world.title}`}>Explore Career<ArrowRight size={18} aria-hidden="true"/></Button></article>;
}
export function CareerWorldDetail({world,onSave,saved=false,canSave=false,busy=false}) {
 const cited=(item)=><>{item.text}<span className="career-citation">{item.source_ids.map(id=><a href={`#source-${id}`} key={id}>[Source]</a>)}</span></>;
 return <article className="panel career-world-detail" data-world-id={world.world_id}><span className="eyebrow">YOUR CAREER WORLD FIELD NOTES</span><h2>{world.title}</h2><p className="career-overview">{cited(world.overview)}</p><div className="career-fact-grid">{[['Career activities','activities'],['Skills you could explore','skills'],['Related educational fields','educational_fields']].map(([title,key])=><section key={key}><h3>{title}</h3>{world[key]?.length?<ul>{world[key].map((item,i)=><li key={i}>{cited(item)}</li>)}</ul>:<p>No supported information is available in this catalogue.</p>}</section>)}</div><p className="career-support">Educational fields are ideas to explore, not school-specific admissions requirements.</p>{world.mission&&<section className="career-try-mission"><h3>Optional try-it mission</h3><p>{world.mission.text}</p><span>CareerQuest demo activity · Optional, not a job requirement</span></section>}<section className="career-evidence"><h3>Sources behind these notes</h3>{world.sources.map(source=><div id={`source-${source.id}`} key={source.id}><Sources sources={[source]}/></div>)}</section><Button busy={busy} disabled={!canSave||saved} onClick={onSave}>{saved?<><Check size={18} aria-hidden="true"/>Saved to My Career Shortlist</>:<><Bookmark size={18} aria-hidden="true"/>Save to My Career Shortlist</>}</Button></article>;
}

export default function CareerWorlds({state,onNavigate,onUpdated,initialData,entry='worlds',onProgress=()=>{},onScreenChange=()=>{}}) {
 const [data,setData]=useState(initialData||null);
 const [loading,setLoading]=useState(!initialData);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const [notice,setNotice]=useState('');
 const [screen,setScreen]=useState(entry==='auto'?'entry':entry==='milestone'?'milestone':'worlds');
 const entered=useRef(entry!=='auto');
 const [celebration,setCelebration]=useState(null);
 const [celebrationBusy,setCelebrationBusy]=useState(false);
 const [celebrationError,setCelebrationError]=useState('');
 const [detail,setDetail]=useState(null);
 const [question,setQuestion]=useState('');
 const [answer,setAnswer]=useState(null);
 const [compare,setCompare]=useState(['','','']);
 const mounted=useRef(true),working=useRef(false);
 const claiming=useRef(false),contextRef=useRef(null);
 const pid=state?.profile.id;
 const confirmed=Boolean(data?.confirmed);
 contextRef.current=data?.profile_context?.confirmation_event_id;
 useEffect(()=>{onScreenChange(screen);},[screen]);
 useEffect(()=>{
  if(!data||entered.current)return;
  entered.current=true;
  const saved=(data.portfolio_completion?.history?.length||0)>0||(data.path_preferences?.history?.length||0)>0;
  setScreen(saved?'portfolio':'milestone');
 },[data]);

 useEffect(()=>{setDetail(null);setAnswer(null);setCelebration(null);setCelebrationError('');},[data?.profile_context?.confirmation_event_id]);
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 const reload=async()=>{
  const value=pid?await api(`/profiles/${pid}/career-discovery`):{worlds:await api('/career-worlds'),portfolio:{explorations:[],shortlist:[]},confirmed:false};
  if(mounted.current){setData(value);onProgress(value);}return value;
 };
 useEffect(()=>{if(initialData)return;let active=true;setLoading(true);setError('');reload().catch(err=>{if(active)setError(err.message);}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[pid,state?.confirmed,state?.profile_version]);
 useEffect(()=>{
  if(screen==='milestone'||screen==='entry'||screen==='portfolio'&&!data?.portfolio_completion?.active||loading||!confirmed||!pid||celebration||claiming.current)return;
  const context=contextRef.current;claiming.current=true;
  api(`/profiles/${pid}/career-celebrations/claim${screen==='portfolio'?'?kind=portfolio_completed':''}`,'POST',{}).then(value=>{if(mounted.current&&context===contextRef.current)setCelebration(value.celebration);}).catch(()=>{/* Optional celebration delivery never blocks saved work. */}).finally(()=>{claiming.current=false;});
 },[data,loading,celebration?.id,screen]);
 const work=async action=>{
  if(working.current)return;working.current=true;setBusy(true);setError('');setNotice('');
  try{return await action();}catch(err){if(mounted.current){setError(err.message);if(err.status===409){await onUpdated();await reload();}}}
  finally{working.current=false;if(mounted.current)setBusy(false);}
 };
 const focusRecommendations=()=>requestAnimationFrame(()=>{const heading=document.getElementById('career-recommendations-heading')||document.getElementById('career-all-heading');heading?.focus();heading?.scrollIntoView({block:'start',behavior:'instant'});});
 const backToRecommendations=()=>{setScreen('worlds');setDetail(null);setAnswer(null);setError('');focusRecommendations();};
 const openMilestone=()=>{setCelebration(null);setScreen('milestone');window.scrollTo({top:0,behavior:'instant'});};
 const focusDetail=()=>requestAnimationFrame(()=>{const heading=document.querySelector('.career-worlds-page .career-world-detail h2');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:false});}});
 const explore=wid=>{
  if(!confirmed){setDetail({preview:data.worlds.find(w=>w.world_id===wid)});return;}
  work(async()=>{const result=await api(`/profiles/${pid}/worlds/${wid}/explore`,'POST',{});if(!mounted.current)return;setDetail(result);await reload();await onUpdated();focusDetail();});
 };
 const save=(wid,eid)=>work(async()=>{
  const alreadySaved=data.portfolio.shortlist.some(item=>item.exploration_id===eid);
  const saved=await api(`/profiles/${pid}/career-shortlist`,'POST',{exploration_id:eid});if(!mounted.current)return;await reload();
  if(alreadySaved||saved.shortlist.length>2){const selected=saved.shortlist.find(item=>item.world_id===wid);setNotice(`${data.nickname?.trim()||'Explorer'}, ${selected.exploration.world.title} ${alreadySaved?'is already in your shortlist.':'is saved. You can keep exploring and change your mind.'}`);}
 });
 const revisit=eid=>work(async()=>{
  const item=await api(`/profiles/${pid}/career-explorations/${eid}`);if(!mounted.current)return;setScreen('worlds');setDetail({status:'ok',worlds:[item.world],exploration_ids:{[item.world_id]:item.id},is_stale:item.is_stale,saved_at:item.created_at});focusDetail();
 });
 const ask=(worldIds=[])=>work(async()=>{
  const result=await api(`/profiles/${pid}/career-guide`,'POST',{message:worldIds.length?'Compare the selected career worlds':question.trim(),world_ids:worldIds});
  if(!mounted.current)return;
  if(result.worlds?.length){setDetail(result);focusDetail();}else setAnswer(result);
  await reload();await onUpdated();
 });
 const worlds=data?.worlds||[];
 const portfolio=data?.portfolio||{explorations:[],shortlist:[]};
 const recommended=confirmed?worlds.filter(w=>w.recommended).slice(0,3):[];
 const other=worlds.filter(w=>!recommended.some(r=>r.world_id===w.world_id));
 const comparisonIds=compare.filter(Boolean);
 const compareReady=confirmed&&comparisonIds.length>=2&&new Set(comparisonIds).size===comparisonIds.length;
 const savePaths=values=>work(async()=>{await api(`/profiles/${pid}/career-paths`,'POST',values);await reload();setNotice('Your exploration choices are saved. Celebrate your selections when you’re ready.');});
 const completePortfolio=signature=>work(async()=>{await api(`/profiles/${pid}/career-portfolio/complete`,'POST',{expected_signature:signature});await reload();});
 const openOverviewSection=id=>{setScreen('worlds');setDetail(null);setAnswer(null);setError('');focusSection(id);};
 const focusSection=id=>requestAnimationFrame(()=>{const heading=document.getElementById(id);if(heading){heading.tabIndex=-1;heading.focus();heading.scrollIntoView({block:'start',behavior:'instant'});}});
 const finishCelebration=async action=>{
  if(celebrationBusy)return;setCelebrationBusy(true);setCelebrationError('');
  try{
   await api(`/profiles/${pid}/career-celebrations/${celebration.id}/acknowledge`,'POST',{});
   if(!mounted.current)return;setCelebration(null);
   if(action==='explore')backToRecommendations();
   else if(action==='shortlist')openOverviewSection('career-shortlist-heading');
   else if(action==='paths')openOverviewSection('career-paths-heading');
   else if(action==='portfolio'){if(screen==='portfolio')focusSection('portfolio-map-title');else openMilestone();}
   else if(action==='profile')onNavigate('confirm');
   else requestAnimationFrame(()=>{const heading=document.querySelector('.career-world-detail h2')||document.querySelector('.career-worlds-page h1');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}});
  }catch(err){if(mounted.current)setCelebrationError('Couldn’t save the dismissal. Please try again.');}
  finally{if(mounted.current)setCelebrationBusy(false);}
 };
 const cards=items=><div className="career-world-grid">{items.map(world=><CareerWorldCard key={world.world_id} world={{...world,recommended:confirmed&&world.recommended,reason:confirmed?world.reason:null}} busy={busy} onExplore={explore} explored={portfolio.explorations.some(e=>e.world_id===world.world_id)} saved={portfolio.shortlist.some(e=>e.world_id===world.world_id)}/>)}</div>;
 const nickname=data?.nickname?.trim()||state?.profile.alias?.trim()||'Explorer';
 const next=data?.next_action;
 const showNext=next&&(next.kind!=='save_career'||!detail);
 const takeNext=()=>{
  if(next.kind==='view_portfolio')openMilestone();
  else if(next.kind==='choose_paths')focusSection('career-paths-heading');
  else if(next.page)onNavigate(next.page);
  else if(next.exploration_id)revisit(next.exploration_id);
  else backToRecommendations();
 };
 if(screen==='portfolio')return <>{celebration&&<div className="portfolio-celebration"><CareerCelebration event={celebration} confirmed={confirmed} onFinish={finishCelebration} busy={celebrationBusy||busy} error={celebrationError}/></div>}{error&&<div role="alert" className="alert error"><p>{error}</p><Button className="secondary" onClick={()=>work(reload)}>Retry</Button></div>}{loading?<p role="status">Assembling your saved possibilities…</p>:<CareerPortfolio completion={data?.portfolio_completion} confirmed={confirmed} nickname={nickname} pid={pid} busy={busy} onConfirm={completePortfolio} onInterests={()=>onNavigate('confirm')} onCareers={backToRecommendations}/>}</>;
 if(screen==='milestone')return <CareerDiscoveryMilestone pid={pid} onCreate={async()=>{await reload();setScreen('portfolio');focusSection('career-portfolio-heading');}} onExplore={backToRecommendations} onShortlist={()=>openOverviewSection('career-shortlist-heading')} onNavigate={onNavigate}/>;
 return <div className="spec-page career-worlds-page" aria-busy={loading||busy}><PageHeading eyebrow="CAREER WORLDS · FOLLOW YOUR CURIOSITY" title={`Career Worlds for ${nickname}`}>{nickname}, choose a world to see what people do, skills you could try and fields you might explore. Save only the careers you want to keep.</PageHeading>
  {celebration&&<CareerCelebration event={celebration} confirmed={confirmed} onFinish={finishCelebration} busy={celebrationBusy||busy} error={celebrationError}/>}
  {error&&<div role="alert" className="alert error"><p>{error}</p><Button className="secondary" disabled={busy} onClick={()=>work(reload)}>Retry</Button></div>}{notice&&<p className="alert notice" role="status">{notice}</p>}
  {loading?<p role="status">Opening your Career Worlds…</p>:<>
   {!confirmed&&!detail&&<div className="career-confirmation-note"><p>You can browse every world. Confirm your Explorer Profile to open personalized research and save selections.</p><Button className="secondary" onClick={()=>onNavigate(state?.quest_complete?'confirm':state?'quests':'profiles')}>Review My Explorer Profile</Button></div>}
   {screen==='worlds'&&<>{detail?<section aria-label="Career research detail"><Button className="secondary career-back" disabled={busy} onClick={backToRecommendations}><ArrowLeft size={18} aria-hidden="true"/>Back to Recommended Careers</Button>
    {detail.preview?<section className="panel"><h2>{detail.preview.title}</h2><p>{detail.preview.description}</p><Gate state={state} onNavigate={onNavigate}/></section>:detail.status==='blocked'?<section className="panel" role="status"><h2>A small pause in the journey</h2><p>{detail.message}</p><p>Your profile and saved careers are safe. No source facts were invented.</p></section>:<>{detail.is_stale&&<p role="status">These notes were saved with an earlier profile. You can revisit them; explore this world again with your current confirmed profile before saving a new selection.</p>}{detail.worlds?.length>1&&<CareerComparison worlds={detail.worlds}/>} {detail.worlds?.map(world=>{const eid=detail.exploration_ids?.[world.world_id];return <CareerWorldDetail key={world.world_id} world={world} busy={busy} canSave={confirmed&&!detail.is_stale&&Boolean(eid)} saved={portfolio.shortlist.some(item=>item.exploration_id===eid)} onSave={()=>save(world.world_id,eid)}/>;})}</>}
   </section>:<><section className="career-recommended" aria-labelledby="career-recommendations-heading"><h2 id="career-recommendations-heading" tabIndex={-1}>Recommended Careers for You</h2><p>{confirmed&&data.confirmed_interests?.length?`From your confirmed interests: ${data.confirmed_interests.join(', ')}.`:'You’re keeping your options open.'} These are possibilities, not rankings.</p>{recommended.length?cards(recommended):<p>{confirmed?'No supported catalogue matches for your confirmed interests. You can explore all careers without a forced recommendation.':'Confirm your Explorer Profile to see personalized recommendations.'}</p>}{recommended.length<3&&<p>We suggest only supported matches. You don’t need three to keep exploring.</p>}<Button className="secondary" onClick={()=>{const heading=document.getElementById('career-all-heading');heading?.focus();heading?.scrollIntoView({block:'start',behavior:'instant'});}}>Explore All Careers</Button></section><section className="career-all-worlds" aria-labelledby="career-all-heading"><h2 id="career-all-heading" tabIndex={-1}>Explore All Careers</h2><p>Every supported career stays accessible. Your recommendations appear above; other possibilities are here.</p>{other.length?cards(other):!worlds.length?<p role="status">The catalogue is unavailable right now. Your saved history is safe.</p>:<p>All current catalogue careers appear in your recommendations above.</p>}</section></>}
   {!detail&&<>
   <section className="panel career-compare" aria-labelledby="career-compare-heading"><h2 id="career-compare-heading">Compare Careers</h2><p>Choose two or three different careers to compare their sourced activities, skills and educational fields.</p>{[0,1,2].map(index=><label key={index} htmlFor={`career-compare-${index}`}>Career {index+1}{index===2?' (optional)':''}<select id={`career-compare-${index}`} value={compare[index]} disabled={!confirmed||busy} onChange={event=>setCompare(values=>values.map((value,i)=>i===index?event.target.value:value))}><option value="">Choose a career</option>{worlds.map(world=><option key={world.world_id} value={world.world_id}>{world.title}</option>)}</select></label>)}<Button className="secondary" disabled={busy||!compareReady} onClick={()=>ask(comparisonIds)}>Compare Careers</Button></section>
   <details className="panel career-ai-guide"><summary>Ask Your AI Career Guide</summary><p>Ask a question or compare two worlds. Your guide uses curated source notes; check the linked sources as you explore.</p><label htmlFor="career-question">Your career question or comparison</label><textarea id="career-question" value={question} onChange={e=>setQuestion(e.target.value)} maxLength={800} rows={3} placeholder="What would you like to learn about a career?" disabled={!confirmed||busy}/><Button className="secondary" disabled={!confirmed||busy||question.trim().length<3} onClick={()=>ask()}>Ask My Career Guide</Button>{answer&&<section className="career-question-answer" aria-live="polite"><h3>Your guide’s notes</h3><p>{answer.trace?.some(t=>t.method==='bounded_policy_fallback')?'AI routing is unavailable. Your guide used saved source notes instead.':'These notes come from the curated sources below, not live web research.'}</p><p>{answer.message}</p>{answer.matches?.map((match,i)=><article key={`${match.source_id}-${i}`}><h4>{match.title}</h4><p>{match.description}</p></article>)}<Sources sources={answer.sources}/></section>}</details>
   {pid&&showNext&&<section className="panel career-next-step" aria-label="Your next step"><h2>Your next step</h2><p>{next.kind==='view_portfolio'?'Your careers and exploration preferences are saved. Celebrate your selections, then review your portfolio preview.':next.kind==='choose_paths'?'Choose a primary path, an optional secondary path, or explicitly keep exploring without priorities.':next.kind==='save_career'?'Your research notes are saved. Choose a career for your shortlist when you’re ready.':next.kind==='review_profile'?'Review your current interests before starting personalized career research.':'Start with your recommended careers, or explore the full catalogue. Nothing is saved until you choose.'}</p><NextAction disabled={busy||next.kind==='explore_world'&&!next.world_id} onClick={takeNext}>{next.kind==='explore_world'?'See Recommended Careers':next.label}</NextAction></section>}
   </>}
   </>}
   {pid&&!detail&&<section className="panel career-portfolio" aria-labelledby="career-portfolio-heading"><h2 id="career-portfolio-heading" tabIndex={-1}>Your saved career choices</h2><p>Exploring saves your notes. Adding a career to your shortlist always takes your explicit choice.</p><h3 id="career-shortlist-heading" tabIndex={-1}>My Career Shortlist</h3>{portfolio.shortlist.length?<div className="career-saved-list">{portfolio.shortlist.map(item=><button key={item.id} disabled={busy} onClick={()=>revisit(item.exploration_id)}><Bookmark size={20} aria-hidden="true"/><span>{item.exploration.world.title}<small>{item.exploration.is_stale?'Saved with an earlier profile':'Saved by you'}</small></span><span>Resume saved detail</span></button>)}</div>:<p>No careers shortlisted yet. Explore a world, then choose Save to My Career Shortlist.</p>}<CareerPortfolioPaths portfolio={portfolio} preferences={data.path_preferences} confirmed={confirmed} context={data.profile_context} busy={busy} onSave={savePaths}/><details><summary>Exploration history ({portfolio.explorations.length})</summary><div className="career-saved-list">{portfolio.explorations.map(item=><button key={item.id} disabled={busy} onClick={()=>revisit(item.id)}><span>{item.world.title}<small>{new Date(item.created_at).toLocaleString()}</small></span><span>Resume saved detail</span></button>)}</div></details>{screen==='worlds'&&<Button className="secondary" onClick={openMilestone}>View My Discovery Milestone</Button>}</section>}
   {!pid&&!detail&&<Button className="secondary" onClick={openMilestone}>View My Discovery Milestone</Button>}

  </>}
 </div>;
}
