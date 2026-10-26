"""Bounded Career World research and explicit portfolio selections; no XP writes."""
import json
import uuid
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from . import discovery_guide as guide, discovery_handoff as handoff
from .profiles import review_state, fields
from .store import profile, events, now, record_run
from . import career_milestones as milestones
from .quests import QUESTS

DETAILS = Path(__file__).resolve().parents[1]/'data'/'career_world_details.json'

class WorldUnknown(ValueError): pass
class CareerConflict(ValueError): pass

def approved(): return {d['id']: d for d in guide.approved_worlds()}

def validate_ids(ids):
    if not 1 <= len(ids) <= 3 or len(set(ids)) != len(ids) or any(i not in approved() for i in ids):
        raise WorldUnknown('Choose one supported career, or two or three different careers to compare')

def confirmation(c,pid):
    review=review_state(c,pid)
    if not review['confirmed']: raise CareerConflict('Confirm your current Explorer Profile before personalized research')
    event=[e for e in events(c,pid) if e['kind']=='profile_confirmed'][-1]
    return {'confirmation_event_id':event['id'],'profile_version':review['profile_version']}

def detail_records():
    try:
        result=json.loads(DETAILS.read_text())
        return result if isinstance(result,dict) else {}
    except (OSError,ValueError): return {}

def research(c,pid,ids,simulate_failure=False):
    validate_ids(ids); context=confirmation(c,pid)
    if simulate_failure: raise ConnectionError('Simulated catalogue outage')
    records=detail_records(); worlds=[]; sources=[]
    for wid in ids:
        doc=records.get(wid,{});doc=doc if isinstance(doc,dict) else {};source=doc.get('source',{})
        valid_source=isinstance(source,dict) and all(isinstance(source.get(k),str) and source[k].strip() for k in ('id','title','source','url'))
        valid_source=valid_source and urlparse(source['url']).scheme=='https' and urlparse(source['url']).hostname in ('www.bls.gov','www.onetonline.org')
        if not valid_source or not isinstance(doc.get('overview'),str) or any(not isinstance(doc.get(k),list) or not doc[k] or any(not isinstance(v,str) or not v for v in doc[k]) for k in ('activities','skills','educational_fields')):
            return {'status':'blocked','message':'Source-grounded details are unavailable for this world. No career facts were invented. Try another world or return later.','sources':[],'worlds':[]}
        source={**source,'live_verified':False}; sources.append(source)
        def items(key):return [{'text':text,'source_ids':[source['id']]} for text in doc[key]]
        worlds.append({'world_id':wid,'title':approved()[wid]['title'],'overview':{'text':doc['overview'],'source_ids':[source['id']]},
            'activities':items('activities'),'skills':items('skills'),'educational_fields':items('educational_fields'),
            'mission':{'text':doc['mission'],'kind':'optional_demo_activity'} if isinstance(doc.get('mission'),str) else None,'sources':[source]})
    return {'status':'ok','message':'Explore possibilities, not career-fit scores. These are curated source notes, not live research.','worlds':worlds,'sources':sources,'profile_context':context,
        'matches':[{'title':w['title'],'description':w['overview']['text'],'source_id':w['sources'][0]['id']} for w in worlds]}

def save_result(c,pid,result):
    """Atomically bind a successful research run and its snapshots to confirmation."""
    with c:
        c.execute('BEGIN IMMEDIATE')
        current=confirmation(c,pid)
        if result.get('status')=='ok' and result.get('profile_context')!=current:
            raise CareerConflict('Your profile changed during research. Review and confirm it before trying again.')
        stamp=now(); snapshots=[]
        first_research=not c.execute('SELECT 1 FROM career_explorations WHERE profile_id=? LIMIT 1',(pid,)).fetchone() and not any(json.loads(row[0]).get('status')=='ok' for row in c.execute("SELECT result FROM runs WHERE profile_id=? AND action='research_careers'",(pid,)))
        for world in result.get('worlds',[]) if result.get('status')=='ok' else []:
            snapshots.append((str(uuid.uuid4()),world))
        result['exploration_ids']={w['world_id']:eid for eid,w in snapshots}
        rid=record_run(c,pid,result.get('action','research_careers'),result)
        for eid,world in snapshots:
            c.execute('INSERT INTO career_explorations VALUES(?,?,?,?,?,?,?,?)',(eid,pid,world['world_id'],current['confirmation_event_id'],current['profile_version'],rid,json.dumps(world,sort_keys=True),stamp))
        if first_research and snapshots:
            eid,world=snapshots[0];milestones.record(c,pid,'first_research',eid,current['confirmation_event_id'],world)
    return {**result,'run_id':rid}

