import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url)),cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'career-milestone-'));let View,Map;
try{for(const name of ['CareerDiscoveryMilestone','CareerPossibilityMap']){const output=join(directory,name+'.cjs');await build({entryPoints:[join(root,'src/pages/'+name+'.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});const module=(await import(pathToFileURL(output).href)).default;if(name==='CareerDiscoveryMilestone')View=module.MilestoneView;else Map=module.default;}}finally{await rm(directory,{recursive:true,force:true});}
const progress={nickname:'Nova Fictional',eligible:true,confirmed:true,counts:{careers_researched:3,careers_shortlisted:2,confirmed_interests:4},count_scope:'Saved backend progress',recovery_page:'worlds',returning_portfolio:false};
const render=(data=progress,extra={})=>renderToStaticMarkup(React.createElement(View,{progress:data,...extra}));
test('eligible screen has personalized emerald adventure copy and exact persisted counts',()=>{
 const html=render();for(const text of ['You did it, Nova Fictional!','FINAL STEP OF THIS ADVENTURE',"You&#x27;ve turned curiosity into possibilities.",'Careers researched','Careers shortlisted','Confirmed interests','<dd>3</dd>','<dd>2</dd>','<dd>4</dd>'])assert.ok(html.includes(text),text);
 assert.match(html,/This is a map of possibilities, not a permanent decision/);assert.match(html,/You can change direction anytime/);assert.match(html,/Create My Career Portfolio/);
});
test('new and anonymous students have honest setup states and no earned achievement claim',()=>{
 for(const data of [{...progress,eligible:false,confirmed:false,recovery_page:'quests',counts:{careers_researched:0,careers_shortlisted:0,confirmed_interests:null}},{...progress,nickname:null,eligible:false,recovery_page:'profiles',counts:{careers_researched:null,careers_shortlisted:null,confirmed_interests:null}}]){
  const html=render(data);assert.doesNotMatch(html,/You did it/);assert.match(html,/<button[^>]*disabled=""[^>]*> Create My Career Portfolio/);assert.match(html,/<dd>—<\/dd>/);
 }
 assert.match(render({...progress,eligible:false,recovery_page:'profiles'}),/Create My Explorer/);
});
test('one or multiple saved careers are never padded to a fabricated achievement',()=>{
 for(const count of [1,2,4]){const html=render({...progress,counts:{...progress.counts,careers_shortlisted:count}});assert.match(html,new RegExp(`<dd>${count}</dd>`));assert.match(html,/Careers shortlisted/);}
});
test('missing nickname and returning portfolio use fallback and preserve revision wording',()=>{
 assert.match(render({...progress,nickname:null}),/You did it, Explorer!/);const html=render({...progress,returning_portfolio:true});assert.match(html,/is-returning/);assert.match(html,/previous portfolio versions are saved/);assert.match(html,/future revision/);
});
test('stale profile presents confirmation recovery and blocked primary entry',()=>{
 const html=render({...progress,eligible:false,confirmed:false,recovery_page:'confirm',counts:{...progress.counts,confirmed_interests:null}});assert.match(html,/Review My Explorer Profile/);assert.match(html,/earlier research and saved choices stay in history/);assert.doesNotMatch(html,/You did it/);
});
test('accessible native actions, labeled progress, loading and retry are present',()=>{
 const html=render();assert.match(html,/<dl[^>]*aria-label="Your saved exploration progress"/);assert.match(html,/id="career-milestone-title" tabindex="-1"/);assert.match(html,/aria-hidden="true" focusable="false"/);assert.match(html,/Explore More Careers/);assert.match(html,/View My Career Shortlist/);assert.match(render(null,{loading:true}),/role="status"/);assert.match(render(null,{error:'Offline'}),/role="alert"/);assert.match(render(null,{error:'Offline'}),/Retry/);
});
test('screen only reads state and server-checks entry, never saves or claims rewards',async()=>{
 const source=await readFile(join(root,'src/pages/CareerDiscoveryMilestone.jsx'),'utf8');assert.match(source,/career-discovery-milestone/);assert.match(source,/career-portfolio\/entry/);assert.doesNotMatch(source,/api\([^\n]*'POST'|career-celebrations|\/complete|localStorage|sessionStorage/);
 const worlds=await readFile(join(root,'src/pages/CareerWorlds.jsx'),'utf8');assert.match(worlds,/if\(screen==='milestone'\)return <CareerDiscoveryMilestone/);assert.match(worlds,/setScreen\('portfolio'\)/);assert.match(worlds,/if\(screen==='milestone'\|\|/);
});
test('motion is opt-in, suppressed for returning students, and disabled for reduced motion',async()=>{
 const css=await readFile(join(root,'src/pages/career-discovery-milestone.css'),'utf8');assert.match(css,/@media\(prefers-reduced-motion:no-preference\).*:not\(\.is-returning\)/);assert.match(css,/@media\(prefers-reduced-motion:reduce\).*animation:none!important;transition:none!important/);assert.match(css,/button:focus-visible/);assert.match(css,/@media\(max-width:500px\)/);
});
test('primary text and white-card contrast exceed WCAG normal-text minimum',async()=>{
 const luminance=hex=>{const rgb=hex.match(/\w\w/g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];};
 const ratio=(a,b)=>{const values=[luminance(a),luminance(b)].sort((x,y)=>y-x);return (values[0]+.05)/(values[1]+.05);};
 const css=await readFile(join(root,'src/pages/career-discovery-milestone.css'),'utf8');const eyebrow=css.match(/\.milestone-eyebrow \{[^}]*color:#([0-9a-f]{6})/)[1];
 for(const [fg,bg] of [['ffffff','117952'],['e4f4ec','117952'],['153f31','ffffff'],['163e30','ffdd80'],[eyebrow,'117952']])assert.ok(ratio(fg,bg)>=4.5,`${fg}/${bg}`);
});
test('portfolio map uses saved interests careers and explicit paths without assigning a path',()=>{
 const html=renderToStaticMarkup(React.createElement(Map,{interests:['art'],portfolio:{shortlist:[{id:'selection',exploration:{is_stale:false,world:{title:'Design'}}}]},paths:null}));assert.match(html,/art/);assert.match(html,/Design/);assert.match(html,/Choose a primary path below/);assert.match(html,/secondary path is optional/);assert.doesNotMatch(html,/<strong>Primary:/);
});
