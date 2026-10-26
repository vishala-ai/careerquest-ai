import React from 'react';
import {ArrowRight} from 'lucide-react';
export default function NextAction({children,onClick,disabled=false,className=''}) {return <button className={`button next-action ${className}`} disabled={disabled} onClick={onClick}>{children}<ArrowRight size={18} aria-hidden="true"/></button>;}
