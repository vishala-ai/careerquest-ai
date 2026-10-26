// Presentation states come from Home's persisted-backend projection.
// Recommendation never changes availability or erases saved completion.
export function trailMilestones(journey) {
  return journey.stages.map(stage => ({
    ...stage,
    primary:stage.primary??stage.active,
    target:(stage.primary??stage.active)?journey.action.target||stage.id:stage.id==='celebrate'&&stage.done?'portfolio':stage.id,
    historicalPortfolio:stage.id==='celebrate'&&stage.previouslyCompleted&&!journey.complete,
    status:stage.locked?'Locked':stage.active?(stage.id==='celebrate'&&stage.previouslyCompleted?'Update available':'Recommended Next'):stage.done?(stage.id==='celebrate'&&stage.previouslyCompleted?'Earlier portfolio saved':'Completed'):'Available',
    prerequisite:!stage.locked?'':stage.prerequisite|| (journey.action.requiresSetup?'Create your explorer above to begin.':stage.id==='confirm'?'Complete all three discovery quests first.':'Confirm your current Explorer Profile first.'),
    actionLabel:(stage.primary??stage.active)?journey.action.label:stage.done?`Revisit ${stage.title}`:`Open ${stage.title}`,
  }));
}
