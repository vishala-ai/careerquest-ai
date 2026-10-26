import React from 'react';
import {Home,Sparkles,Globe2,Map} from 'lucide-react';

export const PRIMARY_PAGES=[['welcome','Home',Home],['quests','Discover',Sparkles],['worlds','Explore Careers',Globe2],['portfolio','My Portfolio',Map]];
export default function Navigation({current,onNavigate,busy=false}) {
 return <nav className="global-navigation" aria-label="Main navigation">{PRIMARY_PAGES.map(([id,label,Icon])=><button key={id} type="button" disabled={busy} onClick={()=>onNavigate(id)} className={current===id?'active':''} aria-current={current===id?'page':undefined}><Icon size={19} aria-hidden="true"/><span>{label}</span></button>)}</nav>;
}
