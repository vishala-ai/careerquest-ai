import test from 'node:test';
import assert from 'node:assert/strict';
import {api,setCsrfToken} from '../src/api.js';

test('authenticated requests use same-origin cookies and an in-memory CSRF header',async()=>{
 const original=globalThis.fetch;let captured;
 globalThis.fetch=async(url,options)=>{captured={url,options};return {ok:true,json:async()=>({saved:true})};};
 try{
  setCsrfToken('test-csrf');await api('/profiles/owned/draft','POST',{interests:['science']});
  assert.equal(captured.options.credentials,'same-origin');assert.equal(captured.options.headers['X-CSRF-Token'],'test-csrf');assert.equal(captured.options.headers['X-CQ-Request'],'1');
  setCsrfToken('');await api('/auth/login','POST',{username:'demo_alias',password:'test passphrase'});assert.equal(captured.options.headers['X-CSRF-Token'],'');
 }finally{globalThis.fetch=original;setCsrfToken('');}
});
test('expired private requests return to login while invalid login stays on the form',async()=>{
 const original=globalThis.fetch,previous=globalThis.window;const events=[];
 globalThis.window={dispatchEvent:event=>events.push(event.type)};
 globalThis.fetch=async()=>({ok:false,status:401,json:async()=>({detail:'Please sign in'})});
 try{
  await assert.rejects(api('/profiles/owned'),/Please sign in/);assert.deepEqual(events,['cq-session-expired']);
  await assert.rejects(api('/auth/login','POST',{}),/Please sign in/);assert.equal(events.length,1);
 }finally{globalThis.fetch=original;globalThis.window=previous;}
});
