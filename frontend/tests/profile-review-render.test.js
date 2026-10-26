import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));const cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'profile-review-'));let Profile,Quests,Panel;
try {
 for(const [name,path] of [['profile','pages/ExplorerProfile.jsx'],['quests','pages/DiscoveryQuests.jsx'],['panel','components/DiscoveryAgentPanel.jsx']]){
  const output=join(directory,name+'.cjs');await build({entryPoints:[join(root,'src',path)],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});
  const component=(await import(pathToFileURL(output).href)).default.default;
  if(name==='profile')Profile=component;else if(name==='quests')Quests=component;else Panel=component;
 }
}finally{await rm(directory,{recursive:true,force:true});}
const quests=[{title:'Discover Your Spark',question:'First?',options:{'Build a mini-app':'technology'}},{title:'Choose Your Mission',question:'Second?',options:{'Analyze the data':'science'}},{title:'Working Style',question:'Third?',options:{'Build something':'building'}}];
const answers=quests.map((q,quest)=>({id:'answer-'+quest,kind:'quest_completed',created_at:'2026-10-25T00:00:00Z',payload:{quest,choice:Object.keys(q.options)[0],interest:Object.values(q.options)[0]}}));
const values={interests:['art'],learning_style:'Creative activities',goal:'Try a mini-project',correction:'For this fictional explorer, art feels right.',not_sure:false};
const story={id:'story-2',version:2,response_version:'current',status:'fallback',model:'openai/gpt-oss-120b',is_stale:false,created_at:'2026-10-25T00:00:00Z',source_answers:answers.map(a=>({choice_id:a.id,choice:a.payload.choice,quest:a.payload.quest})),preferences:{evidence:[]},content:{summary:'A saved fictional discovery summary.',what_this_might_suggest:[{interest_id:'art',choice_ids:['art-preference']}],what_you_could_try_next:[],career_worlds:[]}};
const state={profile:{id:'fictional',alias:'Nova Fictional',grade:10,xp:60,interests:[]},profile_version:1,quest_answers:answers,quest_complete:true,confirmed:false,profile_draft:values,discovery:{quest_xp:60,first_completion_xp:20},discovery_guide:{response_version:'current',latest:story,history:[story],revisions_remaining:2}};
const profile=(overrides={},extra={})=>renderToStaticMarkup(React.createElement(Profile,{state:{...state,...overrides},quests,values,onChange:()=>{},onConfirm:()=>{},onGuideUpdated:()=>{},onPending:()=>{},...extra}));
test('completed quest page has one review CTA, no proposed profile and no review radios',()=>{
 const html=renderToStaticMarkup(React.createElement(Quests,{state:{...state,discovery_outcome:{proposed_profile:values}},quests,onNavigate:()=>{},onAnswer:()=>{}}));
 assert.equal((html.match(/>\s*Review My Explorer Profile</g)||[]).length,1);
 assert.doesNotMatch(html,/proposed Explorer Profile|name="profile-feedback"|name="guide-feedback"|Confirm My Explorer Profile|Edit Interests Manually/);
 for(const a of answers)assert.ok(html.includes(a.payload.choice));
 assert.match(html,/Discovery Story/);assert.match(html,/Your Discovery Clues/);
});
test('profile separates actual choices and editable interpretation with a nickname heading',()=>{
 const html=profile();assert.match(html,/<h1>Does This Feel Like You, Nova Fictional\?<\/h1>/);
 for(const text of ['WHAT YOU CHOSE','Your actual quest choices','WHAT CAREERQUEST SUGGESTS','Preferred activities','Exploration goal','art','Edit Interests Manually'])assert.ok(html.includes(text),text);
 for(const a of answers)assert.ok(html.includes(a.payload.choice));
 assert.equal((html.match(/type="radio" name="profile-feedback"/g)||[]).length,3);
 assert.doesNotMatch(html,/Your proposed Explorer Profile|Agree &amp; Review Explorer Profile/);
});
test('Yes exposes only one explicit confirmation action',()=>{
 const latest={...story,feedback:{verdict:'Yes',correction:''}};
 const html=profile({discovery_guide:{...state.discovery_guide,latest}});
 assert.equal((html.match(/> Confirm My Explorer Profile<\/button>/g)||[]).length,1);
 assert.doesNotMatch(html,/Create a New Proposal|> Revise My Proposal</);
});
test('Somewhat presents retained interests and correction before one revision action',()=>{
 const latest={...story,feedback:{verdict:'Somewhat',correction:'Keep art, add design.'}};
 const html=profile({discovery_guide:{...state.discovery_guide,latest}});
 assert.match(html,/Which interests still feel right/);assert.match(html,/required=""/);assert.match(html,/Revise My Proposal/);
 assert.doesNotMatch(html,/Confirm My Explorer Profile/);
});
test('Not really offers a new proposal or manual editing without a confirmation action',()=>{
 const latest={...story,feedback:{verdict:'Not really',correction:'Prefer another direction.'}};
 const html=profile({discovery_guide:{...state.discovery_guide,latest}});
 assert.match(html,/Create a New Proposal/);assert.match(html,/Edit Interests Manually/);assert.doesNotMatch(html,/Confirm My Explorer Profile/);
});
test('new revised proposal does not inherit Yes from the earlier version',()=>{
 const old={...story,id:'story-1',is_stale:true,feedback:{verdict:'Yes',correction:''}};
 const html=profile({discovery_guide:{...state.discovery_guide,latest:{...story,feedback:null},history:[old,story]}});
 assert.doesNotMatch(html,/<input(?=[^>]*name="profile-feedback")(?=[^>]*checked="")[^>]*>/);
 assert.doesNotMatch(html,/Confirm My Explorer Profile/);
});
test('returning confirmed profile has no repeated feedback controls and keeps edit action',()=>{
 const html=profile({confirmed:true,profile_preferences:values});
 assert.match(html,/Nova Fictional, your curiosity in focus/);assert.match(html,/Confirmed by you/);assert.match(html,/Edit Profile/);assert.match(html,/Explore Career Worlds/);
 assert.doesNotMatch(html,/name="profile-feedback"|Confirm My Explorer Profile/);
 assert.match(profile({profile:{...state.profile,alias:'  '}}),/Does This Feel Like You, Explorer\?/);
});
test('confirmed profile has interest cards and friendly notes with audit versions in secondary details',()=>{
 const selected={...values,interests:['art','biology','coding'],correction:'See if you have to revise the career goals'};
 const html=profile({confirmed:true,profile_version:4,profile_draft:null,profile_preferences:selected},{values:selected});
 const visible=html.split('<details class="profile-record-details">')[0];
 assert.equal((visible.match(/class="profile-interest-card"/g)||[]).length,3);
 for(const title of ['Art','Biology','Coding','How I like to explore','My next exploration goal','I’d like to revisit my goals as I explore.'])assert.ok(visible.includes(title),title);
 assert.doesNotMatch(visible,/Version 4|Profile version|See if you have to revise/);
 assert.match(html,/<summary>Saved profile details<\/summary>/);assert.match(html,/Original saved note/);assert.match(html,/See if you have to revise the career goals/);
});
test('unconfirmed page exposes editable interests alongside feedback controls',()=>{
 const html=profile();
 assert.match(html,/aria-label="Edit interests"/);assert.match(html,/aria-pressed="true"/);
 assert.match(html,/Tap an interest to change it/);assert.match(html,/name="profile-feedback"/);
 assert.doesNotMatch(html.split('<details class="profile-record-details">')[0],/Version 1/);
});
test('reconfirmation opens saved fields and correction controls before final review',()=>{
 const html=profile({profile_preferences:{...values,interests:['science']},profile_version:5});
 assert.match(html,/Make it feel like you, Nova Fictional/);assert.match(html,/Updating your profile/);
 assert.match(html,/Update your saved preferences/);assert.match(html,/id="profile-correction"/);
 assert.match(html,/Creative activities/);assert.match(html,/Review Saved Profile/);assert.match(html,/explicit reconfirmation/);
 assert.doesNotMatch(html,/Explore Career Worlds|> Confirm My Explorer Profile/);
});
test('unsure confirmed student sees an open-options card rather than invented interests',()=>{
 const selected={...values,interests:[],not_sure:true};
 const html=profile({confirmed:true,profile_draft:null,profile_preferences:selected},{values:selected});
 assert.match(html,/Still exploring/);assert.doesNotMatch(html,/class="profile-interest-card"/);
 assert.match(html,/don’t need to choose a career/);
});
test('quest preview cannot answer a saved agent question or open duplicate manual review',()=>{
 const agent={question:{id:'preferred_interests'},status:'manual_edit',engine:'langgraph',trace:[],pending_confirmation:true,clarifications_remaining:1};
 const html=renderToStaticMarkup(React.createElement(Panel,{agent,readOnly:true}));
 assert.match(html,/Continue to Explorer Profile/);assert.doesNotMatch(html,/Continue with My Answer|Open Manual Profile Review/);
});
test('bounded failure leaves a labeled manual proposal and does not reuse an old Yes',()=>{
 const stale={...story,is_stale:true,feedback:{verdict:'Yes',correction:''}};
 const agent={status:'manual_edit',is_stale:false,question:null,trace:[],engine:'langgraph',pending_confirmation:true};
 const html=profile({discovery_guide:{...state.discovery_guide,latest:stale},discovery_agent:agent});
 assert.match(html,/manual proposal, not an AI-generated revision/);
 assert.doesNotMatch(html,/Confirm My Explorer Profile|Open Manual Profile Review/);
 assert.match(html,/Edit Interests Manually/);
 assert.doesNotMatch(html,/<input(?=[^>]*value="Yes")(?=[^>]*checked="")[^>]*>/);
});
