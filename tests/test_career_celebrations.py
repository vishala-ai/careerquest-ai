"""Milestone delivery and portfolio snapshots use real SQLite, never model inference."""
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

class CareerCelebrationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.path=str(Path(temp.name)/'fictional.sqlite3')
        db=patch.object(api,'DB',self.path);db.start();self.addCleanup(db.stop)
        env=patch.dict(os.environ,{'CAREERQUEST_CAREER_GROQ':'0','CAREERQUEST_DEV_TOOLS':'0'});env.start();self.addCleanup(env.stop)
        self.c=TestClient(api.app);self.addCleanup(self.c.close)
        self.pid=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Nova Fictional','grade':11}).json()['profile']['id'];self.base='/api/profiles/'+self.pid
        for i,q in enumerate(api.QUESTS):self.c.post(self.base+f'/quests/{i}',json={'option':next(iter(q['options']))})
        self.c.post(self.base+'/confirm',json={'interests':['technology']})
        self.original_events=self.state()['events']
    def state(self):return self.c.get(self.base).json()
    def overview(self):return self.c.get(self.base+'/career-discovery').json()
    def claim(self):return self.c.post(self.base+'/career-celebrations/claim',json={}).json()['celebration']
    def drain(self):
        receipts=[]
        while (item:=self.claim()) is not None:
            receipts.append(item);self.assertEqual(self.c.post(self.base+'/career-celebrations/'+item['id']+'/acknowledge').status_code,200)
        return receipts
    def research(self,wid='software'):return self.c.post(self.base+f'/worlds/{wid}/explore',json={}).json()
    def save(self,wid='software'):
        result=self.research(wid);eid=result['exploration_ids'][wid]
        self.assertEqual(self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid}).status_code,200);return eid
    def paths(self,primary='software',secondary=None):
        data=self.overview();return self.c.post(self.base+'/career-paths',json={'primary_world_id':primary,'secondary_world_id':secondary,'expected_profile_version':data['profile_context']['profile_version'],'expected_path_version':data['path_preferences']['latest']['version'] if data['path_preferences']['latest'] else 0})
    def complete(self,signature=None):
        return self.c.post(self.base+'/career-portfolio/complete',json={'expected_signature':signature or self.overview()['portfolio_completion']['signature'] or '0'*64})
    def test_first_research_uses_saved_identity_and_named_record_and_never_redelivers(self):
        self.research();item=self.claim();self.assertEqual(item['kind'],'first_research');self.assertEqual(item['nickname'],'Nova Fictional');self.assertEqual(item['career_name'],'Software Development')
        self.research();self.research('design');self.assertIsNone(self.claim())
        with TestClient(api.app) as fresh:self.assertIsNone(fresh.post(self.base+'/career-celebrations/claim').json()['celebration'])
        self.assertEqual(self.state()['profile']['xp'],70)
    def test_failed_research_cannot_create_a_celebration(self):
        with patch('careerquest.career_worlds.detail_records',return_value={}):self.assertEqual(self.research()['status'],'blocked')
        self.assertIsNone(self.claim());self.assertEqual(self.state()['profile']['xp'],70)
    def test_first_and_second_distinct_shortlist_additions_not_repeat_saves_or_snapshots(self):
        eid=self.save();self.drain()
        self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid});self.save('software');self.assertIsNone(self.claim())
        self.save('design');item=self.claim();self.assertEqual(item['kind'],'second_shortlist');self.assertEqual(item['career_name'],'Digital Product Design')
        self.save('environment');self.assertIsNone(self.claim());self.assertEqual(len(self.overview()['portfolio']['shortlist']),3)
    def test_first_shortlist_receipt_uses_actual_saved_career_not_a_recommendation(self):
        self.save('environment');items=self.drain();shortlist=next(i for i in items if i['kind']=='first_shortlist')
        self.assertEqual(shortlist['nickname'],'Nova Fictional');self.assertEqual(shortlist['career_name'],'Environmental Science');self.assertEqual(shortlist['world_id'],'environment')
    def test_primary_and_optional_secondary_are_distinct_once_only_milestones(self):
        self.save();self.save('design');self.drain();self.assertEqual(self.paths().status_code,200)
        item=self.claim();self.assertEqual(item['kind'],'primary_path');self.assertEqual(item['career_name'],'Software Development');self.assertIsNone(self.claim())
        self.paths('software','design');item=self.claim();self.assertEqual(item['kind'],'secondary_path');self.assertEqual(item['career_name'],'Digital Product Design')
        self.paths('design','software');self.paths('software');self.paths('software','design');self.assertIsNone(self.claim())
    def test_both_paths_saved_together_are_delivered_one_at_a_time(self):
        self.save();self.save('design');self.drain();self.paths('software','design')
        self.assertEqual(self.claim()['kind'],'primary_path');self.assertEqual(self.claim()['kind'],'secondary_path');self.assertIsNone(self.claim())
    def test_completion_requires_explicit_review_and_secondary_is_not_required(self):
        self.assertEqual(self.complete().status_code,409);self.save();self.assertEqual(self.complete().status_code,409)
        self.paths();self.drain();state=self.overview()['portfolio_completion'];self.assertTrue(state['ready']);self.assertIsNone(state['active'])
        result=self.complete();self.assertEqual(result.status_code,200);active=result.json()['active'];self.assertEqual(active['version'],1);self.assertEqual(active['profile_version'],1)
        self.assertEqual(len(active['snapshot']['paths']),1);self.assertEqual(active['snapshot']['paths'][0]['priority'],'primary');self.assertTrue(active['snapshot']['shortlist'][0]['sources'])
        self.assertEqual(self.claim()['kind'],'portfolio_completed');self.assertIsNone(self.claim())
    def test_duplicate_completion_and_reload_do_not_duplicate_receipts_xp_or_history(self):
        self.save();self.paths();self.drain();first=self.complete().json();self.claim()
        self.assertEqual(self.complete().json(),first);self.assertIsNone(self.claim())
        with TestClient(api.app) as fresh:self.assertEqual(fresh.get(self.base+'/career-discovery').json()['portfolio_completion'],first)
        self.assertEqual(self.state()['profile']['xp'],70);self.assertEqual(self.state()['events'],self.original_events)
    def test_revised_completion_preserves_history_without_replaying_first_time_party(self):
        self.save();self.paths();self.drain();old=self.complete().json()['active'];self.drain()
        self.save('design');self.drain();self.paths('design');self.drain();new=self.complete().json()
        self.assertEqual(len(new['history']),2);self.assertEqual(new['history'][0]['id'],old['id']);self.assertTrue(new['history'][0]['is_stale']);self.assertIsNone(self.claim())
    def test_changed_shortlist_or_stale_signature_requires_review_again(self):
        self.save();self.paths();old_signature=self.overview()['portfolio_completion']['signature'];self.complete()
        self.save('environment');state=self.overview()['portfolio_completion'];self.assertIsNone(state['active']);self.assertTrue(state['ready'])
        self.assertEqual(self.complete(old_signature).status_code,409);self.assertEqual(len(state['history']),1)
    def test_profile_edits_block_completion_and_suppress_old_pending_celebrations(self):
        self.save();self.paths();self.c.post(self.base+'/draft',json={'interests':['nature'],'start_edit':True})
        self.assertIsNone(self.claim());self.assertFalse(self.overview()['portfolio_completion']['ready']);self.assertEqual(self.complete().status_code,409)
        self.c.post(self.base+'/confirm',json={'interests':['nature']});self.assertIsNone(self.claim());self.assertEqual(self.complete().status_code,409)
    def test_dismissal_is_persisted_idempotent_and_owned(self):
        self.research();item=self.claim();url=self.base+'/career-celebrations/'+item['id']+'/acknowledge'
        self.assertEqual(self.c.post(url).status_code,200);self.assertEqual(self.c.post(url).status_code,200)
        with connect(self.path) as c:self.assertTrue(c.execute('SELECT acknowledged_at FROM career_milestones WHERE id=?',(item['id'],)).fetchone()[0])
        other=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Other Fictional','grade':10}).json()['profile']['id']
        self.assertEqual(self.c.post(f'/api/profiles/{other}/career-celebrations/{item["id"]}/acknowledge').status_code,404)
    def test_returning_history_is_not_backfilled_or_misidentified_as_new(self):
        self.save();self.save('design');self.paths('software','design')
        with connect(self.path) as c:c.execute('DELETE FROM career_milestones WHERE profile_id=?',(self.pid,))
        self.research();self.save('environment');self.paths('design','software');self.assertIsNone(self.claim())
    def test_restart_preserves_delivery_and_completed_snapshot(self):
        self.save();self.paths();self.drain();expected=self.complete().json();self.claim()
        code='import json,sys; from careerquest.store import connect; from careerquest.career_milestones import claim; from careerquest.career_worlds import portfolio_completion; c=connect(sys.argv[1]); print(json.dumps([claim(c,sys.argv[2]),portfolio_completion(c,sys.argv[2])]))'
        r=subprocess.run([sys.executable,'-c',code,self.path,self.pid],check=True,capture_output=True,text=True)
        self.assertEqual(json.loads(r.stdout),[{'celebration':None},expected])
    def test_no_fake_client_milestone_or_reward_can_be_created(self):
        self.assertIsNone(self.c.post(self.base+'/career-celebrations/claim',json={'kind':'portfolio_completed','xp':999}).json()['celebration'])
        self.assertEqual(self.c.post(self.base+'/career-portfolio/complete',json={'expected_signature':'0'*64,'xp':999}).status_code,422)
        self.assertEqual(self.state()['profile']['xp'],70)
    def test_missing_nickname_has_neutral_fallback(self):
        with connect(self.path) as c:c.execute('UPDATE profiles SET alias=? WHERE id=?',('',self.pid))
        self.research();self.assertEqual(self.claim()['nickname'],'Explorer')
    def test_recording_failure_rolls_back_research_and_completion_together_with_milestones(self):
        with patch('careerquest.career_milestones.record',side_effect=RuntimeError('test storage failure')):
            with self.assertRaises(RuntimeError):self.research()
        self.assertEqual(self.overview()['portfolio']['explorations'],[])
        self.save();self.paths();self.drain()
        with patch('careerquest.career_milestones.record',side_effect=RuntimeError('test storage failure')):
            with self.assertRaises(RuntimeError):self.complete()
        self.assertEqual(self.overview()['portfolio_completion']['history'],[])

if __name__=='__main__':unittest.main()
