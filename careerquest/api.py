"""Authenticated, alias-only educational demo API."""
import os,json
from contextlib import contextmanager
from fastapi import FastAPI,HTTPException,Request,Depends,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel,Field,model_validator
from typing import Literal
from uuid import UUID
from . import discovery_guide
from . import discovery_agent
from . import discovery_handoff
from . import career_worlds
from . import career_milestones
from . import developer
from . import auth
from .store import connect,create_profile,profile,events,add_event,latest_plan,save_plan
from .quests import QUESTS,QUEST_REWARD_XP
from .discovery import discovery_state
from .agent import run as core_run
from .profiles import review_state,save_draft,confirm_profile
try:
    from .graph import run_graph as graph_run
    import langgraph
    RUN=graph_run
    ENGINE="langgraph"
except ImportError:
    RUN=core_run
    ENGINE="bounded_policy_fallback"
DB=os.getenv('DATABASE_URL') or os.getenv('CAREERQUEST_DB','var/careerquest-react.sqlite3')
app=FastAPI(title='CareerQuest AI Demo')
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173','http://localhost:5173'],allow_methods=['GET','POST'],allow_headers=['*'])
@app.on_event('startup')
def startup():
    auth.check_configuration()
    with db():pass

@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    # Pydantic errors otherwise echo submitted values, including passwords.
    return JSONResponse(status_code=422,content={'detail':[{'loc':list(item['loc']),'msg':item['msg'],'type':item['type']} for item in error.errors()]})

def authorize(request):
    if not request.url.path.startswith('/api/'):return None
    if request.url.path.startswith('/api/developer/'):
        developer.require_local_developer(request)
    with db() as c:return auth.authorize(c,request)

@app.middleware('http')
async def authentication(request, call_next):
    try:
        try:body_length=int(request.headers.get('content-length','0'))
        except ValueError:raise HTTPException(400,'Invalid request length')
        if body_length<0:raise HTTPException(400,'Invalid request length')
        if body_length>65536:
            raise HTTPException(413,'Request is too large')
        request.state.account=await run_in_threadpool(authorize,request)
        response=await call_next(request)
    except HTTPException as error:
        response=JSONResponse(status_code=error.status_code,content={'detail':error.detail},headers=error.headers)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    if auth.public_origin():response.headers['Strict-Transport-Security']='max-age=31536000'
    return response
@contextmanager
def db():
    c=connect(DB)
    try:
        auth.initialize(c)
        yield c
    finally:
        c.close()
def state(pid):
    with db() as c:
        try:p=profile(c,pid)
        except KeyError:raise HTTPException(404,'Explorer not found')
        es=events(c,pid);done=[e for e in es if e['kind']=='quest_completed'];review=review_state(c,pid)
        research=[json.loads(row['result']) for row in c.execute("SELECT result FROM runs WHERE profile_id=? AND action IN ('research_careers','research_college') ORDER BY rowid",(pid,))]
        successful=[r for r in research if r.get('status')=='ok']
        return {'profile':p,'quest_count':len(done),'quest_complete':len(done)==len(QUESTS),**review,'discovery':discovery_state(pid,es,review['quest_answers']),'discovery_guide':discovery_guide.guide_state(c,pid),'discovery_agent':discovery_agent.present(c,pid),'discovery_outcome':discovery_handoff.outcome(c,pid),'discovery_handoff':discovery_handoff.handoff_state(c,pid),'research_count':len(successful),'last_research':successful[-1] if successful else None,'reflection_count':sum(e['kind']=='reflection' for e in es),'latest_plan':latest_plan(c,pid),'events':es[-30:]}
class New(BaseModel):
    alias:str=Field(min_length=2,max_length=40)
    grade:int=Field(ge=9,le=12,strict=True)
    fictional_ack:bool=Field(strict=True)
    creation_key:UUID|None=None
    @model_validator(mode='after')
    def validate_setup(self):
        if self.fictional_ack is not True:raise ValueError('Confirm that this explorer uses aliases and test data only')
        self.alias=self.alias.strip()
        if len(self.alias)<2:raise ValueError('Enter an explorer nickname of at least two characters')
        return self
class Credentials(BaseModel):
    model_config={'extra':'forbid'}
    username:str=Field(min_length=1,max_length=30)
    password:str=Field(min_length=1,max_length=128)
class Registration(Credentials):
    demo_ack:bool=Field(strict=True)

