import React, {useEffect, useRef, useState} from 'react';
import {ArrowRight, ArrowUpRight, Check, ChevronDown, Compass, Sparkles, Map, Globe2, UserRound, Plus, Flag, BookOpen, ShieldCheck, Zap, Code2, FlaskConical, Palette, HeartHandshake, X, RefreshCw} from 'lucide-react';
import {api} from './api';
import {profileForm} from './journey';
import AppShell from './components/AppShell';
import {studentExperience} from './studentExperience';
import Welcome from './pages/Welcome';
import ExplorerSelection from './components/ExplorerSelection';
import {creationRequest,finishCreation,leaveExplorer} from './explorerSetup';
import DiscoveryQuests from './pages/DiscoveryQuests';
import ExplorerProfile from './pages/ExplorerProfile';
import UnsavedChanges from './components/UnsavedChanges';
import CareerWorlds from './pages/CareerWorlds';
import {Button, PageHeading, Gate, Sources, ActivityTimeline} from './components/Shared';


export default function App({account,onLogout}) {
  const [pid, setPid] = useState(account?.profile_id || '');
  const activeExplorer=useRef(pid);activeExplorer.current=pid;
  const [state, setState] = useState(null);
  const [createdProfileId,setCreatedProfileId]=useState('');
  const creatingFromWelcome=useRef(false);
  const [quests, setQuests] = useState([]);
  const [page, setPage] = useState('welcome');
  const [worldsEntry,setWorldsEntry]=useState(0);
  const [careerEntry,setCareerEntry]=useState('worlds');
  const [careerScreen,setCareerScreen]=useState('worlds');
  const [careerRecord,setCareerRecord]=useState(null);
  const [careerLoading,setCareerLoading]=useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [entryError,setEntryError]=useState(false);
  const [notice, setNotice] = useState('');
  const [explorers, setExplorers] = useState([]);
  const [explorerView,setExplorerView]=useState('switch');
  const [profileValues,setProfileValues]=useState(()=>profileForm(null));
  const [questDirty,setQuestDirty]=useState(false);
  const [interestPending,setInterestPending]=useState(false);
  const [pendingNav,setPendingNav]=useState(null);
  const [query, setQuery] = useState('Explore careers related to my interests');
  const [result, setResult] = useState(null);
  const [proposal, setProposal] = useState(null);
  const [reflection, setReflection] = useState('');
  const [model, setModel] = useState(false);
  const [fail, setFail] = useState(false);

  const profileDirty=page==='confirm' && state && !state.confirmed && (interestPending || JSON.stringify(profileValues)!==JSON.stringify(profileForm(state)));
  const route=next=>{if(next==='profiles'){onLogout();return;}if(['worlds','portfolio','celebrate'].includes(next)){setWorldsEntry(value=>value+1);setCareerEntry(next==='celebrate'?'milestone':next==='portfolio'?'auto':'worlds');setCareerScreen(next==='worlds'?'worlds':next==='celebrate'?'milestone':'portfolio');}if(next==='profiles')setExplorerView('switch');setPage(next==='celebrate'?'portfolio':next);setError('');setNotice('');window.scrollTo({top:0,behavior:'instant'});};
  const navigate=next=>{if(busy)return;if(next!==page && (profileDirty||questDirty)){setPendingNav(next);return;}route(next);};
  const hydrate=data=>setProfileValues(profileForm(data));
  const apply = (data, icon) => {activeExplorer.current=data.profile.id;setState(data);setPid(data.profile.id);setExplorers(current=>[{id:data.profile.id,alias:data.profile.alias,grade:data.profile.grade,avatar:icon||current.find(item=>item.id===data.profile.id)?.avatar||'🧭'}]);};
  async function action(fn) {
    setBusy(true); setError(''); setNotice('');
    try {return await fn();} catch (err) {setError(err.message);return null;} finally {setBusy(false);}
  }
  async function load() {
    setLoading(true); setError('');setEntryError(false);
    try {
      setQuests(await api('/quests'));
      if (pid) {
        try {const saved = await api(`/profiles/${pid}`); apply(saved); hydrate(saved); setResult(saved.last_research);}
        catch (err) {
          if (err.status !== 404) throw err;
          localStorage.removeItem('cq_pid'); setPid(''); setState(null); setPage(current=>current==='welcome'?'welcome':'profiles');
          setNotice('That explorer is no longer available. Choose a saved explorer or create a new one.');
        }
      }
    } catch (err) {setEntryError(true);setError(`Couldn’t connect to your journey. ${err.message}`);} finally {setLoading(false);}
  }
  useEffect(() => {load();}, []);
  const career=careerRecord?.pid===pid&&careerRecord.profileVersion===state?.profile_version&&careerRecord.confirmed===state?.confirmed?careerRecord.data:null;
  const updateCareer=(value,owner)=>{if(activeExplorer.current===owner)setCareerRecord({pid:owner,profileVersion:state?.profile_version,confirmed:state?.confirmed,data:value});};
  useEffect(()=>{
    if(!pid){setCareerRecord(null);setCareerLoading(false);return;}
    let active=true;setCareerLoading(true);
    api(`/profiles/${pid}/career-discovery`).then(value=>{if(active)updateCareer(value,pid);}).catch(()=>{if(active)setCareerRecord(null);}).finally(()=>{if(active)setCareerLoading(false);});
    return()=>{active=false;};
  },[pid,state?.profile_version,state?.confirmed,state?.research_count]);
  useEffect(()=>{const heading=document.querySelector('#main h1');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}},[page,worldsEntry]);

  useEffect(()=>{if(page!=='welcome')setCreatedProfileId('');},[page]);
  useEffect(()=>{
    if(createdProfileId&&page==='welcome'&&createdProfileId===state?.profile?.id){
      const heading=document.querySelector('#main h1');
      if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}
    }
  },[createdProfileId,page,state?.profile?.id]);
  useEffect(()=>{const protect=event=>{event.preventDefault();event.returnValue='';};if(profileDirty||questDirty||reflection.trim()){window.addEventListener('beforeunload',protect);return()=>window.removeEventListener('beforeunload',protect);}},[profileDirty,questDirty,reflection]);
  useEffect(() => {if (proposal?.plan) document.getElementById('roadmap-proposal')?.scrollIntoView({behavior: 'smooth', block: 'start'});}, [proposal]);

  const backToWelcome=()=>{
    if(busy||creatingFromWelcome.current)return;
    leaveExplorer();activeExplorer.current='';setPid('');setState(null);setCareerRecord(null);setCreatedProfileId('');hydrate(null);setResult(null);setProposal(null);setReflection('');setModel(false);setFail(false);setQuestDirty(false);setInterestPending(false);route('welcome');
  };
  const selectExplorer = id => action(async () => {
    const saved = await api(`/profiles/${id}`); setCreatedProfileId(''); apply(saved); hydrate(saved); setResult(saved.last_research); setProposal(null); setReflection(''); setModel(false); setFail(false); route('welcome');
  });
  const createFromWelcome = async values => {
    if(creatingFromWelcome.current)return null;
    creatingFromWelcome.current=true;
    try {
      return await action(async()=>{
        const data=await api('/profiles','POST',creationRequest(values));
        apply(data,values.avatar);finishCreation();hydrate(data);setResult(null);setProposal(null);setReflection('');setModel(false);setFail(false);
        setCreatedProfileId(data.profile.id);route('welcome');
        return data;
      });
    } finally {creatingFromWelcome.current=false;}
  };
  const answer=(step,choice,revise)=>action(async()=>{
    const data=await api(`/profiles/${pid}/quests/${step}`,'POST',{option:choice,revise});
    apply(data);hydrate(data);setProposal(null);
    setNotice(revise?(state.quest_answers.find(event=>event.payload.quest===step)?.payload.choice===choice?'Answer already saved. No additional XP awarded.':'Answer updated. No additional XP awarded. Review your profile again.'):'Clue collected. +20 XP for this first completion!');
    return data;
  });
  const openProfile=()=>navigate('confirm');
  const refreshGuide=async()=>{const data=await api(`/profiles/${pid}`);if(data.profile.id!==activeExplorer.current)return;apply(data);hydrate(data);setProposal(null);};
  const persistDraft=async()=>{if(interestPending)throw Error('Select Add to include your new interest, or clear that field before saving.');const data=await api(`/profiles/${pid}/draft`,'POST',{...profileValues,expected_version:state.profile_version});apply(data);hydrate(data);setProposal(null);return data;};
  const beginEdit=()=>action(async()=>{const data=await api(`/profiles/${pid}/draft`,'POST',{...profileForm(state),expected_version:state.profile_version,start_edit:true});apply(data);hydrate(data);setResult(null);setProposal(null);setNotice('A new draft is ready. Your earlier confirmed profile is preserved.');});
  const saveProfileRevision=review=>action(async()=>{
    if(interestPending)throw Error('Add your new interest or clear that field before saving.');
    const data=await api(`/profiles/${pid}/draft`,'POST',{...profileValues,...review,expected_version:state.profile_version});
    apply(data);hydrate(data);setProposal(null);setNotice('Your changes are saved as an unconfirmed proposal. Review it before confirming.');return data;
  });
  const confirm=reviewStoryId=>action(async()=>{
    if(interestPending)throw Error('Select Add to include your new interest, or clear that field before confirming.');
    if(typeof reviewStoryId==='string')await api(`/profiles/${pid}/discovery-agent`,'POST',{event:'feedback',story_id:reviewStoryId,verdict:'Yes'});
    const data=await api(`/profiles/${pid}/confirm`,'POST',{...profileValues,expected_version:state.profile_version,review_verdict:'Yes',review_story_id:typeof reviewStoryId==='string'?reviewStoryId:null});
    apply(data);hydrate(data);setProposal(null);setResult(null);route('welcome');setNotice('Explorer Profile confirmed. Your next adventure is ready.');
  });
  const explore = () => action(async () => {
    const data = await api(`/profiles/${pid}/explore`, 'POST', {message: query, use_groq: model, simulate_failure: fail});
    setResult(data); apply(await api(`/profiles/${pid}`));
  });
  const propose = () => action(async () => {setProposal(await api(`/profiles/${pid}/roadmap/propose`, 'POST', {}));});
  const save = () => action(async () => {
    apply(await api(`/profiles/${pid}/roadmap/save`, 'POST', {plan: proposal.plan})); setProposal(null); setNotice('Roadmap saved. A little reflection can help you choose what to try next.');
  });
  const reflect = () => action(async () => {
    await api(`/profiles/${pid}/reflect`, 'POST', {message: reflection}); setReflection('');
    const data = await api(`/profiles/${pid}`); apply(data); hydrate(data); route('journey'); setNotice('Reflection saved. +10 XP! Revisit your interests whenever you discover something new.');
  });
  const go=id=>navigate(id);
  const leaveHome=id=>{
    navigate(id);
    requestAnimationFrame(()=>{
      const heading=document.querySelector('#main h1');
      if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}
    });
  };
  const experience=studentExperience(state,career,quests.length||3);
  const currentAvatar=explorers.find(item=>item.id===pid)?.avatar || '🧭';

  return <AppShell page={page} state={state} career={career} careerScreen={careerScreen} progressLoading={careerLoading} avatar={currentAvatar} account={account} onLogout={()=>navigate('profiles')} onNavigate={go} busy={busy}><main id="main" className={`main-content ${page==='welcome'?'is-welcome':''}`} aria-busy={busy || loading}>
    <div className="demo-banner"><ShieldCheck size={14}/><span>Educational demo · Use aliases and test data only</span><span className="banner-note">Explore possibilities. Keep your options open.</span></div>
    {error && (page!=='welcome'||!entryError) && <div className="alert error" role="alert"><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss error"><X size={17}/></button>{!state && <button onClick={load}>Try again</button>}</div>}
    {notice && <div className="alert notice" role="status"><Check size={17}/><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss notification"><X size={17}/></button></div>}
    {loading && page!=='welcome' ? <div className="loading"><Compass className="spin" size={32}/><p>Finding your place on the map…</p></div> : <>

    {page==='profiles'&&<ExplorerSelection onWelcome={backToWelcome} explorers={explorers} pid={pid} view={explorerView} onView={setExplorerView} onSelect={selectExplorer} onCreate={createFromWelcome} busy={busy}/>}

    {page==='welcome'&&<Welcome explorers={explorers} onExplorerChoice={view=>{route('profiles');setExplorerView(view);}} state={state} experience={experience} createdProfileId={createdProfileId} loading={loading} error={entryError?error:''} onRetry={load} onNavigate={leaveHome} onCreate={createFromWelcome} busy={busy} questTotal={quests.length || 3}/>}
    {page==='quests'&&<DiscoveryQuests key={pid} state={state} quests={quests} onNavigate={go} onAnswer={answer} busy={busy} onDirty={setQuestDirty}/>}
    {page==='confirm'&&<ExplorerProfile state={state} quests={quests} values={profileValues} onChange={setProfileValues} onConfirm={confirm} onSaveRevision={saveProfileRevision} onGuideUpdated={refreshGuide} onBeginEdit={beginEdit} onNavigate={go} busy={busy} dirty={profileDirty} onPending={setInterestPending}/>}
    {page==='journey'&&<><PageHeading eyebrow="MY JOURNEY" title="Your story keeps growing.">Revisit saved moments and reflections. Your earlier choices stay part of the story.</PageHeading>{!state?<Gate state={state} onNavigate={go}/>:<section className="panel"><div className="button-row"><Button onClick={()=>navigate('reflect')}>Reflect on my experience<BookOpen size={17}/></Button><Button className="secondary" onClick={openProfile}>Revisit my profile<ArrowUpRight size={17}/></Button></div><div className="story-panel"><ActivityTimeline events={state.events}/></div></section>}</>}

    {(page==='worlds'||page==='portfolio')&&<CareerWorlds key={`${pid||'no-explorer'}:${worldsEntry}`} state={state} entry={careerEntry} onProgress={value=>updateCareer(value,pid)} onScreenChange={setCareerScreen} onNavigate={go} onUpdated={refreshGuide}/>}

    {page === 'roadmap' && <><PageHeading eyebrow="STOP 05 · PLAN" title="Small steps. Open possibilities.">A flexible exploration plan for Grade {state?.profile.grade || '9–12'}. Review it, make it yours, and come back as you grow.</PageHeading>{!state?.confirmed ? <Gate state={state} onNavigate={go}/> : <div className="roadmap-layout"><div><section className="panel roadmap-panel"><div className="panel-title"><span className="icon-block blue"><Map size={23}/></span><div><h2>{state.latest_plan ? 'Your saved roadmap' : 'Your next steps start here'}</h2><p>{state.latest_plan ? `Version ${state.latest_plan.version} · Saved for your explorer` : 'Generate a proposal, then review it before saving.'}</p></div></div>{state.latest_plan ? <><ol className="roadmap-activities">{state.latest_plan.content.activities.map((activity, index) => <li key={index}><span>{String(index + 1).padStart(2, '0')}</span><div><small>EXPLORATION ACTIVITY</small><p>{activity}</p></div></li>)}</ol><p className="small-note">{state.latest_plan.content.note}</p><details className="guide-options"><summary>Sources behind this roadmap</summary><Sources sources={state.latest_plan.content.sources}/></details></> : <div className="roadmap-empty"><Map size={65} strokeWidth={1}/><p>You don’t need the whole future figured out.<br/>Just a few things you’re curious to try.</p></div>}<Button busy={busy} onClick={propose} className={state.latest_plan ? 'secondary' : ''}>{state.latest_plan ? <RefreshCw size={16}/> : <Sparkles size={16}/>} {state.latest_plan ? 'Create a revised proposal' : 'Create my first roadmap'}</Button></section>
      {proposal?.plan && <section id="roadmap-proposal" className="panel proposal-panel" aria-live="polite"><span className="eyebrow">PROPOSED · NOT SAVED YET</span><h2>Does this feel like a good next step?</h2><p className="muted">{state.latest_plan ? "Your saved roadmap stays as it is until you confirm this proposal." : "Review these activities. Your first roadmap is saved only when you confirm."}</p><ol className="roadmap-activities">{proposal.plan.activities.map((activity, index) => <li key={index}><span>{index + 1}</span><p>{activity}</p></li>)}</ol><div className="button-row"><Button busy={busy} onClick={save}>Confirm & save roadmap <Check size={17}/></Button><Button className="ghost" disabled={busy} onClick={() => setProposal(null)}>{state.latest_plan ? "Keep my current plan" : "Discard proposal"}</Button></div></section>}</div><aside><section className="panel plan-next"><span className="icon-block peach"><BookOpen size={25}/></span><span className="eyebrow">THE NEXT STOP</span><h2>A little reflection<br/>goes a long way.</h2><p>What did you enjoy? What surprised you? Your answer can help shape your next adventure.</p><Button className="secondary" onClick={() => navigate('reflect')}>Reflect & adapt <ArrowRight size={16}/></Button></section><div className="gentle-note"><Flag size={23}/><p>This is a map,<br/><strong>not a requirement.</strong></p><span>Verify school requirements and deadlines with official sources and a counselor.</span></div></aside></div>}</>}

    {page === 'reflect' && <><PageHeading eyebrow="STOP 06 · REFLECT & REPEAT" title="What did you discover about you?">A small reflection can open a new direction. There’s always room to change your mind.</PageHeading>{!state?.confirmed ? <Gate state={state} onNavigate={go}/> : <div className="reflection-layout"><section className="panel reflection-panel"><span className="icon-block peach"><BookOpen size={30}/></span><h2>Leave a note for your future self.</h2><div className="reflection-prompts"><span>What felt interesting?</span><span>What would you try again?</span><span>What wasn’t for you?</span></div><label htmlFor="reflection">My reflection <small>Demo information only</small></label><textarea id="reflection" rows={5} value={reflection} maxLength={800} onChange={event => setReflection(event.target.value)} placeholder="I enjoyed building a mini-app. Next, I’d like to try designing an interface…"/><Button busy={busy} disabled={reflection.trim().length < 3} onClick={reflect}>Save reflection <span className="button-xp">+10 XP</span><ArrowRight size={17}/></Button></section><aside className="panel reflection-aside"><Compass size={42} strokeWidth={1.1}/><h2>A new interest?<br/>Make room for it.</h2><p>You’re not starting over. You’re adding to your story.</p><Button className="secondary" onClick={openProfile}>Revisit my interests <ArrowUpRight size={16}/></Button>{state.reflection_count > 0 && <p className="small-note">{state.reflection_count} reflection{state.reflection_count === 1 ? '' : 's'} saved in your journey.</p>}</aside></div>}</>}
    </>}
    <footer><span><Compass size={14}/> CareerQuest AI</span><span>Demo profiles · Offline sources · No admissions predictions</span><button onClick={() => navigate('profiles')}>Sign Out / Switch Account <ArrowUpRight size={13}/></button></footer>
  </main>{pendingNav&&<UnsavedChanges profileDirty={profileDirty} busy={busy} error={error} onStay={()=>setPendingNav(null)} onDiscard={()=>{hydrate(state);setPendingNav(null);route(pendingNav);}} onSave={()=>action(async()=>{await persistDraft();const target=pendingNav;setPendingNav(null);route(target);setNotice('Your draft was saved before leaving.');})}/>}</AppShell>;
}
