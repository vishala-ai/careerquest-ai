import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {build} from 'esbuild';
import {mkdir,mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url)),cache=join(root,'node_modules','.cache');await mkdir(cache,{recursive:true});
const directory=await mkdtemp(join(cache,'developer-research-'));let Page,Receipt;
try{const output=join(directory,'page.cjs');await build({entryPoints:[join(root,'src/pages/DeveloperResearch.jsx')],outfile:output,bundle:true,platform:'node',format:'cjs',external:['react'],loader:{'.css':'empty'},logLevel:'silent'});const module=(await import(pathToFileURL(output).href)).default;Page=module.default;Receipt=module.ResearchReceipt;}finally{await rm(directory,{recursive:true,force:true});}
test('developer controls are not mounted before server authorization',()=>{
 globalThis.localStorage={getItem:()=>null};
 try{const html=renderToStaticMarkup(React.createElement(Page));assert.match(html,/Checking server authorization/);assert.doesNotMatch(html,/type="checkbox"|<textarea|Run controlled research|Sanitized research receipt/);}finally{delete globalThis.localStorage;}
});
test('developer receipt distinguishes deterministic routing, actual Groq model and bounded failures',()=>{
 const receipt={run_id:'saved-run',created_at:'2026-10-25',action:'research_careers',status:'blocked',source_validation:{all_metadata_valid:false,evidence_references_valid:null},trace:[{step:'route',method:'student_world_selection',action:'research_careers'},{step:'route',method:'groq',model:'openai/gpt-oss-120b'},{step:'route',method:'bounded_policy_fallback',error_type:'TimeoutError'},{step:'tool',status:'failed',error_type:'ConnectionError'}]};
 const html=renderToStaticMarkup(React.createElement(Receipt,{receipt}));
 for(const text of ['explicit world selection','Groq-directed routing','openai/gpt-oss-120b','bounded fallback','TimeoutError','ConnectionError','No complete source evidence','Sanitized research receipt'])assert.ok(html.includes(text),text);
});
test('student source cannot send tester flags or render raw receipts and developer view uses protected APIs',async()=>{
 const student=await readFile(join(root,'src/pages/CareerWorlds.jsx'),'utf8');assert.doesNotMatch(student,/use_groq|simulate_failure|<pre|Developer details|career-developer/);
 const developer=await readFile(join(root,'src/pages/DeveloperResearch.jsx'),'utf8');assert.match(developer,/api\('\/developer\/access'\)/);assert.match(developer,/\/developer\/profiles\//);
});