@app.get('/api/auth/session')
def auth_session(request:Request):
    auth.same_origin(request)
    with db() as c:owner=auth.account(c,request,required=False)
    if not owner:return {'authenticated':False}
    return {'authenticated':True,'account':{key:owner[key] for key in ('id','username','profile_id')},'csrf_token':owner['csrf']}
@app.post('/api/auth/register')
def register(x:Registration,request:Request,response:Response):
    with db() as c:
        aid=auth.register(c,x.username,x.password,x.demo_ack,request)
        return auth.start_session(c,aid,request,response)
@app.post('/api/auth/login')
def login(x:Credentials,request:Request,response:Response):
    with db() as c:
        aid=auth.login(c,x.username,x.password,request)
        return auth.start_session(c,aid,request,response)
@app.post('/api/auth/logout')
def logout(request:Request,response:Response):
    with db() as c:return auth.logout(c,request,response)
class Choice(BaseModel):
    option:str
    revise:bool=False
class Confirm(BaseModel):
    interests:list[str]=Field(default_factory=list,max_length=12)
    learning_style:str=Field(default='Hands-on projects',max_length=100)
    goal:str=Field(default='Explore careers and college majors',max_length=150)
    correction:str=Field(default='',max_length=500)
    not_sure:bool=False
    expected_version:int|None=Field(default=None,ge=1)
    selected_world_ids:list[str]|None=Field(default=None,max_length=3)
    review_verdict:Literal['Yes','Somewhat','Not really']|None=None
    review_story_id:str|None=Field(default=None,max_length=100)
class Draft(Confirm):
    start_edit:bool=False
class Ask(BaseModel):
    message:str=Field(min_length=3,max_length=800)
    use_groq:bool=False
    simulate_failure:bool=False
class CareerSettings(BaseModel):
    simulate_failure:bool=False
class CareerQuestion(Ask):
    world_ids:list[str]=Field(default_factory=list,max_length=3)
class CareerSelection(BaseModel):
    exploration_id:str=Field(min_length=1,max_length=100)
class CareerPaths(BaseModel):
    model_config={'extra':'forbid'}
    primary_world_id:str|None=Field(default=None,min_length=1,max_length=100)
    secondary_world_id:str|None=Field(default=None,min_length=1,max_length=100)
    undecided:bool=Field(default=False,strict=True)
    student_reasons:dict[str,str]=Field(default_factory=dict,max_length=12)
    expected_profile_version:int=Field(ge=1)
    expected_path_version:int=Field(ge=0)
    @model_validator(mode='after')
    def validate_selection(self):
        if self.undecided and (self.primary_world_id or self.secondary_world_id):raise ValueError('An undecided selection has no assigned paths')
        if not self.undecided and not self.primary_world_id:raise ValueError('Choose a primary path or explicitly choose I am still exploring')
        if any(len(key)>100 or len(value)>240 for key,value in self.student_reasons.items()):raise ValueError('Use a short reason, up to 240 characters')
        return self
class CompletePortfolio(BaseModel):
    model_config={'extra':'forbid'}
    expected_signature:str=Field(pattern=r'^[0-9a-f]{64}$')
class Plan(BaseModel):plan:dict
class GuideRequest(BaseModel):
    model_config={'extra':'forbid'}
    retry:bool=Field(default=False,strict=True)
class GuideFeedback(BaseModel):
    model_config={'extra':'forbid'}
    verdict:Literal['Yes','Somewhat','Not really']
    correction:str=Field(default='',max_length=500)
class GuideRevision(GuideFeedback):
    verdict:Literal['Somewhat','Not really']
    preferred_interests:list[str]=Field(default_factory=list,max_length=3)
    retained_interest_ids:list[str]=Field(default_factory=list,max_length=3)
    @model_validator(mode='after')
    def require_interests(self):
        if not self.preferred_interests and (self.verdict=='Not really' or not self.retained_interest_ids):raise ValueError('Choose a preferred interest or a clue to keep')
        return self
@app.get('/api/health')
def health():return {'status':'ok','mode':'alias_demo','agent_engine':ENGINE,'authentication':'required'}
@app.get('/api/quests')
def quests():return QUESTS
@app.get('/api/career-worlds')
def career_world_catalogue():return discovery_handoff.catalogue()
@app.get('/api/profiles/{pid}/career-worlds')
def personalized_worlds(pid:str):
    require_confirm(pid)
    with db() as c:handoff=discovery_handoff.handoff_state(c,pid)['active']
    if not handoff:raise HTTPException(409,'Review and explicitly confirm your profile to create a Discovery handoff')
    return {'handoff_id':handoff['id'],'handoff_version':handoff['version'],'profile_version':handoff['profile_version'],'career_worlds':handoff['career_worlds'],'all_worlds':discovery_handoff.catalogue(),'exploratory':handoff['exploratory']}