def exploration(c,pid,eid):
    row=c.execute('SELECT * FROM career_explorations WHERE profile_id=? AND id=?',(pid,eid)).fetchone()
    if not row:raise WorldUnknown('Saved career exploration not found')
    item=dict(row);item['world']=json.loads(item.pop('content'))
    try:item['is_stale']=item['confirmation_event_id']!=confirmation(c,pid)['confirmation_event_id']
    except CareerConflict:item['is_stale']=True
    return item

def portfolio(c,pid):
    profile(c,pid)
    explored=[exploration(c,pid,r['id']) for r in c.execute('SELECT id FROM career_explorations WHERE profile_id=? ORDER BY rowid DESC',(pid,))]
    selected={}
    for row in c.execute('SELECT * FROM career_shortlist WHERE profile_id=? ORDER BY rowid',(pid,)):
        item=dict(row);item['exploration']=exploration(c,pid,row['exploration_id']);selected[row['world_id']]=item
    return {'explorations':explored,'shortlist':list(selected.values())}

def save_selection(c,pid,eid):
    with c:
        c.execute('BEGIN IMMEDIATE')
        context=confirmation(c,pid); item=exploration(c,pid,eid); validate_ids([item['world_id']])
        if item['is_stale']:raise CareerConflict('Explore this world with your current confirmed profile before saving a new selection')
        existing=c.execute('SELECT id FROM career_shortlist WHERE profile_id=? AND world_id=? AND exploration_id=?',(pid,item['world_id'],eid)).fetchone()
        if not existing:
            previous={r[0] for r in c.execute('SELECT DISTINCT world_id FROM career_shortlist WHERE profile_id=?',(pid,))}
            sid=str(uuid.uuid4());c.execute('INSERT INTO career_shortlist VALUES(?,?,?,?,?)',(sid,pid,item['world_id'],eid,now()))
            if item['world_id'] not in previous and len(previous)<2:
                milestones.record(c,pid,'first_shortlist' if not previous else 'second_shortlist',sid,context['confirmation_event_id'],item['world'])
    return portfolio(c,pid)

def path_preferences(c,pid):
    """Immutable student-chosen priorities; an old confirmation is never current."""
    profile(c,pid)
    try:context=confirmation(c,pid)
    except CareerConflict:context=None
    history=[]
    selected={s['world_id']:s for s in portfolio(c,pid)['shortlist']}
    for row in c.execute('SELECT * FROM career_path_preferences WHERE profile_id=? ORDER BY version',(pid,)):
        item=dict(row);item.update(json.loads(item.pop('content')))
        item['is_stale']=not context or item['confirmation_event_id']!=context['confirmation_event_id']
        item['is_stale']=item['is_stale'] or any(p['world_id'] not in selected or selected[p['world_id']]['id']!=p['selection_id'] or selected[p['world_id']]['exploration']['is_stale'] for p in item['paths'])
        history.append(item)
    latest=history[-1] if history else None
    return {'active':latest if latest and not latest['is_stale'] else None,'latest':latest,'history':history}

