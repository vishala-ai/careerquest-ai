import test from 'node:test';
import assert from 'node:assert/strict';
import {discoveryJourney} from '../src/discoveryJourney.js';
const quests=[
 {title:'Discover Your Spark',options:{'Build a mini-app':'technology','Sketch an invention':'art'}},
 {title:'Choose Your Mission',options:{'Analyze the data':'science'}},
 {title:'Find Your Learning Style',options:{'Build something':'building'}},
];
const answer=(quest,choice,interest,kind='quest_completed')=>({id:`fictional-${quest}-${kind}`,kind,created_at:'2026-01-01T00:00:00Z',payload:{quest,choice,interest}});
const answers=[answer(0,'Build a mini-app','technology'),answer(1,'Analyze the data','science'),answer(2,'Build something','building')];
const base={profile:{id:'fictional-discovery',xp:0},quest_answers:[],confirmed:false,discovery:{quest_xp:0,first_completion_xp:20}};

test('new and partial explorers derive the first incomplete quest from persisted answers',()=>{
 assert.equal(discoveryJourney(base,quests).phase,'new');
 assert.equal(discoveryJourney(base,quests).firstIncomplete,0);
 const partial=discoveryJourney({...base,quest_answers:answers.slice(0,1)},quests);
 assert.equal(partial.phase,'partial');assert.equal(partial.firstIncomplete,1);assert.equal(partial.steps[0].choice,'Build a mini-app');
});
test('saved answers rather than counts or visited flags decide which quest remains',()=>{
 const model=discoveryJourney({...base,quest_count:99,quest_complete:true,visited:true,quest_answers:[answers[1]]},quests);
 assert.equal(model.firstIncomplete,0);assert.equal(model.completed,1);assert.equal(model.allComplete,false);
});
test('completed discovery displays current saved choices and clues including a revision',()=>{
 const state={...base,quest_answers:[answer(0,'Sketch an invention','art','quest_revised'),...answers.slice(1)],discovery:{quest_xp:60,first_completion_xp:20}};
 const model=discoveryJourney(state,quests);
 assert.equal(model.phase,'completed');assert.equal(model.firstIncomplete,null);assert.equal(model.steps[0].choice,'Sketch an invention');assert.equal(model.steps[0].clue,'art');assert.equal(model.questXP,60);
});
test('reload restores answers, confirmation requirements and server-reported reward receipts',()=>{
 const state={...base,quest_answers:answers,confirmed:false,profile_preferences:{interests:['technology']},discovery:{quest_xp:42,first_completion_xp:14}};
 const restored=discoveryJourney(JSON.parse(JSON.stringify(state)),quests);
 assert.equal(restored.needsReconfirmation,true);assert.equal(restored.questXP,42);assert.equal(restored.firstCompletionXP,14);
 assert.equal(discoveryJourney({...state,confirmed:true},quests).needsReconfirmation,false);
});
test('discovery projection does not modify persisted answers, profile or XP',()=>{
 const state={...base,quest_answers:answers};const before=JSON.stringify(state);
 discoveryJourney(state,quests);discoveryJourney(state,quests);
 assert.equal(JSON.stringify(state),before);
 assert.equal(discoveryJourney({...state,discovery:undefined},quests).questXP,null);
});
