import test from 'node:test';
import assert from 'node:assert/strict';
import {discoveryEditor,emptyDiscoveryEditor} from '../src/discoveryEditor.js';
import {discoveryJourney} from '../src/discoveryJourney.js';

test('explicit edit prefills the saved answer; cancelling a changed draft restores the persisted choice',()=>{
 const event={id:'saved-quest',payload:{quest:0,choice:'Build a mini-app',interest:'technology'}};
 const backend={profile:{xp:70},confirmed:true,quest_answers:[event]};
 const quests=[{title:'Discover',options:{'Build a mini-app':'technology','Sketch an invention':'art'}}];
 const before=JSON.stringify(backend);
 let editor=discoveryEditor(emptyDiscoveryEditor,{type:'edit',choice:event.payload.choice});
 assert.equal(editor.draft,'Build a mini-app');assert.equal(editor.editing,true);
 editor=discoveryEditor(editor,{type:'choose',choice:'Sketch an invention'});
 assert.equal(editor.draft,'Sketch an invention');
 editor=discoveryEditor(editor,{type:'cancel'});
 assert.equal(editor.editing,false);assert.equal(editor.draft,'');
 assert.equal(discoveryJourney(backend,quests).steps[0].choice,'Build a mini-app');
 assert.equal(JSON.stringify(backend),before);assert.equal(backend.confirmed,true);assert.equal(backend.profile.xp,70);
});
test('a successful save clears only the local draft; the next rendered answer is the backend response',()=>{
 let editor=discoveryEditor(emptyDiscoveryEditor,{type:'edit',choice:'Build a mini-app'});
 editor=discoveryEditor(editor,{type:'choose',choice:'Sketch an invention'});
 editor=discoveryEditor(editor,{type:'reset'});
 assert.deepEqual(editor,emptyDiscoveryEditor);
 assert.equal(Object.hasOwn(editor,'xp'),false);assert.equal(Object.hasOwn(editor,'confirmed'),false);
});
