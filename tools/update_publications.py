#!/usr/bin/env python3
"""Refresh the static homepage from BibSonomy; keep the last snapshot on failure."""
import base64, getpass, html, json, os, re, ssl, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path.home() / 'Library/Application Support/MensXMachina/bibsonomy.json'
PROFILE = 'https://www.bibsonomy.org/user/mensxmachina'
def refresh():
    if CONFIG.exists():
        key = json.loads(CONFIG.read_text())['api_key']
    else:
        key = getpass.getpass('BibSonomy API key (hidden): ').strip()
    if not key:
        raise ValueError('An API key is required.')
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem' if Path('/etc/ssl/cert.pem').exists() else None)
    auth = base64.b64encode(('mensxmachina:' + key).encode()).decode()
    posts = []
    for start in range(0, 10000, 100):
        url = 'https://www.bibsonomy.org/api/posts?' + urlencode(dict(user='mensxmachina', resourcetype='bibtex', start=start, end=start+100))
        with urlopen(Request(url, headers={'Accept':'application/json', 'Authorization':'Basic '+auth}), context=context, timeout=30) as response:
            data = json.load(response)
        page = data['posts'].get('post', [])
        posts.extend(page)
        if len(page) < 100:
            break
    else:
        raise ValueError('Publication limit exceeded; previous snapshot kept.')
    if not posts:
        raise ValueError('No publications returned; previous snapshot kept.')
    pubs = []
    for post in posts:
        bib = post.get('bibtex', {})
        if not bib.get('title'): continue
        year = re.search(r'\d{4}', str(bib.get('year', '')))
        pubs.append(dict(title=bib['title'], authors=bib.get('author',''), year=int(year[0]) if year else 0, venue=bib.get('journal') or bib.get('booktitle') or bib.get('publisher',''), link='https://www.bibsonomy.org/bibtex/'+bib['interhash']+'/mensxmachina' if bib.get('interhash') else PROFILE))
    if not pubs: raise ValueError('No valid publications returned.')
    pubs.sort(key=lambda p:p['year'], reverse=True)
    esc = lambda value: html.escape(str(value), quote=True)
    parts=[]
    current=None
    for p in pubs[:8]:
        year=p['year'] or 'n.d.'
        if year != current:
            if current is not None: parts.append('</div>')
            parts.append(f'<div class="pub-year-group"><div class="pub-year-header">{year}</div>')
            current=year
        title=esc(p['title']); link=esc(p['link']); authors=esc(p['authors'].replace(' and ', ', ')); venue=esc(p['venue'])
        parts.append(f'<div class="pub-item"><div><span class="pub-year-badge">{year}</span> <span class="pub-title"><a href="{link}" target="_blank" rel="noopener">{title}</a></span></div><div class="pub-meta">{authors}'+(f' — <em>{venue}</em>' if venue else '')+f'</div><div class="pub-links"><a href="{link}" target="_blank" rel="noopener">BibSonomy</a></div></div>')
    parts.append('</div>')
    index=ROOT/'index.html'; source=index.read_text()
    source,count=re.subn(r'<!-- PUBLICATIONS SNAPSHOT START -->.*?<!-- PUBLICATIONS SNAPSHOT END -->',lambda _: '<!-- PUBLICATIONS SNAPSHOT START -->\n<div id="pub-list">'+ '\n'.join(parts)+'</div>\n<!-- PUBLICATIONS SNAPSHOT END -->',source,flags=re.S)
    if count != 1: raise ValueError('Homepage snapshot markers missing.')
    (ROOT/'data/publications.json').write_text(json.dumps(pubs,ensure_ascii=False,indent=2)+'\n')
    temp=index.with_suffix('.html.tmp');temp.write_text(source);temp.replace(index)
    if not CONFIG.exists():
        CONFIG.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(CONFIG,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f: json.dump({'api_key':key},f)
    print(f'Updated {len(pubs)} publications. The newest eight are saved in index.html.')
if __name__ == '__main__':
    try: refresh()
    except Exception as error:
        print(f'Update failed: {error}\nYour existing homepage publication list has been kept.',file=sys.stderr)
        sys.exit(1)
