// Welcome-only projection of persisted API records. No local progress flags or writes.
export function welcomeJourney(state, questTotal = 3) {
  const questsComplete = Boolean(state?.quest_complete);
  const confirmed = questsComplete && Boolean(state?.confirmed);
  const explored = (state?.research_count || 0) > 0;
  const planned = Boolean(state?.latest_plan);
  const count = state?.quest_count || 0;
  const stages = [
    {id:'quests', title:'Discover', description:`${count} of ${questTotal} discovery quests complete.`, done:questsComplete, available:Boolean(state)},
    {id:'confirm', title:'Confirm', description:confirmed?'Your Explorer Profile is confirmed.':'Review your clues. Choose what feels right.', done:confirmed, available:questsComplete},
    {id:'worlds', title:'Explore', description:explored?'Your exploration notes are saved.':'Get curious about career possibilities.', done:explored, available:confirmed},
    {id:'roadmap', title:'Plan', description:planned?`Roadmap version ${state.latest_plan.version} saved.`:'Review and save a flexible roadmap.', done:planned, available:confirmed},
    {id:'reflect', title:'Reflect', description:(state?.reflection_count || 0)>0?'Your reflections are part of your journey.':'Notice what you enjoyed and what you might try next.', done:(state?.reflection_count || 0)>0, available:confirmed},
  ];
  const next = stages.find(stage=>!stage.done) || stages[2];
  const labels = {
    quests:count===0?'Start My First Quest':`Continue Quest ${count+1}`,
    confirm:'Review My Explorer Profile', worlds:'Explore Career Worlds',
    roadmap:'Build My Roadmap', reflect:'Reflect on My Journey',
  };
  const headings = {
    quests:'Ready to discover what excites you?', confirm:'Ready to make your profile your own?',
    worlds:'Ready to explore new possibilities?', roadmap:'Ready to plan a small next step?',
    reflect:'Ready to reflect on what you discovered?',
  };
  return {
    greeting:state ? `Hi, ${state.profile?.alias?.trim() || 'explorer'}! 👋` : 'Welcome, future explorer! 👋',
    heading:headings[next.id],
    action:{id:next.id,label:labels[next.id],requiresSetup:!state,questIndex:next.id==='quests'?count:undefined},
    stages:stages.map(stage=>({...stage,active:stage.id===next.id,locked:!stage.available})),
  };
}
