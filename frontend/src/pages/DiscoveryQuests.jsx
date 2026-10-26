import React,{useEffect,useReducer,useState} from 'react';
import {ArrowLeft,ArrowRight,Check,Sparkles,Code2,Palette,FlaskConical,HeartHandshake,Globe2,Compass,Pencil,Save,X} from 'lucide-react';
import {Button,PageHeading,Gate} from '../components/Shared';
import UnsavedChanges from '../components/UnsavedChanges';
import DiscoveryGuide from '../components/DiscoveryGuide';
import {discoveryJourney} from '../discoveryJourney';
import {discoveryEditor,emptyDiscoveryEditor} from '../discoveryEditor';
import './discovery.css';
const iconFor=text=>/build|app|tool/i.test(text)?Code2:/science|data|research|ideas/i.test(text)?FlaskConical:/sketch|poster|visual/i.test(text)?Palette:HeartHandshake;

export function QuestProgress({model,step,onReview,busy}) {
  return <aside className="quest-guide"><span className="eyebrow">YOUR DISCOVERY TRAIL</span>{model.steps.map(quest=><button key={quest.index} className={`quest-index ${step===quest.index?'active':''}`} disabled={busy||(!quest.answer&&quest.index!==model.firstIncomplete)} onClick={()=>onReview(quest.index)} aria-current={step===quest.index?'step':undefined}><span>{quest.answer?<Check size={16} aria-hidden="true"/>:quest.index+1}</span><span><strong>{quest.title}</strong><small>{step===quest.index?'You are here':quest.answer?'Saved · Revisit anytime':quest.index===model.firstIncomplete?'Your next quest':'Up ahead'}</small></span></button>)}{model.firstCompletionXP!==null&&<p><Sparkles size={17} aria-hidden="true"/>{model.firstCompletionXP} XP per first completion</p>}<button className="text-button" disabled={busy} onClick={()=>onReview('summary')}>View Discovery Clues</button></aside>;
}
export function ChoiceTile({choice,index,selected,onSelect,busy}) {
  const Icon=iconFor(choice);
  return <label className={`choice-tile option-${index} ${selected?'selected':''}`}><input type="radio" name="quest-choice" checked={selected} onChange={onSelect} disabled={busy}/><span className="choice-art"><Icon size={26} aria-hidden="true"/></span><strong>{choice}</strong><span className="choice-check" aria-hidden="true">{selected?<Check size={16}/>:index+1}</span></label>;
}

