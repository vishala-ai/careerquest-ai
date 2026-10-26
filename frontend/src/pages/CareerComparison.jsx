import React from 'react';

export default function CareerComparison({worlds}) {
 if(worlds.length<2)return null;
 const facts=items=><ul>{items.map((item,index)=><li key={index}>{item.text} <span className="career-citation">{item.source_ids.map(id=><a key={id} href={`#source-${id}`}>[Source]</a>)}</span></li>)}</ul>;
 return <section className="panel career-comparison" aria-labelledby="career-comparison-heading"><h2 id="career-comparison-heading">Compare Careers</h2><p>Compare supported activities, skills and educational fields. These possibilities are not ranked. Full notes and sources follow below.</p><div className="career-comparison-scroll" role="region" aria-label="Career comparison table" tabIndex={0}><table><caption>Your selected careers, side by side</caption><thead><tr><th scope="col">Career</th><th scope="col">Career activities</th><th scope="col">Skills to explore</th><th scope="col">Educational fields</th></tr></thead><tbody>{worlds.map(world=><tr key={world.world_id}><th scope="row">{world.title}</th><td>{facts(world.activities)}</td><td>{facts(world.skills)}</td><td>{facts(world.educational_fields)}</td></tr>)}</tbody></table></div></section>;
}
