#!/usr/bin/env python3
"""Generate news.html and one page per news item from data/news.json.

Usage:
  python3 tools/build_news.py          rebuild all news pages
  python3 tools/build_news.py --add    interactively add an item, then rebuild
"""
from pathlib import Path
from datetime import date, datetime
import html, json, re, sys, unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'news.json'
OUT = ROOT / 'news'
CATEGORIES = {'general': 'News', 'awards': 'Awards', 'positions': 'Positions'}
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

CSS = '''*{box-sizing:border-box}body{margin:0;font:15px/1.7 'Open Sans',Arial,sans-serif;color:#1a2433;background:#f0f5fb}a{color:#1a4a7a}
main{max-width:1100px;margin:auto;padding:32px 20px 56px}h1{color:#1a4a7a;font-size:32px;margin:0 0 8px}.lead{color:#5a6e84;margin:0 0 24px}
.panel{background:#fff;border:1px solid #dce6f0;padding:12px 32px 32px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 20px}.filters button{background:#fff;color:#1a4a7a;border:1px solid #1a4a7a;padding:6px 14px;font:inherit;font-size:13px;cursor:pointer}.filters button.on{background:#1a4a7a;color:#fff}
.year{font-size:20px;color:#1a4a7a;border-bottom:2px solid #1a4a7a;padding-bottom:6px;margin:28px 0 0}
.news-item{border-bottom:1px solid #dce6f0;padding:18px 0;display:flex;gap:18px}.news-item:last-child{border-bottom:0}
.news-date{min-width:70px;text-align:center}.news-date .day{display:block;font-size:28px;font-weight:700;color:#1a4a7a;line-height:1}
.news-date .month-year{display:block;font-size:11px;color:#7d8da4;text-transform:uppercase;letter-spacing:1px}
.news-body h3{font-size:16px;margin:0 0 6px;line-height:1.4}.news-body h3 a{color:#1a2433;text-decoration:none}.news-body h3 a:hover{color:#1a4a7a}
.news-body p{margin:0;font-size:14px;color:#44566c}
.read-more{display:inline-block;margin-top:6px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;text-decoration:none}
.badge{display:inline-block;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:2px 7px;margin-bottom:6px;background:#e2e8f0;color:#383d41}
.badge.awards{background:#d0eaff;color:#0d4a7a}.badge.positions{background:#d1f5e4;color:#0c5440}
.article{background:#fff;border:1px solid #dce6f0;padding:36px;max-width:820px}.article h1{font-size:30px;line-height:1.25;margin:10px 0 6px}
.meta{color:#7d8da4;font-size:13px;margin:0 0 20px}.summary{font-size:17px;color:#2b3b50;border-left:3px solid #1a4a7a;padding:4px 0 4px 18px;margin:0 0 24px}
.article p{overflow-wrap:anywhere}.ext{display:inline-block;margin:8px 0 0;background:#1a4a7a;color:#fff;padding:10px 18px;text-decoration:none}
.pager{display:flex;justify-content:space-between;gap:16px;margin-top:32px;padding-top:16px;border-top:1px solid #dce6f0;font-size:14px}.pager a{max-width:48%}
.back{display:inline-block;margin-bottom:16px}
@media(max-width:600px){.panel,.article{padding:16px 18px}.news-item{gap:12px}.article h1{font-size:24px}}'''

FILTER_JS = '''<script>
document.querySelectorAll('.filters button').forEach(function(b){b.addEventListener('click',function(){
var c=b.dataset.cat;document.querySelectorAll('.filters button').forEach(function(x){x.classList.toggle('on',x===b)});
document.querySelectorAll('.news-item').forEach(function(i){i.hidden=c!=='all'&&i.dataset.cat!==c});
document.querySelectorAll('.year').forEach(function(y){var n=y.nextElementSibling,any=false;
while(n&&n.classList.contains('news-item')){if(!n.hidden)any=true;n=n.nextElementSibling}y.hidden=!any});});});
</script>'''


def esc(v):
    return html.escape(str(v), quote=True)


