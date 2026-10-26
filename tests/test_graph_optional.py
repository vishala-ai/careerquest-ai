import unittest,tempfile,importlib.util
from unittest.mock import patch
from pathlib import Path
from careerquest.store import connect,create_profile
@unittest.skipUnless(importlib.util.find_spec('langgraph') is not None,'LangGraph dependency unavailable in this environment')
class GraphIntegration(unittest.TestCase):
 def test_route_execute_finish(self):
  from careerquest.graph import run_graph
  with tempfile.TemporaryDirectory() as d:
   c=connect(Path(d)/'x.db');pid=create_profile(c)
   r=run_graph(c,pid,'Explore software careers')
   self.assertEqual(r['action'],'research_careers')
   self.assertEqual(r['status'],'ok')
   self.assertTrue(any(t['step']=='tool' for t in r['trace']))
   c.close()
 def test_groq_routing_and_fallback(self):
  from careerquest.graph import run_graph
  with tempfile.TemporaryDirectory() as d:
   c=connect(Path(d)/'x.db');pid=create_profile(c)
   try:
    with patch('careerquest.graph.groq_choose',return_value='research_college'):
     r=run_graph(c,pid,'Explore careers',use_groq=True)
    self.assertEqual(r['action'],'research_college')
    self.assertEqual(r['trace'][0]['method'],'groq')
    with patch('careerquest.graph.groq_choose',side_effect=TimeoutError):
     r=run_graph(c,pid,'Explore careers',use_groq=True,simulate_failure=True)
    self.assertEqual(r['trace'][0]['method'],'bounded_policy_fallback')
    self.assertEqual(r['status'],'blocked')
    self.assertEqual(r['sources'],[])
   finally:c.close()
