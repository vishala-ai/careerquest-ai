export const STAGES = [
  {id: 'profiles', title: 'Meet your explorer', short: 'Create', description: 'A nickname, an avatar, a fresh start.', icon: 'profile'},
  {id: 'quests', title: 'Discover your spark', short: 'Discover', description: 'Three small choices. Plenty to discover.', icon: 'spark'},
  {id: 'confirm', title: 'Make it your own', short: 'Confirm', description: 'Review your clues. You decide what fits.', icon: 'compass'},
  {id: 'worlds', title: 'Open new worlds', short: 'Explore', description: 'Get curious about careers and college.', icon: 'world'},
  {id: 'roadmap', title: 'Sketch your next steps', short: 'Plan', description: 'Review and save a flexible roadmap.', icon: 'map'},
  {id: 'reflect', title: 'Pause, reflect, repeat', short: 'Reflect', description: 'Notice what you enjoyed. Try a new direction.', icon: 'journal'},
];
export function journeyStages(state) {
  const done = [Boolean(state), Boolean(state?.quest_complete), Boolean(state?.confirmed), (state?.research_count || 0) > 0, Boolean(state?.latest_plan), (state?.reflection_count || 0) > 0];
  const available = [true, Boolean(state), Boolean(state?.quest_complete), Boolean(state?.confirmed), Boolean(state?.confirmed), Boolean(state?.confirmed)];
  const next = done.indexOf(false);
  return STAGES.map((stage, index) => ({...stage, done: done[index], locked: !available[index], current: index === next}));
}
export function nextStop(state) {
  return journeyStages(state).find(stage => !stage.done) || {id: 'worlds', title: 'Follow a new curiosity', description: 'Your journey keeps growing. Explore another possibility.'};
}
export function preferences(state) {
  const saved = state?.profile_draft || state?.profile_preferences;
  return {
    interests: state?.profile_draft ? state.profile_draft.interests : state?.confirmed ? state.profile.interests : [...new Set((state?.quest_answers || state?.events || []).filter(event => ['quest_completed','quest_revised'].includes(event.kind)).map(event => event.payload.interest))],
    learning_style: saved?.learning_style || 'Hands-on projects',
    goal: saved?.goal || 'Explore careers and college majors',
  };
}
export function profileForm(state) {
  const saved = state?.profile_draft || state?.profile_preferences;
  return {...preferences(state), correction: saved?.correction || '', not_sure: saved?.not_sure || false};
}
import {adventureHome} from './adventureHome.js';
export function dashboardNext(state) {return adventureHome(state).mission;}
export function readExplorers() {
  try {const saved = JSON.parse(localStorage.getItem('cq_explorers') || '[]'); return Array.isArray(saved) ? saved.filter(item => item && typeof item.id === 'string') : [];} catch {return [];}
}
export function rememberExplorer(state, avatar) {
  const old = readExplorers();
  const existing = old.find(item => item.id === state.profile.id);
  const item = {id: state.profile.id, alias: state.profile.alias, grade: state.profile.grade, avatar: avatar || existing?.avatar || '🧭'};
  const list = [item, ...old.filter(profile => profile.id !== item.id)];
  localStorage.setItem('cq_explorers', JSON.stringify(list)); localStorage.setItem('cq_pid', item.id);
  return list;
}
