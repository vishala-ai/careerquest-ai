import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {studentExperience,primaryDestination,activeStage} from '../src/studentExperience.js';
const root=fileURLToPath(new URL('../',import.meta.url)),cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'global-ui-'));let Shell,Welcome,PRIMARY_PAGES;
try{const output=join(directory,'components.cjs');await build({stdin:{contents:"export {default as Shell,PRIMARY_PAGES} from './src/components/AppShell.jsx'; export {default as Welcome} from './src/pages/Welcome.jsx';",resolveDir:root},outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});const m=(await import(pathToFileURL(output).href)).default;Shell=m.Shell;Welcome=m.Welcome;PRIMARY_PAGES=m.PRIMARY_PAGES;}finally{await rm(directory,{recursive:true,force:true});}
const fresh={profile:{id:'fictional-global',alias:'Ari Fictional',grade:11,xp:0},quest_count:0,quest_complete:false,confirmed:false,profile_version:1,research_count:0};
const confirmed={...fresh,quest_count:3,quest_complete:true,confirmed:true,profile:{...fresh.profile,xp:70},profile_preferences:{interests:['art']}};
const career={confirmed:true,profile_context:{profile_version:1},portfolio:{explorations:[],shortlist:[]},path_preferences:{history:[]},portfolio_completion:{active:null,history:[]}};
const selection={world_id:'design',exploration:{is_stale:false}};
const eligible={...career,portfolio:{explorations:[{id:'notes'}],shortlist:[selection]}};
const completed={...eligible,portfolio_completion:{active:{id:'completed'},history:[{id:'completed'}]}};
const shell=(state=fresh,extra={},children)=>renderToStaticMarkup(React.createElement(Shell,{page:'welcome',state,career:null,onNavigate:()=>{},...extra},children));
test('exactly four primary destinations retain the existing worlds ID',()=>{
 assert.deepEqual(PRIMARY_PAGES.map(([id,label])=>[id,label]),[['welcome','Home'],['quests','Discover'],['worlds','Explore Careers'],['portfolio','My Portfolio']]);
 const html=shell();const navigation=html.match(/<nav class="global-navigation"[^]*?<\/nav>/)[0];assert.equal((navigation.match(/<button/g)||[]).length,4);assert.doesNotMatch(navigation,/My Roadmap|My Journey|Explorer Profile|Celebrate/);
});
test('Home keeps shared identity with one navigation and no global progress strip',()=>{
 const html=shell();assert.match(html,/Ari Fictional/);assert.match(html,/Grade 11/);assert.match(html,/Explorer Points/);assert.doesNotMatch(html,/Adventure progress|stage-progress/);assert.match(html,/Home/);
});
test('identity menu exposes profile switching and secondary saved activities',()=>{
 const html=shell(confirmed,{page:'worlds',career});for(const text of ['Student profile: Ari Fictional, Grade 11','Explorer Profile','Switch Explorer','Earlier saved activities','My Roadmap','My Journey'])assert.ok(html.includes(text),text);assert.match(html,/<details class="identity-menu"/);
});
test('zero XP is real and missing identity/points have neutral noninvented fallbacks',()=>{
 assert.match(shell(),/<strong>0<\/strong> Explorer Points/);const unknown=shell(null);assert.doesNotMatch(unknown,/Explorer Points|Main navigation|Student profile/);assert.doesNotMatch(unknown,/Grade 11/);assert.match(shell({...fresh,profile:{...fresh.profile,alias:''}}),/Student profile: Explorer/);
});
test('XP explanation is accessible through native details and a described summary',()=>{
 const html=shell();assert.match(html,/<details class="xp-badge"><summary aria-describedby="[^"]+"/);assert.match(html,/Explorer Points \(XP\) mark saved activity/);assert.match(html,/do not measure ability, grades or career fit/);
});
test('new and partial students have four honest stages and resume saved quest count',()=>{
 const empty=studentExperience(null);assert.equal(empty.stages.length,4);assert.ok(empty.stages.every(s=>!s.done));assert.equal(empty.action.id,'profiles');
 const partial=studentExperience({...fresh,quest_count:1});assert.equal(partial.action.label,'Continue Quest 2');assert.equal(partial.stages[0].description,'1 of 3 discovery quests saved.');assert.ok(partial.stages.slice(1).every(s=>s.locked));
});
test('confirmation and career research recommendation follow saved data',()=>{
 assert.equal(studentExperience({...fresh,quest_count:3,quest_complete:true}).action.id,'confirm');assert.equal(studentExperience(confirmed,career).action.id,'worlds');
 const ready=studentExperience(confirmed,eligible);assert.equal(ready.action.id,'celebrate');assert.equal(ready.action.target,'celebrate');assert.equal(ready.stages[2].done,true);
});
test('completed portfolio points Home directly at saved portfolio and remains revisitable',()=>{
 const ready=studentExperience(confirmed,completed);assert.equal(ready.action.label,'View My Portfolio');assert.equal(ready.action.target,'portfolio');assert.ok(ready.stages.every(s=>s.done&&!s.locked));
});
test('profile change names review requirement and keeps historical Explore/Celebrate accessible',()=>{
 const changed={...confirmed,confirmed:false,profile_draft:{version:2},profile_version:2};
 const historical={...completed,confirmed:false,profile_context:null,portfolio:{...completed.portfolio,shortlist:[{...selection,exploration:{is_stale:true}}]},portfolio_completion:{active:null,history:[{id:'old'}]}};
 const result=studentExperience(changed,historical);assert.equal(result.needsReview,true);assert.equal(result.action.id,'confirm');assert.equal(result.stages[1].status,'Profile Needs Review');for(const i of [2,3])assert.ok(result.stages[i].done&&!result.stages[i].locked);
 assert.match(shell(changed,{page:'confirm',career:historical}),/Profile Needs Review/);
});
test('stale parent/child confirmation or version cannot visually unlock personalization',()=>{
 assert.equal(studentExperience({...confirmed,confirmed:false},career).confirmed,false);assert.equal(studentExperience(confirmed,{...career,confirmed:false}).confirmed,false);assert.equal(studentExperience(confirmed,{...career,profile_context:{profile_version:2}}).confirmed,false);
});
test('unknown career progress never invents completion or a permanent lock',()=>{
 const data=studentExperience(confirmed,null);const stage=data.stages[3];assert.equal(stage.done,false);assert.equal(stage.locked,false);assert.equal(stage.status,'Open saved progress');
});
test('milestone and saved portfolio share My Portfolio navigation and Celebrate stage',()=>{
 for(const page of ['worlds','portfolio'])for(const screen of ['milestone','portfolio']){assert.equal(primaryDestination(page,screen),'portfolio');assert.equal(activeStage(page,screen,studentExperience(confirmed,eligible)),'celebrate');}
 assert.equal(primaryDestination('confirm'),null);assert.equal(primaryDestination('worlds','worlds'),'worlds');assert.equal(primaryDestination('roadmap'),null);
});
test('actual Home trail has four stages and one primary action, never repeated in shell',()=>{
 const experience=studentExperience(confirmed,eligible);const home=React.createElement(Welcome,{state:confirmed,experience,onNavigate:()=>{},onCreate:()=>{}});const html=shell(confirmed,{career:eligible},home);
 assert.equal((html.match(/class="student-trail"/g)||[]).length,1);assert.equal((html.match(/class="trail-primary"/g)||[]).length,1);assert.match(html,/Discover, Confirm, Explore, Celebrate adventure trail/);assert.doesNotMatch(shell(confirmed,{page:'worlds',career}),/class="student-trail"/);
});
test('shell highlights only the actual primary page and does not mutate records',()=>{
 const before=JSON.stringify({confirmed,completed});const html=shell(confirmed,{page:'worlds',career:completed});assert.match(html,/aria-current="page"/);assert.doesNotMatch(html,/aria-current="step"/);assert.equal(JSON.stringify({confirmed,completed}),before);
});
test('shared typography layout and reduced motion have explicit rules',async()=>{
 const css=await readFile(join(root,'src/components/global-ui.css'),'utf8');assert.match(css,/max-width:1160px/);assert.match(css,/position:sticky;top:0/);assert.match(css,/font-size:36px/);assert.match(css,/font-size:28px/);assert.match(css,/@media\(prefers-reduced-motion:reduce\)/);assert.match(css,/animation:none!important;transition:none!important/);assert.match(css,/focus-visible/);
});
test('My Portfolio uses the same research component with read-model progress callbacks',async()=>{
 const app=await readFile(join(root,'src/App.jsx'),'utf8');assert.match(app,/page==='worlds'\|\|page==='portfolio'/);assert.match(app,/entry=\{careerEntry\}/);assert.match(app,/career-discovery/);assert.doesNotMatch(app,/from ['"]\.\/pages\/MyPortfolio/);
 const worlds=await readFile(join(root,'src/pages/CareerWorlds.jsx'),'utf8');assert.match(worlds,/onProgress\(value\)/);assert.match(worlds,/setScreen\(saved\?'portfolio':'milestone'\)/);
});
