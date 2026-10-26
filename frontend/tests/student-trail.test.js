import test from 'node:test';
import assert from 'node:assert/strict';
import {welcomeJourney} from '../src/welcomeJourney.js';
import {trailMilestones} from '../src/studentTrail.js';
const fresh={profile:{id:'fictional-trail',alias:'Trail Demo',grade:10,xp:0},quest_count:0,quest_complete:false,confirmed:false,research_count:0,reflection_count:0,latest_plan:null};
const confirmed={...fresh,quest_count:3,quest_complete:true,confirmed:true};
const trail=state=>trailMilestones(welcomeJourney(state));

test('new explorer trail has no completed stages and explains setup prerequisites',()=>{
  const stages=trail(null);
  assert.ok(stages.every(stage=>!stage.done&&stage.status==='Locked'));
  assert.equal(stages.find(stage=>stage.active).id,'quests');
  assert.ok(stages.every(stage=>stage.prerequisite.includes('Create your explorer')));
});
test('partially completed quests remain recommended and future locks describe real prerequisites',()=>{
  const stages=trail({...fresh,quest_count:1});
  assert.equal(stages[0].status,'Recommended Next');
  assert.equal(stages[0].actionLabel,'Continue Quest 2');
  assert.equal(stages[0].description,'1 of 3 discovery quests complete.');
  assert.match(stages[1].prerequisite,/Complete all three/);
  assert.match(stages[3].prerequisite,/Confirm your current/);
});
test('confirmed profile recommends Explore while Plan and Reflect are available',()=>{
  const stages=trail(confirmed);
  assert.equal(stages.find(stage=>stage.active).id,'worlds');
  assert.equal(stages[0].status,'Completed');
  for(const id of ['roadmap','reflect']) {
    const stage=stages.find(stage=>stage.id===id);
    assert.equal(stage.status,'Available');
    assert.equal(stage.locked,false);
    assert.equal(stage.prerequisite,'');
  }
});
test('recommending Explore again never relocks saved Plan or Reflect',()=>{
  for(const research_count of [0,1]) {
    const stages=trail({...confirmed,research_count,latest_plan:{version:3},reflection_count:2});
    assert.equal(stages.find(stage=>stage.active).id,'worlds');
    for(const id of ['roadmap','reflect']) {
      const stage=stages.find(stage=>stage.id===id);
      assert.equal(stage.status,'Completed');
      assert.equal(stage.done,true);
      assert.equal(stage.locked,false);
      assert.match(stage.actionLabel,/Revisit/);
    }
  }
});
test('reconfirmation preserves historical completion and names the genuine unmet gate',()=>{
  const stages=trail({...confirmed,confirmed:false,profile_draft:{version:2},research_count:1,latest_plan:{version:1},reflection_count:1});
  assert.equal(stages.find(stage=>stage.active).id,'confirm');
  assert.equal(stages.find(stage=>stage.id==='confirm').status,'Recommended Next');
  for(const id of ['worlds','roadmap','reflect']) {
    const stage=stages.find(stage=>stage.id===id);
    assert.equal(stage.done,true);
    assert.equal(stage.status,'Locked');
    assert.equal(stage.prerequisite,'Confirm your current Explorer Profile first.');
  }
});
test('trail projection preserves hero CTA, backend values and actual page targets',()=>{
  const state={...confirmed,research_count:1,latest_plan:{version:1},profile:{...fresh.profile,xp:70}};
  const journey=welcomeJourney(state);const before=JSON.stringify(journey);
  const stages=trailMilestones(journey);
  assert.deepEqual(stages.map(stage=>stage.id),['quests','confirm','worlds','roadmap','reflect']);
  assert.equal(JSON.stringify(journey),before);
  assert.equal(journey.action.id,'reflect');
  assert.equal(state.profile.xp,70);
});
