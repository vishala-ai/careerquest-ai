// Use only this snapshot's student-selected priorities, never current preferences.
// Sorting a copy preserves immutable saved records and the order of other careers.
export function orderedPortfolioCareers(snapshot) {
 const ranks=new Map((snapshot.undecided?[]:snapshot.paths||[]).map(path=>[path.world_id,path.priority==='primary'?0:path.priority==='secondary'?1:2]));
 return [...(snapshot.shortlist||[])].sort((a,b)=>(ranks.get(a.world_id)??2)-(ranks.get(b.world_id)??2));
}
