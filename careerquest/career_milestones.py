"""Career celebrations are receipts, never XP or badge awards.

Call record() inside the same transaction as the authoritative milestone.
First-time kinds are unique for the fictional explorer's lifetime.
"""
import json
import uuid
from .store import profile,now

KINDS={'first_research','first_shortlist','second_shortlist','primary_path','secondary_path','portfolio_completed'}

def record(c,pid,kind,source_id,confirmation_id,career=None):
    if kind not in KINDS:raise ValueError('Unknown career milestone')
    payload={'nickname':profile(c,pid)['alias'].strip() or 'Explorer'}
    if career:payload.update(world_id=career['world_id'],career_name=career['title'])
    c.execute('INSERT OR IGNORE INTO career_milestones VALUES(?,?,?,?,?,?,?,?,?)',
        (str(uuid.uuid4()),pid,kind,source_id,confirmation_id,json.dumps(payload,sort_keys=True),now(),None,None))

def claim(c,pid,kind=None):
    """Atomically deliver one unseen receipt. Reload never redelivers a receipt."""
    from .career_worlds import confirmation,CareerConflict
    with c:
        c.execute('BEGIN IMMEDIATE')
        try:context=confirmation(c,pid)
        except CareerConflict:return {'celebration':None}
        if kind is not None and kind!='portfolio_completed':raise ValueError('Unsupported celebration scope')
        row=c.execute('SELECT * FROM career_milestones WHERE profile_id=? AND confirmation_event_id=? AND delivered_at IS NULL AND (? IS NULL OR kind=?) ORDER BY rowid LIMIT 1',(pid,context['confirmation_event_id'],kind,kind)).fetchone()
        if not row:return {'celebration':None}
        c.execute('UPDATE career_milestones SET delivered_at=? WHERE id=?',(now(),row['id']))
        return {'celebration':{'id':row['id'],'kind':row['kind'],**json.loads(row['payload'])}}

def acknowledge(c,pid,mid):
    from .career_worlds import WorldUnknown,CareerConflict
    with c:
        row=c.execute('SELECT * FROM career_milestones WHERE id=? AND profile_id=?',(mid,pid)).fetchone()
        if not row:raise WorldUnknown('Celebration not found')
        if not row['delivered_at']:raise CareerConflict('This celebration has not been delivered')
        c.execute('UPDATE career_milestones SET acknowledged_at=COALESCE(acknowledged_at,?) WHERE id=?',(now(),mid))
    return {'acknowledged':True}
