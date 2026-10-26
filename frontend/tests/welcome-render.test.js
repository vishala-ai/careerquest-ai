import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdtemp,mkdir,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

// Render the actual JSX with the existing Vite/esbuild toolchain, without a browser.
const root=fileURLToPath(new URL('../',import.meta.url));
const cache=join(root,'node_modules','.cache');
await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'welcome-render-'));
let components;
try {
  const output=join(directory,'components.cjs');
  await build({stdin:{contents:"export {default as ExplorerSelection} from './src/components/ExplorerSelection.jsx'; export {default as Welcome} from './src/pages/Welcome.jsx'; export {default as AppShell} from './src/components/AppShell.jsx';",resolveDir:root},outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});
  components=(await import(pathToFileURL(output).href)).default;
} finally {await rm(directory,{recursive:true,force:true});}
const noop=()=>{};
const fresh={profile:{id:'fictional-render',alias:'Render Demo',grade:11,xp:20},quest_count:1,quest_complete:false,confirmed:false};
const confirmed={...fresh,quest_count:3,quest_complete:true,confirmed:true};
const saved={...confirmed,research_count:1,latest_plan:{version:1}};

for(const [name,state] of [
  ['partial quests',fresh],['confirmed profile',confirmed],
  ['saved roadmap',saved],['reconfirmation',{...saved,confirmed:false,profile_preferences:{interests:['science']},profile_draft:{version:2}}],
]) test(`${name}: one trail CTA, no hero navigation, and Switch Explorer only in the header`,()=>{
  const content=React.createElement(components.Welcome,{state,onNavigate:noop,onCreate:noop});
  const html=renderToStaticMarkup(React.createElement(components.AppShell,{page:'welcome',state,avatar:'🧭',onNavigate:noop},content));
  const start=html.indexOf('<section class="welcome-intro"');
  assert.notEqual(start,-1);
  const hero=html.slice(start,html.indexOf('</section>',start));
  assert.doesNotMatch(hero,/<button\b|<a\b/);
  assert.equal((html.match(/class="trail-primary"/g)||[]).length,1);
  assert.equal((html.match(/Switch Explorer/g)||[]).length,state?1:0);
  if(state) assert.ok(html.indexOf('Switch Explorer')<start);

});

test('other-page headers expose the profile menu and four primary destinations',()=>{
  const html=renderToStaticMarkup(React.createElement(components.AppShell,{page:'worlds',state:confirmed,avatar:'🧭',onNavigate:noop}));
  assert.match(html,/class="identity-menu"/);
  assert.match(html,/aria-label="Main navigation"/);
  assert.match(html,/Switch Explorer/);assert.doesNotMatch(html,/welcome-header-switch/);assert.equal((html.match(/aria-current="page"/g)||[]).length,1);
});

