// Presentation only. Never rewrite the saved correction or treat it as policy.
export function studentCorrection(note) {
 const text=String(note||'').trim();
 if(!text)return '';
 if(/^see if you have to revise the career goals[.!?]?$/i.test(text))return 'I’d like to revisit my goals as I explore.';
 const cleaned=text.replace(/^for this fictional (?:explorer|student)[,:]?\s*/i,'');
 if(/^(?:i\b|i[’']|my\b)/i.test(cleaned))return cleaned.charAt(0).toUpperCase()+cleaned.slice(1);
 return 'You’ve shared what you would like to change. Keep shaping your interests and goal until they feel right to you.';
}

export function isReconfirmation(state) {
 return Boolean(state?.quest_complete&&!state.confirmed&&state.profile_preferences);
}

export function manualProfileChanges(state,values) {
 if(!state.profile_draft)return null;
 const previous=state.profile_preferences||{interests:[...new Set((state.quest_answers||[]).map(e=>e.payload.interest))],learning_style:'Hands-on projects',goal:'Explore careers and college majors',not_sure:false};
 const before=previous.interests||[];
 const added=values.interests.filter(i=>!before.includes(i));
 const removed=before.filter(i=>!values.interests.includes(i));
 const details=[['learning_style','Preferred activities'],['goal','Exploration goal'],['not_sure','Keeping options open']].filter(([key])=>previous[key]!==undefined&&previous[key]!==values[key]).map(([key,field])=>({field,before:previous[key],after:values[key]}));
 if(!added.length&&!removed.length&&!details.length&&(previous.correction||'')===(values.correction||''))return null;
 return {mode:'Somewhat',kept:values.interests.filter(i=>before.includes(i)),added,removed,details,correction:values.correction};
}