def save_paths(c,pid,primary,secondary,expected_profile_version,expected_path_version,undecided=False,student_reasons=None):
    with c:
        c.execute('BEGIN IMMEDIATE');context=confirmation(c,pid)
        if context['profile_version']!=expected_profile_version:raise CareerConflict('Your profile changed. Reload before choosing exploration paths.')
        if undecided and (primary or secondary) or not undecided and not primary:raise CareerConflict('Choose a primary path or explicitly save an undecided exploration preference.')
        ids=[] if undecided else [primary]+([secondary] if secondary else [])
        if ids:validate_ids(ids)
        selected={s['world_id']:s for s in portfolio(c,pid)['shortlist'] if not s['exploration']['is_stale'] and s['world_id'] in approved()}
        if not selected or any(w not in selected for w in ids):
            raise CareerConflict('Explicitly save each career with your current confirmed profile before choosing a path.')
        reasons={key:value.strip() for key,value in (student_reasons or {}).items() if value.strip()}
        if any(key not in selected or len(value)>240 for key,value in reasons.items()):raise CareerConflict('Reasons must refer to your current saved careers and be at most 240 characters.')
        previous=path_preferences(c,pid)['latest'];version=previous['version'] if previous else 0
        paths=[{'priority':'primary' if i==0 else 'secondary','world_id':wid,'title':selected[wid]['exploration']['world']['title'],
            'selection_id':selected[wid]['id'],'exploration_id':selected[wid]['exploration_id'],
            'sources':selected[wid]['exploration']['world']['sources']} for i,wid in enumerate(ids)]
        content={'primary_world_id':primary,'secondary_world_id':secondary,'paths':paths,'undecided':undecided,'student_reasons':reasons}
        if previous and not previous['is_stale'] and all(previous.get(k,False if k=='undecided' else {} if k=='student_reasons' else None)==v for k,v in content.items()):return path_preferences(c,pid)
        if version!=expected_path_version:raise CareerConflict('Your path preferences changed. Reload before saving again.')
        had_secondary=any(item['secondary_world_id'] for item in path_preferences(c,pid)['history'])
        pref_id=str(uuid.uuid4())
        c.execute('INSERT INTO career_path_preferences VALUES(?,?,?,?,?,?,?)',(pref_id,pid,version+1,context['confirmation_event_id'],context['profile_version'],json.dumps(content,sort_keys=True),now()))
        had_primary=any(item['primary_world_id'] for item in path_preferences(c,pid)['history'][:-1])
        if primary and not had_primary:milestones.record(c,pid,'primary_path',pref_id,context['confirmation_event_id'],paths[0])
        if secondary and not had_secondary:milestones.record(c,pid,'secondary_path',pref_id,context['confirmation_event_id'],paths[1])
    return path_preferences(c,pid)

def completion_context(c,pid):
    context=confirmation(c,pid);paths=path_preferences(c,pid)['active'];saved=portfolio(c,pid)['shortlist']
    current={s['world_id']:s for s in saved if not s['exploration']['is_stale'] and s['world_id'] in approved()}
    if not paths or not current or not paths['paths'] and not paths.get('undecided'):return None
    if any(p['world_id'] not in current or current[p['world_id']]['id']!=p['selection_id'] for p in paths['paths']):return None
    signature=hashlib.sha256(json.dumps({'schema_version':2,'confirmation':context['confirmation_event_id'],'paths':paths['id'],'selections':sorted(s['id'] for s in current.values())},sort_keys=True).encode()).hexdigest()
    return {'context':context,'paths':paths,'shortlist':list(current.values()),'signature':signature}

