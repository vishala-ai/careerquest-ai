import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));const cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'career-worlds-'));let Page,Card,Detail;
try{const output=join(directory,'page.cjs');await build({entryPoints:[join(root,'src/pages/CareerWorlds.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});const module=(await import(pathToFileURL(output).href)).default;Page=module.default;Card=module.CareerWorldCard;Detail=module.CareerWorldDetail;}finally{await rm(directory,{recursive:true,force:true});}
const worlds=[['bioengineering','Biomedical Engineering'],['software','Software Development'],['design','Digital Product Design'],['environment','Environmental Science']].map(([world_id,title])=>({world_id,title,description:'A curated possibility to explore.',recommended:world_id==='design',reason:world_id==='design'?'Connected to your chosen art interest.':null}));
const state={profile:{id:'fictional',alias:'Nova Fictional',interests:['art']},confirmed:true};
const initialData={confirmed:true,confirmed_interests:['art'],worlds,portfolio:{explorations:[],shortlist:[]}};
const render=(s=state,data=initialData)=>renderToStaticMarkup(React.createElement(Page,{state:s,initialData:data,onNavigate:()=>{},onUpdated:()=>{}}));
test('all supported world cards have an explicit stable-world action',()=>{
 const html=render();assert.equal((html.match(/aria-label="Explore Career:/g)||[]).length,4);
 assert.ok(html.indexOf('Digital Product Design')<html.indexOf('Explore All Careers'));
 assert.equal((html.match(/<h3>Digital Product Design<\/h3>/g)||[]).length,1);
 assert.match(html,/<h1>Career Worlds for Nova Fictional<\/h1>/);assert.match(html,/Nova Fictional, choose a world/);assert.match(html,/From your confirmed interests: art/);
});
test('student guide is collapsed and has no developer controls, raw receipts or prefilled prompt',()=>{
 const html=render();assert.doesNotMatch(html.split('<details class="panel career-ai-guide">')[0],/<textarea|Where shall we explore/);
 assert.match(html,/<summary>Ask Your AI Career Guide<\/summary>/);assert.doesNotMatch(html,/Developer details|demo tools|Groq|Simulate research failure|<pre|type="checkbox"/);
 assert.match(html,/<textarea[^>]*><\/textarea>/);assert.doesNotMatch(html,/<details[^>]*open=""/);
 assert.match(html,/Compare Careers/);
});
test('one next-step action uses the server-supplied persisted-selection state',()=>{
 for(const next_action of [{kind:'explore_world',label:'Explore a Career World',world_id:'design'},{kind:'save_career',label:'Choose a Career to Keep',exploration_id:'saved-notes'},{kind:'view_portfolio',label:'View My Career Discovery Portfolio'},{kind:'review_profile',label:'Review My Explorer Profile',page:'confirm'}]){
  const html=render(state,{...initialData,next_action});assert.equal((html.match(/aria-label="Your next step"/g)||[]).length,1);assert.ok(html.includes(next_action.kind==='explore_world'?'See Recommended Careers':next_action.label));
 }
 assert.match(render(),/id="career-portfolio-heading" tabindex="-1"/);
});
test('unconfirmed student can browse all worlds but cannot submit personalized questions',()=>{
 const html=render({...state,confirmed:false},{...initialData,confirmed:false});assert.match(html,/Confirm your Explorer Profile/);
 assert.equal((html.match(/aria-label="Explore Career:/g)||[]).length,4);
 assert.doesNotMatch(html,/From your confirmed interests/);assert.match(html,/<textarea[^>]*disabled=""/);
});
test('empty portfolio is explicit and never implies automatic shortlist saving',()=>{
 const html=render();assert.match(html,/No careers shortlisted yet/);assert.match(html,/always takes your explicit choice/);
 assert.match(html,/Exploration history \(0\)/);
});
test('career details expose cited sections, educational boundary and optional demo mission',()=>{
 const item={text:'A grounded fact.',source_ids:['bls-design']};
 const world={world_id:'design',title:'Digital Product Design',overview:item,activities:[item],skills:[item],educational_fields:[item],mission:{text:'Sketch a fictional screen.'},sources:[{id:'bls-design',title:'Digital design',source:'BLS',url:'https://www.bls.gov/ooh/computer-and-information-technology/web-developers.htm',live_verified:false}]};
 const html=renderToStaticMarkup(React.createElement(Detail,{world,canSave:true,onSave:()=>{}}));
 for(const title of ['Career activities','Skills you could explore','Related educational fields','Optional try-it mission','Save to My Career Shortlist','not school-specific admissions requirements'])assert.ok(html.includes(title),title);
 assert.equal((html.match(/href="#source-bls-design"/g)||[]).length,4);assert.match(html,/id="source-bls-design"/);assert.match(html,/Not live verified/);
});
test('saved detail has an idempotent disabled save control',()=>{
 const world={world_id:'design',title:'Design',overview:{text:'Notes',source_ids:[]},sources:[]};
 const html=renderToStaticMarkup(React.createElement(Detail,{world,canSave:true,saved:true}));
 assert.match(html,/disabled=""/);assert.match(html,/Saved to My Career Shortlist/);
});
