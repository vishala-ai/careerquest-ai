"""LangGraph workflow: route -> selected bounded tool -> finish, with explicit failure branch.
Application data/history is durable in SQLite; graph checkpoint persistence is not claimed.
"""
from typing import TypedDict
from .agent import choose,groq_choose,execute,routing_model
from .store import profile,save_run
class AgentState(TypedDict,total=False):
    profile_id:str
    message:str
    use_groq:bool
    simulate_failure:bool
    action:str
    result:dict
    trace:list
    world_ids:list
    research_only:bool
    profile_context:dict

def build_graph(connection):
    from langgraph.graph import StateGraph,START,END
    def route(s):
        p=profile(connection,s['profile_id'])
        context=None
        if s.get('research_only'):
            from .career_worlds import confirmation
            context=confirmation(connection,s['profile_id'])
        try:
            action='research_careers' if s.get('world_ids') else groq_choose(s['message'],p) if s.get('use_groq') else choose(s['message'],p)
            trace=[{'step':'route','action':action,'method':'student_world_selection' if s.get('world_ids') else 'groq' if s.get('use_groq') else 'bounded_policy'}]
            if s.get('use_groq') and not s.get('world_ids'):trace[0]['model']=routing_model()
        except Exception as exc:
            action=choose(s['message'],p)
            trace=[{'step':'route','action':action,'status':'model_unavailable','error_type':type(exc).__name__,'method':'bounded_policy_fallback'}]
        if s.get('research_only') and action not in ('research_careers','research_college'):
            trace.append({'step':'research_guard','rejected_action':action,'method':'bounded_policy_fallback'});action='research_careers'
        return {'action':action,'trace':trace,'profile_context':context}
    def tool(s):
        try:
            result=execute(connection,s['profile_id'],s['action'],s['message'],s.get('simulate_failure',False),world_ids=s['world_ids']) if s.get('world_ids') else execute(connection,s['profile_id'],s['action'],s['message'],s.get('simulate_failure',False))
        except (ConnectionError,TimeoutError) as exc:
            result={'status':'blocked','message':'Research unavailable; saved progress preserved. No facts invented.','sources':[]}
            return {'result':result,'trace':s['trace']+[{'step':'tool','status':'failed','error_type':type(exc).__name__}]}
        return {'result':result,'trace':s['trace']+[{'step':'tool','status':'ok','action':s['action']}]}
    def finish(s):
        result=dict(s['result']);result['action']=s['action'];result['trace']=s['trace']
        if s.get('world_ids') or s.get('research_only'):
            from .career_worlds import save_result
            if s.get('profile_context'):result['profile_context']=s['profile_context']
            return {'result':save_result(connection,s['profile_id'],result)}
        result['run_id']=save_run(connection,s['profile_id'],s['action'],result)
        return {'result':result}
    g=StateGraph(AgentState)
    g.add_node('route',route);g.add_node('execute_tool',tool);g.add_node('finish',finish)
    g.add_edge(START,'route');g.add_edge('route','execute_tool');g.add_edge('execute_tool','finish');g.add_edge('finish',END)
    return g.compile()

def run_graph(connection,profile_id,message,use_groq=False,simulate_failure=False,world_ids=None,research_only=False):
    graph=build_graph(connection)
    return graph.invoke({'profile_id':profile_id,'message':message,'use_groq':use_groq,'simulate_failure':simulate_failure,'world_ids':world_ids,'research_only':research_only})['result']


class DiscoveryAgentState(TypedDict,total=False):
    profile_id:str
    session_id:str
    action:str
    decision_id:str
    next:str
    result:dict


def build_discovery_graph(connection):
    """Discovery branch of the same backend: model route -> allowlisted tool -> pause/route.

    Durable application state/tool receipts live in SQLite, not a native graph checkpointer.
    """
    from langgraph.graph import StateGraph,START,END
    from . import discovery_agent as discovery
    graph=StateGraph(DiscoveryAgentState)
    graph.add_node('select_discovery_tool',lambda state:discovery.route_node(connection,state))
    for action in discovery.ACTIONS:
        graph.add_node(action,lambda state:discovery.tool_node(connection,state))
        graph.add_conditional_edges(action,lambda state:state['next'],{'route':'select_discovery_tool','finish':'finish_discovery'})
    graph.add_node('finish_discovery',lambda state:discovery.finish_node(connection,state))
    graph.add_edge(START,'select_discovery_tool')
    graph.add_conditional_edges('select_discovery_tool',lambda state:state['action'],{action:action for action in discovery.ACTIONS})
    graph.add_edge('finish_discovery',END)
    return graph.compile()
