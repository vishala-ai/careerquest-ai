import test from 'node:test';
import assert from 'node:assert/strict';
import {welcomeMode} from '../src/welcomeMode.js';
const saved={profile:{id:'fictional-new',alias:'Nova',grade:11,xp:0},quest_count:0,quest_complete:false};

test('a client receipt cannot create an explorer without a backend profile response',()=>{
  assert.equal(welcomeMode(null,'fictional-new'),'setup');
});
test('only the newly saved backend explorer receives the transient aboard state',()=>{
  assert.equal(welcomeMode(saved,saved.profile.id),'aboard');
  assert.equal(welcomeMode(saved,'different-explorer'),'returning');
});
test('reload and existing backend progress always use returning Home',()=>{
  assert.equal(welcomeMode(JSON.parse(JSON.stringify(saved))),'returning');
  assert.equal(welcomeMode({...saved,quest_count:1},saved.profile.id),'returning');
  assert.equal(welcomeMode({...saved,quest_count:3,quest_complete:true,confirmed:true},saved.profile.id),'returning');
});