def parse_date(s):
    """Accepts YYYY-MM-DD, YYYY-MM or YYYY; returns (date, precision) with precision 'd'/'m'/'y'."""
    for fmt, prec in (('%Y-%m-%d', 'd'), ('%Y-%m', 'm'), ('%Y', 'y')):
        try:
            return datetime.strptime(s, fmt).date(), prec
        except ValueError:
            pass
    raise ValueError(f'Bad date: {s!r} (use YYYY-MM-DD, YYYY-MM or YYYY)')


def fmt_date(s):
    if not s:
        return ''
    d, prec = parse_date(s)
    return {'d': f'{d.day} {MONTHS[d.month - 1]} {d.year}', 'm': f'{MONTHS[d.month - 1]} {d.year}', 'y': str(d.year)}[prec]


def has_page(i):
    return bool(i.get('excerpt') or i.get('body'))


def rich(text):
    """Escape, then allow [label](https://url) links and blank-line paragraphs."""
    paras = [p.strip() for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]
    def link(m):
        return f'<a href="{m[2]}" target="_blank" rel="noopener noreferrer">{m[1]}</a>'
    out = []
    for p in paras:
        e = esc(p).replace('\n', '<br>')
        e = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', link, e)
        out.append(f'<p>{e}</p>')
    return '\n'.join(out)


def shell(title, body, prefix=''):
    header = (ROOT / 'tools' / 'site_header.html').read_text(encoding='utf-8')
    header = header.replace('data-page="news"', 'data-page="news" class="active"')
    header = re.sub(r'href="(?!https?://)([^"]+)"', lambda m: f'href="{prefix}{m[1]}"', header)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)} — mens X machina</title><style>{CSS}</style>'
            f'<link rel="stylesheet" href="{prefix}navigation.css"></head><body>{header}<main>{body}</main></body></html>')


def load():
    items = json.loads(DATA.read_text(encoding='utf-8'))
    ids = [i['id'] for i in items]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate news id in data/news.json')
    for i in items:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', i['id']):
            raise ValueError(f'Invalid id: {i["id"]}')
        if i.get('date'):
            parse_date(i['date'])
    dated = sorted((i for i in items if i.get('date')), key=lambda i: (i['date'], -i.get('rank', 0)), reverse=True)
    undated = sorted((i for i in items if not i.get('date')), key=lambda i: (i.get('rank', 10**6), i['id']))
    return dated + undated


def badge(item):
    cat = item.get('category', 'general')
    return f'<span class="badge {esc(cat)}">{esc(CATEGORIES.get(cat, cat))}</span>'


def date_block(s):
    if not s:
        return ''
    d, prec = parse_date(s)
    if prec == 'd':
        return (f'<div class="news-date"><span class="day">{d.day:02d}</span>'
                f'<span class="month-year">{MONTHS[d.month - 1]} {d.year}</span></div>')
    label = f'{MONTHS[d.month - 1]} {d.year}' if prec == 'm' else str(d.year)
    return f'<div class="news-date"><span class="month-year" style="font-size:13px">{label}</span></div>'


