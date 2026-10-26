"""Streamlit synthetic-only CareerQuest AI demo."""
import os
import streamlit as st
from careerquest.store import connect,create_profile,profile,set_interests,add_event,events,latest_plan,save_plan
from careerquest.agent import run
try:
    from careerquest.graph import run_graph
    import langgraph
    AGENT_RUN = run_graph
    GRAPH_AVAILABLE = True
except ImportError:
    AGENT_RUN = run
    GRAPH_AVAILABLE = False
from careerquest.quests import QUESTS
st.set_page_config(page_title='CareerQuest AI',page_icon='🧭',layout='wide')
st.markdown('''<style>.block-container{max-width:1120px;padding-top:2rem}.stButton button{border-radius:12px}h1{color:#403083}</style>''',unsafe_allow_html=True)
st.title('🧭 CareerQuest AI')
st.caption('Discover interests • Explore pathways • Build your high-school-to-college adventure')
st.info('DEMO ONLY — fictional profiles and illustrative, offline career information. Not admissions, financial-aid or career-placement advice.')
c=connect(os.getenv('CAREERQUEST_DB','var/careerquest.sqlite3'))
if 'pid' not in st.session_state:st.session_state.pid=None
if not st.session_state.pid:
    st.subheader('Start your explorer journey')
    alias=st.text_input('Explorer nickname (fictional)',value='Demo Explorer')
    grade=st.selectbox('Grade',[9,10,11,12],index=2)
    if st.button('Create demo explorer',type='primary'):
        st.session_state.pid=create_profile(c,alias,grade);st.rerun()
    st.stop()
pid=st.session_state.pid;p=profile(c,pid)
st.sidebar.header(f'👋 {p["alias"]}')
st.sidebar.write(f'Grade {p["grade"]} · ⭐ {p["xp"]} XP')
st.sidebar.caption('Local demo profile; no account authentication')
st.sidebar.caption('Agent engine: '+('LangGraph workflow' if GRAPH_AVAILABLE else 'Core fallback — install LangGraph'))
if st.sidebar.button('New fictional explorer'):
    st.session_state.pid=None
    for key in ('quest_step','last_result','last_plan_run','last_reflection'):st.session_state.pop(key,None)
    st.rerun()
tab1,tab2,tab3,tab4=st.tabs(['🎮 Discovery Quests','🌎 Career Worlds','🗺️ My Roadmap','📚 Journey & Agent Trace'])
with tab1:
    st.subheader('Discovery Adventure')
    step=min(len([e for e in events(c,pid) if e['kind']=='quest_completed']),len(QUESTS))
    if step<len(QUESTS):
        q=QUESTS[step];st.progress(step/len(QUESTS));st.markdown(f'### Quest {step+1}: {q["title"]}')
        st.write(q['question']);selection=st.radio('Choose what sounds fun today',list(q['options']),key=f'quest_{step}')
        if st.button('Complete quest +20 XP',key=f'complete_{step}',type='primary'):
            # Award XP once per quest per profile, even on reruns.
            event_id=f'{pid}:quest:{step}'
            add_event(c,pid,'quest_completed',{'quest':step,'choice':selection,'interest':q['options'][selection]},xp=20,event_id=event_id)
            tags=[e['payload']['interest'] for e in events(c,pid) if e['kind']=='quest_completed']
            set_interests(c,pid,tags);st.session_state.quest_step=step+1;st.rerun()
    else:
        st.success('🏅 Curious Explorer badge unlocked! You can now explore career worlds.')
        st.write('Your interests are clues, not permanent labels or a career suitability score.')
        if st.button('Explore career worlds →'):st.session_state.active_hint='career';st.rerun()
    st.write('**Your current exploration interests:**',', '.join(p['interests']) or 'Not yet selected')
    with st.expander('Edit my interests'):
        opts=['science','technology','art','helping','building','research','creative','people','biology','coding','design']
        chosen=st.multiselect('Change your interests at any time',opts,default=[x for x in p['interests'] if x in opts])
        if st.button('Save my interests'):set_interests(c,pid,chosen);st.rerun()
with tab2:
    st.subheader('Explore career and college pathways')
    message=st.text_input('Ask CareerQuest',value='Explore careers that connect to my interests',key='research_prompt')
    col1,col2=st.columns([1,1]);use_groq=col1.checkbox('Use Groq for action selection (cloud, optional)',value=False)
    st.caption('Groq sends your question, grade, and interests to its cloud API. Use fictional demo data only. Without Groq, routing is deterministic; research stays offline in either mode.')
    fail=col2.checkbox('Simulate research-tool failure (demo)',value=False)
    if st.button('Ask my career guide',type='primary'):
        result=AGENT_RUN(c,pid,message,use_groq,fail);st.session_state.last_result=result
    if 'last_result' in st.session_state:
        result=st.session_state.last_result
        if result['status']=='blocked':st.warning(result['message'])
        else:st.write(result['message'])
        for m in result.get('matches',[]):
            with st.container(border=True):st.markdown(f'**{m["title"]}**');st.write(m['description']);st.caption(f'Source record: {m["source_id"]}')
        for s in result.get('sources',[]):
            if s['url']:st.markdown(f'[{s["source"]}: {s["title"]}]({s["url"]}) — *not live verified*')
        with st.expander('Agent decision trace'):st.json(result['trace'])
with tab3:
    st.subheader('Your high-school-to-college roadmap')
    st.write('Suggested activities are exploratory, not required coursework or verified application deadlines.')
    if st.button('Create / revise my roadmap',type='primary'):
        st.session_state.last_plan_run=AGENT_RUN(c,pid,'Create my grade-specific roadmap and next step')
    proposal=st.session_state.get('last_plan_run',{})
    if proposal.get('status')=='awaiting_student_confirmation':
        st.markdown('#### Proposed roadmap — review before saving')
        for item in proposal['plan']['activities']:st.write('• '+item)
        if st.button('Confirm and save roadmap',type='primary'):
            ver=save_plan(c,pid,proposal['plan'])
            st.session_state.pop('last_plan_run',None)
            st.success(f'Saved roadmap version {ver}')
            st.rerun()
    saved=latest_plan(c,pid)
    if saved:
        st.caption(f'Plan version {saved["version"]} · Grade {saved["content"]["grade"]}')
        for i,item in enumerate(saved['content']['activities'],1):st.checkbox(item,key=f'plan_{saved["version"]}_{i}')
        st.caption(saved['content']['note'])
    else:st.info('Complete quests and generate your first roadmap.')
    st.markdown('#### Reflect and adapt')
    reflection=st.text_area('What did you enjoy or want to change? (fictional demo)',height=90)
    if st.button('Save reflection +10 XP') and reflection.strip():
        st.session_state.last_reflection=AGENT_RUN(c,pid,'Reflection: '+reflection);st.success('Reflection saved. Edit interests above and regenerate your roadmap to adapt it.')
with tab4:
    st.subheader('Your journey')
    st.caption('This timeline is stored in SQLite and survives app restarts. It is not a production student account.')
    for e in reversed(events(c,pid)[-20:]):st.write(f'**{e["kind"]}** · {e["created_at"][:19]} · {e["payload"]}')
    st.markdown('#### How the agent works')
    st.code('Student input → action selection → bounded read-only tool → cited evidence / plan → saved state → reflection',language='text')
    st.write('Tool errors produce a blocked result without invented facts. Groq can choose an allowed action; no model can submit applications or change official requirements.')
