import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url)),cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'recommendations-paths-'));const components={};
try{for(const name of ['CareerWorlds','CareerPortfolioPaths','CareerComparison']){const output=join(directory,name+'.cjs');await build({entryPoints:[join(root,'src/pages/'+name+'.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});components[name]=(await import(pathToFileURL(output).href)).default.default;}}finally{await rm(directory,{recursive:true,force:true});}
const render=(Component,props)=>renderToStaticMarkup(React.createElement(Component,props));
const state={profile:{id:'fictional',alias:'Lyra Fictional'},confirmed:true};
const worlds=['software','design','environment','bioengineering'].map((world_id,i)=>({world_id,title:world_id,description:'Supported catalogue description',reason:'Connected to your confirmed technology interest.',recommended:i<3}));
const page=data=>render(components.CareerWorlds,{state,initialData:{confirmed:true,confirmed_interests:['technology'],worlds,portfolio:{explorations:[],shortlist:[]},...data},onNavigate:()=>{},onUpdated:()=>{}});
test('landing starts with three recommendation cards and Why suggested before other careers',()=>{
 const html=page();assert.equal((html.match(/Why suggested\?/g)||[]).length,3);assert.equal((html.match(/aria-label="Explore Career:/g)||[]).length,4);
 assert.ok(html.indexOf('Recommended Careers for You')<html.indexOf('Explore All Careers'));assert.doesNotMatch(html,/YOUR CAREER WORLD FIELD NOTES|Back to Recommended Careers/);
});
test('one two and zero matches show only supported recommendations and all other careers',()=>{
 for(const count of [0,1,2]){const html=page({worlds:worlds.map((w,i)=>({...w,recommended:i<count,reason:i<count?w.reason:null}))});assert.equal((html.match(/Why suggested\?/g)||[]).length,count);assert.equal((html.match(/aria-label="Explore Career:/g)||[]).length,4);assert.match(html,/We suggest only supported matches/);if(!count)assert.match(html,/No supported catalogue matches/);}
});
test('three comparison controls are available outside optional AI questions',()=>{
 const html=page();assert.match(html,/Career 3 \(optional\)/);assert.equal((html.match(/id="career-compare-/g)||[]).length,4);assert.match(html,/two or three different careers/);assert.ok(html.indexOf('career-compare-heading')<html.indexOf('Ask Your AI Career Guide'));
});
test('comparison table uses cited activities skills and fields for all three worlds',()=>{
 const item={text:'A supported fact',source_ids:['bls-software']};const html=render(components.CareerComparison,{worlds:worlds.slice(0,3).map(w=>({...w,activities:[item],skills:[item],educational_fields:[item]}))});
 assert.match(html,/<caption>Your selected careers, side by side/);assert.equal((html.match(/scope="row"/g)||[]).length,3);assert.equal((html.match(/href="#source-bls-software"/g)||[]).length,9);assert.match(html,/aria-label="Career comparison table" tabindex="0"/);
});
test('path controls never auto-assign a career and secondary is optional',()=>{
 const portfolio={shortlist:[{world_id:'software',exploration:{is_stale:false,world:{title:'Software'}}}]};
 const html=render(components.CareerPortfolioPaths,{portfolio,preferences:{history:[],active:null},context:{profile_version:1},confirmed:true,onSave:()=>{}});
 assert.match(html,/<option value="" selected="">Choose a saved career/);assert.match(html,/Secondary Exploration Path \(optional\)/);assert.match(html,/None for now/);assert.match(html,/<button[^>]*disabled=""[^>]*> Save Exploration Paths/);
});
test('stale and unsaved careers cannot become new paths in student UI',()=>{
 const html=render(components.CareerPortfolioPaths,{portfolio:{shortlist:[{world_id:'software',exploration:{is_stale:true}}]},preferences:{history:[]},context:{profile_version:2},confirmed:true});
 assert.match(html,/Save a career with your current confirmed profile/);assert.doesNotMatch(html,/<select/);
});
test('saved path summary and historical profile versions remain visible',()=>{
 const active={id:'path-2',primary_world_id:'design',secondary_world_id:null,paths:[{priority:'primary',title:'Design'}]};
 const html=render(components.CareerPortfolioPaths,{portfolio:{shortlist:[]},preferences:{active,history:[{...active,profile_version:4,created_at:'2026-10-25',is_stale:true}]},confirmed:false});
 assert.match(html,/Primary Exploration Path/);assert.match(html,/Design/);assert.match(html,/Earlier profile/);assert.match(html,/Source profile version 4/);assert.match(html,/Confirm your current Explorer Profile/);
});
test('top navigation remounts Career Worlds and details are only explicit local actions',async()=>{
 const app=await readFile(join(root,'src/App.jsx'),'utf8'),student=await readFile(join(root,'src/pages/CareerWorlds.jsx'),'utf8');
 assert.match(app,/\['worlds','portfolio','celebrate'\]\.includes\(next\)\)\{setWorldsEntry/);assert.match(app,/key=\{`\$\{pid\|\|'no-explorer'\}:\$\{worldsEntry\}`\}/);
 assert.match(student,/\[detail,setDetail\]=useState\(null\)/);assert.match(student,/Back to Recommended Careers/);assert.match(student,/Resume saved detail/);assert.doesNotMatch(student,/else if\(next.world_id\)explore/);
});
