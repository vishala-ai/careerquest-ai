"""Real SQLite/API portfolio snapshots, explicit undecided choices and saved PDFs."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from owned_client import TestClient
from pypdf import PdfReader
from careerquest import api, career_worlds
from careerquest.store import connect


class PortfolioFlowTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.path=str(Path(temp.name)/'fictional.sqlite3')
        db=patch.object(api,'DB',self.path);db.start();self.addCleanup(db.stop)
        env=patch.dict(os.environ,{'CAREERQUEST_CAREER_GROQ':'0','CAREERQUEST_DEV_TOOLS':'0','GROQ_API_KEY':''});env.start();self.addCleanup(env.stop)
        self.c=TestClient(api.app);self.addCleanup(self.c.close)
        self.pid=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Cedar Fictional','grade':10}).json()['profile']['id'];self.base='/api/profiles/'+self.pid
        for i,q in enumerate(api.QUESTS):self.c.post(self.base+f'/quests/{i}',json={'option':next(iter(q['options']))})
        self.c.post(self.base+'/confirm',json={'interests':['technology','art'],'learning_style':'Hands-on projects','goal':'Try a mini-project'})
        self.events=self.c.get(self.base).json()['events']
    def overview(self):return self.c.get(self.base+'/career-discovery').json()
    def save(self,wid='software'):
        result=self.c.post(self.base+f'/worlds/{wid}/explore',json={}).json();eid=result['exploration_ids'][wid]
        self.assertEqual(self.c.post(self.base+'/career-shortlist',json={'exploration_id':eid}).status_code,200)
        return eid
    def choose(self,primary='software',secondary=None,undecided=False,reasons=None):
        data=self.overview();latest=data['path_preferences']['latest']
        return self.c.post(self.base+'/career-paths',json={'primary_world_id':None if undecided else primary,'secondary_world_id':secondary,'undecided':undecided,'student_reasons':reasons or {},'expected_profile_version':data['profile_context']['profile_version'],'expected_path_version':latest['version'] if latest else 0})
    def preview(self):
        response=self.c.get(self.base+'/career-portfolio/preview');self.assertEqual(response.status_code,200);return response.json()
    def complete(self,signature=None):return self.c.post(self.base+'/career-portfolio/complete',json={'expected_signature':signature or self.preview()['signature']})
    def pdf(self,saved):return self.c.get(self.base+'/career-portfolio/versions/'+saved['id']+'/pdf')
    def text(self,response):return ' '.join(' '.join(page.extract_text() for page in PdfReader(io.BytesIO(response.content)).pages).split())
    def assert_rewards_unchanged(self):
        state=self.c.get(self.base).json();self.assertEqual(state['profile']['xp'],70);self.assertEqual(state['events'],self.events)
    def test_shortlist_alone_does_not_invent_path_preferences_or_unlock_portfolio(self):
        self.save();data=self.overview();self.assertIsNone(data['path_preferences']['active']);self.assertEqual(data['next_action']['kind'],'choose_paths')
        self.assertEqual(self.c.get(self.base+'/career-portfolio/entry').status_code,409);self.assertEqual(self.c.get(self.base+'/career-portfolio/preview').status_code,409)
        self.assertFalse(self.c.get(self.base+'/career-discovery-milestone').json()['eligible'])
    def test_one_path_preview_assembles_confirmed_snapshot_and_grounded_details_read_only(self):
        eid=self.save();self.assertEqual(self.choose(reasons={'software':'I want to try making a tiny game.'}).status_code,200)
        before=self.overview()['portfolio_completion']['history'];preview=self.preview();doc=preview['snapshot']
        self.assertEqual(doc['student'],{'id':self.pid,'nickname':'Cedar Fictional','grade':10});self.assertEqual(doc['explorer']['interests'],['technology','art'])
        self.assertEqual(doc['paths'][0]['world_id'],'software');self.assertFalse(doc['undecided']);career=doc['shortlist'][0]
        self.assertEqual(career['exploration_id'],eid);self.assertEqual(career['student_reason'],'I want to try making a tiny game.')
        self.assertTrue(career['world']['skills']);self.assertTrue(career['sources']);self.assertTrue(doc['story']['summary']);self.assertTrue(doc['optional_mission']);self.assertTrue(doc['evidence_references'])
        self.assertEqual(self.overview()['portfolio_completion']['history'],before);self.assert_rewards_unchanged()
    def test_two_priorities_and_reasons_are_saved_separately_before_portfolio(self):
        self.save();self.save('design');response=self.choose('design','software',reasons={'design':'I enjoy sketching screens.'})
        self.assertEqual(response.status_code,200);paths=response.json()['active'];self.assertEqual([p['world_id'] for p in paths['paths']],['design','software'])
        self.assertEqual(self.overview()['portfolio_completion']['history'],[]);self.assertEqual(len(self.preview()['snapshot']['shortlist']),2)
    def test_explicit_undecided_is_a_complete_preference_without_assigned_paths(self):
        self.save();response=self.choose(undecided=True);self.assertEqual(response.status_code,200);self.assertTrue(response.json()['active']['undecided'])
        doc=self.preview()['snapshot'];self.assertTrue(doc['undecided']);self.assertEqual(doc['paths'],[])
        saved=self.complete().json()['active'];self.assertTrue(saved['snapshot']['undecided']);self.assertEqual(saved['snapshot']['paths'],[])
        with connect(self.path) as c:self.assertEqual(c.execute("SELECT count(*) FROM career_milestones WHERE kind IN ('primary_path','secondary_path')").fetchone()[0],0)
        self.assert_rewards_unchanged()
    def test_undecided_does_not_bypass_shortlist_or_allow_contradictory_priorities(self):
        self.assertEqual(self.choose(undecided=True).status_code,409)
        body={'undecided':True,'primary_world_id':'software','expected_profile_version':1,'expected_path_version':0}
        self.assertEqual(self.c.post(self.base+'/career-paths',json=body).status_code,422)
        body['primary_world_id']=None;body['undecided']=False;self.assertEqual(self.c.post(self.base+'/career-paths',json=body).status_code,422)
    def test_reasons_only_accept_saved_careers_and_bounded_text(self):
        self.save();self.assertEqual(self.choose(reasons={'fake':'A fabricated selection'}).status_code,409)
        self.assertEqual(self.choose(reasons={'software':'x'*241}).status_code,422)
        self.assertEqual(self.overview()['path_preferences']['history'],[])
    def test_confirmation_freezes_server_preview_and_retries_are_idempotent(self):
        self.save();self.choose();preview=self.preview();response=self.complete(preview['signature']);self.assertEqual(response.status_code,200)
        saved=response.json()['active'];self.assertEqual(saved['snapshot'],preview['snapshot']);self.assertEqual(saved['version'],1)
        self.assertEqual(self.complete(preview['signature']).json(),response.json());self.assert_rewards_unchanged()
    def test_stale_profile_blocks_confirmation_without_overwriting_saved_version(self):
        self.save();self.choose();old=self.complete().json()['active'];signature=self.preview()['signature']
        self.c.post(self.base+'/draft',json={'interests':['nature'],'start_edit':True})
        self.assertEqual(self.complete(signature).status_code,409);self.assertEqual(self.c.get(self.base+'/career-portfolio/preview').status_code,409)
        self.assertEqual(self.c.get(self.base+'/career-portfolio/versions/'+old['id']).json()['snapshot'],old['snapshot'])
    def test_new_shortlist_creates_new_preview_preserving_original_snapshot(self):
        self.save();self.choose();old=self.complete().json()['active'];self.save('design');new=self.preview()
        self.assertNotEqual(new['signature'],old['signature']);self.assertEqual(len(new['snapshot']['shortlist']),2)
        self.assertEqual(self.complete(old['signature']).status_code,409)
        history=self.complete(new['signature']).json()['history'];self.assertEqual(len(history),2);self.assertEqual(history[0]['snapshot'],old['snapshot'])
    def test_researched_career_reselection_invalidates_its_old_priority_reference(self):
        self.save();self.choose();old=self.preview()['signature'];self.save()
        self.assertIsNone(self.overview()['path_preferences']['active']);self.assertEqual(self.complete(old).status_code,409)
        self.assertEqual(self.choose().status_code,200);self.assertNotEqual(self.preview()['signature'],old)
    def test_changed_priorities_create_versioned_draft_not_an_edited_final(self):
        self.save();self.save('design');self.choose('software','design');old=self.complete().json()['active']
        self.choose('design','software');data=self.overview()['portfolio_completion'];self.assertIsNone(data['active']);self.assertEqual(len(data['history']),1)
        self.assertEqual(data['history'][0]['snapshot'],old['snapshot']);self.assertEqual(data['preview']['paths'][0]['world_id'],'design')
        self.complete();self.assert_rewards_unchanged()
    def test_changed_reason_rejects_previous_preview_signature(self):
        self.save();self.choose();signature=self.preview()['signature'];self.choose(reasons={'software':'I would like to make games.'})
        self.assertEqual(self.complete(signature).status_code,409);self.assertEqual(self.overview()['portfolio_completion']['history'],[])
    def test_pdf_matches_saved_version_after_profile_and_current_choices_change(self):
        self.save();self.choose(reasons={'software':'I want to build a fictional game.'});saved=self.complete().json()['active']
        initial=self.pdf(saved);self.assertEqual(initial.status_code,200);text=self.text(initial)
        for value in ['Cedar Fictional','Grade 10','technology, art','Software Development','I want to build a fictional game.','Programming','https://www.bls.gov','Saved version 1']:
            self.assertIn(value,text)
        self.assertIn(' '.join(saved['snapshot']['story']['summary'].split()),text)
        self.save('design');self.choose('design');self.complete()
        self.c.post(self.base+'/draft',json={'interests':['nature'],'start_edit':True})
        with connect(self.path) as c:c.execute('UPDATE profiles SET alias=? WHERE id=?',('Different Fictional Alias',self.pid))
        again=self.pdf(saved);self.assertEqual(self.text(again),text);self.assertNotIn('Different Fictional Alias',self.text(again));self.assertNotIn('Digital Product Design',self.text(again))
        self.assertEqual(again.headers['content-type'],'application/pdf');self.assertIn('v1.pdf',again.headers['content-disposition'])
    def test_pdf_and_saved_version_are_owned_by_the_requested_explorer(self):
        self.save();self.choose();saved=self.complete().json()['active'];other=self.c.post('/api/profiles',json={'fictional_ack':True,'alias':'Other Fictional','grade':9}).json()['profile']['id']
        for suffix in ['', '/pdf']:
            self.assertEqual(self.c.get(f'/api/profiles/{other}/career-portfolio/versions/{saved["id"]}'+suffix).status_code,404)
            self.assertEqual(self.c.get(self.base+'/career-portfolio/versions/unknown'+suffix).status_code,404)
    def test_snapshot_and_preferences_survive_a_fresh_python_process(self):
        self.save();self.choose(undecided=True);saved=self.complete().json()['active']
        code='import json,sys;from careerquest.store import connect;from careerquest.career_worlds import saved_portfolio;print(json.dumps(saved_portfolio(connect(sys.argv[1]),sys.argv[2],sys.argv[3])))'
        result=subprocess.run([sys.executable,'-c',code,self.path,self.pid,saved['id']],check=True,capture_output=True,text=True)
        self.assertEqual(json.loads(result.stdout)['snapshot'],saved['snapshot'])
        with TestClient(api.app) as client:self.assertTrue(client.get(self.base+'/career-discovery').json()['path_preferences']['active']['undecided'])
    def test_legacy_snapshot_is_exported_honestly_without_current_profile_enrichment(self):
        self.save();self.choose();saved=self.complete().json()['active'];doc=saved['snapshot']
        legacy={'paths':doc['paths'],'shortlist':[{key:item[key] for key in ['selection_id','exploration_id','world_id','career_name','sources']} for item in doc['shortlist']]}
        with connect(self.path) as c:c.execute('UPDATE career_portfolio_completions SET content=? WHERE id=?',(json.dumps(legacy),saved['id']))
        pdf=self.pdf(saved);text=self.text(pdf);self.assertIn('Earlier saved version',text);self.assertIn('Software Development',text);self.assertNotIn('Cedar Fictional',text)
        self.assertEqual(self.c.get(self.base+'/career-portfolio/versions/'+saved['id']).json()['snapshot'],legacy)
    def test_catalogue_outage_blocks_new_confirmation_but_saved_pdf_remains_available(self):
        self.save();self.choose();saved=self.complete().json()['active']
        with patch('careerquest.career_worlds.approved',return_value={}):
            self.assertEqual(self.complete(saved['signature']).status_code,409);self.assertEqual(self.pdf(saved).status_code,200)
    def test_untrusted_reason_text_is_literal_in_pdf_not_pdf_markup(self):
        self.save();self.choose(reasons={'software':'<b>Fictional game</b> & curious <script>text</script>'});saved=self.complete().json()['active']
        self.assertIn('<b>Fictional game</b> & curious <script>text</script>',self.text(self.pdf(saved)))
    def test_pdf_preserves_unicode_nickname_without_lossy_ascii_replacement(self):
        with connect(self.path) as c:c.execute('UPDATE profiles SET alias=? WHERE id=?',('Nova Δ Fictional',self.pid))
        self.save();self.choose();saved=self.complete().json()['active']
        self.assertIn('Nova Δ Fictional',self.text(self.pdf(saved)))
    def test_replit_source_package_includes_pdf_fonts_license_and_research_catalogue(self):
        from scripts.package_replit import source_files
        names={name for _,name in source_files()}
        for name in ['careerquest/assets/fonts/NotoSans-Regular.ttf','careerquest/assets/fonts/NotoSans-Bold.ttf','careerquest/assets/fonts/LICENSE','data/career_world_details.json']:
            self.assertIn(name,names)
        self.assertNotIn('.env',names)
    def test_saved_portfolio_celebration_scope_does_not_consume_other_queued_milestones(self):
        self.save();self.choose();self.complete()
        result=self.c.post(self.base+'/career-celebrations/claim?kind=portfolio_completed').json()
        self.assertEqual(result['celebration']['kind'],'portfolio_completed')
        self.assertIsNone(self.c.post(self.base+'/career-celebrations/claim?kind=portfolio_completed').json()['celebration'])
        self.assertEqual(self.c.post(self.base+'/career-celebrations/claim').json()['celebration']['kind'],'first_research')
        self.assertEqual(self.c.post(self.base+'/career-celebrations/claim?kind=fake').status_code,422)
        self.assert_rewards_unchanged()

if __name__=='__main__':unittest.main()
