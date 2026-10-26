// One view model for all explorers; only saved API responses determine progress.
export function discoveryJourney(state, quests) {
  const byStep=new Map();
  for(const event of state?.quest_answers || []) {
    const step=event.payload?.quest;
    if(Number.isInteger(step)&&quests[step]&&Object.hasOwn(quests[step].options,event.payload.choice)) byStep.set(step,event);
  }
  const steps=quests.map((quest,index)=>({
    ...quest,index,title:index===2?'Your Working Style':quest.title,
    answer:byStep.get(index)||null,
    choice:byStep.get(index)?.payload.choice||'',
    clue:byStep.get(index)?.payload.interest||'',
  }));
  const firstIncomplete=steps.find(step=>!step.answer)?.index??null;
  const completed=steps.filter(step=>step.answer).length;
  const allComplete=steps.length>0&&completed===steps.length;
  const xp=state?.discovery?.quest_xp;
  return {
    steps,firstIncomplete,completed,allComplete,
    phase:allComplete?'completed':completed?'partial':'new',
    questXP:Number.isInteger(xp)&&xp>=0?xp:null,
    firstCompletionXP:state?.discovery?.first_completion_xp??null,
    needsReconfirmation:allComplete&&!state?.confirmed&&Boolean(state?.profile_preferences||state?.confirmation_version),
  };
}
