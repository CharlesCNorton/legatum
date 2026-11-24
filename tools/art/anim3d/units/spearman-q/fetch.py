"""Download only the pinned free Standard uploads, verifying archive hashes."""
import urllib.request,urllib.parse,http.cookiejar,re,json,zipfile,hashlib
from pathlib import Path
root=Path.home()/'LegatumRuns/anim-pilot/assets/spearman-q';root.mkdir(exist_ok=True)
pins={r['pack']:r for r in json.loads((Path(__file__).with_name('downloads.json')).read_text())}
receipt=[]
for p in ['universal-base-characters','universal-animation-library','universal-animation-library-2']:
 op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 u='https://quaternius.itch.io/'+p;t=op.open(u).read().decode();csrf=re.search(r'name="csrf_token" value="([^"]+)',t)[1]
 data=urllib.parse.urlencode({'csrf_token':csrf}).encode()
 page=json.load(op.open(u+'/download_url',data))['url'];t=op.open(page).read().decode()
 ident=re.search(r'data-upload_id="(\d+)"',t)[1]
 assert ident==pins[p]['upload_id'], f'Upstream version changed: {p}'
 d=json.load(op.open(u+'/file/'+ident,data));dest=root/(p+'.zip')
 if not dest.exists():
  with op.open(d['url'],timeout=90) as r:dest.write_bytes(r.read())
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==pins[p]['sha256'], f'Archive changed: {p}'
 with zipfile.ZipFile(dest) as z:
  for entry in z.infolist():
   assert (root/p/entry.filename).resolve().is_relative_to((root/p).resolve())
  z.extractall(root/p)
 receipt.append({'pack':p,'url':u,'upload_id':ident,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size})
 print(receipt[-1],flush=True)
(root/'downloads.json').write_text(json.dumps(receipt,indent=2)+'\n')
