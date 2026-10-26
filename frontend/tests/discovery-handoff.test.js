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
const directory=await mkdtemp(join(cache,'discovery-handoff-'));let Worlds,Proposed;
try {
 const output=join(directory,'outcome.cjs');
 await build({entryPoints:[join(root,'src/components/DiscoveryOutcome.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],logLevel:'silent'});
 const module=(await import(pathToFileURL(output).href)).default;Worlds=module.default;Proposed=module.ProposedExplorer;
}finally{await rm(directory,{recursive:true,force:true});}
const catalogue=[{world_id:'design',title:'Digital Product Design',source:'Curated demo',url:'',live_verified:false},{world_id:'software',title:'Software Development',source:'BLS',url:'https://example.test/software',live_verified:false}];
const render=(state,all=catalogue)=>renderToStaticMarkup(React.createElement(Worlds,{state,onReview:()=>{},initialCatalogue:all}));
const handoff={version:2,profile_version:3,selected_interests:['art'],career_worlds:[{...catalogue[0],explanation:'Connected to your confirmed art interest.'}],exploratory:false,timestamp:'2026-10-25T12:00:00Z',story:{summary:'Saved fictional discovery summary.'},next_mission:{text:'Sketch two ideas.'}};
test('editable proposal shows authoritative corrections without a confirmation control',()=>{
 const html=renderToStaticMarkup(React.createElement(Proposed,{outcome:{profile_origin:'saved_profile',proposed_profile:{interests:['art'],learning_style:'Creative activities',goal:'Explore',correction:'<script>fictional preference</script>'}},onEdit:()=>{}}));
 for(const text of ['proposed Explorer Profile','art','Edit &amp; Review My Explorer Profile','Explicit confirmation is a separate step','&lt;script&gt;fictional preference&lt;/script&gt;'])assert.ok(html.includes(text));
 assert.doesNotMatch(html,/Confirm My Explorer Profile|<script>/);
});
test('personalized worlds cite the confirmed version while other worlds stay accessible',()=>{
 const html=render({confirmed:true,discovery_handoff:{active:handoff}});
 for(const text of ['Profile version 3','Handoff version 2','Connected to your confirmed art interest','All Career Worlds','Software Development','not career rankings','Optional next mission: Sketch two ideas.'])assert.ok(html.includes(text));
 assert.match(html,/data-world-id="design"/);assert.match(html,/href="https:\/\/example.test\/software"/);
});
test('unconfirmed profile with archived handoff hides personalized content but allows catalogue browsing',()=>{
 const html=render({confirmed:false,discovery_handoff:{active:null,latest:handoff}});
 assert.match(html,/explicit profile confirmation/);assert.match(html,/Review My Explorer Profile/);assert.match(html,/Software Development/);
 assert.doesNotMatch(html,/Connected to your confirmed art interest|Saved fictional discovery summary/);
});
test('uncertain students can explore without a forced career',()=>{
 const html=render({confirmed:true,discovery_handoff:{active:{...handoff,exploratory:true,career_worlds:[],selected_interests:[]}}});
 assert.match(html,/No career choice is required/);assert.match(html,/No personalized world is selected/);assert.match(html,/Digital Product Design/);
});
test('empty catalogue and legacy handoff have honest review and unavailable states',()=>{
 const html=render({confirmed:true,discovery_handoff:{active:null}},[]);
 assert.match(html,/explicitly confirm your saved profile/);assert.match(html,/catalogue is unavailable right now/);
 assert.doesNotMatch(html,/data-world-id=/);
});
