import React from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import DeveloperResearch from './pages/DeveloperResearch';
import AuthGate from './components/AuthGate';
import './style.css';

createRoot(document.getElementById('root')).render(<AuthGate>{(account,onLogout)=>window.location.pathname==='/developer'?<DeveloperResearch/>:<App key={account.id} account={account} onLogout={onLogout}/>}</AuthGate>);

import './spec.css';
import './components/global-ui.css';
