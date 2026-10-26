"""Read-only milestone progress and server-side portfolio-entry checks."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from careerquest import api
from careerquest.store import connect

class CareerDiscoveryMilestoneTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.path=str(Path(temp.name)/'fictional.sqlite3')
        db=patch.object(api,'DB',self.path);db.start();self.addCleanup(db.stop)
        env=patch.dict(os.environ,{'CAREERQUEST_CAREER_GROQ':'0','CAREERQUEST_DEV_TOOLS':'0'});env.start();self.addCleanup(env.stop)
        self.c=TestClient(api.app);self.addCleanup(self.c.close)
        self.pid=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Fictional Emerald Explorer','grade':10}).json()['profile']['id'];self.base='/api/profiles/'+self.pid
        for i,q in enumerate(api.QUESTS):self.c.post(self.base+f'/quests/{i}',json={'option':next(iter(q['options']))})
        self.c.post(self.base+'/confirm',json={'interests':['technology','art']})
    def progress(self):return self.c.get(self.base+'/career-discovery-milestone').json()
    def save(self,wid):
        result=self.c.post(self.base+f'/worlds/{wid}/explore',json={}).json();eid=result['exploration_ids'][wid]
        self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid})
    def choose(self,wid):
        data=self.c.get(self.base+'/career-discovery').json()
        latest=data['path_preferences']['latest']
        response=self.c.post(self.base+'/career-paths',json={'primary_world_id':wid,'expected_profile_version':data['profile_context']['profile_version'],'expected_path_version':latest['version'] if latest else 0})
        self.assertEqual(response.status_code,200)
    def rows(self):
        with connect(self.path) as c:
            return {name:[tuple(r) for r in c.execute('SELECT * FROM "'+name+'" ORDER BY rowid')] for name, in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    def test_anonymous_has_no_invented_counts_or_success_claim(self):
        value=self.c.get('/api/career-discovery-milestone').json();self.assertFalse(value['eligible']);self.assertTrue(all(v is None for v in value['counts'].values()));self.assertEqual(value['recovery_page'],'profiles')
    def test_new_student_progress_is_zero_and_entry_is_blocked(self):
        pid=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'New Fictional','grade':9}).json()['profile']['id'];base='/api/profiles/'+pid
        value=self.c.get(base+'/career-discovery-milestone').json();self.assertEqual(value['counts'],{'careers_researched':0,'careers_shortlisted':0,'confirmed_interests':None});self.assertFalse(value['eligible']);self.assertEqual(value['recovery_page'],'quests');self.assertEqual(self.c.get(base+'/career-portfolio/entry').status_code,409)
    def test_confirmed_without_shortlist_cannot_skip_eligibility(self):
        self.assertFalse(self.progress()['eligible']);self.assertEqual(self.c.get(self.base+'/career-portfolio/entry').status_code,409)
        self.c.post(self.base+'/worlds/software/explore',json={});self.assertFalse(self.progress()['eligible']);self.assertEqual(self.c.get(self.base+'/career-portfolio/entry').status_code,409)
    def test_one_and_multiple_careers_use_distinct_persisted_counts(self):
        self.save('software');self.save('software');self.choose('software');one=self.progress();self.assertTrue(one['eligible']);self.assertEqual(one['counts'],{'careers_researched':1,'careers_shortlisted':1,'confirmed_interests':2})
        self.save('design');two=self.progress();self.assertEqual(two['counts']['careers_researched'],2);self.assertEqual(two['counts']['careers_shortlisted'],2);self.assertEqual(two['current_shortlist_count'],2)
    def test_view_entry_reload_are_read_only_including_xp_and_celebrations(self):
        self.save('software');self.choose('software');before=self.rows()
        for _ in range(3):
            self.assertEqual(self.c.get(self.base+'/career-discovery-milestone').status_code,200);self.assertEqual(self.c.get(self.base+'/career-portfolio/entry').json()['allowed'],True)
        with TestClient(api.app) as fresh:self.assertEqual(fresh.get(self.base+'/career-discovery-milestone').json(),self.progress())
        self.assertEqual(self.rows(),before)
        with connect(self.path) as c:self.assertEqual(c.execute('SELECT xp FROM profiles WHERE id=?',(self.pid,)).fetchone()[0],70);self.assertEqual(c.execute('SELECT count(*) FROM career_milestones WHERE delivered_at IS NOT NULL').fetchone()[0],0)
    def test_missing_nickname_returns_none_for_neutral_client_fallback(self):
        self.save('software');self.choose('software')
        with connect(self.path) as c:c.execute('UPDATE profiles SET alias=? WHERE id=?',('',self.pid))
        self.assertIsNone(self.progress()['nickname']);self.assertTrue(self.progress()['eligible'])
    def test_stale_profile_keeps_history_counts_but_blocks_current_entry(self):
        self.save('software');self.c.post(self.base+'/draft',json={'interests':['nature'],'start_edit':True})
        stale=self.progress();self.assertFalse(stale['eligible']);self.assertIsNone(stale['counts']['confirmed_interests']);self.assertEqual(stale['counts']['careers_shortlisted'],1);self.assertEqual(stale['current_shortlist_count'],0);self.assertEqual(stale['recovery_page'],'confirm');self.assertEqual(self.c.get(self.base+'/career-portfolio/entry').status_code,409)
        self.c.post(self.base+'/confirm',json={'interests':['nature']});self.assertFalse(self.progress()['eligible']);self.assertEqual(self.c.get(self.base+'/career-portfolio/entry').status_code,409)
        self.save('environment');self.choose('environment');self.assertTrue(self.progress()['eligible']);self.assertEqual(self.progress()['counts']['confirmed_interests'],1)
    def test_returning_completed_portfolio_is_preserved_without_new_versions_or_rewards(self):
        self.save('software');data=self.c.get(self.base+'/career-discovery').json()
        self.c.post(self.base+'/career-paths',json={'primary_world_id':'software','expected_profile_version':data['profile_context']['profile_version'],'expected_path_version':0})
        ready=self.c.get(self.base+'/career-discovery').json()['portfolio_completion'];self.c.post(self.base+'/career-portfolio/complete',json={'expected_signature':ready['signature']})
        before=self.rows();self.assertTrue(self.progress()['returning_portfolio']);self.assertTrue(self.progress()['eligible']);self.assertEqual(self.c.get(self.base+'/career-portfolio/entry').status_code,200);self.assertEqual(self.rows(),before)
    def test_client_progress_flags_cannot_override_server_entry_gate(self):
        response=self.c.get(self.base+'/career-portfolio/entry?eligible=true&shortlisted=999&confirmed=true');self.assertEqual(response.status_code,409);self.assertEqual(self.progress()['counts']['careers_shortlisted'],0)
    def test_unknown_explorer_is_404(self):
        self.assertEqual(self.c.get('/api/profiles/unknown/career-discovery-milestone').status_code,404);self.assertEqual(self.c.get('/api/profiles/unknown/career-portfolio/entry').status_code,404)

if __name__=='__main__':unittest.main()
