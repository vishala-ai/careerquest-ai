import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {studentExperience} from '../src/studentExperience.js';
import {orderedPortfolioCareers} from '../src/portfolioOrder.js';
const root=fileURLToPath(new URL('../',import.meta.url)),cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const dir=await mkdtemp(join(cache,'portfolio-flow-'));let Page,Snapshot,Paths;
try{const outfile=join(dir,'components.cjs');await build({stdin:{contents:"export {default as Page,PortfolioSnapshot as Snapshot} from './src/pages/CareerPortfolio.jsx'; export {default as Paths} from './src/pages/CareerPortfolioPaths.jsx';",resolveDir:root},outfile,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});const m=(await import(pathToFileURL(outfile).href)).default;Page=m.Page;Snapshot=m.Snapshot;Paths=m.Paths;}finally{await rm(dir,{recursive:true,force:true});}
const source={id:'bls-software',title:'Software developers',source:'BLS',url:'https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm',live_verified:false};
const career={world_id:'software',career_name:'Software Development',student_reason:'I want to try making a game.',world:{overview:{text:'Design and test applications.'},skills:[{text:'Programming',source_ids:[source.id]}]},sources:[source]};
const snapshot={schema_version:2,student:{id:'fictional',nickname:'Cedar Fictional',grade:10},explorer:{interests:['technology','art'],learning_style:'Hands-on projects',goal:'Try a mini-project'},story:{summary:'Cedar, your saved choices connect technology and art.',status:'deterministic_saved_choices'},paths:[{world_id:'software',priority:'primary'}],undecided:false,shortlist:[career],optional_mission:{text:'Sketch a fictional game screen.'}};
const preview={ready:true,signature:'real-saved-state-signature',preview:snapshot,active:null,history:[]};
const render=(props={})=>renderToStaticMarkup(React.createElement(Page,{completion:preview,confirmed:true,nickname:'Cedar Fictional',pid:'fictional',...props}));
test('portfolio preview has no path dropdowns or redundant save-path controls',()=>{
 const html=render();assert.doesNotMatch(html,/<select|Save Exploration Paths|Choose your Exploration Paths|<textarea/);assert.match(html,/Confirm &amp; Save My Portfolio/);assert.equal((html.match(/<button class="button\s*"/g)||[]).length,1);
});
test('visual portfolio contains saved identity interests story branches careers skills reasons and sources',()=>{
 const html=render();for(const text of ['Cedar Fictional','Grade 10','General interests','technology','My Discovery Story','My branching adventure map','Software Development','Programming','I want to try making a game.','Sketch a fictional game screen.','Supporting sources'])assert.ok(html.includes(text),text);
 assert.match(html,/href="#portfolio-source-software-bls-software"/);assert.match(html,/id="portfolio-source-software-bls-software"/);assert.match(html,/Not live verified/);assert.match(html,/Preview · Not saved/);
});
test('two saved priorities are displayed as choices rather than career rankings',()=>{
 const two={...snapshot,paths:[...snapshot.paths,{world_id:'design',priority:'secondary'}],shortlist:[career,{...career,world_id:'design',career_name:'Digital Product Design'}]};const html=render({completion:{...preview,preview:two}});
 assert.match(html,/Primary Exploration Path/);assert.match(html,/Secondary Exploration Path/);assert.match(html,/Digital Product Design/);assert.doesNotMatch(html,/best match|%|perfect fit|aptitude/i);
});
test('undecided snapshot is valid and never assigns a primary career',()=>{
 const html=render({completion:{...preview,preview:{...snapshot,undecided:true,paths:[]}}});assert.match(html,/I’m Still Exploring/);assert.match(html,/without a primary or secondary priority/);assert.doesNotMatch(html,/Primary Exploration Path|Secondary Exploration Path/);assert.match(html,/Confirm &amp; Save My Portfolio/);
});
test('saved view downloads the exact immutable version and has no confirmation or editing controls',()=>{
 const saved={id:'saved-version-1',version:1,snapshot,created_at:'2026-10-25',is_stale:false};const html=render({completion:{...preview,active:saved,history:[saved]}});
 assert.match(html,/Download PDF/);assert.match(html,/Create Updated Version/);assert.match(html,/versions\/saved-version-1\/pdf/);assert.match(html,/Saved by you/);assert.doesNotMatch(html,/Confirm &amp; Save My Portfolio|<select|<textarea/);assert.match(html,/View saved version 1/);
});
test('stale profile preserves readable history and offers upstream changes',()=>{
 const saved={id:'old',version:1,snapshot,created_at:'2026-10-25',is_stale:true};const html=render({confirmed:false,completion:{ready:false,preview:null,active:null,history:[saved]}});
 assert.match(html,/earlier saved version/);assert.match(html,/Cedar Fictional/);assert.match(html,/Download PDF/);assert.match(html,/Change my interests in Explorer Profile/);assert.match(html,/Change my careers or paths in Explore Careers/);assert.doesNotMatch(html,/Confirm &amp; Save My Portfolio/);
});
test('missing prerequisites offer recovery without fabricating preview fields',()=>{
 const html=render({completion:{ready:false,preview:null,active:null,history:[]}});assert.match(html,/Finish My Exploration Choices/);assert.doesNotMatch(html,/Grade 10|My Discovery Story|Confirm &amp; Save My Portfolio/);
 assert.match(render({confirmed:false,completion:null}),/Review My Explorer Profile/);
});
test('legacy final portfolios are read honestly without rebuilding old interests from today',()=>{
 const html=renderToStaticMarkup(React.createElement(Snapshot,{snapshot:{paths:[],shortlist:[{world_id:'software',career_name:'Software Development',sources:[source]}]},saved:true,version:1}));assert.match(html,/full Explorer Snapshot was not captured/);assert.match(html,/Software Development/);assert.doesNotMatch(html,/Grade 10|>technology<|>Programming</);
});
test('saved undecided preference resumes on Explore Careers without an automatic priority',()=>{
 const html=renderToStaticMarkup(React.createElement(Paths,{portfolio:{shortlist:[{world_id:'software',exploration:{is_stale:false,world:{title:'Software'}}}]},preferences:{active:{id:'undecided',undecided:true,paths:[],student_reasons:{}},history:[]},confirmed:true,context:{profile_version:1}}));
 assert.match(html,/I’m Still Exploring/);assert.match(html.match(/<input[^>]*value="undecided"[^>]*>/)[0],/checked=""/);assert.doesNotMatch(html,/<select/);assert.match(html,/No path priority assigned/);
});
test('Home recommends preference selection before Celebrate when required by backend',()=>{
 const state={profile:{id:'fictional',alias:'Cedar Fictional',grade:10,xp:70},quest_count:3,quest_complete:true,confirmed:true,profile_version:1,research_count:1};
 const careerState={confirmed:true,profile_context:{profile_version:1},portfolio:{explorations:[{}],shortlist:[{exploration:{is_stale:false}}]},next_action:{kind:'choose_paths'}};
 const result=studentExperience(state,careerState);assert.equal(result.action.id,'worlds');assert.equal(result.action.label,'Choose My Exploration Preferences');assert.equal(result.stages[3].locked,true);
});
test('student text is escaped and no unsupported story is called AI-generated',()=>{
 const html=render({completion:{...preview,preview:{...snapshot,shortlist:[{...career,student_reason:'<script>fictional</script>'}]}}});assert.match(html,/&lt;script&gt;fictional&lt;\/script&gt;/);assert.doesNotMatch(html,/<script>/);assert.match(html,/deterministic content is not live AI output/);
});
test('portfolio styling has readable vertical mobile branches and reduced motion',async()=>{
 const css=await readFile(join(root,'src/pages/career-portfolio.css'),'utf8');assert.match(css,/@media\(max-width:800px\)\{\.portfolio-branches\{grid-template-columns:1fr/);assert.match(css,/prefers-reduced-motion:reduce/);assert.match(css,/font-size:17px/);assert.match(css,/min-height:44px/);
});

test('portfolio only claims its saved completion receipt and never consumes previews or other milestones',async()=>{const source=await readFile(join(root,'src/pages/CareerWorlds.jsx'),'utf8');assert.match(source,/screen==='portfolio'&&!data\?\.portfolio_completion\?\.active/);assert.match(source,/screen==='entry'/);assert.match(source,/kind=portfolio_completed/);assert.match(source,/portfolio-celebration/);});

const shuffledCareers=[['environment','Environmental Science'],['design','Digital Product Design'],['software','Software Development'],['bioengineering','Biomedical Engineering']].map(([world_id,career_name])=>({...career,world_id,career_name}));
const orderedSnapshot={...snapshot,shortlist:shuffledCareers,paths:[{world_id:'design',priority:'secondary'},{world_id:'software',priority:'primary'}]};
test('preview and saved portfolio order map branches and career notes by saved primary secondary and other priorities',()=>{
 const before=JSON.stringify(orderedSnapshot);
 for(const saved of [false,true]){
  const record={id:'ordered-saved',version:3,snapshot:orderedSnapshot,created_at:'2026-10-25',is_stale:false};
  const html=render({completion:{...preview,preview:orderedSnapshot,...(saved?{active:record,history:[record]}:{})}});
  const map=html.slice(html.indexOf('class="portfolio-branches"'),html.indexOf('class="portfolio-career-notes"'));
  const notes=html.slice(html.indexOf('class="portfolio-career-notes"'));
  for(const section of [map,notes]){
   const positions=['Software Development','Digital Product Design','Environmental Science','Biomedical Engineering'].map(title=>section.indexOf(title));
   assert.ok(positions.every(p=>p>=0));assert.deepEqual(positions,[...positions].sort((a,b)=>a-b));
  }
 }
 assert.equal(JSON.stringify(orderedSnapshot),before);
});
test('primary only moves that career first and keeps the other saved careers in their original order',()=>{
 const doc={...orderedSnapshot,paths:[{world_id:'software',priority:'primary'}]};
 assert.deepEqual(orderedPortfolioCareers(doc).map(c=>c.world_id),['software','environment','design','bioengineering']);
});
test('undecided and legacy snapshots preserve saved order without inventing priorities',()=>{
 for(const doc of [{...orderedSnapshot,undecided:true},{...orderedSnapshot,paths:[]}])assert.deepEqual(orderedPortfolioCareers(doc).map(c=>c.world_id),shuffledCareers.map(c=>c.world_id));
 assert.deepEqual(orderedPortfolioCareers({}),[]);
});
test('historical snapshots sort using their own priorities and tolerate frozen saved records',()=>{
 const old=Object.freeze({...orderedSnapshot,shortlist:Object.freeze([...shuffledCareers]),paths:Object.freeze([{world_id:'environment',priority:'primary'}])});
 const current={...orderedSnapshot,paths:[{world_id:'software',priority:'primary'}]};
 assert.equal(orderedPortfolioCareers(old)[0].world_id,'environment');assert.equal(orderedPortfolioCareers(current)[0].world_id,'software');assert.equal(old.shortlist[0].world_id,'environment');
});
