"""Portfolio presentation/PDF ordering never rewrites saved student snapshots."""
import io,json,unittest
from pypdf import PdfReader
from careerquest.portfolio_pdf import ordered_careers,render_portfolio

class PortfolioOrderTests(unittest.TestCase):
    def snapshot(self):
        return {'shortlist':[{'world_id':wid,'career_name':title,'sources':[]} for wid,title in [('environment','Environmental Science'),('design','Digital Product Design'),('software','Software Development'),('bioengineering','Biomedical Engineering')]],'paths':[{'world_id':'design','priority':'secondary'},{'world_id':'software','priority':'primary'}],'undecided':False}
    def test_primary_secondary_then_stable_other_order_without_mutation(self):
        snapshot=self.snapshot();before=json.dumps(snapshot,sort_keys=True)
        self.assertEqual([c['world_id'] for c in ordered_careers(snapshot)],['software','design','environment','bioengineering'])
        self.assertEqual(json.dumps(snapshot,sort_keys=True),before)
    def test_primary_only_no_paths_and_undecided(self):
        snapshot=self.snapshot();snapshot['paths']=[{'world_id':'software','priority':'primary'}]
        self.assertEqual([c['world_id'] for c in ordered_careers(snapshot)],['software','environment','design','bioengineering'])
        for change in [{'paths':[]},{'undecided':True}]:
            with self.subTest(change=change):self.assertEqual([c['world_id'] for c in ordered_careers(snapshot|change)],['environment','design','software','bioengineering'])
        self.assertEqual(ordered_careers({}),[])
    def test_pdf_map_and_career_notes_share_the_saved_priority_order(self):
        snapshot=self.snapshot();before=json.dumps(snapshot,sort_keys=True)
        result=render_portfolio({'snapshot':snapshot,'version':4,'created_at':'2026-10-25T12:00:00'})
        reader=PdfReader(io.BytesIO(result));texts=[];headings=[];names={c['career_name'] for c in snapshot['shortlist']}
        def visit(text,cm,tm,font,size):
            if size==16 and text.strip() in names:headings.append(text.strip())
        for page in reader.pages:texts.append(page.extract_text(visitor_text=visit))
        text=' '.join(texts);expected=['Software Development','Digital Product Design','Environmental Science','Biomedical Engineering']
        self.assertEqual(headings,expected)
        positions=[text.index(name) for name in expected];self.assertEqual(positions,sorted(positions))
        self.assertEqual(json.dumps(snapshot,sort_keys=True),before)
    def test_pdf_undecided_keeps_original_order_and_never_assigns_a_path(self):
        snapshot=self.snapshot()|{'undecided':True}
        result=render_portfolio({'snapshot':snapshot,'version':1,'created_at':'2026-10-25T12:00:00'})
        text=' '.join(page.extract_text() for page in PdfReader(io.BytesIO(result)).pages)
        expected=[c['career_name'] for c in snapshot['shortlist']];positions=[text.index(name) for name in expected]
        self.assertEqual(positions,sorted(positions));self.assertNotIn('Primary',text);self.assertNotIn('Secondary',text)
