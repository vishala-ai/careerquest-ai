"""Read-only discovery progress and reward receipts, including legacy API events."""
from .quests import QUESTS, QUEST_REWARD_XP


def discovery_state(pid, history, answers):
    completed = {}
    original_index = 0
    for event in history:
        if event['kind'] != 'quest_completed':
            continue
        step = event['payload'].get('quest', original_index)
        original_index += 1
        if type(step) is not int or not 0 <= step < len(QUESTS) or step in completed:
            continue
        reward = event['payload'].get('xp_awarded')
        # Prior API receipts used this unique ID and the fixed 20-XP policy.
        # Never rewrite those persisted records or infer XP from later revisions.
        if reward is None and event['id'] == f'{pid}:quest:{step}':
            reward = QUEST_REWARD_XP
        if type(reward) is not int or reward < 0:
            reward = None
        completed[step] = {'event_id': event['id'], 'quest': step, 'xp_awarded': reward}
    receipts = [completed[step] for step in sorted(completed)]
    saved = {event['payload'].get('quest') for event in answers}
    return {
        'total': len(QUESTS),
        'first_incomplete': next((step for step in range(len(QUESTS)) if step not in saved), None),
        'first_completion_xp': QUEST_REWARD_XP,
        'quest_xp': sum(receipt['xp_awarded'] for receipt in receipts) if all(receipt['xp_awarded'] is not None for receipt in receipts) else None,
        'xp_events': receipts,
    }
