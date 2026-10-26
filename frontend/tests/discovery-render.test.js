import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'discovery-render-'));let Page;
try {
 const output=join(directory,'page.cjs');
 await build({entryPoints:[join(root,'src/pages/DiscoveryQuests.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});
 Page=(await import(pathToFileURL(output).href)).default.default;
} finally {await rm(directory,{recursive:true,force:true});}
const quests=[
 {title:'Discover Your Spark',question:'Quest 1 scenario?',options:{'Build a mini-app':'technology','Sketch an invention':'art'}},
 {title:'Choose Your Mission',question:'Quest 2 scenario?',options:{'Analyze the data':'science'}},
 {title:'Working Style',question:'Quest 3 scenario?',options:{'Build something':'building'}},
];
const choices=['Build a mini-app','Analyze the data','Build something'];
const interests=['technology','science','building'];
const answers=choices.map((choice,quest)=>({id:`fictional-${quest}`,created_at:'2026-01-01T00:00:00Z',kind:'quest_completed',payload:{quest,choice,interest:interests[quest]}}));
const base={profile:{id:'fictional-render',xp:0},quest_answers:[],confirmed:false,discovery:{quest_xp:0,first_completion_xp:20}};
const render=state=>renderToStaticMarkup(React.createElement(Page,{state,quests,onNavigate:()=>{},onAnswer:()=>{}}));
test('new explorer renders unanswered Quest 1 without saved selections',()=>{
 const html=render(base);assert.match(html,/<h2>Quest 1 scenario\?<\/h2>/);assert.doesNotMatch(html,/checked=""/);assert.match(html,/aria-valuenow="0"/);
});
test('partial explorer and reload render the first incomplete Quest 2',()=>{
 const state={...base,quest_answers:answers.slice(0,1),discovery:{quest_xp:20,first_completion_xp:20}};
 for(const restored of [state,JSON.parse(JSON.stringify(state))]){
  const html=render(restored);assert.match(html,/<h2>Quest 2 scenario\?<\/h2>/);assert.doesNotMatch(html,/checked=""/);assert.match(html,/aria-valuenow="1"/);
 }
});
test('completed explorer renders all saved answers, Discovery Clues, explicit edits and actual reward total',()=>{
 const html=render({...base,quest_answers:answers,confirmed:true,discovery:{quest_xp:42}});
 assert.match(html,/Your Discovery Clues/);for(const choice of choices)assert.ok(html.includes(choice));
 assert.equal((html.match(/aria-label="Edit answer for /g)||[]).length,3);
 assert.match(html,/42 quest XP earned/);assert.doesNotMatch(html,/60 QUEST XP/);
});
