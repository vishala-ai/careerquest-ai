"""Discovery proposal read model and immutable, explicitly confirmed handoffs.

No model calls, XP awards or implicit profile confirmation happen here. Catalogue
matching is deterministic; a model's candidate IDs are revalidated against the
student's accepted interests before crossing the confirmation boundary.
"""
import json
import uuid

from . import discovery_guide as guide
from .profiles import fields, review_state
from .store import events, now, profile


def catalogue():
    return [{'world_id': d['id'], 'title': d['title'], 'source': d['source'],
             'url': d['url'], 'description': d.get('text', '') if isinstance(d.get('text', ''), str) else '',
             'live_verified': False} for d in guide.approved_worlds()]


def references(connection, pid, values, confirmation_id=None):
    review = review_state(connection, pid)
    refs = [{'id': e['id'], 'kind': 'quest_response', 'quest': e['payload']['quest'],
             'choice': e['payload']['choice'], 'interest': e['payload']['interest']}
            for e in review['quest_answers']]
    # Profile interests are explicit selections only after a saved draft or
    # confirmation. Initial suggestions instead reference their actual quests.
    saved = confirmation_id or review['profile_draft'] or review['profile_preferences']
    source = confirmation_id or f'profile-proposal:{pid}:{review["profile_version"]}'
    if saved:
        refs.extend({'id': f'{source}:interest:{i}', 'kind': 'confirmed_interest' if confirmation_id else 'saved_profile_interest',
                     'interest': interest, 'confirmation_event_id': confirmation_id}
                    for i, interest in enumerate(values['interests']))
    if values['correction']:
        refs.append({'id': f'{source}:correction', 'kind': 'student_correction', 'text': values['correction'],
                     'confirmation_event_id': confirmation_id})
    return refs


def supported_worlds(values, refs):
    accepted = set(values['interests'])
    result = {}
    for doc in guide.approved_worlds():
        interests = [i for i in values['interests'] if i in doc['tags']]
        support = [r['id'] for r in refs if r.get('interest') in accepted and r.get('interest') in interests]
        if interests and support:
            result[doc['id']] = {'world_id': doc['id'], 'title': doc['title'], 'source': doc['source'],
                'url': doc['url'], 'live_verified': False, 'choice_ids': support,
                'explanation': 'Connected to the interests you chose to explore: ' + ', '.join(interests) + '.'}
    return result


def select_worlds(values, refs, candidates=(), selected_ids=None):
    supported = supported_worlds(values, refs)
    approved = {d['id'] for d in guide.approved_worlds()}
    if selected_ids is not None:
        if len(selected_ids) > 3 or len(set(selected_ids)) != len(selected_ids):
            raise ValueError('Select up to three different Career Worlds')
        if any(w not in approved for w in selected_ids):
            raise ValueError('Career World IDs must belong to the approved catalogue')
        if any(w not in supported for w in selected_ids):
            raise ValueError('Selected Career Worlds need supporting selected interests')
        return [supported[w] for w in selected_ids], 'student_selected_catalogue'
    if values['not_sure'] or not values['interests']:
        return [], 'exploratory_profile'
    valid = list(dict.fromkeys(w for w in candidates if isinstance(w, str) and w in supported))[:3]
    if valid:
        return [supported[w] for w in valid], 'validated_discovery_proposal'
    return list(supported.values())[:3], 'deterministic_catalogue'


