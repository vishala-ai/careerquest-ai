import test from 'node:test';
import assert from 'node:assert/strict';
import {availableExplorers,creationRequest,finishCreation,setupProblems,leaveExplorer} from '../src/explorerSetup.js';
import {welcomeMode} from '../src/welcomeMode.js';
const valid={nickname:' Fictional Orbit ',grade:'10',fictional:true,avatar:'🚀'};
const storage=()=>{const items=new Map();return {getItem:key=>items.get(key)||null,setItem:(key,value)=>items.set(key,value),removeItem:key=>items.delete(key)};};
test('all four entry states are distinct without automatic explorer selection',()=>{
 assert.equal(welcomeMode(null),'setup');assert.equal(welcomeMode(null,'',[{id:'saved'}]),'choose');
 assert.equal(welcomeMode({profile:{id:'active'},quest_count:1},'',[{id:'other'}]),'returning');
 // Explicit switching remains a separate existing page, independent of Home mode.
 assert.equal(welcomeMode({profile:{id:'active'},quest_count:0},'active'),'aboard');
});
test('nickname grade and fictional acknowledgement are required',()=>{
 assert.equal(setupProblems({}).length,3);assert.equal(setupProblems(valid).length,0);
 for(const change of [{nickname:'  '},{grade:''},{grade:'8'},{fictional:false}])assert.ok(setupProblems({...valid,...change}).length);
});
test('lost response retry and reload retain the same request identity',()=>{
 const saved=storage();let count=0;const key=()=>`key-${++count}`;
 const first=creationRequest(valid,saved,key);const reloaded=creationRequest(JSON.parse(JSON.stringify(valid)),saved,key);
 assert.deepEqual(first,reloaded);assert.equal(count,1);assert.equal(first.alias,'Fictional Orbit');assert.equal(first.fictional_ack,true);
 assert.ok(!('avatar' in first));assert.ok(!('xp' in first));assert.ok(!('confirmed' in first));
 finishCreation(saved);assert.notEqual(creationRequest(valid,saved,key).creation_key,first.creation_key);
});
test('invalid form never stores a receipt, changed setup gets a new identity',()=>{
 const saved=storage();let count=0;const key=()=>`key-${++count}`;
 assert.throws(()=>creationRequest({...valid,grade:''},saved,key));assert.equal(count,0);
 const first=creationRequest(valid,saved,key);assert.notEqual(creationRequest({...valid,nickname:'Another Fictional'},saved,key).creation_key,first.creation_key);
});
test('only remembered IDs are checked and backend saved identity refreshes local metadata',async()=>{
 const calls=[],remembered=[{id:'a',alias:'old',avatar:'🌱'},{id:'missing'}];
 const result=await availableExplorers(remembered,async id=>{calls.push(id);if(id==='missing')throw {status:404};return {profile:{id,alias:'Fictional Saved',grade:12}};});
 assert.deepEqual(calls,['a','missing']);assert.deepEqual(result,[{id:'a',alias:'Fictional Saved',grade:12,avatar:'🌱'}]);assert.equal(remembered[0].alias,'old');
});
test('unavailable backend cannot be mistaken for a fresh session',async()=>{
 await assert.rejects(()=>availableExplorers([{id:'known'}],async()=>{throw new Error('Unavailable');}),/Unavailable/);
});

test('explicit Back to Welcome clears only the active selection and preserves remembered explorers and retries',()=>{
 const saved=storage();saved.setItem('cq_pid','existing-explorer');saved.setItem('cq_explorers',JSON.stringify([{id:'existing-explorer',alias:'Fictional Saved'}]));saved.setItem('cq_pending_creation','unchanged-receipt');
 leaveExplorer(saved);assert.equal(saved.getItem('cq_pid'),null);assert.deepEqual(JSON.parse(saved.getItem('cq_explorers')),[{id:'existing-explorer',alias:'Fictional Saved'}]);assert.equal(saved.getItem('cq_pending_creation'),'unchanged-receipt');
 leaveExplorer(saved);assert.equal(welcomeMode(null,'',JSON.parse(saved.getItem('cq_explorers'))),'choose');
});