def snapshot(c,pid,ready):
    """Freeze display data from confirmed evidence and explicit saved selections."""
    p=profile(c,pid);review=review_state(c,pid);values=fields(review['profile_preferences'])
    accepted=handoff.handoff_state(c,pid)['active'];story=accepted.get('story') if accepted else None
    nickname=p['alias'].strip() or 'Explorer'
    careers=[{'selection_id':s['id'],'exploration_id':s['exploration_id'],'world_id':s['world_id'],
        'career_name':s['exploration']['world']['title'],'world':s['exploration']['world'],
        'sources':s['exploration']['world']['sources'],'student_reason':ready['paths'].get('student_reasons',{}).get(s['world_id'],'')} for s in ready['shortlist']]
    undecided=bool(ready['paths'].get('undecided'))
    if not story:
        interests=', '.join(values['interests']) or 'keeping your interests open'
        names=', '.join(item['career_name'] for item in careers)
        story={'summary':f'{nickname}, your confirmed interests include {interests}. You saved {names} as possibilities to explore. '+('You chose to keep your path priorities open for now. ' if undecided else 'Your saved Exploration Paths show what you would like to try first. ')+'These choices are a starting point, not a permanent decision. Try a small activity, notice what interests you and change direction whenever you learn something new.','status':'deterministic_saved_choices','id':None}
    mission=next((item['world']['mission'] for item in careers if item['world'].get('mission')),None)
    return {'schema_version':2,'student':{'id':pid,'nickname':nickname,'grade':p['grade']},
        'explorer':{**values,'profile_version':ready['context']['profile_version'],'confirmation_event_id':ready['context']['confirmation_event_id']},
        'story':story,'paths':ready['paths']['paths'],'undecided':undecided,'shortlist':careers,'optional_mission':mission,
        'evidence_references':accepted['evidence_references'] if accepted else handoff.references(c,pid,values,ready['context']['confirmation_event_id'])}

def portfolio_preview(c,pid):
    ready=completion_context(c,pid)
    if not ready:raise CareerConflict('Save a current researched career and choose your path preferences or I am still exploring on Explore Careers first.')
    return {'signature':ready['signature'],'snapshot':snapshot(c,pid,ready)}

def saved_portfolio(c,pid,cid):
    """Historical exports never join mutable profile/catalogue data."""
    row=c.execute('SELECT * FROM career_portfolio_completions WHERE profile_id=? AND id=?',(pid,cid)).fetchone()
    if not row:raise WorldUnknown('Saved portfolio version not found')
    result=dict(row);result['snapshot']=json.loads(result.pop('content'));return result

def portfolio_completion(c,pid):
    try:ready=completion_context(c,pid)
    except CareerConflict:ready=None
    history=[]
    for row in c.execute('SELECT * FROM career_portfolio_completions WHERE profile_id=? ORDER BY version',(pid,)):
        item=dict(row);item['snapshot']=json.loads(item.pop('content'));item['is_stale']=not ready or item['signature']!=ready['signature'];history.append(item)
    active=next((item for item in reversed(history) if not item['is_stale']),None)
    return {'ready':bool(ready),'signature':ready['signature'] if ready else None,'preview':snapshot(c,pid,ready) if ready else None,'active':active,'history':history}

def complete_portfolio(c,pid,expected_signature):
    with c:
        c.execute('BEGIN IMMEDIATE');ready=completion_context(c,pid)
        if not ready:raise CareerConflict('Confirm your current profile, save a career and review your saved paths before completing your portfolio. A secondary path is optional.')
        if ready['signature']!=expected_signature:raise CareerConflict('Your portfolio changed. Reload and review it before completing this snapshot.')
        existing=c.execute('SELECT id FROM career_portfolio_completions WHERE profile_id=? AND signature=?',(pid,ready['signature'])).fetchone()
        if not existing:
            version=c.execute('SELECT COALESCE(MAX(version),0)+1 FROM career_portfolio_completions WHERE profile_id=?',(pid,)).fetchone()[0]
            cid=str(uuid.uuid4());context=ready['context']
            content=snapshot(c,pid,ready)
            c.execute('INSERT INTO career_portfolio_completions VALUES(?,?,?,?,?,?,?,?,?)',(cid,pid,version,context['confirmation_event_id'],context['profile_version'],ready['paths']['id'],ready['signature'],json.dumps(content,sort_keys=True),now()))
            milestones.record(c,pid,'portfolio_completed',cid,context['confirmation_event_id'])
    return portfolio_completion(c,pid)

