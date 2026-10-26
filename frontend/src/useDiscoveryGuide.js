import {useEffect,useRef,useState} from 'react';
import {api} from './api';
import {discoveryAgentView} from './components/DiscoveryAgentPanel';

// Both pages read the same persisted session. Only Profile review submits feedback.
export default function useDiscoveryGuide(state) {
 const [bundle,setBundle]=useState(()=>({guide:state.discovery_guide,agent:state.discovery_agent}));
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState('');
 const mounted=useRef(true);
 const pid=state.profile.id;
 const version=state.discovery_guide?.response_version;
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 const adopt=result=>{if(mounted.current)setBundle({...result,guide:discoveryAgentView(result)});return result;};
 useEffect(()=>{
  let active=true;setLoading(true);setError('');
  setBundle({guide:state.discovery_guide,agent:state.discovery_agent});
  api(`/profiles/${pid}/discovery-agent`,'POST',{event:'discover'}).then(result=>{if(active)adopt(result);}).catch(err=>{if(active)setError(err.message);}).finally(()=>{if(active)setLoading(false);});
  return()=>{active=false;};
 },[pid,version]);
 const request=async body=>{
  setLoading(true);setError('');
  try{return adopt(await api(`/profiles/${pid}/discovery-agent`,'POST',body));}
  catch(err){if(mounted.current)setError(err.message);throw err;}
  finally{if(mounted.current)setLoading(false);}
 };
 const latest=bundle.guide?.latest;
 const ready=Boolean(latest?.content&&!latest.is_stale&&latest.response_version===bundle.guide?.response_version);
 return {...bundle,latest,ready,loading,error,request};
}
