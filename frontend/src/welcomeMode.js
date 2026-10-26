// Existence/progress comes from the backend. A creation receipt is only a
// transient acknowledgement of a successful POST, never a persisted user flag.
export function welcomeMode(state, createdProfileId = '', explorers = []) {
  if (!state) return explorers.length ? 'choose' : 'setup';
  if (createdProfileId && createdProfileId === state.profile?.id && state.quest_count === 0 && !state.quest_complete) return 'aboard';
  return 'returning';
}