def discovery_milestone(c,pid):
    """Read-only transition: lifetime distinct career counts, current interests/gates."""
    p=profile(c,pid);review=review_state(c,pid);saved=portfolio(c,pid)
    current=[item for item in saved['shortlist'] if not item['exploration']['is_stale'] and item['world_id'] in approved()]
    confirmed=bool(review['confirmed']);paths=path_preferences(c,pid)['active'];eligible=confirmed and bool(current) and bool(paths)
    interests=fields(review['profile_preferences'])['interests'] if confirmed else None
    recovery='quests' if len(review['quest_answers'])<len(QUESTS) else 'confirm' if not confirmed else 'worlds'
    return {'nickname':p['alias'].strip() or None,'confirmed':confirmed,'eligible':eligible,
        'counts':{'careers_researched':len({item['world_id'] for item in saved['explorations']}),
            'careers_shortlisted':len({item['world_id'] for item in saved['shortlist']}),
            'confirmed_interests':len(interests) if interests is not None else None},
        'count_scope':'Distinct saved careers across your exploration history; interests from your current confirmed profile.',
        'current_shortlist_count':len(current),'recovery_page':recovery,
        'profile_context':confirmation(c,pid) if confirmed else None,
        'saved_preferences':{'undecided':paths.get('undecided',False),'paths':paths['paths']} if paths else None,
        'returning_portfolio':bool(portfolio_completion(c,pid)['history'])}

def portfolio_entry(c,pid):
    progress=discovery_milestone(c,pid)
    if not progress['confirmed']:raise CareerConflict('Review and confirm your current Explorer Profile before creating your portfolio.')
    if not progress['eligible']:raise CareerConflict('Save at least one current researched career, then save your path preferences or I am still exploring on Explore Careers.')
    return {'allowed':True,'profile_context':progress['profile_context']}

def overview(c,pid):
    review=review_state(c,pid); p=profile(c,pid); worlds=handoff.catalogue(); recommended=[]
    if review['confirmed']:
        accepted=handoff.handoff_state(c,pid)['active']
        values=fields(review['profile_preferences']); refs=handoff.references(c,pid,values,confirmation(c,pid)['confirmation_event_id'])
        supported=handoff.supported_worlds(values,refs)
        if not values['not_sure']:
            candidates=(accepted['suggested_world_ids'] if accepted else [])+list(supported)
            recommended=[supported[i] for i in dict.fromkeys(candidates) if i in supported][:3]
    reasons={w['world_id']:w['explanation'] for w in recommended}
    saved=portfolio(c,pid)
    if not review['confirmed']:
        next_action={'label':'Review My Explorer Profile','page':'confirm','kind':'review_profile'}
    elif any(not item['exploration']['is_stale'] for item in saved['shortlist']):
        next_action={'label':'Celebrate My Saved Selections','kind':'view_portfolio'} if path_preferences(c,pid)['active'] else {'label':'Choose My Exploration Preferences','kind':'choose_paths'}
    elif any(not item['is_stale'] for item in saved['explorations']):
        next_action={'label':'Choose a Career to Keep','exploration_id':next(item['id'] for item in saved['explorations'] if not item['is_stale']),'kind':'save_career'}
    else:
        next_action={'label':'Explore a Career World','world_id':(recommended[0]['world_id'] if recommended else worlds[0]['world_id']) if worlds else None,'kind':'explore_world'}
    return {'nickname':p['alias'],'confirmed':review['confirmed'],'confirmed_interests':fields(review['profile_preferences'])['interests'] if review['confirmed'] else [],
        'profile_context':confirmation(c,pid) if review['confirmed'] else None,
        'recommendation_method':'confirmed_interest_catalogue' if recommended else 'no_supported_matches',
        'worlds':[{**w,'recommended':w['world_id'] in reasons,'reason':reasons.get(w['world_id']),
            'evidence_ids':next((r['choice_ids'] for r in recommended if r['world_id']==w['world_id']),[])} for w in worlds],
        'portfolio':saved,'path_preferences':path_preferences(c,pid),'portfolio_completion':portfolio_completion(c,pid),'next_action':next_action}