def outcome(connection, pid):
    """Four-part editable proposal, never a confirmation or live inference."""
    try:
        guide.snapshot(connection, pid)
    except guide.GuideConflict:
        return None
    review = review_state(connection, pid)
    values = fields(review['profile_draft'] or review['profile_preferences'] or {
        'interests': [e['payload']['interest'] for e in review['quest_answers']]})
    refs = references(connection, pid, values)
    latest = guide.guide_state(connection, pid)['latest']
    fresh = latest if latest and not latest['is_stale'] and latest['content'] else None
    from .discovery_agent import present
    agent = present(connection, pid)
    active_agent = agent if agent and not agent['is_stale'] else None
    candidates = [w.get('world_id') for w in (active_agent['recommendations'] if active_agent else
        fresh['content']['career_worlds'] if fresh else []) if isinstance(w, dict)]
    valid_ids = supported_worlds(values, refs)
    candidates = list(dict.fromkeys(w for w in candidates if isinstance(w, str) and w in valid_ids))[:3]
    worlds, method = select_worlds(values, refs, candidates)
    # Don't show new recommendations while the agent still needs clarification.
    if active_agent and active_agent['question']:
        worlds, method = [], 'awaiting_clarification'
    result = {'student_id': pid, 'profile_version': review['profile_version'],
        'pending_confirmation': not review['confirmed'], 'proposed_profile': values,
        'profile_origin': 'saved_profile' if review['profile_draft'] or review['profile_preferences'] else 'quest_clues_to_review',
        'story': {'id': fresh['id'], 'version': fresh['version'], 'summary': fresh['content']['summary'],
                  'status': fresh['status'], 'model': fresh['model']} if fresh else None,
        'career_worlds': worlds, 'recommendation_method': method,
        'candidate_world_ids': candidates,
        'next_mission': fresh['content'].get('mini_mission') if fresh else None,
        'evidence_references': refs,
        'agent_session_id': active_agent['session_id'] if active_agent else None}
    accepted = handoff_state(connection, pid)['active']
    if accepted:
        result.update(story=accepted['story'], career_worlds=accepted['career_worlds'],
            next_mission=accepted['next_mission'], recommendation_method=accepted['recommendation_method'],
            agent_session_id=accepted['agent_session_id'])
    return result


def persist(connection, pid, confirmation_id, payload, prepared, selected_ids=None):
    """Caller owns the transaction shared with the confirmation event and XP."""
    existing = connection.execute('SELECT id FROM discovery_handoffs WHERE profile_id=? AND confirmation_event_id=?', (pid, confirmation_id)).fetchone()
    if existing:
        return existing['id']
    values = fields(payload)
    refs = references(connection, pid, values, confirmation_id)
    # Keep feedback/corrections separately from the untouched raw quest records.
    corrections = [dict(r) for r in connection.execute('SELECT id,story_id,verdict,correction,created_at FROM discovery_feedback WHERE profile_id=? ORDER BY rowid', (pid,))]
    for correction in corrections:
        refs.append({'id': correction['id'], 'kind': 'story_feedback', **correction})
    worlds, method = select_worlds(values, refs, prepared['candidate_world_ids'], selected_ids)
    # Unsaved manual edits may differ from the proposal reviewed on the quest
    # page. Do not promote an earlier story/mission as evidence for those edits.
    same_story_context = all(values[k] == prepared['proposed_profile'][k] for k in ('interests', 'correction', 'not_sure'))
    version = connection.execute('SELECT COALESCE(MAX(version),0)+1 FROM discovery_handoffs WHERE profile_id=?', (pid,)).fetchone()[0]
    timestamp, hid = now(), str(uuid.uuid4())
    content = {'id': hid, 'version': version, 'student_id': pid, 'profile_version': payload['version'],
        'confirmation_event_id': confirmation_id, 'selected_interests': values['interests'],
        'exploratory': values['not_sure'] or not values['interests'], 'confirmed_profile': values,
        'suggested_world_ids': [w['world_id'] for w in worlds], 'career_worlds': worlds,
        'recommendation_method': method, 'evidence_references': refs,
        'story': prepared['story'] if same_story_context else None,
        'source_story_id': prepared['story']['id'] if prepared['story'] else None,
        'next_mission': prepared['next_mission'] if same_story_context else None,
        'agent_session_id': prepared['agent_session_id'], 'timestamp': timestamp}
    connection.execute('INSERT INTO discovery_handoffs VALUES(?,?,?,?,?,?,?)',
        (hid, pid, version, payload['version'], confirmation_id, json.dumps(content, sort_keys=True), timestamp))
    return hid


def handoff_state(connection, pid):
    profile(connection, pid)
    review = review_state(connection, pid)
    confirmations = [e for e in events(connection, pid) if e['kind'] == 'profile_confirmed']
    current_id = confirmations[-1]['id'] if confirmations and review['confirmed'] else None
    history = []
    for row in connection.execute('SELECT * FROM discovery_handoffs WHERE profile_id=? ORDER BY version', (pid,)):
        item = json.loads(row['content'])
        item['is_stale'] = row['confirmation_event_id'] != current_id
        history.append(item)
    latest = history[-1] if history else None
    active = latest if latest and not latest['is_stale'] else None
    return {'latest': latest, 'active': active, 'history': history, 'pending_confirmation': not review['confirmed']}