@app.post('/api/profiles')
def create(x:New,request:Request):
    try:
        with db() as c:pid=auth.create_owned_profile(c,request.state.account,x.alias,x.grade)
    except ValueError as error:raise HTTPException(409,str(error))
    return state(pid)
@app.get('/api/profiles/{pid}')
def get(pid:str):return state(pid)
@app.post('/api/profiles/{pid}/quests/{step}')
def answer(pid:str,step:int,x:Choice):
    s=state(pid)
    if x.revise:
        old=next((event for event in s['quest_answers'] if event['payload'].get('quest')==step),None)
        if old is None or step<0 or step>=len(QUESTS):raise HTTPException(409,'Complete this quest before editing it')
        if x.option not in QUESTS[step]['options']:raise HTTPException(400,'Unknown quest choice')
        if old['payload']['choice']==x.option:return s
        with db() as c:
            add_event(c,pid,'quest_revised',{'quest':step,'choice':x.option,'interest':QUESTS[step]['options'][x.option],'previous_choice':old['payload']['choice'],'xp_awarded':0})
            if s['quest_complete']:
                previous=s['profile_draft'] or s['profile_preferences'] or {'interests':[]}
                save_draft(c,pid,previous,start_edit=True)
        return state(pid)
    if step!=s['quest_count'] or step>=len(QUESTS):raise HTTPException(409,'Quest out of order or already completed')
    if x.option not in QUESTS[step]['options']:raise HTTPException(400,'Unknown quest choice')
    with db() as c:add_event(c,pid,'quest_completed',{'quest':step,'choice':x.option,'interest':QUESTS[step]['options'][x.option],'xp_awarded':QUEST_REWARD_XP},xp=QUEST_REWARD_XP,event_id=f'{pid}:quest:{step}')
    return state(pid)
@app.get('/api/profiles/{pid}/summary')
def summary(pid:str):
    s=state(pid)
    if not s['quest_complete']:raise HTTPException(409,'Finish all quests first')
    choices=[e['payload'] for e in s['quest_answers']]
    return {'choices':choices,'suggested_interests':list(dict.fromkeys(x['interest'] for x in choices)),'note':'Exploration clues, not a career-fit score.'}
def guide_operation(pid,operation):
    state(pid)  # Existing 404 behavior, no caller-supplied student context.
    try:
        with db() as c:return operation(c)
    except discovery_guide.GuideConflict as exc:raise HTTPException(409,str(exc),headers={'Retry-After':'60'})
    except discovery_guide.GuideLimit as exc:raise HTTPException(429,str(exc),headers={'Retry-After':'3600'})
@app.post('/api/profiles/{pid}/discovery-guide')
def generate_guide(pid:str,x:GuideRequest):
    return guide_operation(pid,lambda c:discovery_guide.generate(c,pid,x.retry))
@app.post('/api/profiles/{pid}/discovery-agent')
def student_discovery_agent(pid:str,x:discovery_agent.AgentRequest):
    return guide_operation(pid,lambda c:discovery_agent.run_discovery_agent(c,pid,x))
@app.post('/api/profiles/{pid}/discovery-guide/{sid}/feedback')
def guide_feedback(pid:str,sid:str,x:GuideFeedback):
    return guide_operation(pid,lambda c:discovery_guide.save_feedback(c,pid,sid,x.verdict,x.correction.strip()))
@app.post('/api/profiles/{pid}/discovery-guide/{sid}/revise')
def revise_guide(pid:str,sid:str,x:GuideRevision):
    if any(not i.strip() or len(i)>40 for i in x.preferred_interests+x.retained_interest_ids):raise HTTPException(422,'Use short interest names, up to 40 characters each')
    return guide_operation(pid,lambda c:discovery_guide.generate(c,pid,revision=(sid,x.model_dump())))
@app.post('/api/profiles/{pid}/confirm')
def confirm(pid:str,x:Confirm):
    s=state(pid)
    if not s['quest_complete']:raise HTTPException(409,'Complete the quests first')
    if x.expected_version is not None and x.expected_version!=s['profile_version']:raise HTTPException(409,'This profile changed. Reload and review the latest version.')
    if x.review_verdict is not None and x.review_verdict!='Yes':raise HTTPException(409,'Review the revised proposal and choose Yes before explicit confirmation')
    with db() as c:
        try:confirm_profile(c,pid,x.model_dump())
        except ValueError as exc:raise HTTPException(422,str(exc))
    return state(pid)
