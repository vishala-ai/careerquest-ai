"""Demo storage: local SQLite, optional cloud PostgreSQL. API ownership is enforced separately."""
import sqlite3,json,uuid,datetime,os
from pathlib import Path
DEFAULT_DB=Path('var/careerquest.sqlite3')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
SCHEMA='''CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,alias TEXT NOT NULL,grade INTEGER NOT NULL CHECK(grade BETWEEN 9 AND 12),interests TEXT NOT NULL,xp INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS explorer_creation_receipts(request_key TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),request_payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL,version INTEGER NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(profile_id,version));
    CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL,action TEXT NOT NULL,result TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discovery_stories(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),version INTEGER NOT NULL,response_version TEXT NOT NULL,source_answers TEXT NOT NULL,status TEXT NOT NULL,model TEXT NOT NULL,content TEXT,error_type TEXT,created_at TEXT NOT NULL,UNIQUE(profile_id,version));
    CREATE INDEX IF NOT EXISTS discovery_story_profile ON discovery_stories(profile_id,version);
    CREATE TABLE IF NOT EXISTS discovery_feedback(id TEXT PRIMARY KEY,story_id TEXT NOT NULL REFERENCES discovery_stories(id),profile_id TEXT NOT NULL REFERENCES profiles(id),verdict TEXT NOT NULL,correction TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discovery_adjustments(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),base_story_id TEXT NOT NULL REFERENCES discovery_stories(id),feedback_id TEXT NOT NULL REFERENCES discovery_feedback(id),quest_version TEXT NOT NULL,profile_signature TEXT NOT NULL,preferences TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discovery_story_context(story_id TEXT PRIMARY KEY REFERENCES discovery_stories(id),metadata TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discovery_agent_sessions(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),quest_version TEXT NOT NULL,context_version TEXT NOT NULL,kind TEXT NOT NULL,verdict TEXT,request_key TEXT NOT NULL UNIQUE,state TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discovery_agent_turns(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES discovery_agent_sessions(id),profile_id TEXT NOT NULL REFERENCES profiles(id),request_key TEXT NOT NULL UNIQUE,input TEXT NOT NULL,status TEXT NOT NULL,owner_pid INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discovery_agent_decisions(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES discovery_agent_sessions(id),turn_id TEXT NOT NULL REFERENCES discovery_agent_turns(id),sequence INTEGER NOT NULL,action TEXT NOT NULL,method TEXT NOT NULL,model TEXT NOT NULL,tool_input TEXT NOT NULL,tool_output TEXT,status TEXT NOT NULL,error TEXT,created_at TEXT NOT NULL,UNIQUE(session_id,sequence));
    CREATE TABLE IF NOT EXISTS discovery_agent_preferences(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),session_id TEXT NOT NULL REFERENCES discovery_agent_sessions(id),quest_version TEXT NOT NULL,profile_signature TEXT NOT NULL,preferences TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discovery_handoffs(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),version INTEGER NOT NULL,profile_version INTEGER NOT NULL,confirmation_event_id TEXT NOT NULL REFERENCES events(id),content TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(profile_id,version),UNIQUE(profile_id,confirmation_event_id));
    CREATE TABLE IF NOT EXISTS career_explorations(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),world_id TEXT NOT NULL,confirmation_event_id TEXT NOT NULL REFERENCES events(id),profile_version INTEGER NOT NULL,run_id TEXT NOT NULL REFERENCES runs(id),content TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(run_id,world_id));
    CREATE TABLE IF NOT EXISTS career_shortlist(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),world_id TEXT NOT NULL,exploration_id TEXT NOT NULL REFERENCES career_explorations(id),created_at TEXT NOT NULL,UNIQUE(profile_id,world_id,exploration_id));
    CREATE TABLE IF NOT EXISTS career_path_preferences(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),version INTEGER NOT NULL,confirmation_event_id TEXT NOT NULL REFERENCES events(id),profile_version INTEGER NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(profile_id,version));
    CREATE TABLE IF NOT EXISTS career_milestones(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),kind TEXT NOT NULL,source_id TEXT NOT NULL,confirmation_event_id TEXT NOT NULL REFERENCES events(id),payload TEXT NOT NULL,created_at TEXT NOT NULL,delivered_at TEXT,acknowledged_at TEXT,UNIQUE(profile_id,kind));
    CREATE TABLE IF NOT EXISTS career_portfolio_completions(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL REFERENCES profiles(id),version INTEGER NOT NULL,confirmation_event_id TEXT NOT NULL REFERENCES events(id),profile_version INTEGER NOT NULL,path_preference_id TEXT NOT NULL REFERENCES career_path_preferences(id),signature TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(profile_id,version),UNIQUE(profile_id,signature));'''
