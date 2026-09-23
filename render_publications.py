"""Render curated public metadata only. No network access or manuscript files."""
from pathlib import Path
from html import escape
from urllib.parse import urlsplit
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def authors(value):
    soup = BeautifulSoup(value, 'html.parser')
    for tag in soup.find_all(True):
        if tag.name not in ('strong','sup') or tag.attrs:
            raise ValueError('Author markup must contain only strong/sup without attributes')
    return str(soup)
def heading(id, title, korean, count):
    return f'<section class="publication-group" id="{id}"><div class="publication-group-heading"><h2>{escape(title)}<span lang="ko">{escape(korean)}</span></h2><span class="record-count">{count:02d}</span></div>'
def cover_gallery():
    parts=['<section class="journal-covers" aria-labelledby="covers-heading"><h2 id="covers-heading">Journal covers<span lang="ko">학술지 표지 선정</span></h2><div class="cover-grid">']
    for cover in read('covers-data.json')['covers']:
        title=escape(cover['title']); image=escape(cover['image'],quote=True)
        parts.append(f'<figure class="cover-card"><a class="cover-image-link" href="{image}" target="_blank" rel="noopener noreferrer" aria-label="{escape(cover["journal"])} {cover["issue"]} {cover["kind"]} 전체 이미지"><img src="{image}" width="761" height="1000" alt="{escape(cover["journal"])} · {cover["issue"]} · {cover["kind"]}"/></a><figcaption><p class="cover-kind">{cover["kind"]} · {cover["issue"]}</p><h3>{escape(cover["journal"])}</h3><a class="cover-paper-title" href="https://doi.org/{cover["doi"]}" target="_blank" rel="noopener noreferrer">{title} <span aria-hidden="true">↗</span></a></figcaption></figure>')
    return ''.join(parts)+'</div></section>'
def paper(p, i, submitted=False):
    title=escape(p['title'])
    meta='Submitted · 투고 완료' if submitted else escape(p['journal'])
    if not submitted:
        if urlsplit(p['url']).scheme!='https': raise ValueError('Published paper requires HTTPS URL')
        url=escape(p['url'],quote=True)
        title=f'<a href="{url}" rel="noopener noreferrer" target="_blank">{title}</a>'
        arrow=f'<a class="paper-link" href="{url}" rel="noopener noreferrer" target="_blank" aria-label="{escape(p["title"],quote=True)} 논문 보기">↗</a>'
    else: arrow=''
    cls='paper submitted-paper' if submitted else 'paper'
    return f'<article class="{cls}" data-record-id="{escape(p["id"],quote=True)}"><div class="paper-index">{i:02d}</div><div><p class="journal">{meta}</p><h3>{title}</h3><p class="authors">{authors(p["authors_html"])}</p></div>{arrow}</article>'
def render(data, html):
    records=data['publications']
    if any(p.get('category') not in ('sci','other') for p in records):
        raise ValueError('Every paper must have a reviewed SCI(E)/other classification')
    submitted=read('submitted-data.json')['manuscripts']
    patents=read('patents-data.json')['patents']
    sci=[p for p in records if p['category']=='sci']; other=[p for p in records if p['category']=='other']
    sections=['<p class="section-label">05 / PUBLICATIONS</p><h1 class="page-heading">Publications<span class="ko-translation" lang="ko">논문 및 특허</span></h1>',cover_gallery(),
      '<nav class="publication-tabs" aria-label="Publication type"><a id="tab-papers" href="#papers">Papers <span>논문</span></a><a id="tab-patents" href="#patents">Patents <span>특허</span></a></nav>',
      '<div class="publication-panel" id="papers"><nav class="publication-jumps" aria-label="Paper categories">',
      f'<a href="#sci">SCI(E) · {len(sci)}</a><a href="#other">Other journals · {len(other)}</a><a href="#submitted">Submitted · {len(submitted)}</a></nav>',
      f'<p class="list-note">{len(records)} published papers · {len(submitted)} submitted manuscripts<br/><sup>†</sup> First / co-first author · <sup>*</sup> Corresponding author</p>']
    for id,title,korean,group in [('sci','SCI(E) journals','SCI·SCIE 학술지',sci),('other','Other journals','SCI(E) 외 학술지 · ESCI, Scopus, KCI 등',other)]:
        sections.append(heading(id,title,korean,len(group)))
        for i,p in enumerate(sorted(group,key=lambda p:p['sort_date'],reverse=True),1): sections.append(paper(p,i))
        sections.append('</section>')
    sections.append(heading('submitted','Submitted manuscripts','투고 논문',len(submitted)))
    for i,p in enumerate(submitted,1): sections.append(paper(p,i,True))
    sections.append('</section></div><div class="publication-panel" id="patents">')
    sections.append('<nav class="publication-jumps" aria-label="Patent categories"><a href="#granted">Korean grants · 12</a><a href="#applications">Korean applications · 2</a><a href="#international">International applications</a></nav>')
    sections.append('<p class="list-note">Granted patents and applications · Republic of Korea, United States &amp; Europe<span class="ko-translation" lang="ko">국내 등록·출원 및 미국·유럽 출원</span></p>')
    for category,id,title,korean in [('granted','granted','Granted patents · Korea','국내 등록특허'),('application','applications','Patent applications · Korea','국내 출원특허'),('international','international','International patent applications','해외 출원특허')]:
        group=sorted([p for p in patents if p['category']==category],key=lambda p:p.get('date',''),reverse=True)
        sections.append(heading(id,title,korean,len(group)))
        for i,p in enumerate(group,1):
            number=p.get('number') or ' · '.join(p['numbers'])
            date=(' · '+p['date'].replace('-','.')) if p.get('date') else ''
            names=escape(p['inventors']).replace('Deokjae Heo','<strong>Deokjae Heo</strong>')
            names_ko=escape(p['inventors_ko']).replace('허덕재','<strong>허덕재</strong>')
            sections.append(f'<article class="patent-entry"><div class="paper-index">{i:02d}</div><div><p class="journal">{escape(number+date)}</p><h3>{escape(p["title"])}<span class="ko-translation" lang="ko">{escape(p["title_ko"])}</span></h3><p class="authors">{names}<span class="patent-inventors-ko" lang="ko">{names_ko}</span></p></div></article>')
        sections.append('</section>')
    sections.append('</div>')
    soup=BeautifulSoup(html,'html.parser')
    container=soup.select_one('main .publications'); container.clear()
    container.append(BeautifulSoup(''.join(sections),'html.parser'))
    if not soup.select_one('script[src="publications.js"]'):
        soup.body.append(soup.new_tag('script',src='publications.js',defer=''))
    return str(soup)+'\n'
def main():
    path=ROOT/'publications.html'
    path.write_text(render(read('publications-data.json'),path.read_text(encoding='utf-8')),encoding='utf-8')
if __name__=='__main__': main()
