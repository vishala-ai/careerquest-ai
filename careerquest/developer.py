"""Local-only tester boundary and allowlisted research diagnostics; no identity auth.

Off by default. Never enable this mode on a shared server, tunnel or proxy.
"""
import ipaddress
import json
import os
import re
from urllib.parse import urlsplit
from fastapi import HTTPException, Request

def require_local_developer(request: Request):
    def loopback(host):
        if host == 'localhost': return True
        try: return ipaddress.ip_address(host or '').is_loopback
        except ValueError: return False
    enabled = os.getenv('CAREERQUEST_ENV') == 'local' and os.getenv('CAREERQUEST_DEV_TOOLS') == '1' and loopback(os.getenv('CAREERQUEST_HOST','127.0.0.1'))
    peer = request.client.host if request.client else None
    # Host/Origin checks prevent DNS rebinding and remote browser requests. Never
    # accept forwarded identity: this environment must have a direct local socket.
    forwarded = any(k.lower() == 'forwarded' or k.lower().startswith('x-forwarded-') for k in request.headers)
    origin = request.headers.get('origin')
    try:
        host_ok = loopback(urlsplit('//'+request.headers.get('host','')).hostname)
        origin_url = urlsplit(origin) if origin else None
        origin_ok = not origin or (origin_url.scheme in ('http','https') and loopback(origin_url.hostname))
    except ValueError: host_ok = origin_ok = False
    # Top-level navigation may be cross-site (for example from a bookmark or
    # browser controller). It serves only the UI shell, never receipts/actions.
    document_navigation = request.method=='GET' and request.url.path=='/developer' and request.headers.get('sec-fetch-mode')=='navigate' and request.headers.get('sec-fetch-dest')=='document'
    fetch_ok = request.headers.get('sec-fetch-site') != 'cross-site' or document_navigation
    if not (enabled and peer and peer != 'localhost' and loopback(peer) and host_ok and origin_ok and not forwarded and fetch_ok):
        raise HTTPException(403, 'Developer tools are disabled outside an explicitly enabled, direct local development environment')

METHODS = {'student_world_selection','groq','bounded_policy','bounded_policy_fallback'}
ACTIONS = {'research_careers','research_college','create_plan','reflect','ask_question'}
def identifier(value):
    return value if isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_./:-]{1,120}',value) else None

def receipt(row):
    """Project saved receipts; never return prompts, interests, answers or provider bodies."""
    result = json.loads(row['result']); trace=[]
    for item in result.get('trace',[]):
        safe={k:item[k] for k in ('step','action','rejected_action','method','status','model','error_type') if k in item and identifier(item[k])}
        if safe.get('method') not in METHODS: safe.pop('method',None)
        trace.append(safe)
    sources=result.get('sources',[])
    metadata=[]
    for source in sources:
        try: url=urlsplit(source.get('url','')); https=bool(url.scheme=='https' and url.hostname)
        except ValueError: https=False
        metadata.append({'id':identifier(source.get('id')),'metadata_present':all(bool(source.get(k)) for k in ('id','title','source','url')),'https_url':https,'live_verified':source.get('live_verified') is True})
    known={s['id'] for s in metadata if s['id']}
    refs=[i.get('source_ids',[]) for world in result.get('worlds',[]) for i in [world.get('overview',{}),*world.get('activities',[]),*world.get('skills',[]),*world.get('educational_fields',[])]]
    return {'run_id':row['id'],'created_at':row['created_at'],'action':row['action'] if row['action'] in ACTIONS else 'unknown',
        'status':result.get('status') if result.get('status') in ('ok','blocked','needs_input','awaiting_student_confirmation') else 'unknown',
        'trace':trace,'world_ids':[w['world_id'] for w in result.get('worlds',[]) if identifier(w.get('world_id'))],
        'source_validation':{'sources':metadata,'all_metadata_valid':bool(metadata) and all(s['metadata_present'] and s['https_url'] for s in metadata),
            'evidence_references_valid':all(bool(r) and set(r)<=known for r in refs) if refs else None,'live_research':False}}

def receipts(c,pid,limit=20):
    return [receipt(row) for row in c.execute("SELECT * FROM runs WHERE profile_id=? AND action IN ('research_careers','research_college') ORDER BY rowid DESC LIMIT ?",(pid,limit))]
