"""Conservative, weekly public-profile sync. No login, proxies or CAPTCHA bypass.

Existing publications and author-role annotations are never removed. Only changes
observed since the saved Scholar snapshot update existing bibliographic fields.
New records require a matching Crossref DOI and an unambiguous Deokjae Heo author.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlsplit, parse_qs, quote
from html import escape
from difflib import SequenceMatcher
from datetime import datetime, timezone
import argparse
import json
import re
import unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
PROFILE = '-ATOsVMAAAAJ'
BASE = 'https://deokjaeheo.github.io/'
PROFILE_URL = 'https://scholar.google.com/citations?' + urlencode({'user': PROFILE, 'hl': 'en', 'pagesize': 100, 'sortby': 'pubdate'})
AGENT = 'SENDLabPublicationSync/1.0 (+https://deokjaeheo.github.io/)'

def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKC', value).casefold() if c.isalnum())

def fetch(url):
    request = Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html,application/json,text/plain'})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f'HTTP {response.status}: existing publications retained')
        return response.read().decode(response.headers.get_content_charset() or 'utf-8')

def robots_allows(robots, url):
    """Longest matching Allow/Disallow rule for Google's wildcard user-agent."""
    groups = []; agents = []; rules = []
    for raw in robots.splitlines() + ['User-agent: __end__']:
        line = raw.split('#', 1)[0].strip()
        if ':' not in line: continue
        key, value = [x.strip() for x in line.split(':', 1)]
        key = key.casefold()
        if key == 'user-agent':
            if rules:
                groups.append((agents, rules)); agents = []; rules = []
            agents.append(value.casefold())
        elif key in ('allow', 'disallow') and value:
            rules.append((key, value))
    wildcard = [r for a, rs in groups if '*' in a for r in rs]
    if not wildcard: raise RuntimeError('Could not interpret Scholar robots.txt')
    split = urlsplit(url); target = split.path + ('?' + split.query if split.query else '')
    matches = []
    for kind, pattern in wildcard:
        end = pattern.endswith('$'); raw = pattern[:-1] if end else pattern
        regex = '^' + re.escape(raw).replace(r'\*', '.*') + ('$' if end else '')
        if re.search(regex, target): matches.append((len(raw.replace('*','')), kind == 'allow'))
    return max(matches)[1] if matches else True

def parse_profile(html):
    s = BeautifulSoup(html, 'html.parser')
    profile = s.select_one('#gsc_prf_in')
    if not profile or norm(profile.get_text()) != norm('Deokjae Heo'):
        raise RuntimeError('Unexpected profile or access challenge: no files changed')
    rows = {}
    for node in s.select('.gsc_a_tr'):
        a = node.select_one('.gsc_a_at'); year = node.select_one('.gsc_a_y')
        gray = node.select('.gs_gray')
        if not a or len(gray) < 2 or not year: raise RuntimeError('Scholar layout changed')
        sid = parse_qs(urlsplit(a.get('href','')).query).get('citation_for_view',[''])[0]
        if not sid.startswith(PROFILE + ':'): raise RuntimeError('Unexpected Scholar article owner')
        ys = year.get_text(strip=True)
        rows[sid] = {'title':a.get_text(' ',strip=True), 'authors':gray[0].get_text(' ',strip=True),
                     'journal':gray[1].get_text(' ',strip=True), 'year':int(ys) if ys.isdigit() else None}
    if len(rows) < 20: raise RuntimeError('Incomplete Scholar response: no files changed')
    return rows

def is_cover(title):
    return bool(re.search(r'\b(front|back|inside)\s*cover\b|\(Adv\..*\d+/\d{4}\)\.?$', title, re.I))

def resolve_crossref(row):
    query = urlencode({'query.bibliographic':row['title'], 'rows':5})
    items = json.loads(fetch('https://api.crossref.org/works?' + query))['message']['items']
    candidates = []
    for item in items:
        title = BeautifulSoup(' '.join(item.get('title',[])), 'html.parser').get_text(' ',strip=True)
        ratio = SequenceMatcher(None,norm(title),norm(row['title'])).ratio()
        authors = item.get('author',[])
        identity = any(norm(a.get('given','')) == 'deokjae' and norm(a.get('family','')) == 'heo' for a in authors)
        years = [d.get('date-parts',[[None]])[0][0] for key,d in item.items() if key in ('published','published-print','published-online','issued')]
        if ratio >= .98 and identity and item.get('type') == 'journal-article' and item.get('DOI') and row['year'] in years:
            if all(a.get('family') and a.get('given') for a in authors): candidates.append((item,title))
    distinct = {i['DOI'].casefold():(i,t) for i,t in candidates}
    if len(distinct) != 1: return None
    item,title = next(iter(distinct.values()))
    date = item.get('published',item.get('issued',{})).get('date-parts',[[row['year']]])[0]
    date = (date + [1,1])[:3]
    parts = []
    for author in item['author']:
        name = author['given'] + ' ' + author['family']
        val = escape(name)
        if norm(name) == 'deokjaeheo': val = '<strong>' + val + '</strong>'
        parts.append(val)
    venue = ' '.join(item.get('container-title',[]))
    if item.get('volume'): venue += ' ' + item['volume']
    if item.get('issue'): venue += '(' + item['issue'] + ')'
    page = item.get('page') or item.get('article-number')
    if page: venue += ', ' + page
    venue += f" ({row['year']})"
    return {'id':item['DOI'].casefold(), 'title':title, 'journal':venue,
            'authors_html':', '.join(parts), 'url':'https://doi.org/' + item['DOI'],
            'year':row['year'], 'sort_date':'-'.join(str(x).zfill(2) for x in date),
            'author_roles_review_needed':True}

