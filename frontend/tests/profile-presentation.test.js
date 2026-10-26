import test from 'node:test';
import assert from 'node:assert/strict';
import {studentCorrection,isReconfirmation,manualProfileChanges} from '../src/profilePresentation.js';

test('known instructional correction becomes a student-friendly presentation without changing its source',()=>{
 const original='See if you have to revise the career goals';
 assert.equal(studentCorrection(original),'I’d like to revisit my goals as I explore.');
 assert.equal(original,'See if you have to revise the career goals');
 assert.equal(studentCorrection('For this fictional explorer, I prefer art.'),'I prefer art.');
 assert.equal(studentCorrection('My goal is to keep exploring.'),'My goal is to keep exploring.');
});
test('unknown notes are not given an invented interpretation',()=>{
 const note='Some instruction that is not a student preference';
 assert.match(studentCorrection(note),/You’ve shared what you would like to change/);
 assert.doesNotMatch(studentCorrection(note),/science|art|coding|career fit/);
 assert.equal(studentCorrection(''),'');
});
test('all three profile states are distinguished using backend records',()=>{
 assert.equal(isReconfirmation({quest_complete:true,confirmed:false,profile_preferences:null}),false);
 assert.equal(isReconfirmation({quest_complete:true,confirmed:true,profile_preferences:{version:4}}),false);
 assert.equal(isReconfirmation({quest_complete:true,confirmed:false,profile_preferences:{version:4},profile_draft:{version:5}}),true);
});
test('saved draft changes remain reconstructable after reload without modifying audit objects',()=>{
 const previous={interests:['science','art'],learning_style:'Hands-on projects',goal:'Explore',correction:'',not_sure:false};
 const updated={interests:['art','coding'],learning_style:'Creative activities',goal:'Try a mini-project',correction:'I prefer making things.',not_sure:false};
 const state={profile_preferences:previous,profile_draft:updated};const before=JSON.stringify(state);
 const result=manualProfileChanges(state,updated);
 assert.deepEqual(result.kept,['art']);assert.deepEqual(result.added,['coding']);assert.deepEqual(result.removed,['science']);
 assert.deepEqual(result.details.map(d=>d.field),['Preferred activities','Exploration goal']);
 assert.deepEqual(manualProfileChanges(JSON.parse(before),JSON.parse(before).profile_draft),result);
 assert.equal(JSON.stringify(state),before);
 assert.equal(manualProfileChanges({profile_preferences:previous,profile_draft:previous},previous),null);
});
test('legacy missing preferences do not produce undefined change descriptions',()=>{
 const state={profile_preferences:{interests:['art']},profile_draft:{interests:['art']}};
 const result=manualProfileChanges(state,{interests:['coding'],learning_style:'Hands-on projects',goal:'Explore',not_sure:false,correction:''});
 assert.deepEqual(result.details,[]);
});
