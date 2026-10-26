import test from 'node:test';
import assert from 'node:assert/strict';
import {journeyStages, nextStop, preferences, profileForm, dashboardNext, readExplorers, rememberExplorer} from '../src/journey.js';

const profile = {id: 'synthetic-one', alias: 'Nova Test', grade: 11, interests: ['coding']};

test('new visitors must create an explorer before starting discovery', () => {
  assert.equal(nextStop(null).id, 'profiles');
  assert.deepEqual(journeyStages(null).filter(stop => !stop.locked).map(stop => stop.id), ['profiles']);
});
test('completed quests lead to profile confirmation, keeping research locked', () => {
  const state = {profile, quest_complete: true, confirmed: false};
  assert.equal(nextStop(state).id, 'confirm');
  assert.equal(journeyStages(state).find(stop => stop.id === 'worlds').locked, true);
});
test('saved research and roadmap move the next step to reflection after reload', () => {
  const state = {profile, quest_complete: true, confirmed: true, research_count: 2, latest_plan: {version: 1}};
  assert.equal(nextStop(state).id, 'reflect');
  assert.equal(journeyStages(state).filter(stop => stop.done).length, 5);
  assert.equal(nextStop({...state, reflection_count: 1}).id, 'worlds');
});
test('confirmed style and goal are restored without needing a recent confirmation event', () => {
  const restored = preferences({profile, confirmed: true, events: [], profile_preferences: {
    learning_style: 'Creative activities', goal: 'Try a mini-project',
  }});
  assert.deepEqual(restored, {interests: ['coding'], learning_style: 'Creative activities', goal: 'Try a mini-project'});
});
test('profile switching remembers separate explorers without erasing either', () => {
  const storage = new Map();
  globalThis.localStorage = {getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value)};
  rememberExplorer({profile}, '🚀');
  rememberExplorer({profile: {...profile, id: 'synthetic-two', alias: 'Orbit Test', grade: 9}}, '🌱');
  rememberExplorer({profile});
  assert.equal(storage.get('cq_pid'), 'synthetic-one');
  assert.equal(readExplorers().length, 2);
  assert.equal(readExplorers()[0].avatar, '🚀');
  assert.equal(readExplorers()[1].grade, 9);
});
test('Dashboard resumes quests or required confirmation before personalized exploration',()=>{
  assert.equal(dashboardNext({profile,quest_count:1}).id,'quests');
  assert.equal(dashboardNext({profile,quest_count:3,quest_complete:true,confirmed:false}).id,'confirm');
  assert.equal(dashboardNext({profile,quest_complete:true,confirmed:true}).id,'worlds');
});
test('an unconfirmed draft restores edits while the old confirmed profile remains intact',()=>{
  const state={profile,confirmed:false,profile_preferences:{interests:['coding']},profile_draft:{interests:['design'],learning_style:'Creative activities',goal:'Try a mini-project',not_sure:false,correction:'Synthetic correction'}};
  assert.deepEqual(profileForm(state),{interests:['design'],learning_style:'Creative activities',goal:'Try a mini-project',not_sure:false,correction:'Synthetic correction'});
  assert.deepEqual(state.profile.interests,['coding']);
  assert.equal(journeyStages(state).find(stage=>stage.id==='worlds').locked,true);
});
