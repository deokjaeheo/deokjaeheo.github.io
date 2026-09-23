"""Check completeness, grouping, and unpublished-file isolation."""
import unittest
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
from render_publications import ROOT, read, render

class PublicationsTest(unittest.TestCase):
    def setUp(self):
        self.data=read('publications-data.json')
        self.html=render(self.data,(ROOT/'publications.html').read_text(encoding='utf-8'))
        self.soup=BeautifulSoup(self.html,'html.parser')
    def test_published_records_preserved_and_sorted(self):
        ids=[p['id'] for p in self.data['publications']]
        self.assertEqual(len(ids),len(set(ids)))
        shown=[p['data-record-id'] for p in self.soup.select('#sci .paper, #other .paper')]
        self.assertCountEqual(ids,shown)
        for group in ('sci','other'):
            expected=sorted([p for p in self.data['publications'] if p['category']==group],key=lambda p:p['sort_date'],reverse=True)
            self.assertEqual([p['id'] for p in expected],[p['data-record-id'] for p in self.soup.select(f'#{group} .paper')])
    def test_submitted_records_have_no_file_links(self):
        records=self.soup.select('#submitted .submitted-paper')
        self.assertEqual(len(records),len(read('submitted-data.json')['manuscripts']))
        for record in records: self.assertFalse(record.select('a,iframe,img,object,embed'))
        for p in read('submitted-data.json')['manuscripts']:
            self.assertEqual(set(p),{'id','title','authors_html','status'})
        one=self.soup.select_one('[data-record-id="onesnap"] .authors')
        self.assertEqual([p.text for p in one.select('sup')],['†','†','*'])
        self.assertIn('Hyungsoon Im<sup>*</sup>',str(one))
        self.assertNotIn('Jinkee Hong<sup>*</sup>',str(one))
    def test_patents_complete_and_sorted(self):
        patents=read('patents-data.json')['patents']
        self.assertEqual(len(patents),len(self.soup.select('.patent-entry')))
        for p in patents:
            self.assertNotRegex(p['title'],r'^\d+[).]\s')
            self.assertNotIn('\n',p['title'])
            for number in ([p['number']] if 'number' in p else p['numbers']): self.assertIn(number,self.soup.get_text())
        for category in ('granted','application'):
            dates=[p['date'] for p in sorted([p for p in patents if p['category']==category],key=lambda p:p['date'],reverse=True)]
            target='#granted' if category=='granted' else '#applications'
            self.assertEqual(dates,[p.text.split(' · ')[1].replace('.','-') for p in self.soup.select(target+' .journal')])
    def test_recent_submissions_precede_published_groups(self):
        self.assertEqual([p['id'] for p in self.soup.select('#papers > .publication-group')],['submitted','sci','other'])
        self.assertEqual([p['href'] for p in self.soup.select('#papers .publication-jumps a')],['#submitted','#sci','#other'])
    def test_render_is_repeatable(self):
        self.assertEqual(self.html,render(self.data,self.html))
    def test_covers_match_published_papers(self):
        covers=read('covers-data.json')['covers']
        self.assertEqual(len(covers),3)
        self.assertEqual(len(self.soup.select('.cover-card')),3)
        ids={p['id'] for p in self.data['publications']}
        for p in covers:
            self.assertIn(p['doi'],ids)
            self.assertTrue((ROOT/p['image']).is_file())
    def test_private_documents_not_linked(self):
        for page in ROOT.glob('*.html'):
            soup=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser')
            for tag in soup.select('[href],[src]'):
                url=tag.get('href',tag.get('src','')).lower()
                self.assertFalse('onesnap' in url or '.docx' in url or 'file:' in url or 'dropbox' in url,(page.name,url))
    def test_site_structure_and_local_links(self):
        for page in ROOT.glob('*.html'):
            soup=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser')
            ids=[node['id'] for node in soup.select('[id]')]
            self.assertEqual(len(ids),len(set(ids)),page.name)
            self.assertEqual(len(soup.select('h1')),1,page.name)
            self.assertFalse(soup.select('img:not([alt])'),page.name)
            self.assertNotIn('\ufffd',soup.get_text(),page.name)
            for node in soup.select('[href], [src]'):
                url=urlsplit(node.get('href',node.get('src','')))
                if url.scheme or url.netloc: continue
                target=ROOT/unquote(url.path) if url.path else page
                self.assertTrue(target.is_file(),(page.name,str(target)))
                if url.fragment and target.suffix=='.html':
                    target_soup=soup if target==page else BeautifulSoup(target.read_text(encoding='utf-8'),'html.parser')
                    self.assertIsNotNone(target_soup.find(id=unquote(url.fragment)),(page.name,url.geturl()))

if __name__=='__main__': unittest.main()
