import os,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from owned_client import TestClient
from careerquest import api
class APITests(unittest.TestCase):
 def setUp(self):
  local=patch.dict(os.environ,{'CAREERQUEST_ENV':'local','CAREERQUEST_DEV_TOOLS':'1'});local.start();self.addCleanup(local.stop)
  self.tmp=tempfile.TemporaryDirectory();api.DB=str(Path(self.tmp.name)/'demo.sqlite3');self.c=TestClient(api.app,base_url='http://127.0.0.1',client=('127.0.0.1',50000))
  r=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Demo Learner','grade':11});self.assertEqual(r.status_code,200);self.pid=r.json()['profile']['id']
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def url(self,path):return f'/api/profiles/{self.pid}'+path
 def complete(self):
  for i,quest in enumerate(api.QUESTS):
   r=self.c.post(self.url(f'/quests/{i}'),json={'option':next(iter(quest['options']))});self.assertEqual(r.status_code,200)
 def confirm(self):return self.c.post(self.url('/confirm'),json={'interests':['science','technology'],'learning_style':'Hands-on projects','goal':'Explore careers'})
 def test_confirm_gate_and_versions(self):
  self.assertEqual(self.c.post(self.url('/roadmap/propose'),json={}).status_code,409)
  self.assertEqual(self.confirm().status_code,409)
  self.complete();self.assertEqual(self.c.post(self.url('/explore'),json={'message':'Explore careers'}).status_code,409)
  self.assertEqual(self.confirm().json()['confirmation_version'],1)
  self.assertEqual(self.confirm().json()['confirmation_version'],1)
  updated=self.c.post(self.url('/confirm'),json={'interests':['art'],'learning_style':'Creative activities','goal':'Explore careers'})
  self.assertEqual(updated.json()['confirmation_version'],2)
  self.assertEqual(self.c.get(self.url('')).json()['confirmation_version'],2)
 def test_quest_invalid_and_idempotency(self):
  self.assertEqual(self.c.post(self.url('/quests/1'),json={'option':'invalid'}).status_code,409)
  self.assertEqual(self.c.post(self.url('/quests/0'),json={'option':'invalid'}).status_code,400)
  opt=next(iter(api.QUESTS[0]['options']))
  self.assertEqual(self.c.post(self.url('/quests/0'),json={'option':opt}).status_code,200)
  self.assertEqual(self.c.post(self.url('/quests/0'),json={'option':opt}).status_code,409)
  self.assertEqual(self.c.get(self.url('')).json()['profile']['xp'],20)
 def test_research_failure_and_plan_tamper(self):
  self.complete();self.confirm()
  fail=self.c.post(self.url('/explore'),json={'message':'Explore careers','simulate_failure':True}).json()
  self.assertEqual(fail['status'],'blocked')
  proposal=self.c.post(self.url('/roadmap/propose'),json={}).json()['plan']
  tampered=dict(proposal);tampered['activities']=['Guaranteed admission']
  self.assertEqual(self.c.post(self.url('/roadmap/save'),json={'plan':tampered}).status_code,409)
  saved=self.c.post(self.url('/roadmap/save'),json={'plan':proposal})
  self.assertEqual(saved.status_code,200)
  self.assertEqual(saved.json()['latest_plan']['version'],1)
 def test_profile_history_survives_timeline_window(self):
  self.complete();self.confirm()
  for _ in range(31):
   r=self.c.post(self.url('/reflect'),json={'message':'Synthetic reflection'})
   self.assertEqual(r.status_code,200)
  before=self.c.get(self.url('')).json()
  self.assertEqual(len(before['events']),30)
  self.assertEqual(len(before['quest_answers']),len(api.QUESTS))
  summary=self.c.get(self.url('/summary')).json()
  self.assertEqual(len(summary['choices']),len(api.QUESTS))
  self.assertEqual(summary['suggested_interests'],['technology','science','building'])
  repeated=self.confirm().json()
  self.assertEqual(repeated['confirmation_version'],1)
  self.assertEqual(repeated['profile']['xp'],before['profile']['xp'])
  self.assertEqual(before['profile_preferences']['learning_style'],'Hands-on projects')
  self.assertEqual(before['profile_preferences']['goal'],'Explore careers')
  self.assertEqual(before['reflection_count'],31)
 def test_journey_research_progress_survives_reload_and_failure(self):
  self.complete();self.confirm()
  self.assertEqual(self.c.get(self.url('')).json()['research_count'],0)
  researched=self.c.post(self.url('/explore'),json={'message':'Explore software careers'}).json()
  self.assertEqual(researched['status'],'ok')
  self.c.post(self.url('/explore'),json={'message':'Explore college majors','simulate_failure':True})
  persisted=self.c.get(self.url('')).json()
  self.assertEqual(persisted['research_count'],1)
  self.assertEqual(persisted['last_research']['matches'],researched['matches'])
  self.assertTrue(all(s['live_verified'] is False for s in persisted['last_research']['sources']))
 def test_groq_api_routing_and_confirmation_gate(self):
  target='careerquest.graph.groq_choose' if api.ENGINE=='langgraph' else 'careerquest.agent.groq_choose'
  with patch(target,return_value='research_college') as model:
   self.assertEqual(self.c.post(self.url('/explore'),json={'message':'Explore careers','use_groq':True}).status_code,409)
   model.assert_not_called()
   self.complete();self.confirm()
   response=self.c.post(self.url('/explore'),json={'message':'Explore careers','use_groq':True})
   self.assertEqual(response.status_code,200)
   self.assertEqual(response.json()['action'],'research_college')
   self.assertEqual(response.json()['trace'][0]['method'],'groq')
   model.assert_called_once()
 def test_quest_revisions_keep_history_and_do_not_repeat_rewards(self):
  self.complete();self.confirm()
  before=self.c.get(self.url('')).json()
  edited=self.c.post(self.url('/quests/0'),json={'option':'Sketch an invention','revise':True}).json()
  self.assertEqual(edited['profile']['xp'],before['profile']['xp'])
  self.assertFalse(edited['confirmed'])
  self.assertEqual(edited['profile_version'],2)
  self.assertEqual(edited['quest_count'],3)
  self.assertEqual(edited['quest_answers'][0]['payload']['choice'],'Sketch an invention')
  self.assertTrue(any(e['kind']=='quest_completed' and e['payload']['choice']=='Build a mini-app' for e in edited['events']))
  repeated=self.c.post(self.url('/quests/0'),json={'option':'Sketch an invention','revise':True}).json()
  self.assertEqual(repeated['profile']['xp'],before['profile']['xp'])
  summary=self.c.get(self.url('/summary')).json()
  self.assertEqual(summary['choices'][0]['choice'],'Sketch an invention')
  for path,body in [('/explore',{'message':'Explore careers'}),('/roadmap/propose',{}),('/roadmap/save',{'plan':{}})]:
   self.assertEqual(self.c.post(self.url(path),json=body).status_code,409)
 def test_profile_drafts_are_persisted_and_require_reconfirmation(self):
  self.complete();self.confirm()
  original=self.c.get(self.url('')).json()
  values={'interests':['art'],'learning_style':'Creative activities','goal':'Try a mini-project','correction':'Synthetic correction: explore design','expected_version':1,'start_edit':True}
  drafted=self.c.post(self.url('/draft'),json=values).json()
  self.assertFalse(drafted['confirmed'])
  self.assertEqual(drafted['profile_version'],2)
  self.assertEqual(drafted['profile']['interests'],original['profile']['interests'])
  self.assertEqual(drafted['profile']['xp'],70)
  self.assertEqual(self.c.get(self.url('')).json()['profile_draft']['correction'],values['correction'])
  self.assertEqual(self.c.post(self.url('/explore'),json={'message':'Explore careers'}).status_code,409)
  stale=self.c.post(self.url('/confirm'),json={**values,'expected_version':1})
  self.assertEqual(stale.status_code,409)
  confirmed=self.c.post(self.url('/confirm'),json={**values,'expected_version':2}).json()
  self.assertTrue(confirmed['confirmed'])
  self.assertEqual(confirmed['confirmation_version'],2)
  self.assertEqual(confirmed['profile']['interests'],['art'])
  self.assertEqual(confirmed['profile_preferences']['quest_answers'][0]['choice'],'Build a mini-app')
  self.assertTrue(confirmed['profile_preferences']['quest_answers'][0]['answered_at'])
  duplicate=self.c.post(self.url('/confirm'),json={**values,'expected_version':2}).json()
  self.assertEqual(duplicate['profile']['xp'],80)
 def test_unsure_profile_and_optional_correction(self):
  self.assertEqual(self.c.post(self.url('/draft'),json={}).status_code,409)
  self.complete()
  response=self.c.post(self.url('/confirm'),json={'interests':[],'not_sure':True,'correction':'Synthetic explorer is still deciding','goal':'Not sure yet'})
  self.assertEqual(response.status_code,200)
  self.assertTrue(response.json()['profile_preferences']['not_sure'])
  self.assertEqual(response.json()['profile']['interests'],[])
 def test_reopening_an_unchanged_profile_cannot_repeat_xp(self):
  self.complete();self.confirm()
  for version in (1,2):
   body={'interests':['science','technology'],'learning_style':'Hands-on projects','goal':'Explore careers','expected_version':version,'start_edit':True}
   draft=self.c.post(self.url('/draft'),json=body).json()
   self.assertFalse(draft['confirmed'])
   confirmed=self.c.post(self.url('/confirm'),json={**body,'expected_version':version+1}).json()
   self.assertTrue(confirmed['confirmed'])
   self.assertEqual(confirmed['profile']['xp'],70)
if __name__=='__main__':unittest.main()
