import test from 'node:test';
import assert from 'node:assert/strict';
import {welcomeHero} from '../src/welcomeHero.js';
const fresh={profile:{id:'fictional-hero',alias:'Hero Demo',grade:10,xp:0},quest_count:0,quest_complete:false,confirmed:false};
const discovered={...fresh,quest_count:3,quest_complete:true};
const confirmed={...discovered,confirmed:true};

test('new student gets a first-discovery welcome without invented grade or points',()=>{
  const hero=welcomeHero(null);
  assert.match(hero.message,/first discovery quest/);
  assert.equal(hero.grade,null);
  assert.equal(hero.points,null);
});
test('partial quests use the persisted count and actual quest total',()=>{
  assert.match(welcomeHero({...fresh,quest_count:1}).message,/1 of 3/);
  assert.match(welcomeHero({...fresh,quest_count:2},4).message,/2 of 4/);
});
test('completed quests never receive the old start-three-quests instruction',()=>{
  for(const state of [discovered,confirmed,{...confirmed,research_count:1},{...confirmed,latest_plan:{version:1}},{...confirmed,latest_plan:{version:1},reflection_count:1}]) {
    assert.doesNotMatch(welcomeHero(state).message,/Start with three|first discovery quest|short discovery quests/i);
  }
  assert.match(welcomeHero(confirmed).message,/Profile is confirmed/);
});
test('legacy roadmap fields do not leak into Home and reconfirmation remains explicit',()=>{
  const saved={...confirmed,latest_plan:{version:2},profile_preferences:{interests:['science']}};
  assert.doesNotMatch(welcomeHero(saved).message,/roadmap|reflect/i);assert.match(welcomeHero(saved).message,/Career Worlds/);
  assert.match(welcomeHero({...saved,confirmed:false,profile_draft:{version:2}}).message,/updated Explorer Profile.*review/);
  assert.doesNotMatch(welcomeHero({...saved,confirmed:false}).message,/Profile is confirmed/);
});
test('metadata uses saved grade and earned XP, including a genuine zero',()=>{
  assert.deepEqual([welcomeHero(fresh).grade,welcomeHero(fresh).points],[10,0]);
  assert.equal(welcomeHero({...fresh,profile:{...fresh.profile,xp:80}}).points,80);
  for(const profile of [{},{grade:8,xp:-1},{grade:'11',xp:'70'}]) {
    assert.equal(welcomeHero({...fresh,profile}).grade,null);
    assert.equal(welcomeHero({...fresh,profile}).points,null);
  }
});
test('hero rendering decisions do not mutate saved progress',()=>{
  const state={...confirmed,latest_plan:{version:1},profile:{...fresh.profile,xp:70}};
  const before=JSON.stringify(state);
  welcomeHero(state);
  assert.equal(JSON.stringify(state),before);
});
