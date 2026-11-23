"""Pack and validate the existing 40-frame atlas contract. No reduced frame counts.
Usage: python deliver.py [--validate-only]
"""
import os,json,io,hashlib,sys
from pathlib import Path
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/tank';review=R/'review/3d-v2'
OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
FRAME={'w':256,'h':256,'ax':127,'ay':221}
if '--validate-only' not in sys.argv:
    atlas=Image.new('RGBA',(2560,1280));meta={'frame':FRAME,'clips':{}};hashes={};renders={}
    for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
        meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop}
        folder=M/'renders'/f'e-{clip}';renders[clip]=json.loads((folder/'render.json').read_text())
        for i in range(count):
            p=folder/f'{i:02}.png';im=Image.open(p).convert('RGBA')
            assert im.size[0]>=256, 'Do not ship upscaled CPU thumbnails'
            im=im.resize((256,256),Image.Resampling.LANCZOS)
            a=im.getchannel('A').point(lambda x:round(round(x*31/255)*255/31));im.putalpha(a)
            im.paste((0,0,0,0),mask=a.point(lambda x:255 if x==0 else 0))
            atlas.paste(im,(i*256,row*256));hashes[f'{clip}/{i}']=hashlib.sha256(p.read_bytes()).hexdigest()
    assert len({r['grade_sha256'] for r in renders.values()})==1, 'Clips use different rest grades; rerender all clips'
    start=int(os.environ.get("WEBP_START_QUALITY","85"))
    assert 40<=start<=85
    for quality in sorted(set(range(85,39,-5)) | {start}, reverse=True):
        if quality>start:continue
        buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,alpha_quality=100,method=6,exact=True)
        print(f'WebP quality {quality}: {len(buf.getvalue())} bytes',flush=True)
        if len(buf.getvalue())<=200000:break
    else:raise RuntimeError('Atlas exceeds 200000 bytes at quality 40; preserve frames and inspect content')
    # Refine within the final five-point interval to keep the best finish under the cap.
    for finer in range(min(start,quality+4),quality,-1):
        trial=io.BytesIO();atlas.save(trial,format='WEBP',quality=finer,alpha_quality=100,method=6,exact=True)
        print(f'WebP quality {finer}: {len(trial.getvalue())} bytes',flush=True)
        if len(trial.getvalue())<=200000:quality=finer;buf=trial;break
    (OUT/'tank.webp').write_bytes(buf.getvalue());(OUT/'tank.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    (review/'tank-pack.json').write_text(json.dumps({'bytes':len(buf.getvalue()),'quality':quality,'alpha_quality':100,'frames':40,'renders':renders,'source_sha256':hashes,'atlas_sha256':hashlib.sha256(buf.getvalue()).hexdigest()},indent=2))
meta=json.loads((OUT/'tank.json').read_text());atlas=Image.open(OUT/'tank.webp').convert('RGBA')
assert atlas.size==(2560,1280);assert (OUT/'tank.webp').stat().st_size<=200000;assert meta['frame']==FRAME
boxes={};motion={}
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
    assert meta['clips'][clip]=={'row':row,'frames':count,'fps':fps,'loop':loop}
    frames=[]
    for i in range(10):
        im=atlas.crop((i*256,row*256,(i+1)*256,(row+1)*256));a=im.getchannel('A')
        if i>=count:assert not a.getbbox(),f'{clip} padding';continue
        box=a.point(lambda x:255 if x>16 else 0).getbbox();assert box,f'{clip}/{i} empty'
        assert box[0]>=2 and box[1]>=2 and box[2]<=254 and box[3]<=254,f'{clip}/{i} clips frame: {box}'
        boxes[f'{clip}/{i}']=box;frames.append(im)
    motion[clip]=any(ImageChops.difference(frames[0],f).getbbox(alpha_only=False) for f in frames[1:]);assert motion[clip],f'{clip} has no motion'
terminal=M/'renders/e-death'
assert Image.open(terminal/'08.png').convert('RGBA').tobytes()==Image.open(terminal/'09.png').convert('RGBA').tobytes(),'Death terminal not held'
report={'contract':'PASS','bytes':(OUT/'tank.webp').stat().st_size,'frames':40,'bounds':boxes,'motion':motion,'held_death':True}
(review/'tank-validation.json').write_text(json.dumps(report,indent=2))
print('PASS: 40 frames; 2560x1280; exact JSON; transparent padding; 2px margins; all clips move; held death; byte cap:',report['bytes'])
