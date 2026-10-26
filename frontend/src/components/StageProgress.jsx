import React from 'react';
import {Check,LockKeyhole,RefreshCw} from 'lucide-react';

export default function StageProgress({stages,current,onNavigate,busy=false,loading=false}) {
 return <nav className="stage-progress" aria-label="Adventure progress" aria-busy={loading}><ol>{stages.map((stage,index)=>{const Icon=stage.locked?LockKeyhole:stage.previouslyCompleted?RefreshCw:stage.done?Check:null;return <li key={stage.id} className={`stage-${stage.id}${stage.done?' is-complete':''}${current===stage.id?' is-current':''}`}><button disabled={busy||stage.locked} onClick={()=>onNavigate(stage.id)} aria-current={current===stage.id?'step':undefined} aria-label={`${stage.title}: ${stage.locked?'Locked':stage.status}. ${stage.previouslyCompleted?'Previously completed. ':''}${stage.description}`}><span className="stage-marker" aria-hidden="true">{Icon?<Icon size={15}/>:index+1}</span><span className="stage-label">{stage.title}<small>{stage.locked?'Up ahead':stage.status}</small></span></button></li>;})}</ol></nav>;
}
