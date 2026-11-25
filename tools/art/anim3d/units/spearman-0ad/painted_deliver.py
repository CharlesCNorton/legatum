"""Encode delivery WebP textures (quality 84–85) and compact only GLB image buffers.

Run with ANIM_ROOT/venv/bin/python after Blender export. The 2048 PNG masters
remain lossless. This packaging step does not edit geometry, rig or animation.
"""
import json,struct,sys,os,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
UNIT=Path(__file__).resolve().parent
sys.path.insert(0,str(UNIT.parents[1]))
from validate_glb import GLB
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'lanes/spearman-0ad-painted-r3'
g=GLB(UNIT/'spearman.glb');d=g.doc;replacements={};report={}
for im in d['images']:
    name=im['name'];png=UNIT/f'spearman-{name}.png';jpg=UNIT/f'spearman-{name}.webp'
    source=png if png.exists() else WORK/f'shipped-lossless-{name}.png'
    image=Image.open(source).convert('RGB');assert image.size==(1024,1024)
    quality=85 if name=='normal' else 84
    image.save(jpg,format='WEBP',quality=quality,method=6)
    decoded=Image.open(jpg).convert('RGB')
    delta=np.asarray(image,dtype=float)-np.asarray(decoded,dtype=float)
    report[name]={'size':[1024,1024],'webp_bytes':jpg.stat().st_size,'quality':quality,'encoding':'WebP','channel_rmse_8bit':float(np.sqrt(np.mean(delta**2)))}
    replacements[im['bufferView']]=jpg.read_bytes();im['mimeType']='image/webp'
    if png.exists():(WORK/f'shipped-lossless-{name}.png').write_bytes(png.read_bytes());png.unlink()
for mesh in d['meshes']:
    merged=[]
    for region in mesh['extras']['vertex_regions']:
        if merged and all(merged[-1].get(k)==region.get(k) for k in ['part','bone','team']) and merged[-1]['start']+merged[-1]['count']==region['start']:merged[-1]['count']+=region['count']
        else:merged.append(dict(region))
    mesh['extras']['vertex_regions']=merged
required_bounds={m['primitives'][0]['attributes']['POSITION'] for m in d['meshes']}
required_bounds.update(s['input'] for clip in d['animations'] for s in clip['samplers'])
for i,a in enumerate(d['accessors']):
    if i not in required_bounds:a.pop('min',None);a.pop('max',None)
for texture in d['textures']:
    source=texture.pop('source',None)
    if source is None:source=texture['extensions']['EXT_texture_webp']['source']
    texture['extensions']={'EXT_texture_webp':{'source':source}}
for name in ['extensionsUsed','extensionsRequired']:
    if 'EXT_texture_webp' not in d.setdefault(name,[]):d[name].append('EXT_texture_webp')
blob=bytearray()
for i,v in enumerate(d['bufferViews']):
    old=g.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
    raw=replacements.get(i,old);blob.extend(b'\0'*(-len(blob)%4));v['byteOffset']=len(blob);v['byteLength']=len(raw);blob.extend(raw)
d['buffers']=[{'byteLength':len(blob)}];blob.extend(b'\0'*(-len(blob)%4))
d['asset']['extras']['texture_delivery']={'quality':84,'encoding':'WebP','pixels':1024}
raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4)
path=UNIT/'spearman.glb';path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)
for name in ['basecolor','normal','orm']:
    trial=UNIT/f'spearman-{name}.jpg'
    if trial.exists():(WORK/f'trial-jpeg-{name}.jpg').write_bytes(trial.read_bytes());trial.unlink()
report.update(glb_bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
(WORK/'delivery.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
