import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url)),cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'career-celebrations-'));const modules={};
try{for(const name of ['CareerCelebration','CareerPortfolioCompletion']){const output=join(directory,name+'.cjs');await build({entryPoints:[join(root,'src/pages/'+name+'.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});modules[name]=(await import(pathToFileURL(output).href)).default;}}finally{await rm(directory,{recursive:true,force:true});}
const render=(Component,props)=>renderToStaticMarkup(React.createElement(Component,props));
const event={id:'receipt-1',kind:'first_shortlist',nickname:'Nova Fictional',career_name:'Environmental Science'};
const card=(e=event,extra={})=>render(modules.CareerCelebration.default,{event:e,onFinish:()=>{},...extra});
test('first shortlist celebration uses saved nickname and the actual selected career',()=>{
 const html=card();assert.match(html,/Way to go, Nova Fictional!/);assert.match(html,/You saved Environmental Science/);assert.match(html,/you can always change direction/);assert.match(html,/View My Shortlist/);
});
test('six distinct milestones have supportive and contextual next actions with no invented rewards',()=>{
 for(const kind of ['first_research','first_shortlist','second_shortlist','primary_path','secondary_path','portfolio_completed']){
  const message=modules.CareerCelebration.celebrationMessage({...event,kind});assert.ok(message.title.includes('Nova Fictional'));assert.ok(message.label);
  assert.doesNotMatch(message.text,/\d+\s*(XP|points)|career.fit|aptitude|admission|perfect career|personality|%/i);
 }
 assert.match(card({...event,kind:'second_shortlist'}),/more than one possibility/);assert.match(card({...event,kind:'primary_path'}),/not a permanent career decision/);assert.match(card({...event,kind:'secondary_path'}),/update either path later/);
});
test('celebration is a polite nonmodal status with keyboard-native controls and persistent dismissal',()=>{
 const html=card();assert.match(html,/role="status" aria-live="polite" aria-atomic="true"/);assert.match(html,/aria-label="Dismiss celebration"/);assert.equal((html.match(/<button/g)||[]).length,2);assert.doesNotMatch(html,/role="dialog"|autofocus|setTimeout/);
 assert.match(card(event,{busy:true}),/<button[^>]*disabled=""/);assert.match(card(event,{error:'Try again'}),/role="alert">Try again/);
});
test('largest celebration is reserved for portfolio completion and unknown kinds render nothing',()=>{
 assert.doesNotMatch(card(),/is-portfolio-complete/);assert.match(card({...event,kind:'portfolio_completed'}),/is-portfolio-complete/);assert.equal(card({...event,kind:'unknown'}),'');
});
test('nickname fallback and escaped text remain safe and student friendly',()=>{
 assert.match(card({...event,nickname:''}),/Way to go, Explorer!/);const html=card({...event,nickname:'<script>fictional</script>'});assert.doesNotMatch(html,/<script>/);assert.match(html,/&lt;script&gt;/);assert.match(card(event,{confirmed:false}),/Review My Explorer Profile/);
});
test('reduced-motion styling disables motion and animation is opt-in to no-preference',async()=>{
 const css=await readFile(join(root,'src/pages/career-worlds.css'),'utf8');assert.match(css,/@media\(prefers-reduced-motion:no-preference\)\{\.career-celebration\{animation:/);assert.match(css,/@media\(prefers-reduced-motion:reduce\)\{\.career-celebration,\.career-celebration \*\{animation:none!important;transition:none!important;scroll-behavior:auto!important;/);assert.match(css,/max-height:65vh;overflow-y:auto/);
});
test('portfolio completion is explicit after review and secondary remains optional',()=>{
 const Completion=modules.CareerPortfolioCompletion.default;
 const before=render(Completion,{completion:{ready:false,active:null,history:[]}});assert.doesNotMatch(before,/Complete My Career Discovery Portfolio<\/button>/);assert.match(before,/secondary path is optional/);
 const ready=render(Completion,{completion:{ready:true,signature:'saved-signature',active:null,history:[]}});assert.match(ready,/Complete My Career Discovery Portfolio/);assert.match(ready,/Review your saved careers/);
 const done=render(Completion,{completion:{ready:true,active:{id:'completed'},history:[]}});assert.match(done,/snapshot is complete/);assert.doesNotMatch(done,/<button/);
});
test('student page uses persisted claim and acknowledgement APIs instead of local reward flags',async()=>{
 const source=await readFile(join(root,'src/pages/CareerWorlds.jsx'),'utf8');assert.match(source,/career-celebrations\/claim/);assert.match(source,/career-celebrations\/\$\{celebration.id\}\/acknowledge/);assert.doesNotMatch(source,/Saved to your Career Shortlist\. You can revisit|localStorage.*celebrat|sessionStorage.*celebrat/);assert.match(source,/career-portfolio\/complete/);
});