def connect(path=DEFAULT_DB):
    # An explicit SQLite path must remain local, especially in test fixtures.
    # Only callers choosing a PostgreSQL URL can access the cloud database.
    if str(path).startswith(('postgres://','postgresql://')):
        from .postgres import connect as postgres_connect
        return postgres_connect(str(path),SCHEMA,schema=os.getenv('CAREERQUEST_DATABASE_SCHEMA') or None)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(path);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
    c.executescript(SCHEMA);c.commit();return c
def create_profile(c,alias='Demo Explorer',grade=11,request_key=None):
    if not 9<=int(grade)<=12:raise ValueError('Grade 9–12 only')
    payload=json.dumps({'alias':alias,'grade':int(grade)},sort_keys=True)
    # Serialize retries and the first insert together, including across workers.
    with c:
        c.execute('BEGIN IMMEDIATE')
        if request_key:
            old=c.execute('SELECT * FROM explorer_creation_receipts WHERE request_key=?',(request_key,)).fetchone()
            if old:
                if old['request_payload']!=payload:raise ValueError('Creation request changed. Start a new Explorer setup.')
                return old['profile_id']
        pid=str(uuid.uuid4())
        c.execute('INSERT INTO profiles VALUES(?,?,?,?,?)',(pid,alias,int(grade),'[]',0))
        if request_key:c.execute('INSERT INTO explorer_creation_receipts VALUES(?,?,?)',(request_key,pid,payload))
    return pid
def profile(c,pid):
    row=c.execute('SELECT * FROM profiles WHERE id=?',(pid,)).fetchone()
    if not row:raise KeyError('Unknown profile')
    obj=dict(row);obj['interests']=json.loads(obj['interests']);return obj
def add_event(c,pid,kind,payload,xp=0,event_id=None):
    with c:return record_event(c,pid,kind,payload,xp,event_id)
def record_event(c,pid,kind,payload,xp=0,event_id=None):
    """Record an event inside the caller's transaction, without committing it."""
    profile(c,pid);eid=event_id or str(uuid.uuid4());body=json.dumps(payload,sort_keys=True)
    old=c.execute('SELECT * FROM events WHERE id=?',(eid,)).fetchone()
    if old:
        if old['payload']!=body or old['kind']!=kind or old['profile_id']!=pid:raise ValueError('Idempotency conflict')
        return eid
    c.execute('INSERT INTO events VALUES(?,?,?,?,?)',(eid,pid,kind,body,now()))
    c.execute('UPDATE profiles SET xp=xp+? WHERE id=?',(xp,pid))
    return eid
def events(c,pid):return [dict(r)|{'payload':json.loads(r['payload'])} for r in c.execute('SELECT * FROM events WHERE profile_id=? ORDER BY created_at,id',(pid,))]
def set_interests(c,pid,values):
    clean=list(dict.fromkeys(str(x).strip().lower() for x in values if str(x).strip()))[:12]
    with c:c.execute('UPDATE profiles SET interests=? WHERE id=?',(json.dumps(clean),pid))
    add_event(c,pid,'interests_updated',{'interests':clean});return clean
def save_plan(c,pid,plan):
    profile(c,pid)
    with c:
        ver=c.execute('SELECT COALESCE(MAX(version),0)+1 FROM plans WHERE profile_id=?',(pid,)).fetchone()[0]
        c.execute('INSERT INTO plans VALUES(?,?,?,?,?)',(str(uuid.uuid4()),pid,ver,json.dumps(plan,sort_keys=True),now()))
    return ver
def latest_plan(c,pid):
    row=c.execute('SELECT * FROM plans WHERE profile_id=? ORDER BY version DESC LIMIT 1',(pid,)).fetchone()
    return dict(row)|{'content':json.loads(row['content'])} if row else None
def save_run(c,pid,action,result):
    with c:return record_run(c,pid,action,result)
def record_run(c,pid,action,result):
    rid=str(uuid.uuid4());c.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(rid,pid,action,json.dumps(result,sort_keys=True),now()));return rid
