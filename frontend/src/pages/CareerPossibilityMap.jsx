import React from 'react';

export default function CareerPossibilityMap({interests,portfolio,paths}) {
 const saved=portfolio.shortlist.filter(item=>!item.exploration.is_stale);
 return <section className="career-possibility-map" aria-labelledby="career-map-heading"><h3 id="career-map-heading">Your visual map of possibilities</h3><p>Your confirmed interests, saved careers and chosen paths, together. The connections show your exploration journey, not career-fit predictions.</p><ol className="career-map-columns"><li><h4>Confirmed interests</h4>{interests.length?<ul>{interests.map(interest=><li key={interest}>{interest}</li>)}</ul>:<p>You’re keeping your interests open.</p>}</li><li><h4>Careers saved by you</h4>{saved.length?<ul>{saved.map(item=><li key={item.id}>{item.exploration.world.title}</li>)}</ul>:<p>Save a current career to add it to your map.</p>}</li><li><h4>Your Exploration Paths</h4>{paths?.paths?.length?<ul>{paths.paths.map(path=><li key={path.priority}><strong>{path.priority==='primary'?'Primary':'Secondary'}:</strong> {path.title}</li>)}</ul>:<p>Choose a primary path below. A secondary path is optional.</p>}</li></ol></section>;
}
