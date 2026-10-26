import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {studentExperience,primaryDestination} from '../src/studentExperience.js';
import {welcomeHero} from '../src/welcomeHero.js';
import {trailMilestones} from '../src/studentTrail.js';
const root=fileURLToPath(new URL('../',import.meta.url)),cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const dir=await mkdtemp(join(cache,'home-header-'));let Shell,Welcome;
try{const outfile=join(dir,'components.cjs');await build({stdin:{contents:"export {default as Shell} from './src/components/AppShell.jsx';export {default as Welcome} from './src/pages/Welcome.jsx';",resolveDir:root},outfile,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});const m=(await import(pathToFileURL(outfile).href)).default;Shell=m.Shell;Welcome=m.Welcome;}finally{await rm(dir,{recursive:true,force:true});}
const fresh={profile:{id:'fictional-home',alias:'Aster Fictional',grade:10,xp:0},quest_count:0,quest_complete:false,confirmed:false,profile_version:1,research_count:0};
const discovered={...fresh,quest_count:3,quest_complete:true};
const confirmed={...discovered,confirmed:true,profile:{...fresh.profile,xp:70},profile_preferences:{interests:['art']}};
const research={confirmed:true,profile_context:{profile_version:1},portfolio:{explorations:[{id:'research'}],shortlist:[]},portfolio_completion:{ready:false,active:null,history:[]},path_preferences:{history:[]}};
const ready={...research,portfolio:{...research.portfolio,shortlist:[{world_id:'design',exploration:{is_stale:false}}]},portfolio_completion:{ready:true,active:null,history:[]},next_action:{kind:'view_portfolio'}};
const saved={...ready,portfolio_completion:{ready:true,active:{id:'portfolio-1',is_stale:false},history:[{id:'portfolio-1'}]}};
const home=(state,career=null)=>{const experience=studentExperience(state,career);return renderToStaticMarkup(React.createElement(Shell,{state,career,page:'welcome',onNavigate:()=>{}},React.createElement(Welcome,{state,experience,onNavigate:()=>{}})));};
const hero=(state,career=null)=>welcomeHero(state,3,studentExperience(state,career));
test('shared header has exactly one four-item primary menu and no progress-strip navigation',()=>{
 for(const page of ['welcome','quests','confirm','worlds','portfolio']){const html=renderToStaticMarkup(React.createElement(Shell,{state:confirmed,career:saved,page,careerScreen:page==='portfolio'?'portfolio':'worlds',onNavigate:()=>{}}));assert.equal((html.match(/<nav\b/g)||[]).length,1);assert.doesNotMatch(html,/Adventure progress|stage-progress/);const menu=html.match(/<nav[^]*?<\/nav>/)[0];for(const label of ['Home','Discover','Explore Careers','My Portfolio'])assert.ok(menu.includes(label));assert.doesNotMatch(menu,/Celebrate|Confirm|My Roadmap|My Journey/);}
});
test('only actual destinations are highlighted; profile and synthetic switcher have no false Home selection',()=>{
 assert.equal(primaryDestination('welcome'),'welcome');assert.equal(primaryDestination('quests'),'quests');assert.equal(primaryDestination('worlds','worlds'),'worlds');assert.equal(primaryDestination('portfolio','portfolio'),'portfolio');
 for(const page of ['confirm','profiles','journey','roadmap'])assert.equal(primaryDestination(page),null);
 for(const screen of ['milestone','portfolio'])assert.equal(primaryDestination('worlds',screen),'portfolio');
});
test('new partial and unconfirmed states use saved counts and profile gates',()=>{
 assert.equal(hero(fresh).phase,'new');assert.equal(hero({...fresh,quest_count:1}).phase,'partial');assert.match(hero({...fresh,quest_count:1}).message,/1 of 3/);assert.equal(hero(discovered).phase,'review');
 assert.equal(studentExperience({...fresh,quest_count:1}).action.label,'Continue Quest 2');assert.equal(studentExperience(discovered).action.id,'confirm');assert.ok(studentExperience(discovered).stages.find(s=>s.id==='worlds').locked);
});
test('confirmed research and portfolio-ready messages correspond to persisted backend state',()=>{
 assert.equal(hero(confirmed).phase,'research_ready');assert.equal(hero({...confirmed,research_count:1},research).phase,'research');assert.equal(hero({...confirmed,research_count:1},ready).phase,'ready');assert.match(hero(confirmed,ready).message,/Career Discovery Portfolio/);
});
test('current portfolio uses an accurate greeting and four completed stages without recommendations',()=>{
 const result=studentExperience(confirmed,saved),html=home(confirmed,saved);assert.equal(result.finished,true);assert.equal(result.journey.complete,true);assert.equal(hero(confirmed,saved).title,'Hi, Aster Fictional! Your career portfolio is ready.');assert.match(html,/brought together your interests and career choices/);
 assert.equal((html.match(/\bis-completed\b/g)||[]).length,4);assert.doesNotMatch(html,/Recommended Next|Previously completed|Your Next Adventure|is-recommended/);assert.match(html,/Portfolio saved\./);assert.equal((html.match(/class="trail-primary"/g)||[]).length,1);assert.equal((html.match(/class="trail-revisit"/g)||[]).length,3);
 const milestone=trailMilestones(result.journey).find(s=>s.id==='celebrate');assert.equal(milestone.target,'portfolio');assert.equal(milestone.actionLabel,'View My Portfolio');assert.equal(milestone.status,'Completed');
});
test('earlier saved portfolio is not represented as current after career choices change',()=>{
 const changed={...saved,portfolio_completion:{ready:true,active:null,history:[{id:'portfolio-1'}]}};const result=studentExperience(confirmed,changed),html=home(confirmed,changed);
 assert.equal(result.finished,false);assert.equal(hero(confirmed,changed).phase,'changed');assert.match(html,/earlier career portfolio stays saved/);assert.doesNotMatch(html,/Your career portfolio is ready\./);assert.equal((html.match(/\bis-recommended\b/g)||[]).length,1);assert.match(html,/Earlier portfolio saved/);assert.doesNotMatch(html,/Previously completed/);
});
test('changed profile keeps historical stages revisitable and explicitly requests reconfirmation',()=>{
 const state={...confirmed,confirmed:false,profile_version:2},career={...saved,confirmed:false,profile_context:null,portfolio_completion:{ready:false,active:null,history:[{id:'portfolio-1'}]}};const result=studentExperience(state,career),stages=trailMilestones(result.journey);
 assert.equal(result.action.id,'confirm');assert.match(hero(state,career).message,/updated Explorer Profile.*review/);for(const id of ['worlds','celebrate'])assert.equal(stages.find(s=>s.id===id).locked,false);assert.equal(stages.find(s=>s.id==='celebrate').target,'portfolio');assert.match(home(state,career),/Profile Needs Review/);
});
test('stale or mismatched active portfolio data cannot claim the current portfolio is ready',()=>{
 for(const [state,career] of [[{...confirmed,confirmed:false},saved],[confirmed,{...saved,profile_context:{profile_version:2}}],[confirmed,{...saved,portfolio_completion:{...saved.portfolio_completion,active:{id:'old',is_stale:true}}}]]){assert.equal(studentExperience(state,career).finished,false);assert.doesNotMatch(hero(state,career).title,/portfolio is ready/);}
});
test('legacy roadmap reflection fields never control the Home message',()=>{
 for(const career of [null,research,ready,saved]){const state={...confirmed,latest_plan:{version:99},reflection_count:100};assert.doesNotMatch(hero(state,career).title+' '+hero(state,career).message,/roadmap|reflection/i);}
});
test('returning hero remains informational with one dominant action inside the Home trail',()=>{
 for(const [state,career] of [[fresh,null],[{...fresh,quest_count:1},null],[discovered,null],[confirmed,research],[confirmed,ready],[confirmed,saved]]){const html=home(state,career),intro=html.match(/<section class="welcome-intro"[^]*?<\/section>/)[0];assert.doesNotMatch(intro,/<button|<a\b/);assert.equal((html.match(/class="trail-primary"/g)||[]).length,1);}
});
test('full trail appears only on Home; profile menu remains available on other pages',()=>{
 const html=renderToStaticMarkup(React.createElement(Shell,{state:confirmed,career:saved,page:'worlds',onNavigate:()=>{}}));assert.doesNotMatch(html,/student-trail/);assert.match(html,/Explorer Profile/);assert.match(html,/Switch Explorer/);assert.match(home(confirmed,saved),/trail-confirm/);
});
test('long saved nickname is escaped and remains fully accessible without fabricated metadata',()=>{
 const nickname='FictionalExplorerOfManyBrightPossibilities';const state={...fresh,profile:{...fresh.profile,alias:nickname}};const html=home(state);assert.ok(html.includes(`Student profile: ${nickname}, Grade 10`));assert.match(html,/<strong>0<\/strong> Explorer Points/);assert.ok(html.includes(`Hi, ${nickname}!`));assert.equal(hero(null).grade,null);assert.equal(hero(null).points,null);
});
test('projection and repeated renders cannot mutate XP selections or portfolio history',()=>{
 const before=JSON.stringify({confirmed,saved});for(let i=0;i<3;i++){home(confirmed,saved);studentExperience(confirmed,saved);hero(confirmed,saved);}assert.equal(JSON.stringify({confirmed,saved}),before);
});
test('trail colors control sizes focus and reduced motion are explicit',async()=>{
 const css=await readFile(join(root,'src/components/student-trail.css'),'utf8');for(const color of ['#6D28D9','#0F766E','#1D4ED8','#065F46','#FBBF24','#17213D'])assert.ok(css.includes(color));assert.match(css,/background:#fff/);assert.match(css,/width:104px;height:104px/);assert.match(css,/min-height:48px/);assert.match(css,/grid-template-columns:72px minmax\(0,1fr\)/);assert.match(css,/focus-visible/);assert.match(css,/prefers-reduced-motion:reduce/);
});
test('shared header measures its own height without resetting scroll and adapts for short zoomed viewports',async()=>{
 const source=await readFile(join(root,'src/components/AppShell.jsx'),'utf8'),css=await readFile(join(root,'src/components/global-ui.css'),'utf8');assert.match(source,/ResizeObserver/);assert.doesNotMatch(source,/scrollTo|StageProgress/);assert.match(css,/var\(--header-offset/);assert.match(css,/@media\(max-height:500px\)/);assert.match(css,/max-width:1160px/);assert.match(css,/text-overflow:ellipsis/);
});
test('saturated trail buttons and gold completion action meet normal-text contrast',async()=>{
 const css=await readFile(join(root,'src/components/student-trail.css'),'utf8');
 const lightness=hex=>{const values=hex.match(/\w\w/g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*values[0]+.7152*values[1]+.0722*values[2];};
 const contrast=(a,b)=>{const [hi,lo]=[lightness(a),lightness(b)].sort((a,b)=>b-a);return (hi+.05)/(lo+.05);};
 const palette=[...css.matchAll(/--stop-color:#([A-Fa-f0-9]{6})/g)].map(match=>match[1]);assert.equal(new Set(palette).size,4);
 for(const color of palette)assert.ok(contrast('ffffff',color)>=4.5,color);
 assert.ok(contrast('17213D','FBBF24')>=4.5);
});
