import React from 'react';
import {Button} from '../components/Shared';

export default function CareerPortfolioCompletion({completion,busy,onComplete}) {
 if(!completion)return null;
 return <section className="career-completion" aria-labelledby="career-completion-heading"><h3 id="career-completion-heading">Review and complete your portfolio</h3><p>Review your saved careers and Exploration Paths above. A secondary path is optional. Completing this snapshot keeps a record of your choices; you can update them later.</p>{completion.active?<p className="career-completion-status">Your Career Discovery Portfolio snapshot is complete.</p>:completion.ready?<Button disabled={busy} onClick={()=>onComplete(completion.signature)}>Complete My Career Discovery Portfolio</Button>:<p>Confirm your current profile, save a career and save your paths to complete a current portfolio snapshot.</p>}{completion.history.length>0&&<details><summary>Completed portfolio history ({completion.history.length})</summary><ol>{[...completion.history].reverse().map(item=><li key={item.id}><p>{item.snapshot.paths.map(path=>`${path.priority==='primary'?'Primary':'Secondary'}: ${path.title}`).join(' · ')}</p><small>{item.is_stale?'Earlier choices · ':'Completed · '}{new Date(item.created_at).toLocaleString()}</small></li>)}</ol></details>}</section>;
}