@app.post('/api/profiles/{pid}/draft')
def draft(pid:str,x:Draft):
    s=state(pid)
    if not s['quest_complete']:raise HTTPException(409,'Complete all quests before editing your Explorer Profile')
    if x.expected_version is not None and x.expected_version!=s['profile_version']:raise HTTPException(409,'This profile changed. Reload and review the latest version.')
    with db() as c:
        try:save_draft(c,pid,x.model_dump(),x.start_edit)
        except ValueError as exc:raise HTTPException(409,str(exc))
    return state(pid)
def require_confirm(pid):
    if not state(pid)['confirmed']:raise HTTPException(409,'Confirm Explorer Profile before personalized research')
def career_operation(pid,operation,personalized=False):
    state(pid)
    if personalized:require_confirm(pid)
    try:
        with db() as c:return operation(c)
    except career_worlds.WorldUnknown as exc:raise HTTPException(404,str(exc))
    except career_worlds.CareerConflict as exc:raise HTTPException(409,str(exc))
@app.get('/api/profiles/{pid}/career-discovery')
def career_discovery(pid:str):return career_operation(pid,lambda c:career_worlds.overview(c,pid))
@app.get('/api/career-discovery-milestone')
def anonymous_discovery_milestone():
    return {'nickname':None,'confirmed':False,'eligible':False,'counts':{'careers_researched':None,'careers_shortlisted':None,'confirmed_interests':None},'count_scope':'Create a fictional explorer to see saved progress.','current_shortlist_count':0,'recovery_page':'profiles','profile_context':None,'returning_portfolio':False}
@app.get('/api/profiles/{pid}/career-discovery-milestone')
def career_discovery_milestone(pid:str):return career_operation(pid,lambda c:career_worlds.discovery_milestone(c,pid))
@app.get('/api/profiles/{pid}/career-portfolio/entry')
def career_portfolio_entry(pid:str):return career_operation(pid,lambda c:career_worlds.portfolio_entry(c,pid),True)
@app.post('/api/profiles/{pid}/worlds/{wid}/explore')
def research_world(pid:str,wid:str,x:CareerSettings,request:Request):
    if x.simulate_failure:developer.require_local_developer(request)
    def research(c):
        career_worlds.validate_ids([wid])
        return RUN(c,pid,'Explore selected Career World',simulate_failure=x.simulate_failure,world_ids=[wid],research_only=True)
    return career_operation(pid,research,True)
@app.post('/api/profiles/{pid}/career-guide')
def ask_career_guide(pid:str,x:CareerQuestion,request:Request):
    # Explicit routing overrides are tester controls. Normal students use the
    # server policy and cannot switch providers or inject failures.
    if {'use_groq','simulate_failure'} & x.model_fields_set:developer.require_local_developer(request)
    def research(c):
        if x.world_ids:career_worlds.validate_ids(x.world_ids)
        use_groq=x.use_groq if 'use_groq' in x.model_fields_set else os.getenv('CAREERQUEST_CAREER_GROQ')=='1'
        return RUN(c,pid,x.message,use_groq,x.simulate_failure,world_ids=x.world_ids or None,research_only=True)
    return career_operation(pid,research,True)
