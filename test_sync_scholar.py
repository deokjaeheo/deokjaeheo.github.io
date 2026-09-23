import unittest
from sync_scholar import reconcile, robots_allows, parse_profile, render, PROFILE_URL

class SyncSafetyTests(unittest.TestCase):
    def fixture(self):
        row={'title':'Known paper','journal':'Journal 1, 10','authors':'D Heo, S Lee','year':2026}
        paper={'id':'10.1/known','title':'Known paper','journal':'Journal 1, 10 (2026.09)',
               'authors_html':'<strong>Deokjae Heo</strong><sup>†</sup>, Sangmin Lee<sup>*</sup>',
               'url':'https://doi.org/10.1/known','year':2026,'sort_date':'2026-09-01'}
        return {'publications':[paper]}, {'articles':{'id':{'record_id':'10.1/known','snapshot':row}},'review':{}}, row

    def test_unchanged_profile_preserves_curated_metadata_and_roles(self):
        data,state,row=self.fixture()
        result,_,changes=reconcile(data,state,{'id':row})
        self.assertEqual(result,data);self.assertEqual(changes,[])

    def test_missing_profile_row_never_deletes_publication(self):
        data,state,_=self.fixture()
        result,_,_=reconcile(data,state,{})
        self.assertEqual(result,data)

    def test_changed_authors_require_review_and_preserve_role_markers(self):
        data,state,row=self.fixture(); changed={**row,'authors':'D Heo, New Author, S Lee'}
        result,next_state,_=reconcile(data,state,{'id':changed})
        self.assertEqual(result,data);self.assertIn('id',next_state['review'])

    def test_changed_year_updates_order_but_not_roles(self):
        data,state,row=self.fixture()
        result,_,_=reconcile(data,state,{'id':{**row,'year':2027}})
        self.assertEqual(result['publications'][0]['sort_date'],'2027-01-01')
        self.assertEqual(result['publications'][0]['journal'],'Journal 1, 10 (2027)')
        self.assertEqual(result['publications'][0]['authors_html'],data['publications'][0]['authors_html'])

    def test_unresolved_new_paper_stays_in_review(self):
        data,state,row=self.fixture()
        result,next_state,_=reconcile(data,state,{'new':{**row,'title':'Uncertain new paper'}},resolver=lambda _:None)
        self.assertEqual(result,data);self.assertIn('new',next_state['review'])

    def test_updated_venue_keeps_display_year(self):
        data,state,row=self.fixture()
        result,_,_=reconcile(data,state,{'id':{**row,'journal':'New Journal 2, 11'}})
        self.assertEqual(result['publications'][0]['journal'],'New Journal 2, 11 (2026)')

    def test_verified_new_paper_is_added_without_inventing_roles(self):
        data,state,row=self.fixture()
        candidate={**data['publications'][0],'id':'10.1/new','authors_html':'<strong>Deokjae Heo</strong>, New Author'}
        result,next_state,_=reconcile(data,state,{'new':row},resolver=lambda _:candidate)
        self.assertEqual(len(result['publications']),2)
        self.assertNotIn('<sup>',result['publications'][1]['authors_html'])
        self.assertIn('new',next_state['review'])

    def test_duplicate_doi_is_linked_without_duplicate_record(self):
        data,state,row=self.fixture()
        result,next_state,_=reconcile(data,state,{'new':row},resolver=lambda _:data['publications'][0])
        self.assertEqual(len(result['publications']),1)
        self.assertEqual(next_state['articles']['new']['record_id'],'10.1/known')

    def test_robots_longest_match_blocks_pagination_and_details(self):
        rules='User-agent: *\nDisallow: /citations?\nAllow: /citations?user=\nDisallow: /citations?*cstart=\n'
        self.assertTrue(robots_allows(rules,PROFILE_URL))
        self.assertFalse(robots_allows(rules,PROFILE_URL+'&cstart=100'))
        self.assertFalse(robots_allows(rules,'https://scholar.google.com/citations?view_op=view_citation'))

    def test_challenge_or_empty_profile_fails(self):
        with self.assertRaises(RuntimeError):parse_profile('<html>unusual traffic</html>')

    def test_network_failure_cannot_partially_mutate_input_data(self):
        data,state,row=self.fixture()
        def fail(_):raise RuntimeError('Access denied')
        with self.assertRaises(RuntimeError):reconcile(data,state,{'new':{**row,'title':'New'}},resolver=fail)
        self.assertEqual(len(data['publications']),1);self.assertNotIn('new',state['articles'])

    def test_remote_title_is_escaped_in_rendered_html(self):
        data,_,_=self.fixture();data['publications'][0]['title']='<img src=x onerror=alert(1)>'
        result=render(data,'<main><div><article class="paper"></article></div></main>')
        self.assertNotIn('<img src=x',result);self.assertIn('&lt;img',result)

if __name__=='__main__':unittest.main()
