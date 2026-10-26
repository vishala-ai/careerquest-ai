"""Event-backed profile review. Existing history and confirmed interests are retained."""
import json
from .store import events, add_event, record_event


def fields(values):
    return {
        'interests': list(dict.fromkeys(value.strip().lower() for value in values.get('interests', []) if value.strip())),
        'learning_style': values.get('learning_style', 'Hands-on projects'),
        'goal': values.get('goal', 'Explore careers and college majors'),
        'correction': values.get('correction', ''),
        'not_sure': values.get('not_sure', False),
    }


def review_state(connection, pid):
    history = events(connection, pid)
    answers = {}
    original_count = 0
    confirmations = []
    drafts = []
    last_change = -1
    for index, event in enumerate(history):
        kind = event['kind']
        if kind in ('quest_completed', 'quest_revised'):
            step = event['payload'].get('quest', original_count)
            if kind == 'quest_completed':
                original_count += 1
            answers[step] = event
        if kind == 'profile_confirmed':
            confirmations.append((index, event))
        if kind == 'profile_drafted':
            drafts.append((index, event))
        if kind in ('profile_drafted', 'quest_revised'):
            last_change = index
    latest = confirmations[-1] if confirmations else None
    draft = drafts[-1] if drafts and (not latest or drafts[-1][0] > latest[0]) else None
    confirmed = bool(latest and latest[0] > last_change)
    versions = [event['payload'].get('version', 0) for _, event in confirmations + drafts]
    maximum = max([len(confirmations), 0, *versions])
    current_version = draft[1]['payload']['version'] if draft else (latest[1]['payload'].get('version', len(confirmations)) if latest else 1)
    return {
        'quest_answers': [answers[key] for key in sorted(answers)],
        'confirmed': confirmed,
        'confirmation_version': len(confirmations),
        'profile_version': current_version,
        'profile_preferences': latest[1]['payload'] if latest else None,
        'profile_draft': draft[1]['payload'] if draft else None,
        'max_profile_version': maximum,
    }


def evidence(review):
    return [{'event_id': event['id'], **event['payload'], 'answered_at': event['created_at']} for event in review['quest_answers']]


def save_draft(connection, pid, values, start_edit=False):
    review = review_state(connection, pid)
    body = fields(values)
    existing = review['profile_draft'] or review['profile_preferences']
    if existing and body == fields(existing) and not start_edit:
        return
    version = review['profile_draft']['version'] if review['profile_draft'] else review['max_profile_version'] + 1
    metadata = review_feedback(connection, pid, values)
    if metadata and values.get('review_verdict') in ('Somewhat', 'Not really'):
        previous = fields(existing or {'interests': [e['payload']['interest'] for e in review['quest_answers']]})
        metadata['review_feedback']['changes'] = {
            'mode': values['review_verdict'], 'kept': [i for i in body['interests'] if i in previous['interests']],
            'added': [i for i in body['interests'] if i not in previous['interests']],
            'removed': [i for i in previous['interests'] if i not in body['interests']], 'correction': body['correction'],
            'details': [{'field': label, 'before': previous[key], 'after': body[key]}
                        for key, label in (('learning_style', 'Preferred activities'), ('goal', 'Exploration goal'), ('not_sure', 'Keeping options open'))
                        if previous[key] != body[key]],
        }
    add_event(connection, pid, 'profile_drafted', {**body, 'version': version, 'quest_answers': evidence(review), **metadata})


def review_feedback(connection, pid, values):
    verdict = values.get('review_verdict')
    if verdict is None:
        return {}
    if verdict not in ('Yes', 'Somewhat', 'Not really'):
        raise ValueError('Unknown profile review choice')
    sid = values.get('review_story_id')
    if sid:
        from .discovery_guide import guide_state
        latest = guide_state(connection, pid)['latest']
        if not latest or latest['id'] != sid or latest['is_stale']:
            raise ValueError('This story changed. Review the current proposal first.')
    return {'review_feedback': {'verdict': verdict, 'story_id': sid,
                              'correction': values.get('correction', ''), 'source': 'explorer_profile'}}


def confirm_profile(connection, pid, values):
    with connection:
        if not connection.in_transaction:
            connection.execute('BEGIN IMMEDIATE')
        _confirm_profile(connection, pid, values)


def _confirm_profile(connection, pid, values):
    from . import discovery_handoff as handoff
    review = review_state(connection, pid)
    if values.get('expected_version') is not None and values['expected_version'] != review['profile_version']:
        raise ValueError('This profile changed. Reload and review the latest version.')
    body = fields(values)
    accepted_review = (review['profile_preferences'] or {}).get('review_feedback')
    replay = (review['confirmed'] and body == fields(review['profile_preferences']) and accepted_review
              and values.get('review_verdict') == accepted_review['verdict']
              and values.get('review_story_id') == accepted_review['story_id'])
    # Confirmation makes the source story stale. An exact retry of that already
    # accepted review remains idempotent; a different stale story is rejected.
    metadata = {'review_feedback': accepted_review} if replay else review_feedback(connection, pid, values)
    if values.get('review_verdict') not in (None, 'Yes'):
        raise ValueError('Review the revised proposal before confirmation')
    prepared = handoff.outcome(connection, pid)
    if prepared is None:
        raise ValueError('Complete all discovery quests before confirming a profile')
    selected_ids = values.get('selected_world_ids')
    # Validate caller-selected IDs before any profile, event or XP write.
    handoff.select_worlds(body, handoff.references(connection, pid, body, 'pending-confirmation'), prepared['candidate_world_ids'], selected_ids)
    current = handoff.handoff_state(connection, pid)['active']
    same_selection = selected_ids is None or current and selected_ids == current['suggested_world_ids']
    if review['confirmed'] and body == fields(review['profile_preferences']) and (same_selection or current is None):
        confirmation = [e for e in events(connection, pid) if e['kind'] == 'profile_confirmed'][-1]
        handoff.persist(connection, pid, confirmation['id'], confirmation['payload'], prepared, selected_ids)
        return
    version = review['profile_draft']['version'] if review['profile_draft'] else review['max_profile_version'] + 1
    payload = {**body, 'version': version, 'quest_answers': evidence(review), **metadata}
    previous = review['profile_preferences']
    changed = not previous or fields(previous) != body or previous.get('quest_answers', payload['quest_answers']) != payload['quest_answers']
    connection.execute('UPDATE profiles SET interests=? WHERE id=?', (json.dumps(body['interests']), pid))
    confirmation_id = record_event(connection, pid, 'profile_confirmed', payload, xp=10 if changed else 0, event_id=f'{pid}:profile-confirm:{version}')
    handoff.persist(connection, pid, confirmation_id, payload, prepared, selected_ids)
