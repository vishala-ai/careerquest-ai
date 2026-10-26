// Shared read-only projection. Browser storage selects an explorer, never progress.
export function studentExperience(state,career=null,questTotal=3) {
 const exists=Boolean(state?.profile),discovered=Boolean(state?.quest_complete);
 const contextMatches=!career?.profile_context||!state?.profile_version||career.profile_context.profile_version===state.profile_version;
 const confirmed=Boolean(discovered&&state?.confirmed&&(career?.confirmed??true)&&contextMatches);
 const needsReview=!confirmed&&Boolean(state?.profile_preferences||state?.confirmation_version);
 const explored=(career?.portfolio?.explorations?.length||0)>0||(state?.research_count||0)>0;
 const selected=(career?.portfolio?.shortlist||[]).filter(item=>!item.exploration.is_stale);
 const finished=Boolean(confirmed&&career?.portfolio_completion?.active&&!career.portfolio_completion.active.is_stale);
 const portfolioReady=Boolean(confirmed&&career?.portfolio_completion?.ready);
 const earlierPortfolio=(career?.portfolio_completion?.history?.length||0)>0;
 const hasPaths=(career?.path_preferences?.history?.length||0)>0;
 const careerKnown=career!==null;
 const count=Number.isInteger(state?.quest_count)?state.quest_count:0;
 let action;
 if(!exists)action={id:'profiles',label:'Create My Explorer',requiresSetup:true};
 else if(!discovered)action={id:'quests',label:count===0?'Start My First Quest':`Continue Quest ${count+1}`,questIndex:count};
 else if(!confirmed)action={id:'confirm',label:needsReview?'Review Updated Profile':'Review My Explorer Profile'};
 else if(!explored)action={id:'worlds',label:'Explore Careers'};
 else if(!selected.length)action={id:'worlds',label:'Explore Careers to Shortlist'};
 else if(career?.next_action?.kind==='choose_paths')action={id:'worlds',label:'Choose My Exploration Preferences'};
 else action={id:'celebrate',target:finished?'portfolio':'celebrate',label:finished?'View My Portfolio':'Review My Discovery Milestone'};
 const stages=[
  {id:'quests',title:'Discover',done:discovered,available:exists,description:`${count} of ${questTotal} discovery quests saved.`,status:discovered?'Completed':'In progress'},
  {id:'confirm',title:'Confirm',done:confirmed,available:discovered||needsReview,previouslyCompleted:needsReview,description:confirmed?'Your Explorer Profile is confirmed.':needsReview?'Your preferences changed. Review and explicitly reconfirm.':'Review your clues and confirm what feels right.',status:needsReview?'Profile Needs Review':confirmed?'Completed':'Review your profile'},
  {id:'worlds',title:'Explore',done:explored,available:confirmed||explored,description:explored?'Your saved research remains yours to revisit.':'Explore supported careers, then save a possibility you want to keep.',status:explored?'Completed':'Explore careers'},
  {id:'celebrate',title:'Celebrate',done:finished||earlierPortfolio,available:(confirmed&&(selected.length>0||!careerKnown)&&career?.next_action?.kind!=='choose_paths')||earlierPortfolio||hasPaths,previouslyCompleted:earlierPortfolio&&!finished,prerequisite:!exists?'Create your explorer above to begin.':!confirmed?'Confirm your current Explorer Profile first.':career?.next_action?.kind==='choose_paths'?'Save your exploration preferences or choose I’m Still Exploring on Explore Careers first.':'Save a career with your confirmed profile to begin your portfolio.',description:finished?'Your current Career Discovery Portfolio snapshot is saved.':earlierPortfolio?'Previous portfolio snapshots are saved. Review current choices before a new version.':'Bring your confirmed interests, saved careers and paths together.',status:!careerKnown&&confirmed?'Open saved progress':finished?'Completed':earlierPortfolio?'Earlier portfolio saved':hasPaths?'Paths saved':'Create your portfolio'},
 ].map(stage=>({...stage,locked:!stage.available,active:!finished&&stage.id===action.id,primary:stage.id===action.id}));
 return {confirmed,needsReview,explored,finished,portfolioReady,earlierPortfolio,careerKnown,action,stages,
  journey:{greeting:exists?`Hi, ${state.profile.alias?.trim()||'explorer'}! 👋`:'Welcome, future explorer! 👋',complete:finished,action,stages}};
}

export function primaryDestination(page,screen='worlds') {
 if(page==='welcome')return 'welcome';
 if(page==='quests')return 'quests';
 if((page==='worlds'||page==='portfolio')&&screen==='worlds')return 'worlds';
 if(page==='portfolio'||page==='celebrate'||(page==='worlds'&&screen!=='worlds'))return 'portfolio';
 if(page==='worlds')return 'worlds';
 return null; // Preserved roadmap/reflection/history pages are secondary destinations.
}

export function activeStage(page,screen,experience) {
 if(page==='quests')return 'quests';
 if(page==='confirm')return 'confirm';
 if((page==='worlds'||page==='portfolio')&&screen==='worlds')return 'worlds';
 if(page==='portfolio'||page==='celebrate'||page==='worlds')return 'celebrate';
 return experience.action.id==='profiles'?'quests':experience.action.id;
}
