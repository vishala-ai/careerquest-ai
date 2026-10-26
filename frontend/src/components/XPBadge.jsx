import React,{useId} from 'react';
import {Zap,HelpCircle} from 'lucide-react';

export default function XPBadge({state}) {
 const id=useId(),value=state?.profile?.xp,known=Number.isInteger(value)&&value>=0;
 return <details className="xp-badge"><summary aria-describedby={id}><Zap size={18} aria-hidden="true"/><span><strong>{known?value:'—'}</strong> Explorer Points</span><HelpCircle size={17} aria-hidden="true"/></summary><p id={id}>Explorer Points (XP) mark saved activity in your adventure. Your total comes from backend records. Points do not measure ability, grades or career fit.</p></details>;
}
