// Read-only domain projection of the GET /profiles/{id} persistence contract.
// Browser storage only selects an explorer; it never supplies progress here.
export function adventureHome(state, questTotal = 3) {
  const count = state?.quest_count || 0;
  const complete = Boolean(state?.quest_complete);
  const confirmed = complete && Boolean(state?.confirmed);
  const explored = (state?.research_count || 0) > 0;
  const planned = Boolean(state?.latest_plan);
  const updated = !confirmed && Boolean(state?.profile_preferences || state?.confirmation_version);
  let mission;
  if (!state) mission = {id:'profiles', label:'Create My Explorer', title:'Meet your explorer', description:'Choose a explorer nickname and grade. Your adventure starts with curiosity.'};
  else if (!complete) mission = {id:'quests', label:'Continue Quests', title:`Your next clue: Quest ${count + 1}`, description:`${count} of ${questTotal} quests complete. Pick up at the first unfinished quest. There are no right or wrong answers.`, questIndex:count};
  else if (!confirmed) mission = {id:'confirm', label:updated?'Review Updated Profile':'Review My Profile', title:updated?'Make your new direction yours':'Your clues. Your say.', description:'Review your interests and confirm what feels right before personalized exploration or planning.'};
  else if (planned) mission = {id:'journey', label:'My Journey', title:'Pause, reflect, keep growing', description:'Your roadmap is saved. Revisit your progress and reflect on what you would like to try.'};
  else if (!explored) mission = {id:'worlds', label:'Explore Career Worlds', title:'Follow a little curiosity', description:'Explore career possibilities using curated sources. You do not have to choose one path.'};
  else mission = {id:'roadmap', label:'Build My Roadmap', title:'Turn curiosity into a small step', description:'Create a proposal, review the suggested activities, and decide whether to save it.'};

  const stages = [
    {id:'profiles', title:'Meet your explorer', description:'A explorer nickname and a fresh start.', done:Boolean(state), available:true},
    {id:'quests', title:'Discover your spark', description:`${count} of ${questTotal} quests complete.`, done:complete, available:Boolean(state)},
    {id:'confirm', title:'Make it your own', description:confirmed?'Your Explorer Profile is confirmed.':updated?'Review and confirm your updated clues.':'Review your clues. You decide what fits.', done:confirmed, available:complete},
    {id:'worlds', title:'Explore career worlds', description:explored?'Exploration notes saved in your journey.':'Get curious about a few possibilities.', done:explored, available:confirmed},
    {id:'roadmap', title:'Sketch your next steps', description:planned?`Saved roadmap · Version ${state.latest_plan.version}`:'Review and save a flexible roadmap.', done:planned, available:confirmed},
    {id:'journey', title:'Grow your story', description:'Revisit progress and reflect at your pace.', done:(state?.reflection_count || 0)>0, available:Boolean(state)},
  ].map(stage => ({...stage, current:stage.id===mission.id, locked:!stage.available}));
  return {
    greeting:state?.profile?.alias?.trim() ? `Hi ${state.profile.alias.trim()}!` : 'Hi, explorer!',
    grade:state?.profile?.grade, xp:state?.profile?.xp || 0,
    count, questTotal, confirmed, explored, planned, updated, mission, stages,
    completed:stages.filter(stage=>stage.done).length,
  };
}
