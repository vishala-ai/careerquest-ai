"""Career Worlds: fictional fixtures, real LangGraph/SQLite, model calls mocked."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api, agent, career_worlds as worlds
from careerquest.store import connect

class CareerWorldTests(unittest.TestCase):
    def setUp(self):
        local=patch.dict(os.environ,{'CAREERQUEST_ENV':'local','CAREERQUEST_DEV_TOOLS':'1','CAREERQUEST_CAREER_GROQ':'0'});local.start();self.addCleanup(local.stop)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=str(Path(self.temp.name)/'fictional.sqlite3')
        override=patch.object(api,'DB',self.path);override.start();self.addCleanup(override.stop)
        self.c=TestClient(api.app,base_url='http://127.0.0.1',client=('127.0.0.1',50000));self.addCleanup(self.c.close)
        self.pid=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Career Explorer','grade':10}).json()['profile']['id']
        self.base='/api/profiles/'+self.pid
        for step,quest in enumerate(api.QUESTS):self.c.post(self.base+f'/quests/{step}',json={'option':next(iter(quest['options']))})
        self.c.post(self.base+'/confirm',json={'interests':['art'],'goal':'Explore'} )
    def state(self):return self.c.get(self.base).json()
    def overview(self):return self.c.get(self.base+'/career-discovery').json()
    def explore(self,wid='design',**body):return self.c.post(self.base+f'/worlds/{wid}/explore',json=body)
    def test_confirmed_personalization_and_complete_catalogue(self):
        result=self.overview();self.assertTrue(result['confirmed']);self.assertEqual(result['confirmed_interests'],['art'])
        self.assertEqual([w['world_id'] for w in result['worlds'] if w['recommended']],['design'])
        self.assertEqual({w['world_id'] for w in result['worlds']},set(worlds.approved()))
        self.assertEqual(result['portfolio'],{'explorations':[],'shortlist':[]})
    def test_legacy_confirmed_profile_uses_saved_interests_without_handoff_backfill(self):
        with connect(self.path) as c:c.execute('DELETE FROM discovery_handoffs WHERE profile_id=?',(self.pid,))
        self.assertEqual([w['world_id'] for w in self.overview()['worlds'] if w['recommended']],['design'])
        self.assertIsNone(self.state()['discovery_handoff']['active'])
    def test_every_world_invokes_research_tool_with_stable_ids_and_evidence(self):
        target='careerquest.graph.execute' if api.ENGINE=='langgraph' else 'careerquest.agent.execute'
        for wid in worlds.approved():
            with patch(target,wraps=agent.execute) as execute:
                response=self.explore(wid)
            self.assertEqual(response.status_code,200);result=response.json();self.assertEqual(result['action'],'research_careers')
            self.assertEqual(execute.call_args.kwargs['world_ids'],[wid])
            world=result['worlds'][0];self.assertEqual(world['world_id'],wid)
            self.assertEqual(result['trace'][0]['method'],'student_world_selection')
            sources={s['id'] for s in world['sources']};self.assertTrue(sources)
            for item in [world['overview'],*world['activities'],*world['skills'],*world['educational_fields']]:self.assertTrue(set(item['source_ids'])<=sources)
            self.assertTrue(all(s['url'].startswith('https://') and s['live_verified'] is False for s in world['sources']))
        self.assertEqual(len(self.overview()['portfolio']['explorations']),4)
        self.assertEqual(self.overview()['portfolio']['shortlist'],[])
        self.assertEqual(self.state()['profile']['xp'],70)
    def test_explicit_shortlist_is_idempotent_and_revisitable(self):
        result=self.explore().json();eid=result['exploration_ids']['design']
        self.assertEqual(self.overview()['portfolio']['shortlist'],[])
        saved=self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid})
        self.assertEqual(saved.status_code,200);self.assertEqual(len(saved.json()['shortlist']),1)
        self.assertEqual(self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid}).json(),saved.json())
        before=self.state();item=self.c.get(self.base+'/career-explorations/'+eid).json()
        self.assertEqual(item['world'],result['worlds'][0]);self.assertFalse(item['is_stale'])
        self.assertEqual(self.state(),before)
    def test_unconfirmed_gates_all_personalized_operations(self):
        self.c.post(self.base+'/draft',json={'interests':['art'],'start_edit':True})
        before=self.state()
        for path,body in [('/worlds/design/explore',{}),('/career-guide',{'message':'Compare careers','use_groq':True}),('/career-shortlist',{'exploration_id':'unknown'})]:
            self.assertEqual(self.c.post(self.base+path,json=body).status_code,409)
        self.assertTrue(all(not w['recommended'] for w in self.overview()['worlds']));self.assertEqual(len(self.overview()['worlds']),4)
        self.assertEqual(self.state(),before)
    def test_unsupported_ids_do_not_create_runs_or_exploration(self):
        before=self.state()
        for wid in ('made-up','college','aid','onet'):
            self.assertEqual(self.explore(wid).status_code,404)
        self.assertEqual(self.c.post(self.base+'/career-guide',json={'message':'Compare','world_ids':['design','design']}).status_code,404)
        self.assertEqual(self.state(),before);self.assertEqual(self.overview()['portfolio']['explorations'],[])
    def test_missing_sources_and_simulated_failure_invent_nothing(self):
        docs=copy.deepcopy(worlds.detail_records());docs['design']['source']={}
        with patch('careerquest.career_worlds.detail_records',return_value=docs):result=self.explore().json()
        self.assertEqual(result['status'],'blocked');self.assertEqual(result['sources'],[]);self.assertEqual(result['worlds'],[])
        failed=self.explore(simulate_failure=True).json();self.assertEqual(failed['status'],'blocked');self.assertEqual(failed['sources'],[])
        self.assertEqual(self.overview()['portfolio']['explorations'],[])
    def test_groq_timeout_uses_labeled_bounded_research_fallback(self):
        target='careerquest.graph.groq_choose' if api.ENGINE=='langgraph' else 'careerquest.agent.groq_choose'
        with patch(target,side_effect=TimeoutError):result=self.c.post(self.base+'/career-guide',json={'message':'Explore software careers','use_groq':True}).json()
        self.assertEqual(result['status'],'ok');self.assertEqual(result['trace'][0]['method'],'bounded_policy_fallback')
        self.assertTrue(result['sources']);self.assertEqual(self.state()['profile']['xp'],70)
    def test_optional_ai_routing_cannot_reflect_or_create_plans(self):
        target='careerquest.graph.groq_choose' if api.ENGINE=='langgraph' else 'careerquest.agent.groq_choose'
        for action in ('reflect','create_plan','ask_question'):
            with patch(target,return_value=action):result=self.c.post(self.base+'/career-guide',json={'message':'I prefer a different career','use_groq':True}).json()
            self.assertEqual(result['action'],'research_careers');self.assertTrue(any(t.get('step')=='research_guard' for t in result['trace']))
        self.assertEqual(self.state()['reflection_count'],0);self.assertIsNone(self.state()['latest_plan']);self.assertEqual(self.state()['profile']['xp'],70)
    def test_optional_college_question_and_explicit_comparison_routing(self):
        result=self.c.post(self.base+'/career-guide',json={'message':'Explore college majors'}).json();self.assertEqual(result['action'],'research_college')
        compare=self.c.post(self.base+'/career-guide',json={'message':'Compare these worlds','world_ids':['design','software']}).json()
        self.assertEqual([w['world_id'] for w in compare['worlds']],['design','software']);self.assertEqual(len(compare['exploration_ids']),2)
        self.assertEqual(self.overview()['portfolio']['shortlist'],[])
    def test_profile_change_preserves_history_but_blocks_new_saves(self):
        result=self.explore().json();eid=result['exploration_ids']['design'];self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid})
        self.c.post(self.base+'/draft',json={'interests':['coding'],'start_edit':True})
        old=self.c.get(self.base+'/career-explorations/'+eid).json();self.assertTrue(old['is_stale'])
        self.c.post(self.base+'/confirm',json={'interests':['coding']})
        self.assertEqual(self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid}).status_code,409)
        self.assertEqual(len(self.overview()['portfolio']['shortlist']),1)
    def test_cross_profile_selection_and_revisit_rejected(self):
        eid=self.explore().json()['exploration_ids']['design']
        other=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Other Fictional','grade':12}).json()['profile']['id']
        self.assertEqual(self.c.get('/api/profiles/'+other+'/career-explorations/'+eid).status_code,404)
        with connect(self.path) as c:
            with self.assertRaises(worlds.WorldUnknown):worlds.exploration(c,other,eid)
    def test_profile_change_during_model_request_does_not_persist_stale_research(self):
        target='careerquest.graph.groq_choose' if api.ENGINE=='langgraph' else 'careerquest.agent.groq_choose'
        def changed(*args):
            self.c.post(self.base+'/draft',json={'interests':['science'],'start_edit':True});return 'research_careers'
        with patch(target,side_effect=changed):response=self.c.post(self.base+'/career-guide',json={'message':'Explore career ideas','use_groq':True})
        self.assertEqual(response.status_code,409)
        with connect(self.path) as c:self.assertEqual(c.execute('SELECT count(*) FROM runs WHERE profile_id=?',(self.pid,)).fetchone()[0],0)
    def test_portfolio_survives_reload_and_fresh_process_without_xp_changes(self):
        eid=self.explore().json()['exploration_ids']['design'];self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid});expected=self.overview()['portfolio']
        with TestClient(api.app) as fresh:self.assertEqual(fresh.get(self.base+'/career-discovery').json()['portfolio'],expected)
        code='import json,sys; from careerquest.store import connect; from careerquest.career_worlds import portfolio; c=connect(sys.argv[1]); print(json.dumps(portfolio(c,sys.argv[2])))'
        result=subprocess.run([sys.executable,'-c',code,self.path,self.pid],check=True,capture_output=True,text=True)
        self.assertEqual(json.loads(result.stdout),expected);self.assertEqual(self.state()['profile']['xp'],70)
    def test_core_fallback_supports_the_same_stable_world_tool(self):
        with connect(self.path) as c:result=agent.run(c,self.pid,'Explore selected world',world_ids=['software'],research_only=True)
        self.assertEqual(result['worlds'][0]['world_id'],'software');self.assertEqual(result['action'],'research_careers')
        self.assertEqual(len(self.overview()['portfolio']['explorations']),1)
    def test_run_and_exploration_roll_back_together_on_storage_failure(self):
        from careerquest.store import record_run
        def fail_after_run(*args):
            record_run(*args);raise RuntimeError('Synthetic storage failure')
        with patch('careerquest.career_worlds.record_run',side_effect=fail_after_run):
            with self.assertRaises(RuntimeError):self.explore()
        with connect(self.path) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM runs').fetchone()[0],0)
            self.assertEqual(c.execute('SELECT count(*) FROM career_explorations').fetchone()[0],0)

if __name__=='__main__':unittest.main()
