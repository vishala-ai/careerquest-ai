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
const directory=await mkdtemp(join(cache,'discovery-guide-render-'));let Guide,Review;
try {
 const output=join(directory,'guide.cjs');
 await build({entryPoints:[join(root,'src/components/DiscoveryGuide.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],logLevel:'silent'});
 Guide=(await import(pathToFileURL(output).href)).default.default;
 const reviewOutput=join(directory,'review.cjs');
 await build({entryPoints:[join(root,'src/components/ProfileDiscoveryReview.jsx')],outfile:reviewOutput,bundle:true,platform:'node',format:'cjs',external:['react'],logLevel:'silent'});
 Review=(await import(pathToFileURL(reviewOutput).href)).default.default;
} finally {await rm(directory,{recursive:true,force:true});}
const item={id:'guide-1',version:1,model:'openai/gpt-oss-120b',response_version:'source-1',status:'groq',is_stale:false,created_at:'2026-10-24T12:00:00Z',feedback:null,
 source_answers:[{choice_id:'c1',choice:'Sketch an invention'}],
 content:{what_you_chose:[{choice_id:'c1',choice:'Sketch an invention'}],what_this_might_suggest:[{text:'These choices might be a reason to explore visual ideas.',choice_ids:['c1']}],what_you_could_try_next:[{text:'Draw two designs.',choice_ids:['c1']}],career_worlds:[{world_id:'design',title:'Digital Product Design',choice_ids:['c1'],source:'Curated demo',url:''}]}};
const render=(latest=item,version='source-1',review=false)=>renderToStaticMarkup(React.createElement(review?Review:Guide,{values:{interests:['art'],learning_style:'Creative activities',goal:'Try a mini-project',correction:''},state:{profile:{id:'fictional',alias:'Nova Demo',grade:10},discovery_guide:{response_version:version,latest,history:latest?[latest]:[]}}}));
test('quest story keeps grounded content and technical details without profile feedback',()=>{
 const html=render();for(const text of ['Groq-generated Discovery Story','openai/gpt-oss-120b','What You Chose','What This Might Suggest','What You Could Try Next','Nova Demo','Sketch an invention','Digital Product Design'])assert.ok(html.includes(text));
 assert.doesNotMatch(html,/type="radio"|Confirm My Explorer Profile|proposed Explorer Profile/);
});
test('fallback has explicit deterministic labeling and a Groq retry',()=>{
 const html=render({...item,status:'fallback'});assert.match(html,/Deterministic Discovery Summary · Not AI-generated/);assert.match(html,/Retry with Groq/);assert.doesNotMatch(html,/Groq-generated Discovery Story/);
});
test('changed response version withholds stale story and feedback from current guide',()=>{
 const html=render(item,'source-2');assert.match(html,/earlier guide is stale/);assert.doesNotMatch(html,/Save my feedback/);assert.match(html,/Version 1 · Stale/);
});
test('feedback is restored and escaped from backend data',()=>{
 const html=render({...item,feedback:{verdict:'Not really',correction:'<script>fictional</script>'}},'source-1',true);assert.match(html,/<input(?=[^>]*value="Not really")(?=[^>]*checked="")[^>]*>/);assert.match(html,/&lt;script&gt;fictional&lt;\/script&gt;/);assert.doesNotMatch(html,/<script>/);
});

test('refined story has nickname heading and a 70–110 word summary with technical details collapsed',()=>{
 const html=render();assert.match(html,/<h2 id="discovery-guide-title">Nova Demo, your Discovery Story<\/h2>/);
 const summary=html.match(/<p class="discovery-story-summary">([^<]+)<\/p>/)[1];assert.ok(summary.split(/\s+/).length>=70&&summary.split(/\s+/).length<=110);
 const beforeDetails=html.split('<details class="guide-generation">')[0];assert.doesNotMatch(beforeDetails,/openai\/gpt-oss|Generation status|What You Chose/);
 assert.match(html,/<summary>How this was generated<\/summary>/);assert.match(html,/Optional mini-mission/);
});
test('Somewhat requires a correction and lets students keep agreed clues',()=>{
 const html=render({...item,feedback:{verdict:'Somewhat',correction:''}},'source-1',true);assert.match(html,/Which interests still feel right/);assert.match(html,/What should we change\? \(required\)/);assert.match(html,/minLength="3" required=""/);assert.match(html,/What would you prefer to explore/);assert.match(html,/Revise My Proposal/);
});
test('Not really asks for preferred interests without retaining original inferences',()=>{
 const html=render({...item,feedback:{verdict:'Not really',correction:''}},'source-1',true);assert.match(html,/Let’s start with your interests instead/);assert.doesNotMatch(html,/class="guide-retained"/);assert.match(html,/Create a New Proposal/);assert.match(html,/Edit Interests Manually/);
});
test('Yes offers the single explicit confirmation action on profile review',()=>{
 const html=render({...item,feedback:{verdict:'Yes',correction:''}},'source-1',true);assert.match(html,/Confirm My Explorer Profile/);assert.match(html,/Confirming saves this profile version/);assert.doesNotMatch(html,/class="guide-preferences"/);
});
test('mixed provenance clearly labels catalogue fallback suggestions outside technical details',()=>{
 const html=render({...item,recommendation_source:'catalogue_fallback'});const beforeDetails=html.split('<details class="guide-generation">')[0];assert.match(beforeDetails,/Catalogue-based suggestions · Not Groq-generated/);
});
test('revised proposal shows changes and manual editing remains available after the revision cap',()=>{
 const revised={...item,changes:{mode:'Somewhat',kept:['technology'],added:['art'],removed:['science'],correction:'Explore art instead.'},feedback:{verdict:'Somewhat',correction:'Explore art instead.'}};
 const html=renderToStaticMarkup(React.createElement(Review,{values:{interests:['art'],learning_style:'Creative activities',goal:'Explore',correction:''},state:{profile:{id:'fictional',alias:'Nova Demo',grade:10},discovery_guide:{response_version:'source-1',latest:revised,history:[revised],revisions_remaining:0}}}));
 for(const text of ['What changed','Kept: technology','Added: art','Set aside: science','Edit Interests Manually'])assert.ok(html.includes(text),text);
 assert.match(html,/You’ve tried three guided revisions/);assert.match(html,/<button[^>]*disabled=""[^>]*> Revise My Proposal<\/button>/);
});