@app.get('/api/profiles/{pid}/career-explorations/{eid}')
def revisit_career(pid:str,eid:str):return career_operation(pid,lambda c:career_worlds.exploration(c,pid,eid))
@app.post('/api/profiles/{pid}/career-shortlist')
def shortlist_career(pid:str,x:CareerSelection):return career_operation(pid,lambda c:career_worlds.save_selection(c,pid,x.exploration_id),True)
@app.post('/api/profiles/{pid}/career-paths')
def choose_career_paths(pid:str,x:CareerPaths):return career_operation(pid,lambda c:career_worlds.save_paths(c,pid,x.primary_world_id,x.secondary_world_id,x.expected_profile_version,x.expected_path_version,x.undecided,x.student_reasons),True)
@app.post('/api/profiles/{pid}/career-celebrations/claim')
def claim_career_celebration(pid:str,kind:Literal['portfolio_completed']|None=None):return career_operation(pid,lambda c:career_milestones.claim(c,pid,kind))
@app.post('/api/profiles/{pid}/career-celebrations/{mid}/acknowledge')
def acknowledge_career_celebration(pid:str,mid:str):return career_operation(pid,lambda c:career_milestones.acknowledge(c,pid,mid))
@app.post('/api/profiles/{pid}/career-portfolio/complete')
def complete_career_portfolio(pid:str,x:CompletePortfolio):return career_operation(pid,lambda c:career_worlds.complete_portfolio(c,pid,x.expected_signature),True)
@app.get('/api/profiles/{pid}/career-portfolio/preview')
def preview_career_portfolio(pid:str):return career_operation(pid,lambda c:career_worlds.portfolio_preview(c,pid),True)
@app.get('/api/profiles/{pid}/career-portfolio/versions/{cid}')
def saved_career_portfolio(pid:str,cid:str):return career_operation(pid,lambda c:career_worlds.saved_portfolio(c,pid,cid))
@app.get('/api/profiles/{pid}/career-portfolio/versions/{cid}/pdf')
def download_career_portfolio(pid:str,cid:str):
    saved=career_operation(pid,lambda c:career_worlds.saved_portfolio(c,pid,cid))
    from .portfolio_pdf import render_portfolio
    return Response(render_portfolio(saved),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="careerquest-portfolio-v{saved["version"]}.pdf"','Cache-Control':'private, no-store'})
@app.post('/api/profiles/{pid}/explore')
def explore(pid:str,x:Ask,request:Request):
    require_confirm(pid)
    if {'use_groq','simulate_failure'} & x.model_fields_set:developer.require_local_developer(request)
    with db() as c:return RUN(c,pid,x.message,x.use_groq,x.simulate_failure)
@app.post('/api/profiles/{pid}/roadmap/propose')
def propose(pid:str):
    require_confirm(pid)
    with db() as c:return RUN(c,pid,'Create my grade-specific roadmap and next step')
@app.post('/api/profiles/{pid}/roadmap/save')
def save(pid:str,x:Plan):
    require_confirm(pid)
    with db() as c:
        proposed=RUN(c,pid,'Create my grade-specific roadmap and next step')['plan']
        if x.plan!=proposed:raise HTTPException(409,'Roadmap changed. Please review the latest version.')
        version=save_plan(c,pid,proposed)
        add_event(c,pid,'roadmap_saved',{'version':version})
    return state(pid)
@app.post('/api/profiles/{pid}/reflect')
def reflect(pid:str,x:Ask,request:Request):
    require_confirm(pid)
    if {'use_groq','simulate_failure'} & x.model_fields_set:developer.require_local_developer(request)
    with db() as c:return RUN(c,pid,'Reflection: '+x.message)

@app.get('/api/developer/access',dependencies=[Depends(developer.require_local_developer)])
def developer_access():return {'enabled':True,'mode':'explicit_local_development','identity_authentication':True,'agent_engine':ENGINE}
@app.get('/api/developer/profiles/{pid}/research-receipts',dependencies=[Depends(developer.require_local_developer)])
def research_receipts(pid:str,limit:int=Query(default=20,ge=1,le=50)):
    return career_operation(pid,lambda c:{'receipts':developer.receipts(c,pid,limit)})
@app.post('/api/developer/profiles/{pid}/research',dependencies=[Depends(developer.require_local_developer)])
def developer_research(pid:str,x:CareerQuestion):
    def research(c):
        if x.world_ids:career_worlds.validate_ids(x.world_ids)
        result=RUN(c,pid,x.message,x.use_groq,x.simulate_failure,world_ids=x.world_ids or None,research_only=True)
        row=c.execute('SELECT * FROM runs WHERE id=? AND profile_id=?',(result['run_id'],pid)).fetchone()
        return {'receipt':developer.receipt(row)}
    return career_operation(pid,research,True)

# Optional single-port demo: after `npm run build`, FastAPI serves the built UI.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
DIST=Path(__file__).resolve().parents[1]/'frontend'/'dist'
@app.get('/developer',dependencies=[Depends(developer.require_local_developer)],include_in_schema=False)
def developer_page():
    if not (DIST/'index.html').is_file():raise HTTPException(503,'Build the frontend first')
    return FileResponse(DIST/'index.html',headers={'Cache-Control':'no-store','X-Frame-Options':'DENY','X-Content-Type-Options':'nosniff'})
if DIST.is_dir():
    app.mount('/',StaticFiles(directory=DIST,html=True),name='frontend')
from .request_limits import BodyLimit
app.add_middleware(BodyLimit)