const justCreated={profile:{id:'fictional-created',alias:'Orbit Demo',grade:10,xp:0},quest_count:0,quest_complete:false,confirmed:false};
test('first-time setup includes avatars explicit grade and fictional acknowledgment before creation',()=>{
  const html=renderToStaticMarkup(React.createElement(components.Welcome,{state:null,onCreate:noop,onNavigate:noop}));
  assert.match(html,/WELCOME TO CAREERQUEST AI/);
  assert.match(html,/Your next chapter starts with curiosity/);
  assert.equal((html.match(/type="radio"/g)||[]).length,6);
  assert.match(html,/type="checkbox" required/);
  assert.match(html,/Choose your grade/);
  assert.match(html,/Before you start/);
  assert.equal((html.match(/<select\b/g)||[]).length,1);
  assert.match(html,/Create My Explorer/);
  assert.doesNotMatch(html,/Start My First Quest|class="student-trail"|Explorer Points earned/);
});
test('successful backend creation shows Welcome aboard and a single First Mission CTA with zero saved points',()=>{
  const html=renderToStaticMarkup(React.createElement(components.Welcome,{state:justCreated,createdProfileId:justCreated.profile.id,onNavigate:noop}));
  assert.match(html,/Welcome aboard, Orbit Demo!/);
  assert.match(html,/FIRST MISSION/);
  assert.match(html,/Discover Your Spark/);
  assert.equal((html.match(/Start My First Quest/g)||[]).length,1);
  assert.match(html,/0 Explorer Points earned/);
  assert.doesNotMatch(html,/Create My Explorer|class="student-trail"/);
});
test('reload with a saved explorer shows returning Home and its one Trail CTA',()=>{
  const html=renderToStaticMarkup(React.createElement(components.Welcome,{state:justCreated,onNavigate:noop}));
  assert.match(html,/Hi, Orbit Demo! 👋/);
  assert.equal((html.match(/class="trail-primary"/g)||[]).length,1);
  assert.doesNotMatch(html,/Create My Explorer|Welcome aboard|FIRST MISSION/);
});
test('creation acknowledgement handles a missing saved nickname gracefully',()=>{
  const state={...justCreated,profile:{...justCreated.profile,alias:''}};
  const html=renderToStaticMarkup(React.createElement(components.Welcome,{state,createdProfileId:state.profile.id,onNavigate:noop}));
  assert.match(html,/Welcome aboard, explorer!/);
  assert.doesNotMatch(html,/undefined|null/);
});
test('loading and errors never expose an accidental creation form',()=>{
  const loading=renderToStaticMarkup(React.createElement(components.Welcome,{state:null,loading:true}));
  const error=renderToStaticMarkup(React.createElement(components.Welcome,{state:null,error:'Synthetic connection error',onRetry:noop}));
  assert.match(loading,/role="status"/);
  assert.match(error,/role="alert"/);
  assert.match(error,/Try again/);
  assert.doesNotMatch(loading+error,/Create My Explorer|<form\b/);
});

test('saved explorers without an active selection show a choice, not the setup or saved names',()=>{
 const html=renderToStaticMarkup(React.createElement(components.Welcome,{state:null,explorers:[{id:'saved',alias:'Hidden saved name'}],onExplorerChoice:noop}));
 assert.match(html,/Continue My Adventure/);assert.match(html,/Create a New Explorer/);assert.doesNotMatch(html,/<form|Hidden saved name|class="student-trail"/);
});
test('unselected header omits student identity points and personalized navigation',()=>{
 const html=renderToStaticMarkup(React.createElement(components.AppShell,{page:'welcome',state:null,onNavigate:noop}));
 assert.match(html,/CareerQuest AI Home/);assert.doesNotMatch(html,/Explorer Points|Student profile|Main navigation|Grade/);
});

for(const view of ['switch','create','saved'])test(`explorer selection ${view} keeps saved profiles separate and never prefills a new explorer`,()=>{
 const html=renderToStaticMarkup(React.createElement(components.ExplorerSelection,{view,explorers:[{id:'local',alias:'Fictional Saved',grade:12}],pid:'local',onCreate:noop,onSelect:noop,onView:noop}));
 if(view==='saved'){assert.doesNotMatch(html,/<form/);assert.match(html,/Fictional Saved/);}
 else{
 const form=html.slice(html.indexOf('<form'),html.indexOf('</form>'));
 assert.match(form,/value=""/);assert.match(form,/<option value="" disabled="" selected=""/);assert.doesNotMatch(form,/Fictional Saved|value="12" selected/);assert.match(form,/type="checkbox" required=""/);
 if(view==='create')assert.doesNotMatch(html,/Fictional Saved/);
 }
});

test('switch view provides a visible keyboard-accessible return to Welcome without deleting explorers',()=>{
 const html=renderToStaticMarkup(React.createElement(components.ExplorerSelection,{view:'switch',explorers:[{id:'saved',alias:'Fictional Saved',grade:10}],pid:'saved',onCreate:noop,onSelect:noop,onView:noop,onWelcome:noop}));
 assert.match(html,/<button[^>]*aria-describedby="welcome-return-help"[^>]*> Back to Welcome<\/button>/);assert.match(html,/Your saved explorers and progress stay available/);assert.match(html,/Fictional Saved/);
});
