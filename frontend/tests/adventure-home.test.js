import test from 'node:test';
import assert from 'node:assert/strict';
import {adventureHome} from '../src/adventureHome.js';
const profile={id:'fictional-home',alias:'Orbit',grade:10,xp:0,interests:[]};
const fresh={profile,quest_count:0,quest_complete:false,confirmed:false,research_count:0,latest_plan:null};
const reviewed={...fresh,quest_count:3,quest_complete:true};
const confirmed={...reviewed,confirmed:true,profile_preferences:{interests:['technology']},confirmation_version:1};
const explored={...confirmed,research_count:1};
const planned={...explored,latest_plan:{version:2,content:{activities:['Try a project']}}};

test('all Adventure Home mission transitions follow backend state',()=>{
  for(const [state,id,label] of [
    [null,'profiles','Create My Explorer'],[fresh,'quests','Continue Quests'],
    [{...fresh,quest_count:2},'quests','Continue Quests'],
    [reviewed,'confirm','Review My Profile'],[confirmed,'worlds','Explore Career Worlds'],
    [explored,'roadmap','Build My Roadmap'],[planned,'journey','My Journey'],
    [{...planned,confirmed:false,profile_draft:{version:2}},'confirm','Review Updated Profile'],
  ]) {
    const home=adventureHome(state);
    assert.equal(home.mission.id,id);
    assert.equal(home.mission.label,label);
    assert.equal(home.stages.filter(stage=>stage.current).length,1);
  }
});
test('saved roadmap leads to My Journey even without earlier career research',()=>{
  assert.equal(adventureHome({...confirmed,latest_plan:planned.latest_plan}).mission.id,'journey');
});
test('new visitor and missing, blank or whitespace nickname use a neutral greeting',()=>{
  assert.equal(adventureHome(null).greeting,'Hi, explorer!');
  for(const alias of [undefined,null,'','   ']) assert.equal(adventureHome({...fresh,profile:{...profile,alias}}).greeting,'Hi, explorer!');
  assert.equal(adventureHome({...fresh,profile:{...profile,alias:' Orbit '}}).greeting,'Hi Orbit!');
});
test('returning explorer resumes the first incomplete quest from saved count',()=>{
  for(let count=0;count<3;count++) {
    const restored=JSON.parse(JSON.stringify({...fresh,quest_count:count}));
    assert.equal(adventureHome(restored).mission.questIndex,count);
    assert.match(adventureHome(restored).mission.title,new RegExp(`Quest ${count+1}`));
  }
});
test('read-only home and revisits do not mutate backend progress or grant XP',()=>{
  const restored=structuredClone(planned);restored.profile.xp=80;
  const before=JSON.stringify(restored);
  for(let i=0;i<4;i++) {
    const home=adventureHome(restored);
    assert.equal(home.xp,80);
    assert.equal(home.grade,10);
    assert.ok(home.stages.filter(stage=>stage.done).every(stage=>!stage.locked));
  }
  assert.equal(JSON.stringify(restored),before);
});
test('an edited profile locks personalized map steps despite saved historical work',()=>{
  const home=adventureHome({...planned,confirmed:false,profile_draft:{version:2}});
  assert.equal(home.mission.label,'Review Updated Profile');
  for(const id of ['worlds','roadmap']) assert.equal(home.stages.find(stage=>stage.id===id).locked,true);
  assert.equal(home.stages.find(stage=>stage.id==='roadmap').done,true);
  assert.equal(home.stages.find(stage=>stage.id==='quests').locked,false);
});
test('failed research never counts as saved exploration, and proposals are not saved roadmaps',()=>{
  assert.equal(adventureHome({...confirmed,last_research:{status:'blocked'}}).mission.id,'worlds');
  assert.equal(adventureHome({...explored,proposal:{plan:{}}}).mission.id,'roadmap');
});
