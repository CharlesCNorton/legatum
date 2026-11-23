"""Trim 160 px frames into five rows, retain offsets, enforce quality >=75 / 200KB."""
import os,json,hashlib,io
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/legionary';V=R/'review/3d-v2';DEST=Path('app/src/assets/units/anim');DEST.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=sha(M/'legionary.blend');grade=sha(M/'grade.json');prepared={};provenance={};maxw=0;y=0
meta={'format':'trimmed-rows-v1','frame':{'w':160,'h':160,'ax':79.375,'ay':138.125},'clips':{}}
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
    folder=M/'renders'/f'e-{clip}';manifest=json.loads((folder/'render.json').read_text());assert manifest['source_master_sha256']==source,f'Stale {clip} model';assert manifest['grade_sha256']==grade,f'Stale {clip} grade';assert manifest['resolution']==512,f'{clip} missing genuine 512 masters';assert manifest['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),f'Stale {clip} render'
    files=sorted((folder/'256').glob('*.png'));assert len(files)==count
    tiles=[];x=0;rowh=0;rects=[]
    for i,p in enumerate(files):
        assert sha(folder/'raw'/p.name)==manifest['raw_sha256'][p.name]
        assert (folder/'512'/p.name).exists()
        im=Image.open(p).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
        im.putalpha(im.getchannel('A').point(lambda a:0 if a<5 else a));box=im.getchannel('A').getbbox();assert box
        crop=im.crop(box);rect={'x':x,'y':y,'w':crop.width,'h':crop.height,'ox':box[0],'oy':box[1]};rects.append(rect);tiles.append(crop);x+=crop.width+2;rowh=max(rowh,crop.height)
    prepared[clip]=tiles;meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects};maxw=max(maxw,x-2);y+=rowh+2
    provenance[clip]={'render':manifest,'frames256_sha256':{p.name:sha(p) for p in files},'frames512_sha256':{p.name:sha(folder/'512'/p.name) for p in files}}
atlas=Image.new('RGBA',(maxw,y-2))
for clip,tiles in prepared.items():
    for im,r in zip(tiles,meta['clips'][clip]['rects']):atlas.paste(im,(r['x'],r['y']))
trials=[];data=None
for quality in [90,85,80,75]:
    stream=io.BytesIO();atlas.save(stream,format='WEBP',quality=quality,method=6,exact=True);candidate=stream.getvalue();trials.append({'quality':quality,'bytes':len(candidate)})
    if len(candidate)<=200000:data=candidate;break
assert data,'Atlas exceeds 200KB at quality75; do not reduce quality or drop frames'
meta['atlas']={'w':atlas.width,'h':atlas.height};(DEST/'legionary.webp').write_bytes(data);(DEST/'legionary.json').write_text(json.dumps(meta,indent=2)+'\n')
report={'bytes':len(data),'quality':quality,'trials':trials,'atlas_sha256':sha(DEST/'legionary.webp'),'json_sha256':sha(DEST/'legionary.json'),'source_master_sha256':source,'grade_sha256':grade,'clips':provenance}
(V/'legionary-pack.json').write_text(json.dumps(report,indent=2));print('PACKED',len(data),'bytes',quality,'quality',atlas.size)
