"""Install pinned MPFB and CC0 system assets solely in ANIM_ROOT. Run with Python 3."""
import os,sys,subprocess,zipfile,shutil,hashlib,json
from pathlib import Path
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=ROOT/'assets';A.mkdir(parents=True,exist_ok=True)
version='2.0.18'
LOCK=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
def verify(p):
 key=str(p.relative_to(A))
 if key in LOCK and hashlib.sha256(p.read_bytes()).hexdigest()!=LOCK[key]:raise ValueError('Source checksum changed: '+key)
def download(url,name):
 p=A/name
 if not p.exists():subprocess.run(['curl','-L','--fail','-sS',url,'-o',str(p)],check=True)
 verify(p)
 return p
addon=download(f'https://codeload.github.com/makehumancommunity/mpfb2/zip/refs/tags/v{version}',f'mpfb2-v{version}.zip')
with zipfile.ZipFile(addon) as z:z.extractall(A)
source=A/f'mpfb2-{version}'/'src/mpfb';dest=ROOT/'blender-user/extensions/user_default/mpfb'
shutil.copytree(source,dest,dirs_exist_ok=True)
pack=A/'makehuman_system_assets_cc0.zip'
if not pack.exists() or not zipfile.is_zipfile(pack):
 subprocess.run(['curl','-L','--fail','-sS','-C','-','https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip','-o',str(pack)],check=True)
verify(pack)
data=ROOT/'blender-user/extensions/.user/user_default/mpfb/data';data.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(pack) as z:
 for name in z.namelist():
  if not (data/name).resolve().is_relative_to(data.resolve()):raise ValueError('Unsafe archive path')
 z.extractall(data)
for name in ['02_01','77_02']:
 subject=name.split('_')[0].zfill(3)
 download(f'https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/{subject}/{name}.bvh',f'cmu-{name}.bvh')
download('https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/READMEFIRST.txt','cmu-READMEFIRST.txt')
subprocess.run([sys.executable,str(Path(__file__).with_name('download-materials.py'))],check=True)
source_art=download('https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/spearman-source.png','spearman-source.png')
master_dir=ROOT/'masters/spearman-3d-v2';master_dir.mkdir(parents=True,exist_ok=True)
shutil.copy2(source_art,master_dir/'spearman-source.png')
venv=ROOT/'venv'
if not (venv/'bin/python').exists():subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
subprocess.run([str(venv/'bin/python'),'-m','pip','install','Pillow==13.0.0'],check=True)
manifest={str(p.relative_to(A)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [addon,pack,A/'cmu-02_01.bvh',A/'cmu-77_02.bvh']}
(A/'install-sha256.json').write_text(json.dumps(manifest,indent=2));print('MPFB',version,'and CC0 system pack installed in',ROOT)

rows=[
 ('MPFB 2.0.18',f'https://codeload.github.com/makehumancommunity/mpfb2/zip/refs/tags/v{version}','GPL-3.0-or-later software; CC0 body, targets and rig output'),
 ('MakeHuman system assets','https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip','CC0; high-poly eyes and young_caucasian_male2 skin used'),
 ('CMU 02_01 walk','https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/002/02_01.bvh','CMU permissive commercial/research use; Bruce Hahne 2010 conversion adds no restrictions'),
 ('CMU 77_02 standing','https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/077/77_02.bvh','Same CMU terms; see cmu-READMEFIRST.txt'),
 ('Blender 5.3.0','https://www.blender.org/','GPL software; existing executable'),
 ('Pillow 13.0.0','https://pypi.org/project/pillow/13.0.0/','MIT-CMU permissive software'),
 ('Legatum spearman painting','https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/spearman-source.png','Project CC BY 4.0; visual reference'),
]
for record in json.loads((A/'materials-manifest.json').read_text()):
 rows.append((record['file']+' (1K)',record['url'],record['license']))
text='# Spearman 3D v2 sources\n\nPinned download hashes: install-sha256.json, materials-manifest.json and repository assets.lock.json. Raw packs remain outside git.\n\n| Asset / version | URL | Licence |\n| --- | --- | --- |\n'
text+=''.join('| '+ ' | '.join(row)+' |\n' for row in rows)
text+='\nThe data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217. Original kit and keys: tools/art/anim3d, MIT scripts / CC BY 4.0 rendered art. Hunyuan3D, TRELLIS and Rokoko are not installed.\n'
(A/'SOURCES.md').write_text(text)
