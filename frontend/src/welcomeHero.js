import {studentExperience} from './studentExperience.js';

// Informational copy only. Progress and current-vs-historical portfolios come
// from the same persisted-record projection as Home's Adventure Trail.
export function welcomeHero(state, questTotal=3, progress=studentExperience(state)) {
  const nickname=state?.profile?.alias?.trim()||'explorer';
  let title=`Hi, ${nickname}! 👋`,message,phase;
  if(!state){phase='setup';message='Your first discovery quest is waiting. Choose a explorer nickname and grade, then begin from your Adventure Trail. There are no right or wrong answers.';}
  else if(!state.quest_complete){phase=state.quest_count>0?'partial':'new';message=state.quest_count>0
    ?`You’ve completed ${state.quest_count} of ${questTotal} discovery quests. Every clue helps you notice what sparks your curiosity.`
    :`A fresh adventure is waiting for you. ${questTotal} short discovery quests will help you collect your first clues.`;}
  else if(!progress.confirmed){phase='review';message=progress.needsReview
    ?'Your interests can grow with you. Your updated Explorer Profile is ready for another review. Any earlier career selections and portfolios stay saved.'
    :'Your discovery quests are complete. These clues are yours to shape into an Explorer Profile that feels right.';}
  else if(progress.finished){phase='saved';title=`Hi, ${nickname}! Your career portfolio is ready.`;message='You’ve brought together your interests and career choices. You can explore a new direction whenever you’re ready.';}
  else if(progress.earlierPortfolio){phase='changed';message=progress.portfolioReady
    ?'Your earlier career portfolio stays saved. Your current choices have changed, and a new preview is ready for you to review.'
    :'Your earlier career portfolio stays saved. Explore your current interests and career choices before creating an updated version.';}
  else if(progress.portfolioReady){phase='ready';message='Your confirmed interests and saved career choices are ready to come together. Celebrate your discoveries, then review your Career Discovery Portfolio.';}
  else if(progress.explored){phase='research';message='You’ve started exploring career possibilities. Keep the careers that interest you and choose your exploration preferences—or keep your priorities open.';}
  else {phase='research_ready';message='Your Explorer Profile is confirmed. Explore Career Worlds, compare possibilities and save the careers you want to revisit.';}
  const grade=state?.profile?.grade,points=state?.profile?.xp;
  return {title,message,phase,grade:Number.isInteger(grade)&&grade>=9&&grade<=12?grade:null,points:Number.isInteger(points)&&points>=0?points:null};
}