def reconcile(data, state, rows, resolver=resolve_crossref):
    import copy
    data = copy.deepcopy(data); state = copy.deepcopy(state)
    records = {x['id']:x for x in data['publications']}
    review = dict(state.get('review',{})); changes = []
    for sid,row in rows.items():
        previous = state['articles'].get(sid)
        if previous and previous.get('ignore'): continue
        rid = previous.get('record_id') if previous else None
        if rid in records:
            prior = previous['snapshot']; record = records[rid]
            if prior == row: continue
            # Keep precise curated fields until that same source field changes.
            for field in ('title','journal','year'):
                if row[field] != prior[field] and row[field]:
                    if isinstance(row[field],str) and ('…' in row[field] or '...' in row[field]):
                        review[sid] = {'title':row['title'],'reason':'Truncated updated metadata; existing values retained'}
                        continue
                    record[field] = row[field]
                    if field == 'journal': record['journal'] = row['journal'] + f" ({record['year']})"
                    if field == 'year':
                        record['sort_date'] = str(row['year']) + '-01-01'
                        record['journal'] = re.sub(r'\s*\(\d{4}(?:[.\-/]\d{1,2})*\)\s*$', '', record['journal']) + f" ({row['year']})"
                    changes.append(f'Updated {field}: {row["title"]}')
            if row['authors'] != prior['authors']:
                review[sid] = {'title':row['title'],'reason':'Author list changed; review full authors and first/corresponding roles before editing'}
            previous['snapshot'] = row
            continue
        if is_cover(row['title']):
            state['articles'][sid] = {'ignore':'Journal cover record, not an additional research article','snapshot':row}
            continue
        # No automatic fuzzy identity matching or publication deletion.
        candidate = resolver(row)
        if candidate is None:
            review[sid] = {'title':row['title'],'reason':'No unambiguous DOI/full-author match; manual review needed'}
            continue
        if candidate['id'] not in records:
            records[candidate['id']] = candidate; data['publications'].append(candidate)
            changes.append('Added: ' + candidate['title'])
            review[sid] = {'title':row['title'],'reason':'Added verified DOI metadata; check co-first/corresponding-author annotations'}
        state['articles'][sid] = {'record_id':candidate['id'],'snapshot':row}
    state['review'] = review
    return data,state,changes

def render(data, html):
    s = BeautifulSoup(html,'html.parser')
    nodes = s.select('.paper')
    if not nodes: raise RuntimeError('Publications template missing')
    parent = nodes[0].parent
    if any(n.parent is not parent for n in nodes): raise RuntimeError('Unexpected publications layout')
    for node in nodes: node.decompose()
    ordered = sorted(data['publications'],key=lambda p:p['sort_date'],reverse=True)
    for i,p in enumerate(ordered,1):
        if urlsplit(p['url']).scheme != 'https': raise RuntimeError('Publication URL must use HTTPS')
        article = f'<article class="paper"><div class="paper-index">{i:02d}</div><div><p class="journal">{escape(p["journal"])}</p><h3><a href="{escape(p["url"],quote=True)}" rel="noopener noreferrer" target="_blank">{escape(p["title"])}</a></h3><p class="authors">{p["authors_html"]}</p></div><a aria-label="{escape(p["title"],quote=True)} 논문 보기" class="paper-link" href="{escape(p["url"],quote=True)}" rel="noopener noreferrer" target="_blank">↗</a></article>'
        parent.append(BeautifulSoup(article,'html.parser'))
    return str(s)+'\n'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--snapshot',type=Path); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--render-only',action='store_true'); args=ap.parse_args()
    data=json.loads((ROOT/'publications-data.json').read_text(encoding='utf-8'))
    if args.render_only:
        path=ROOT/'publications.html'
        path.write_text(render(data,path.read_text(encoding='utf-8')),encoding='utf-8')
        return
    state=json.loads((ROOT/'scholar-sync-state.json').read_text(encoding='utf-8'))
    if args.snapshot: html=args.snapshot.read_text(encoding='utf-8')
    else:
        robots=fetch('https://scholar.google.com/robots.txt')
        if not robots_allows(robots,PROFILE_URL): raise RuntimeError('Scholar robots.txt disallows this URL; no files changed')
        html=fetch(PROFILE_URL)
    rows=parse_profile(html)
    data,state,changes=reconcile(data,state,rows)
    print(json.dumps({'profile_records':len(rows),'publications':len(data['publications']),'changes':changes,'review_items':len(state.get('review',{}))},ensure_ascii=False,indent=2))
    if args.dry_run:return
    rendered=render(data,(ROOT/'publications.html').read_text(encoding='utf-8'))
    state['last_successful_check']=datetime.now(timezone.utc).isoformat(timespec='seconds')
    # All downloads/parsing/validation have succeeded before any file is changed.
    payloads={'publications-data.json':json.dumps(data,ensure_ascii=False,indent=2)+'\n',
              'scholar-sync-state.json':json.dumps(state,ensure_ascii=False,indent=2)+'\n',
              'publications.html':rendered}
    for name,text in payloads.items():
        path=ROOT/name; temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(text,encoding='utf-8');temp.replace(path)

if __name__=='__main__': main()
