import test from 'node:test';
import assert from 'node:assert/strict';
import {welcomeJourney} from '../src/welcomeJourney.js';
const fresh={profile:{id:'fictional-welcome',alias:'Nova',grade:10,xp:0},quest_count:0,quest_complete:false,confirmed:false,research_count:0,reflection_count:0,latest_plan:null};
const discovered={...fresh,quest_count:3,quest_complete:true};
const confirmed={...discovered,confirmed:true};
const explored={...confirmed,research_count:1};
const planned={...explored,latest_plan:{version:1}};

test('first-time Welcome requires setup then starts the actual first quest',()=>{
  const result=welcomeJourney(null);
  assert.equal(result.action.requiresSetup,true);
  assert.equal(result.action.id,'quests');
  assert.equal(result.action.label,'Start My First Quest');
  assert.equal(result.stages[0].active,true);
  assert.ok(result.stages.every(stage=>stage.locked));
});
test('Welcome uses the saved nickname with a neutral fallback',()=>{
  assert.equal(welcomeJourney(fresh).greeting,'Hi, Nova! 👋');
  for(const alias of ['',null,'  ']) assert.equal(welcomeJourney({...fresh,profile:{...fresh.profile,alias}}).greeting,'Hi, explorer! 👋');
});
test('Welcome primary CTA resumes the first unfinished saved activity',()=>{
  for(const [state,id,label] of [
    [fresh,'quests','Start My First Quest'],
    [{...fresh,quest_count:1},'quests','Continue Quest 2'],
    [{...fresh,quest_count:2},'quests','Continue Quest 3'],
    [discovered,'confirm','Review My Explorer Profile'],
    [confirmed,'worlds','Explore Career Worlds'],
    [explored,'roadmap','Build My Roadmap'],
    [planned,'reflect','Reflect on My Journey'],
  ]){
    const restored=JSON.parse(JSON.stringify(state));
    assert.equal(welcomeJourney(restored).action.id,id);
    assert.equal(welcomeJourney(restored).action.label,label);
    assert.equal(welcomeJourney(restored).stages.filter(stage=>stage.active).length,1);
  }
});
test('five stages preserve history while an edited profile requires confirmation again',()=>{
  const result=welcomeJourney({...planned,confirmed:false,profile_draft:{version:2}});
  assert.deepEqual(result.stages.map(stage=>stage.title),['Discover','Confirm','Explore','Plan','Reflect']);
  assert.deepEqual(result.stages.map(stage=>stage.done),[true,false,true,true,false]);
  assert.equal(result.action.id,'confirm');
  for(const id of ['worlds','roadmap','reflect']) assert.equal(result.stages.find(stage=>stage.id===id).locked,true);
});
test('a saved plan cannot hide the first incomplete exploration stage',()=>{
  assert.equal(welcomeJourney({...confirmed,latest_plan:{version:1}}).action.id,'worlds');
  assert.equal(welcomeJourney({...explored,proposal:{plan:{}}}).action.id,'roadmap');
});
test('rendering and revisiting Welcome cannot change persisted XP or completion',()=>{
  const state={...planned,profile:{...fresh.profile,xp:70}};
  const before=JSON.stringify(state);
  for(let index=0;index<4;index++) welcomeJourney(state);
  assert.equal(JSON.stringify(state),before);
  const finished=welcomeJourney({...state,reflection_count:1});
  assert.ok(finished.stages.every(stage=>stage.done));
  assert.equal(finished.action.id,'worlds');
});
