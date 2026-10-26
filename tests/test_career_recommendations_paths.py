"""Recommendations-first contracts and immutable, explicitly chosen paths."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api,career_worlds
from careerquest.store import connect

class CareerRecommendationPathTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.path=str(Path(temp.name)/'fictional.sqlite3')
        db=patch.object(api,'DB',self.path);db.start();self.addCleanup(db.stop)
        env=patch.dict(os.environ,{'CAREERQUEST_CAREER_GROQ':'0','CAREERQUEST_DEV_TOOLS':'0'});env.start();self.addCleanup(env.stop)
        self.c=TestClient(api.app);self.addCleanup(self.c.close)
        self.pid=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Path Explorer','grade':10}).json()['profile']['id'];self.base='/api/profiles/'+self.pid
        for i,q in enumerate(api.QUESTS):self.c.post(self.base+f'/quests/{i}',json={'option':next(iter(q['options']))})
        self.confirm(['technology'])
    def confirm(self,interests,**extra):return self.c.post(self.base+'/confirm',json={'interests':interests,**extra})
    def overview(self):return self.c.get(self.base+'/career-discovery').json()
    def explore(self,wid):return self.c.post(self.base+f'/worlds/{wid}/explore',json={}).json()
    def save(self,wid):
        eid=self.explore(wid)['exploration_ids'][wid]
        self.assertEqual(self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid}).status_code,200)
        return eid
    def paths(self,primary='software',secondary=None,**extra):
        data=self.overview();body={'primary_world_id':primary,'secondary_world_id':secondary,'expected_profile_version':data['profile_context']['profile_version'] if data['profile_context'] else 1,'expected_path_version':data['path_preferences']['latest']['version'] if data['path_preferences']['latest'] else 0,**extra}
        return self.c.post(self.base+'/career-paths',json=body)
    def test_three_supported_recommendations_are_distinct_and_grounded_in_latest_confirmation(self):
        data=self.overview();recommended=[w for w in data['worlds'] if w['recommended']]
        self.assertEqual(len(recommended),3);self.assertEqual(len({w['world_id'] for w in recommended}),3)
        for w in recommended:
            self.assertIn('technology',w['reason']);self.assertTrue(w['description']);self.assertTrue(w['evidence_ids'])
            self.assertTrue(any(ref.startswith(data['profile_context']['confirmation_event_id']) for ref in w['evidence_ids']))
        self.assertEqual(data['portfolio']['shortlist'],[]);self.assertIsNone(data['path_preferences']['active'])
    def test_one_two_and_zero_matches_never_pad_or_hide_catalogue(self):
        for interests,expected in [(['art'],1),(['biology'],2),(['unmatched interest'],0),([],0)]:
            self.assertEqual(self.confirm(interests).status_code,200);data=self.overview()
            self.assertEqual(len([w for w in data['worlds'] if w['recommended']]),expected,interests)
            self.assertEqual({w['world_id'] for w in data['worlds']},set(career_worlds.approved()))
    def test_confirmed_handoff_is_prioritized_but_other_supported_matches_can_be_suggested(self):
        self.confirm(['technology'],selected_world_ids=['software'])
        recommended=[w['world_id'] for w in self.overview()['worlds'] if w['recommended']]
        self.assertEqual(set(recommended),{'bioengineering','software','design'})
        # The handoff remains the student's immutable approved record.
        self.assertEqual(self.c.get(self.base).json()['discovery_handoff']['active']['suggested_world_ids'],['software'])
    def test_exploratory_profile_does_not_force_recommendations_or_paths(self):
        self.confirm(['technology'],not_sure=True);data=self.overview()
        self.assertFalse(any(w['recommended'] for w in data['worlds']));self.assertIsNone(data['path_preferences']['active'])
    def test_landing_reads_do_not_resume_research_or_change_saved_state(self):
        self.explore('software')
        with connect(self.path) as c:before=[tuple(r) for r in c.execute('SELECT * FROM runs')]
        for _ in range(3):
            data=self.overview();self.assertNotIn('selected_detail',data);self.assertEqual(len([w for w in data['worlds'] if w['recommended']]),3)
        with connect(self.path) as c:self.assertEqual([tuple(r) for r in c.execute('SELECT * FROM runs')],before)
    def test_two_and_three_career_comparisons_use_real_tool_and_citations_without_saving_shortlist(self):
        for ids in (['design','software'],['design','software','environment']):
            response=self.c.post(self.base+'/career-guide',json={'message':'Compare careers','world_ids':ids});self.assertEqual(response.status_code,200)
            result=response.json();self.assertEqual(result['action'],'research_careers');self.assertEqual([w['world_id'] for w in result['worlds']],ids)
            for world in result['worlds']:
                sources={s['id'] for s in world['sources']}
                for item in [world['overview'],*world['skills'],*world['activities'],*world['educational_fields']]:self.assertTrue(set(item['source_ids'])<=sources)
        self.assertEqual(self.overview()['portfolio']['shortlist'],[])
    def test_comparison_rejects_duplicates_unknown_ids_and_more_than_three(self):
        for ids,code in [(['software','software'],404),(['fake','design'],404),(['software','design','bioengineering','environment'],422)]:
            self.assertEqual(self.c.post(self.base+'/career-guide',json={'message':'Compare careers','world_ids':ids}).status_code,code)
    def test_paths_require_explicit_current_shortlist_not_recommendations_or_exploration_alone(self):
        self.assertEqual(self.paths().status_code,409);self.explore('software');self.assertEqual(self.paths().status_code,409)
        self.save('software');data=self.overview();self.assertIsNone(data['path_preferences']['active'])
        response=self.paths();self.assertEqual(response.status_code,200);active=response.json()['active'];self.assertEqual(active['primary_world_id'],'software');self.assertIsNone(active['secondary_world_id'])
        self.assertEqual(active['profile_version'],data['profile_context']['profile_version']);self.assertEqual(active['confirmation_event_id'],data['profile_context']['confirmation_event_id'])
        self.assertTrue(active['paths'][0]['sources']);self.assertTrue(active['paths'][0]['selection_id']);self.assertTrue(active['paths'][0]['exploration_id'])
    def test_explicit_primary_secondary_changes_append_history_and_are_idempotent(self):
        self.save('software');self.save('design')
        first=self.paths('software','design').json();self.assertEqual(len(first['history']),1)
        repeat=self.paths('software','design',expected_path_version=0).json();self.assertEqual(first,repeat)
        second=self.paths('design','software').json();self.assertEqual(len(second['history']),2);self.assertEqual(second['history'][0],first['history'][0]);self.assertEqual(second['active']['version'],2)
        third=self.paths('design').json();self.assertIsNone(third['active']['secondary_world_id']);self.assertEqual(len(third['history']),3)
        self.assertEqual(self.c.get(self.base).json()['profile']['xp'],70)
    def test_paths_reject_same_or_unsupported_careers_and_unsaved_secondary(self):
        self.save('software')
        self.assertEqual(self.paths('software','software').status_code,404)
        self.assertEqual(self.paths('software','fake').status_code,404)
        self.assertEqual(self.paths('software','design').status_code,409)
        self.assertEqual(self.paths(None).status_code,422)
        self.assertEqual(self.overview()['path_preferences']['history'],[])
    def test_stale_browser_versions_cannot_overwrite_paths(self):
        self.save('software');self.save('design');self.paths('software')
        self.assertEqual(self.paths('design',expected_path_version=0).status_code,409)
        self.assertEqual(self.paths('design',expected_profile_version=999).status_code,409)
        self.assertEqual(self.overview()['path_preferences']['active']['primary_world_id'],'software')
    def test_profile_changes_invalidate_recommendations_and_paths_preserving_history(self):
        self.save('software');self.paths('software');old=self.overview()['path_preferences']['active']
        self.c.post(self.base+'/draft',json={'interests':['nature'],'start_edit':True})
        draft=self.overview();self.assertFalse(any(w['recommended'] for w in draft['worlds']));self.assertIsNone(draft['path_preferences']['active'])
        self.assertTrue(draft['path_preferences']['latest']['is_stale']);self.assertEqual(self.paths().status_code,409)
        self.confirm(['nature']);updated=self.overview();self.assertEqual([w['world_id'] for w in updated['worlds'] if w['recommended']],['environment'])
        self.assertEqual(self.paths('software').status_code,409);self.save('environment')
        fresh=self.paths('environment').json();self.assertEqual(len(fresh['history']),2);self.assertEqual(fresh['history'][0]['id'],old['id']);self.assertTrue(fresh['history'][0]['is_stale'])
    def test_preferences_survive_client_reload_and_fresh_python_process(self):
        self.save('software');expected=self.paths('software').json()
        with TestClient(api.app) as fresh:self.assertEqual(fresh.get(self.base+'/career-discovery').json()['path_preferences'],expected)
        code='import json,sys; from careerquest.store import connect; from careerquest.career_worlds import path_preferences; c=connect(sys.argv[1]); print(json.dumps(path_preferences(c,sys.argv[2])))'
        result=subprocess.run([sys.executable,'-c',code,self.path,self.pid],check=True,capture_output=True,text=True)
        self.assertEqual(json.loads(result.stdout),expected)
    def test_other_students_shortlist_cannot_supply_a_path(self):
        self.save('software');other=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Other Fictional','grade':11}).json()['profile']['id']
        for i,q in enumerate(api.QUESTS):self.c.post(f'/api/profiles/{other}/quests/{i}',json={'option':next(iter(q['options']))})
        self.c.post(f'/api/profiles/{other}/confirm',json={'interests':['technology']})
        response=self.c.post(f'/api/profiles/{other}/career-paths',json={'primary_world_id':'software','expected_profile_version':1,'expected_path_version':0})
        self.assertEqual(response.status_code,409)

if __name__=='__main__':unittest.main()
