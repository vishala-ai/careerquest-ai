"""Explicit-local tester boundary; mock model inference, real graph and SQLite."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api
from careerquest.store import connect

class DeveloperResearchTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        db=patch.object(api,'DB',str(Path(temp.name)/'fictional.sqlite3'));db.start();self.addCleanup(db.stop)
        env=patch.dict(os.environ,{'CAREERQUEST_ENV':'production','CAREERQUEST_DEV_TOOLS':'0','CAREERQUEST_HOST':'127.0.0.1','CAREERQUEST_CAREER_GROQ':'0'});env.start();self.addCleanup(env.stop)
        self.c=TestClient(api.app,base_url='http://127.0.0.1',client=('127.0.0.1',49001));self.addCleanup(self.c.close)
        self.pid=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Debug Explorer','grade':11}).json()['profile']['id'];self.base='/api/profiles/'+self.pid
        for i,q in enumerate(api.QUESTS):self.c.post(self.base+f'/quests/{i}',json={'option':next(iter(q['options']))})
        self.c.post(self.base+'/confirm',json={'interests':['art'],'correction':'PRIVATE_AUDIT_SENTINEL'})
        self.dev='/api/developer/profiles/'+self.pid
        self.target='careerquest.graph.groq_choose' if api.ENGINE=='langgraph' else 'careerquest.agent.groq_choose'
    def local(self):return patch.dict(os.environ,{'CAREERQUEST_ENV':'local','CAREERQUEST_DEV_TOOLS':'1'})
    def overview(self):return self.c.get(self.base+'/career-discovery').json()
    def test_default_student_cannot_open_debug_page_read_receipts_or_run_tools(self):
        with patch.object(api,'RUN') as run:
            for url in ('/developer','/api/developer/access',self.dev+'/research-receipts'):
                self.assertEqual(self.c.get(url).status_code,403)
            self.assertEqual(self.c.post(self.dev+'/research',json={'message':'Explore careers','simulate_failure':True}).status_code,403)
            run.assert_not_called()
    def test_production_and_shared_bind_stay_disabled_even_with_tools_flag(self):
        for env in ({'CAREERQUEST_ENV':'production','CAREERQUEST_DEV_TOOLS':'1'},{'CAREERQUEST_ENV':'local','CAREERQUEST_DEV_TOOLS':'0'},{'CAREERQUEST_ENV':'local','CAREERQUEST_DEV_TOOLS':'1','CAREERQUEST_HOST':'0.0.0.0'}):
            with patch.dict(os.environ,env):self.assertEqual(self.c.get('/api/developer/access').status_code,403)
    def test_local_mode_rejects_remote_peers_hosts_origins_and_proxy_headers(self):
        with self.local():
            with TestClient(api.app,base_url='http://127.0.0.1',client=('203.0.113.5',40000)) as remote:
                self.assertEqual(remote.get('/api/developer/access',headers={'x-forwarded-for':'127.0.0.1'}).status_code,403)
                self.assertEqual(remote.get('/api/developer/access').status_code,403)
            for headers in ({'host':'shared.example'},{'origin':'https://remote.example'},{'origin':'null'},{'sec-fetch-site':'cross-site'},{'forwarded':'for=127.0.0.1'},{'x-forwarded-host':'localhost'},{'x-forwarded-for':'127.0.0.1'},{'host':'['}):
                self.assertEqual(self.c.get('/api/developer/access',headers=headers).status_code,403,headers)
    def test_local_top_level_navigation_can_open_shell_but_cannot_fetch_receipts_cross_site(self):
        headers={'sec-fetch-site':'cross-site','sec-fetch-mode':'navigate','sec-fetch-dest':'document'}
        with self.local():
            page=self.c.get('/developer',headers=headers)
            self.assertIn(page.status_code,(200,503))  # 503 is the explicit not-built state.
            if page.status_code==200:self.assertEqual(page.headers['x-frame-options'],'DENY')
            self.assertEqual(self.c.get(self.dev+'/research-receipts',headers=headers).status_code,403)
            self.assertEqual(self.c.get('/developer',headers={**headers,'sec-fetch-dest':'iframe'}).status_code,403)
        self.assertEqual(self.c.get('/developer',headers=headers).status_code,403)
    def test_student_cannot_inject_routing_or_failure_controls_through_new_or_legacy_routes(self):
        with patch.object(api,'RUN') as run:
            for suffix,body in [('/worlds/design/explore',{'simulate_failure':True}),('/career-guide',{'message':'Explore careers','use_groq':True}),('/career-guide',{'message':'Explore careers','use_groq':False}),('/career-guide',{'message':'Explore careers','simulate_failure':True}),('/explore',{'message':'Explore careers','simulate_failure':True}),('/explore',{'message':'Explore careers','use_groq':True}),('/reflect',{'message':'Explore careers','simulate_failure':True})]:
                self.assertEqual(self.c.post(self.base+suffix,json=body).status_code,403,suffix)
            run.assert_not_called()
    def test_local_developer_inspects_actual_sanitized_saved_traces_without_student_data(self):
        result=self.c.post(self.base+'/worlds/design/explore',json={}).json()
        with self.local():
            access=self.c.get('/api/developer/access');self.assertEqual(access.status_code,200)
            saved=self.c.get(self.dev+'/research-receipts').json()['receipts'][0]
        self.assertEqual(saved['run_id'],result['run_id']);self.assertEqual(saved['trace'][0]['method'],'student_world_selection')
        self.assertEqual(saved['world_ids'],['design']);self.assertTrue(saved['source_validation']['all_metadata_valid']);self.assertTrue(saved['source_validation']['evidence_references_valid'])
        self.assertNotIn('Fictional Debug Explorer',json.dumps(saved));self.assertNotIn('PRIVATE_AUDIT_SENTINEL',json.dumps(saved));self.assertNotIn('interests',json.dumps(saved))
    def test_local_failure_simulation_is_bounded_and_does_not_award_xp_or_shortlist(self):
        before=self.c.get(self.base).json()['profile']['xp']
        with self.local():
            response=self.c.post(self.dev+'/research',json={'message':'Explore career','world_ids':['design'],'simulate_failure':True})
        self.assertEqual(response.status_code,200);receipt=response.json()['receipt'];self.assertEqual(receipt['status'],'blocked')
        self.assertTrue(any(t.get('error_type')=='ConnectionError' for t in receipt['trace']));self.assertFalse(receipt['source_validation']['all_metadata_valid'])
        self.assertEqual(self.overview()['portfolio'],{'explorations':[],'shortlist':[]});self.assertEqual(self.c.get(self.base).json()['profile']['xp'],before)
    def test_controlled_request_returns_its_own_receipt_if_another_run_finishes(self):
        run=api.RUN;ids=[]
        def interleaved(c,pid,*args,**kwargs):
            result=run(c,pid,*args,**kwargs);ids.append(result['run_id'])
            run(c,pid,'Explore another career',world_ids=['software'],research_only=True)
            return result
        with self.local(),patch.object(api,'RUN',side_effect=interleaved):
            response=self.c.post(self.dev+'/research',json={'message':'Explore careers','world_ids':['design']})
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['receipt']['run_id'],ids[0]);self.assertEqual(response.json()['receipt']['world_ids'],['design'])
    def test_groq_model_is_recorded_only_for_actual_model_routing_and_survives_configuration_change(self):
        with self.local(),patch.dict(os.environ,{'GROQ_MODEL':'openai/gpt-oss-120b'}),patch(self.target,return_value='research_college'):
            result=self.c.post(self.dev+'/research',json={'message':'PRIVATE_QUESTION_SENTINEL college','use_groq':True}).json()['receipt']
        self.assertEqual(result['trace'][0]['model'],'openai/gpt-oss-120b');self.assertEqual(result['trace'][0]['method'],'groq');self.assertEqual(result['action'],'research_college')
        self.assertNotIn('PRIVATE_QUESTION_SENTINEL',json.dumps(result))
        with self.local(),patch.dict(os.environ,{'GROQ_MODEL':'changed-model'}):
            saved=self.c.get(self.dev+'/research-receipts').json()['receipts'][0]
        self.assertEqual(saved,result)
    def test_model_timeout_is_labeled_fallback_and_never_exposes_exception_body(self):
        with self.local(),patch(self.target,side_effect=TimeoutError('SECRET_PROVIDER_BODY')):
            response=self.c.post(self.dev+'/research',json={'message':'Explore careers','use_groq':True})
        r=response.json()['receipt'];self.assertEqual(r['trace'][0]['method'],'bounded_policy_fallback');self.assertEqual(r['trace'][0]['error_type'],'TimeoutError')
        self.assertNotIn('model',r['trace'][0]);self.assertNotIn('SECRET_PROVIDER_BODY',response.text)
    def test_local_tools_still_require_confirmed_profile_and_valid_catalogue(self):
        with self.local():
            self.assertEqual(self.c.post(self.dev+'/research',json={'message':'Explore careers','world_ids':['fake']}).status_code,404)
            self.c.post(self.base+'/draft',json={'interests':['science'],'start_edit':True})
            self.assertEqual(self.c.post(self.dev+'/research',json={'message':'Explore careers','world_ids':['design']}).status_code,409)
    def test_student_selection_and_next_step_survive_reload_and_profile_edits(self):
        self.assertEqual(self.overview()['next_action']['kind'],'explore_world')
        result=self.c.post(self.base+'/worlds/design/explore',json={}).json();eid=result['exploration_ids']['design']
        self.assertEqual(self.overview()['next_action']['kind'],'save_career');self.assertEqual(self.overview()['next_action']['exploration_id'],eid)
        for _ in range(2):self.assertEqual(self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid}).status_code,200)
        self.assertEqual(self.overview()['next_action']['kind'],'choose_paths');self.assertEqual(len(self.overview()['portfolio']['shortlist']),1)
        data=self.overview()
        self.assertEqual(self.c.post(self.base+'/career-paths',json={'primary_world_id':'design','expected_profile_version':data['profile_context']['profile_version'],'expected_path_version':0}).status_code,200)
        self.assertEqual(self.overview()['next_action']['kind'],'view_portfolio')
        with TestClient(api.app) as fresh:self.assertEqual(fresh.get(self.base+'/career-discovery').json(),self.overview())
        self.c.post(self.base+'/draft',json={'interests':['science'],'start_edit':True})
        self.assertEqual(self.overview()['next_action']['kind'],'review_profile')
        self.c.post(self.base+'/confirm',json={'interests':['science']})
        self.assertEqual(self.overview()['next_action']['kind'],'explore_world');self.assertEqual(len(self.overview()['portfolio']['shortlist']),1)
    def test_student_comparisons_and_server_selected_groq_policy_still_work(self):
        compare=self.c.post(self.base+'/career-guide',json={'message':'Compare worlds','world_ids':['design','software']})
        self.assertEqual(compare.status_code,200);self.assertEqual(len(compare.json()['worlds']),2)
        with patch.dict(os.environ,{'CAREERQUEST_CAREER_GROQ':'1'}),patch(self.target,return_value='research_college') as model:
            result=self.c.post(self.base+'/career-guide',json={'message':'Explore college options'}).json()
        model.assert_called_once();self.assertEqual(result['trace'][0]['method'],'groq');self.assertEqual(result['action'],'research_college')
    def test_older_receipts_do_not_claim_current_model(self):
        result=self.c.post(self.base+'/worlds/design/explore',json={}).json()
        with connect(api.DB) as c:
            row=c.execute('SELECT result FROM runs WHERE id=?',(result['run_id'],)).fetchone();data=json.loads(row[0]);data['trace']=[{'step':'route','method':'groq','action':'research_careers'}]
            c.execute('UPDATE runs SET result=? WHERE id=?',(json.dumps(data),result['run_id']))
        with self.local():r=self.c.get(self.dev+'/research-receipts').json()['receipts'][0]
        self.assertNotIn('model',r['trace'][0])

if __name__=='__main__':unittest.main()
