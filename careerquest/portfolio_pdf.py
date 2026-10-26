"""PDF derived only from a chosen immutable portfolio document. No live joins."""
from io import BytesIO
from html import escape
from urllib.parse import urlparse
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR=Path(__file__).parent/'assets'/'fonts'
pdfmetrics.registerFont(TTFont('QuestSans',str(FONT_DIR/'NotoSans-Regular.ttf')))
pdfmetrics.registerFont(TTFont('QuestSans-Bold',str(FONT_DIR/'NotoSans-Bold.ttf')))


def ordered_careers(snapshot):
    """Present saved priorities first without mutating the immutable snapshot."""
    ranks = {} if snapshot.get('undecided') else {
        path['world_id']: {'primary': 0, 'secondary': 1}.get(path.get('priority'), 2)
        for path in snapshot.get('paths', [])
    }
    return sorted(snapshot.get('shortlist', []), key=lambda career: ranks.get(career['world_id'], 2))


def render_portfolio(saved):
    data=saved['snapshot'];careers=ordered_careers(data);buffer=BytesIO();styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='QuestTitle',fontName='QuestSans-Bold',fontSize=25,leading=31,textColor=colors.HexColor('#07573f'),spaceAfter=14))
    styles.add(ParagraphStyle(name='QuestSection',fontName='QuestSans-Bold',fontSize=16,leading=22,textColor=colors.HexColor('#07573f'),spaceBefore=17,spaceAfter=8,keepWithNext=True))
    styles.add(ParagraphStyle(name='QuestText',fontName='QuestSans',fontSize=11,leading=17,spaceAfter=8))
    styles.add(ParagraphStyle(name='QuestNote',fontName='QuestSans',fontSize=9,leading=13,textColor=colors.HexColor('#465c55'),spaceAfter=6))
    styles.add(ParagraphStyle(name='QuestNode',parent=styles['QuestText'],alignment=TA_CENTER,textColor=colors.HexColor('#07573f')))
    def text(value):
        return escape(str(value).replace('—','-').replace('–','-').replace('’',"'").replace('→','to'))
    def p(value,style='QuestText'):return Paragraph(text(value),styles[style])
    story=[p('CareerQuest AI','QuestNote'),p('My Career Discovery Portfolio','QuestTitle'),p(f"Saved version {saved['version']} | {saved['created_at'][:10]}",'QuestNote')]
    student=data.get('student');explorer=data.get('explorer',{})
    if student:
        story += [p(f"{student['nickname']} | Grade {student['grade']}",'QuestSection'),p('Explorer Snapshot','QuestSection'),p('Interests: '+(', '.join(explorer.get('interests',[])) or 'Keeping options open')),p('Preferred activities: '+explorer.get('learning_style','')),p('Exploration goal: '+explorer.get('goal',''))]
    else:story.append(p('Earlier saved version: an Explorer Snapshot and Discovery Story were not captured in this historical record. Its original saved careers, paths and sources are preserved.','QuestNote'))
    if data.get('story'):
        story += [p('My Discovery Story','QuestSection'),p(data['story']['summary']),p('Saved confirmed story' if data['story'].get('status')=='groq' else 'Saved summary; deterministic fallback content is not live AI output.','QuestNote')]
    story.append(p('My branching adventure map','QuestSection'))
    names={path['world_id']:path['priority'].title() for path in data.get('paths',[])}
    nodes=[]
    for career in careers:
        label='Still exploring' if data.get('undecided') else names.get(career['world_id'],'Also exploring')
        nodes.append([p(label+'\n'+career['career_name'],'QuestNode')])
    if nodes:
        root=Table([[p('My confirmed interests and curiosity','QuestNode')]],colWidths=[480])
        root.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e5f4ed')),('BOX',(0,0),(-1,-1),1,colors.HexColor('#70a88f')),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        branches=Table([[cell[0] for cell in nodes]],colWidths=[480/len(nodes)]*len(nodes))
        branches.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f2f7fc')),('BOX',(0,0),(-1,-1),1,colors.HexColor('#bed4cd')),('INNERGRID',(0,0),(-1,-1),1,colors.HexColor('#bed4cd')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        story.append(KeepTogether([root,p('Branches of possibility','QuestNote'),branches]))
    for career in careers:
        world=career.get('world',{});story += [p(career['career_name'],'QuestSection')]
        label='I am still exploring' if data.get('undecided') else names.get(career['world_id'],'Another saved possibility')
        story.append(p(label))
        if world.get('overview'):story.append(p(world['overview']['text']))
        if world.get('skills'):story.append(p('Skills to explore: '+', '.join(item['text'] for item in world['skills'])))
        story.append(p('My reason: '+career['student_reason']) if career.get('student_reason') else p('You explicitly saved this career. No personal reason was added.','QuestNote'))
        source_lines=[p('Supporting sources','QuestNote')]
        for source in career.get('sources',[]):
            url=source.get('url','');label=source.get('source','')+' - '+source.get('title','')
            source_lines.append(p(label,'QuestNote'))
            if urlparse(url).scheme=='https':
                source_lines.append(Paragraph(f'<link href="{escape(url,quote=True)}" color="#225d9b">{text(url)}</link>',styles['QuestNote']))
            source_lines.append(p('Curated source notes. Not live verified.','QuestNote'))
        story.append(KeepTogether(source_lines))
    if data.get('optional_mission'):
        story += [p('Optional mini-mission','QuestSection'),p(data['optional_mission']['text']),p('A CareerQuest demo activity, not a job requirement.','QuestNote')]
    story += [Spacer(1,14),p('This is a map of possibilities, not a permanent decision. You can change direction anytime.','QuestText')]
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('QuestSans',8);canvas.setFillColor(colors.HexColor('#465c55'))
        canvas.drawString(54,30,f"CareerQuest AI | Educational demo | Saved portfolio version {saved['version']}")
        canvas.drawRightString(558,30,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(buffer,pagesize=(612,792),rightMargin=54,leftMargin=54,topMargin=44,bottomMargin=52,title=f"CareerQuest Portfolio v{saved['version']}",author='CareerQuest AI',pageCompression=0)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return buffer.getvalue()