export default function DiscoveryQuests({state,quests,onNavigate,onAnswer,busy=false,onDirty=()=>{}}) {
  const model=discoveryJourney(state,quests);
  const [view,setView]=useState(()=>model.firstIncomplete??'summary');
  const [editor,dispatchEditor]=useReducer(discoveryEditor,emptyDiscoveryEditor);
  const {editing,draft}=editor;
  const [pendingView,setPendingView]=useState(null);
  const [feedback,setFeedback]=useState('');
  const quest=typeof view==='number'?model.steps[view]:null;
  const original=quest?.choice||'';
  const dirty=Boolean(draft&&draft!==original);
  useEffect(()=>{onDirty(dirty);return()=>onDirty(false);},[dirty,onDirty]);
  const show=target=>{setView(target);dispatchEditor({type:'reset'});setFeedback('');};
  const requestView=target=>{if(dirty){setPendingView(target);return;}show(target);};
  const edit=index=>{setView(index);dispatchEditor({type:'edit',choice:model.steps[index].choice});setFeedback('');};
  const cancel=()=>{dispatchEditor({type:'cancel'});setFeedback('Edits cancelled. Your saved answer and points are unchanged.');};
  const save=async()=>{
    const revised=Boolean(quest.answer);
    const saved=await onAnswer(quest.index,draft,revised);
    if(!saved)return;
    dispatchEditor({type:'reset'});
    if(revised){setFeedback('Answer updated. No extra quest XP was awarded.');return;}
    const updated=discoveryJourney(saved,quests);
    setView(updated.firstIncomplete??'summary');
    setFeedback('Your discovery has been saved.');
  };
  if(!state)return <div className="spec-page discovery-page"><Gate state={state} onNavigate={onNavigate}/></div>;
  const selection=editing||!quest?.answer?draft:original;
  const editable=Boolean(quest)&&(!quest.answer||editing);
  const reviewLabel='Review My Explorer Profile';
  return <div className="spec-page discovery-page"><PageHeading eyebrow="DISCOVERY QUESTS · COLLECT YOUR CLUES" title={`${state?.profile.alias?.trim()||'Explorer'}, discover what sparks your curiosity.`}>Short scenarios. No right answers, no ability scores—just possibilities to explore.</PageHeading>
    {model.needsReconfirmation&&<div className="quest-review-alert" role="status"><strong>Your updated clues need another review.</strong><p>Your earlier confirmed profile and saved roadmaps are preserved. Confirm the updated Explorer Profile before personalized research or new plans.</p></div>}
    {feedback&&<p className="quest-save-feedback" role="status">{feedback}</p>}
    {model.allComplete&&<div hidden={view!=='summary'}><DiscoveryGuide key={state.profile.id} state={state}/></div>}
    {view!=='summary'&&!model.allComplete&&<p className="small-note">After all three quests, your saved demo choices and grade go to Groq to create your Discovery Guide. If unavailable, you’ll see a labeled deterministic summary. No XP is awarded for guide generation.</p>}
    {view==='summary'?<section className="panel discovery-clues"><span className="eyebrow">{model.allComplete?'DISCOVERY COMPLETE':'YOUR SAVED DISCOVERIES'}</span><h2>Your Discovery Clues</h2><p>{model.completed} of {model.steps.length} quests saved.{model.questXP!==null&&<> {model.questXP} quest XP earned.</>}</p><p>These clues come from your saved answers. They are possibilities to explore, not fixed labels or career-fit scores.</p><div className="discovery-clue-grid">{model.steps.map(item=><article className="discovery-clue" key={item.index}><span className="clue-number">{String(item.index+1).padStart(2,'0')}</span><h3>{item.title}</h3>{item.answer?<><span className="saved-answer-label">You chose</span><p className="saved-answer-text">{item.choice}</p><span className="discovery-interest">Clue to explore: {item.clue}</span><time dateTime={item.answer.created_at}>Saved {new Date(item.answer.created_at).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})}</time><button className="text-button" disabled={busy} aria-label={`Edit answer for ${item.title}`} onClick={()=>edit(item.index)}><Pencil size={16} aria-hidden="true"/>Edit answer</button></>:<p>Not answered yet. Your next clue is waiting.</p>}</article>)}</div><Button disabled={busy} onClick={()=>model.allComplete?onNavigate('confirm'):show(model.firstIncomplete)}>{model.allComplete?reviewLabel:'Continue my next quest'}<ArrowRight size={17} aria-hidden="true"/></Button><p className="small-note">Revisiting, cancelling edits and saving changed answers never grant quest XP twice.</p></section>:quest&&<div className="quest-layout"><QuestProgress model={model} step={view} busy={busy} onReview={requestView}/><section className="panel quest-panel"><div className="quest-meta"><span>QUEST {quest.index+1} OF {model.steps.length}</span><span className="xp-pill">{quest.answer?'Saved · Edits earn no extra XP':model.firstCompletionXP!==null?`+${model.firstCompletionXP} XP on first completion`:'Rewards saved with your explorer'}</span></div><div className="quest-progress" role="progressbar" aria-label="Completed quests" aria-valuenow={model.completed} aria-valuemin={0} aria-valuemax={model.steps.length}><span style={{width:`${model.completed/Math.max(model.steps.length,1)*100}%`}}/></div><div className="scenario-illustration" aria-hidden="true"><span/><span/>{quest.index===0?<Sparkles size={58}/>:quest.index===1?<Globe2 size={58}/>:<Compass size={58}/>}</div><span className="eyebrow">{quest.title}</span><h2>{quest.question}</h2>{quest.answer&&<p className="quest-saved-answer"><Check size={18} aria-hidden="true"/><strong>Saved answer:</strong> {original}</p>}<p>{quest.answer?(editing?'Choose a replacement, then save it explicitly. Cancel keeps your saved answer.':'This answer is saved. Select Edit answer to make a change.'):'Choose whatever sounds interesting today. You can edit your answer later.'}</p><fieldset className="quest-choices" disabled={busy||!editable}><legend className="sr-only">{editable?'Choose one activity':'Your saved answer'}</legend>{Object.keys(quest.options).map((option,index)=><ChoiceTile key={`${quest.index}:${option}`} choice={option} index={index} selected={selection===option} busy={busy||!editable} onSelect={()=>dispatchEditor({type:'choose',choice:option})}/>)}</fieldset>{editable&&selection&&<p className="choice-feedback">A useful clue to explore. This choice doesn’t define what you can do.</p>}
      {quest.answer&&editing?<div className="quest-controls"><Button className="ghost" disabled={busy} onClick={cancel}><X size={16} aria-hidden="true"/>Cancel edits</Button><Button busy={busy} disabled={!draft||draft===original} onClick={save}><Save size={16} aria-hidden="true"/>Save changes</Button></div>:<div className="quest-controls"><Button className="ghost" disabled={busy||quest.index===0} onClick={()=>requestView(quest.index-1)}><ArrowLeft size={16} aria-hidden="true"/>Previous</Button>{quest.answer?<div className="quest-saved-controls"><Button className="secondary" disabled={busy} onClick={()=>edit(quest.index)}><Pencil size={16} aria-hidden="true"/>Edit answer</Button><Button disabled={busy} onClick={()=>requestView(quest.index+1<model.steps.length?quest.index+1:'summary')}>{quest.index+1<model.steps.length?'Next quest':'View Discovery Clues'}<ArrowRight size={16} aria-hidden="true"/></Button></div>:<Button busy={busy} disabled={!draft} onClick={save}>{quest.index===model.steps.length-1?'Finish discovery':'Continue'}<ArrowRight size={16} aria-hidden="true"/></Button>}</div>}
      {quest.answer&&<p className="small-note">Only Save changes updates a saved answer. Changed answers reopen profile review; earlier confirmed profiles and saved roadmaps stay in history.</p>}
    </section></div>}
    {pendingView!==null&&<UnsavedChanges profileDirty={false} busy={busy} description="This quest answer has unsaved changes. Keep editing, or discard the draft before changing quests." onStay={()=>setPendingView(null)} onDiscard={()=>{show(pendingView);setPendingView(null);}}/>}
  </div>;
}