def build(items):
    OUT.mkdir(exist_ok=True)
    keep = {f'{i["id"]}.html' for i in items if has_page(i)}
    for f in OUT.glob('*.html'):
        if f.name not in keep:
            try:
                f.unlink()
            except OSError:
                print(f'Could not remove stale page {f.name}; delete it manually.')

    cats = [c for c in CATEGORIES if any(i.get('category', 'general') == c for i in items)]
    filters = '<div class="filters"><button class="on" data-cat="all">All</button>' + ''.join(
        f'<button data-cat="{c}">{CATEGORIES[c]}</button>' for c in cats) + '</div>'
    rows, group = [], None
    for i in items:
        g = parse_date(i['date'])[0].year if i.get('date') else 'Earlier news'
        if g != group:
            group = g
            rows.append(f'<h2 class="year">{group}</h2>')
        if has_page(i):
            title = f'<a href="news/{i["id"]}.html">{esc(i["title"])}</a>'
            more = f'<p>{esc(i["excerpt"])}</p><a class="read-more" href="news/{i["id"]}.html">Read more »</a>' if i.get('excerpt') else f'<a class="read-more" href="news/{i["id"]}.html">Read more »</a>'
        else:
            title, more = esc(i['title']), ''
        rows.append(
            f'<div class="news-item" data-cat="{esc(i.get("category", "general"))}">{date_block(i.get("date"))}'
            f'<div class="news-body">{badge(i)}<h3>{title}</h3>{more}</div></div>')
    listing = ('<h1>News</h1><p class="lead">Announcements, awards and open positions from the group.</p>'
               + filters + '<div class="panel">' + ''.join(rows or ['<p>No news yet.</p>']) + '</div>' + FILTER_JS)
    (ROOT / 'news.html').write_text(shell('News', listing), encoding='utf-8')

    paged = [i for i in items if has_page(i)]
    for n, i in enumerate(paged):
        newer = paged[n - 1] if n > 0 else None
        older = paged[n + 1] if n + 1 < len(paged) else None
        ext = i.get('link', '')
        ext_html = (f'<p><a class="ext" href="{esc(ext)}" target="_blank" rel="noopener noreferrer">Related link →</a></p>'
                    if ext.startswith(('http://', 'https://')) else '')
        src = i.get('source_url', '')
        src_html = (f'<p><a href="{esc(src)}" target="_blank" rel="noopener noreferrer">Original post (Internet Archive) →</a></p>'
                    if src.startswith(('http://', 'https://')) else '')
        body = rich(i['body']) if i.get('body') else ''
        pager = ('<div class="pager"><span>' + (f'<a href="{newer["id"]}.html">← {esc(newer["title"])}</a>' if newer else '')
                 + '</span><span style="text-align:right">' + (f'<a href="{older["id"]}.html">{esc(older["title"])} →</a>' if older else '')
                 + '</span></div>')
        page = (f'<a class="back" href="../news.html">← All news</a><article class="article">{badge(i)}'
                f'<h1>{esc(i["title"])}</h1><p class="meta">{esc(fmt_date(i.get("date")) or "Archive")}</p>'
                + (f'<p class="summary">{esc(i["excerpt"])}</p>' if i.get('excerpt') else '')
                + f'{body}{src_html}{ext_html}{pager}</article>')
        (OUT / f'{i["id"]}.html').write_text(shell(i['title'], page, '../'), encoding='utf-8')
    print(f'Built news.html ({len(items)} items) and {len(paged)} news pages.')


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:50] or 'item'


def ask(prompt, default=''):
    v = input(f'{prompt}' + (f' [{default}]' if default else '') + ': ').strip()
    return v or default


def add():
    items = json.loads(DATA.read_text(encoding='utf-8'))
    title = ask('Title')
    if not title:
        sys.exit('Title is required.')
    d = ask('Date YYYY-MM-DD', date.today().isoformat())
    parse_date(d)
    cat = ask('Category (' + '/'.join(CATEGORIES) + ')', 'general')
    if cat not in CATEGORIES:
        sys.exit('Unknown category.')
    excerpt = ask('Short description (1-3 sentences)')
    if not excerpt:
        sys.exit('Description is required.')
    print('Full text (optional). Finish with an empty line twice, or just press Return to skip:')
    lines, blanks = [], 0
    while True:
        line = input()
        blanks = blanks + 1 if not line.strip() else 0
        if blanks >= (2 if lines else 1):
            break
        lines.append(line)
    link = ask('Related external link (optional)')
    ident = f'{d}-{slug(title)}'
    while any(i['id'] == ident for i in items):
        ident += '-2'
    item = {'id': ident, 'date': d, 'title': title, 'excerpt': excerpt, 'category': cat}
    if '\n'.join(lines).strip():
        item['body'] = '\n'.join(lines).strip()
    if link:
        item['link'] = link
    items.append(item)
    DATA.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Added {ident}')


if __name__ == '__main__':
    if '--add' in sys.argv:
        add()
    build(load())
