import unittest,tempfile
from pathlib import Path
from careerquest.store import connect,create_profile,profile,set_interests,add_event,events,latest_plan,save_plan
from careerquest.agent import choose,run,groq_choose
from careerquest.catalog import retrieve
class CareerQuestTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'demo.db';self.c=connect(self.path);self.pid=create_profile(self.c,'Fictional Student',11)
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def test_grade_validation(self):
  with self.assertRaises(ValueError):create_profile(self.c,'X',8)
 def test_first_question(self):self.assertEqual(run(self.c,self.pid,'Hello')['action'],'ask_question')
 def test_quest_idempotent_xp(self):
  eid=self.pid+':quest:0';add_event(self.c,self.pid,'quest_completed',{'interest':'science'},20,eid)
  add_event(self.c,self.pid,'quest_completed',{'interest':'science'},20,eid)
  self.assertEqual(profile(self.c,self.pid)['xp'],20)
  with self.assertRaises(ValueError):add_event(self.c,self.pid,'quest_completed',{'interest':'art'},20,eid)
 def test_routing(self):
  p=profile(self.c,self.pid)
  self.assertEqual(choose('Show college majors',p),'research_college')
  self.assertEqual(choose('Create a roadmap',p),'create_plan')
  self.assertEqual(choose('I changed my mind',p),'reflect')
 def test_retrieval_grounded(self):
  ds=retrieve('biology engineering',('biology',))
  self.assertTrue(ds)
  self.assertTrue(all(d['id'] and d['source'] for d in ds))
 def test_plan_persists_and_revises(self):
  set_interests(self.c,self.pid,['biology','technology'])
  one=run(self.c,self.pid,'Create my roadmap');self.assertEqual(one['status'],'awaiting_student_confirmation')
  self.assertIsNone(latest_plan(self.c,self.pid))
  save_plan(self.c,self.pid,one['plan'])
  self.assertEqual(latest_plan(self.c,self.pid)['version'],1)
  self.c.close();self.c=connect(self.path)
  set_interests(self.c,self.pid,['art','design'])
  two=run(self.c,self.pid,'Revise my roadmap')
  save_plan(self.c,self.pid,two['plan'])
  self.assertEqual(latest_plan(self.c,self.pid)['version'],2)
  self.assertEqual(two['plan']['interests'],['art','design'])
 def test_failure_no_hallucination(self):
  r=run(self.c,self.pid,'Research college majors',simulate_failure=True)
  self.assertEqual(r['status'],'blocked');self.assertEqual(r['sources'],[])
  self.assertIsNone(latest_plan(self.c,self.pid))
 def test_reflection_persisted(self):
  run(self.c,self.pid,'Reflection: I enjoy building more than reading')
  self.assertTrue(any(e['kind']=='reflection' for e in events(self.c,self.pid)))
 def test_no_unapproved_model_endpoint(self):
  with self.assertRaises(ValueError):groq_choose('Hi',profile(self.c,self.pid),url='https://public.example')
 def test_research_does_not_write_plan(self):
  run(self.c,self.pid,'Explore engineering careers')
  self.assertIsNone(latest_plan(self.c,self.pid))
 def test_career_sources_are_not_live_verified(self):
  r=run(self.c,self.pid,'Explore software careers')
  self.assertTrue(all(s['live_verified'] is False for s in r['sources']))
if __name__=='__main__':unittest.main()
