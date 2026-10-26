"""Run a fully offline synthetic end-to-end journey; no Streamlit or Groq required."""
import tempfile
from pathlib import Path
from careerquest.store import connect,create_profile,set_interests,add_event,latest_plan,profile,save_plan
from careerquest.agent import run
with tempfile.TemporaryDirectory() as d:
 c=connect(Path(d)/'demo.sqlite3');pid=create_profile(c,'Alex Explorer',11)
 for i,interest in enumerate(['science','technology','building']):
  add_event(c,pid,'quest_completed',{'quest':i,'interest':interest},20,f'{pid}:quest:{i}')
 set_interests(c,pid,['biology','technology'])
 research=run(c,pid,'Explore biomedical engineering careers')
 first=run(c,pid,'Create my roadmap');save_plan(c,pid,first['plan'])
 reflect=run(c,pid,'Reflection: I prefer coding and design over lab work')
 set_interests(c,pid,['technology','design','coding'])
 second=run(c,pid,'Create my roadmap');save_plan(c,pid,second['plan'])
 failed=run(c,pid,'Research college majors',simulate_failure=True)
 assert research['status']=='ok' and first['status']=='awaiting_student_confirmation' and second['status']=='awaiting_student_confirmation'
 assert latest_plan(c,pid)['version']==2 and failed['status']=='blocked'
 assert profile(c,pid)['xp']==70
 print('CORE SMOKE PASS: 3 quests, 60 XP, research, 2 roadmap versions, reflection +10 XP, safe tool failure')
 print('Model calls: 0 | Real student records: 0 | Live admissions verification: 0')
 c.close()
