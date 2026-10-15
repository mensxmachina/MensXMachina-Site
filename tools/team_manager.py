#!/usr/bin/env python3
"""Local-only team editor and static profile generator; Python standard library only."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from email.parser import BytesParser
from email.policy import default
import html, json, re, secrets, threading, webbrowser, sys, unicodedata
ROOT=Path(__file__).resolve().parents[1]
TOKEN=secrets.token_urlsafe(32)
GROUPS={'faculty':'Faculty','phd':'PhD Students','staff':'Staff','alumni':'Alumni'}
CSS='''*{box-sizing:border-box}body{margin:0;font:15px/1.7 Arial,sans-serif;color:#1a2433;background:#f0f5fb}a{color:#1a4a7a}header{background:#1a2433;color:white;padding:24px}header div,main{max-width:1100px;margin:auto}header a{color:white;text-decoration:none}header strong{font-size:28px}nav{display:flex;gap:24px;margin-top:12px}main{padding:32px 20px}h1,h2{color:#1a4a7a}h1{font-size:32px}h2{border-bottom:2px solid #1a4a7a;padding-bottom:8px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.card,.panel{background:white;padding:28px;border:1px solid #dce6f0}.card{text-align:center}.avatar{width:110px;height:110px;border-radius:50%;object-fit:cover;margin:0 auto 16px;display:block}.initials{background:#1a4a7a;color:white;line-height:110px;font-size:32px;text-align:center}.role{color:#5a6e84}.profile{display:grid;grid-template-columns:230px minmax(0,1fr);gap:32px}.bio{white-space:pre-line;overflow-wrap:anywhere}label{display:block;font-weight:bold;margin:16px 0 5px}input,select,textarea{width:100%;padding:12px;font:inherit;border:1px solid #aebed0}button,.button{background:#1a4a7a;color:white;border:0;padding:12px 20px;font:inherit;cursor:pointer;display:inline-block;margin-top:20px}.notice{color:#5a6e84}form{max-width:720px}.contact{overflow-wrap:anywhere}@media(max-width:700px){.grid,.profile{grid-template-columns:1fr}nav{flex-wrap:wrap}}'''
def esc(v): return html.escape(str(v),quote=True)
def page(title,body,prefix=''):
 header=(ROOT/'tools/site_header.html').read_text()
 header=header.replace('data-page="people"','data-page="people" class="active"')
 header=re.sub(r'href="(?!https?://)([^"]+)"',lambda m: 'href="'+prefix+m[1]+'"',header)
 return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} — mens X machina</title><style>{CSS}</style><link rel="stylesheet" href="{prefix}navigation.css"></head><body>{header}<main>{body}</main></body></html>'
def avatar(m,prefix=''):
 fallback=f'<span class="avatar initials">{esc(m.get("initials",""))}</span>'
 photo=m.get('photo','')
 if photo and (ROOT/photo).is_file(): return f'<img class="avatar" src="{prefix}{esc(photo)}" alt="{esc(m["name"])}">'
 return fallback

def generate(members):
 (ROOT/'people').mkdir(exist_ok=True)
 sections=[]
 for group,label in GROUPS.items():
  cards=[]
  for m in members:
   if m['group']!=group: continue
   ident=m['id']
   if not re.fullmatch('[a-z0-9_-]+',ident): raise ValueError('Invalid member ID')
   cards.append(f'<article class="card"><a href="people/{ident}.html">{avatar(m)}<h3>{esc(m["name"])}</h3></a><p class="role">{esc(m["role"])}</p></article>')
  if cards: sections.append(f'<section id="{group}"><h2>{label}</h2><div class="grid">'+''.join(cards)+'</div></section>')
  else: sections.append(f'<section id="{group}"><h2>{label}</h2><p>No members currently listed.</p></section>')
 for m in members:
  links=[]
  if m.get('email'): links.append(f'<p><a href="mailto:{esc(m["email"])}">{esc(m["email"])}</a></p>')
  if m.get('url','').startswith(('http://','https://')): links.append(f'<p><a href="{esc(m["url"])}" target="_blank" rel="noopener noreferrer">Personal website →</a></p>')
  if m.get('phone'): links.append(f'<p>Phone: {esc(m["phone"])}</p>')
  if m.get('office'): links.append(f'<p>Office: {esc(m["office"])}</p>')
  body=f'<a href="../team.html">← Full team</a><h1>{esc(m["name"])}</h1><div class="profile"><aside class="panel">{avatar(m,"../")}<p class="role">{esc(m["role"])}</p></aside><article class="panel"><h2>Biography</h2><p class="bio">{esc(m.get("bio", ""))}</p><h2>Contact</h2><div class="contact">'+(''.join(links) or '<p>Contact the group for enquiries.</p>')+'</div></article></div>'
  (ROOT/'people'/f'{m["id"]}.html').write_text(page(m['name'],body,'../'),encoding='utf-8')
 (ROOT/'team.html').write_text(page('Our Team','<h1>Our Team</h1><p>Meet the people behind mens X machina.</p>'+''.join(sections)),encoding='utf-8')

def form(message=''):
 fields=''
 for name,label,typ,req in [('name','Full name','text',True),('role','Role / title','text',True),('email','Email','email',False),('url','Personal website','url',False),('phone','Phone','text',False),('office','Office / location','text',False)]:
  fields+=f'<label for="{name}">{label}</label><input id="{name}" name="{name}" type="{typ}" maxlength="300" '+('required' if req else '')+'>'
 return page('Add team member',f'<h1>Add team member</h1><p class="notice">This local tool saves directly to your website folder. Only contact information you enter will appear publicly.</p><p role="status">{esc(message)}</p><form method="post" action="/admin" enctype="multipart/form-data"><input type="hidden" name="token" value="{TOKEN}">{fields}<label for="group">Group</label><select id="group" name="group">'+''.join(f'<option value="{k}">{v}</option>' for k,v in GROUPS.items())+'</select><label for="bio">Biography</label><textarea id="bio" name="bio" rows="7" maxlength="12000" required></textarea><label for="photo">Photo (JPEG or PNG, up to 8 MB)</label><input id="photo" name="photo" type="file" accept="image/jpeg,image/png"><p class="notice">Optional. Without a photo, the profile shows initials.</p><button type="submit">Save member &amp; create profile</button></form>')
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
 def allowed(self): return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
 def sendhtml(self,body,status=200):
  data=body.encode();self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  if not self.allowed(): return self.send_error(403)
  if self.path in ('/admin','/admin/'): return self.sendhtml(form())
  return super().do_GET()
 def do_POST(self):
  if not self.allowed() or self.path!='/admin': return self.send_error(403)
  if self.headers.get('Origin')!=f'http://127.0.0.1:{self.server.server_port}': return self.send_error(403)
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<9*1024*1024: raise ValueError('The submitted form is too large.')
   msg=BytesParser(policy=default).parsebytes(('Content-Type: '+self.headers.get('Content-Type','')+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+self.rfile.read(size))
   fields={}; photo=b''
   for part in msg.iter_parts():
    name=part.get_param('name',header='content-disposition'); data=part.get_payload(decode=True) or b''
    if name=='photo': photo=data
    else: fields[name]=data.decode('utf-8').strip()
   if not secrets.compare_digest(fields.get('token',''),TOKEN): return self.send_error(403)
   if not all(fields.get(x) for x in ('name','role','bio')): raise ValueError('Name, role and biography are required.')
   if fields.get('group') not in GROUPS: raise ValueError('Choose a valid group.')
   if fields.get('url') and not re.match(r'^https?://[^\s]+$',fields['url']): raise ValueError('Website must begin with http:// or https://.')
   if fields.get('email') and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',fields['email']): raise ValueError('Enter a valid email address.')
   ident=re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',fields['name']).encode('ascii','ignore').decode().lower()).strip('-') or 'member'
   members=json.loads((ROOT/'data/team.json').read_text())
   if any(m['name'].casefold()==fields['name'].casefold() for m in members): raise ValueError('A member with this name already exists.')
   base=ident; n=2
   while any(m['id']==ident for m in members) or (ROOT/'people'/f'{ident}.html').exists(): ident=f'{base}-{n}';n+=1
   photo_path=''
   if photo:
    ext='jpg' if photo.startswith(b'\xff\xd8\xff') else 'png' if photo.startswith(b'\x89PNG\r\n\x1a\n') else None
    if not ext or len(photo)>8*1024*1024: raise ValueError('Choose a JPEG or PNG photo smaller than 8 MB.')
    (ROOT/'photos').mkdir(exist_ok=True);photo_path=f'photos/{ident}.{ext}';(ROOT/photo_path).write_bytes(photo)
   m={k:fields.get(k,'') for k in ('name','role','group','email','url','phone','office','bio')}
   m.update(id=ident,photo=photo_path,initials=''.join(x[0] for x in m['name'].split()[:2]).upper(),color='#1a4a7a')
   members.append(m);generate(members)
   temp=ROOT/'data/team.json.tmp';temp.write_text(json.dumps(members,ensure_ascii=False,indent=2)+'\n');temp.replace(ROOT/'data/team.json')
   self.sendhtml(page('Member added',f'<h1>Member added</h1><p>{esc(m["name"])} is now listed on the homepage and full-team page.</p><p><a href="people/{ident}.html">View profile →</a></p><p><a href="team.html">View full team →</a></p><a class="button" href="/admin">Add another member</a>'))
  except (ValueError,KeyError,UnicodeError) as e: self.sendhtml(form(str(e)),400)
if __name__=='__main__':
 generate(json.loads((ROOT/'data/team.json').read_text()))
 if '--generate' in sys.argv: print('Generated team and profile pages.');sys.exit()
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 url=f'http://127.0.0.1:{server.server_port}/admin'
 print('Team manager: '+url,flush=True)
 if '--no-browser' not in sys.argv: webbrowser.open(url)
 try: server.serve_forever()
 except KeyboardInterrupt: server.server_close()
