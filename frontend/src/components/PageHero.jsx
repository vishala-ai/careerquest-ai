import React from 'react';
export function MissionInstruction({children}) {return children?<p className="mission-instruction">{children}</p>:null;}
export default function PageHero({eyebrow,title,children}) {
 return <div className="page-heading page-hero"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><MissionInstruction>{children}</MissionInstruction></div>;
}
