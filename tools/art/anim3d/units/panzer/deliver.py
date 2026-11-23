"""Trim 160px frame cells, retain clip rows/anchors, quality >=75 and <=200000 bytes."""
import os, json, io, hashlib, sys
from pathlib import Path
from PIL import Image, ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=R/'masters/panzer'; REVIEW=R/'review/3d-v2'; OUT=Path('app/src/assets/units/anim')
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
FRAME={'w':160,'h':160,'ax':79.375,'ay':138.125}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def restore(atlas, rect):
    x,y,w,h,ox,oy=(rect[k] for k in ('x','y','w','h','ox','oy'))
    im=Image.new('RGBA',(160,160));im.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy));return im

def pack():
    OUT.mkdir(parents=True,exist_ok=True)
    meta={'version':2,'trimmed':True,'frame':FRAME,'clips':{}}
    rows=[];hashes={};renders={};width=0;height=0
    for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
        folder=M/'renders'/f'e-{clip}'
        renders[clip]=json.loads((folder/'render.json').read_text())
        assert renders[clip]['blend_sha256']==digest(M/'clips'/f'{clip}.blend'), 'Frames use stale clip geometry'
        rects=[];crops=[];x=2;rh=0;seen={}
        for i in range(count):
            p=folder/f'{i:02}.png';im=Image.open(p).convert('RGBA')
            assert im.width>=256 and im.width==im.height,'No upscaled preview masters'
            im=im.resize((160,160),Image.Resampling.LANCZOS)
            # Remove imperceptible alpha tails, preserving all visible details.
            a=im.getchannel('A').point(lambda v:0 if v<3 else v);im.putalpha(a)
            im.paste((0,0,0,0),mask=a.point(lambda v:255 if v==0 else 0))
            box=a.getbbox(); assert box
            assert box[0]>=1 and box[1]>=1 and box[2]<=159 and box[3]<=159, (clip,i,box)
            crop=im.crop(box);w,h=crop.size
            key=hashlib.sha256(im.tobytes()).hexdigest()
            if key in seen:
                rects.append(dict(seen[key]));crops.append(None)
            else:
                rect=dict(x=x,y=height+2,w=w,h=h,ox=box[0],oy=box[1]);seen[key]=rect
                rects.append(rect);crops.append(crop);x+=w+4
            rh=max(rh,h)
            hashes[f'{clip}/{i}']=digest(p)
        rows.append((rects,crops));width=max(width,x);height+=rh+4
        meta['clips'][clip]=dict(row=row,frames=count,fps=fps,loop=loop,rects=rects)
    assert len({r['grade_sha256'] for r in renders.values()})==1,'Mixed rest grades'
    atlas=Image.new('RGBA',(width,height))
    for rects,crops in rows:
        for rect,crop in zip(rects,crops):
            if crop is not None:atlas.paste(crop,(rect['x'],rect['y']))
    for quality in (95,90,85,80,75):
        buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,alpha_quality=100,method=6,exact=True)
        print(f'WebP quality {quality}: {len(buf.getvalue())} bytes',flush=True)
        if len(buf.getvalue())<=200000:break
    else:raise RuntimeError('Cannot fit at quality 75: preserve all frames and report, never lower quality')
    (OUT/'panzer.webp').write_bytes(buf.getvalue())
    (OUT/'panzer.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    (REVIEW/'panzer-pack.json').write_text(json.dumps(dict(bytes=len(buf.getvalue()),quality=quality,alpha_quality=100,frames=40,cell=160,trimmed=True,renders=renders,source_sha256=hashes,atlas_sha256=digest(OUT/'panzer.webp')),indent=2))

def validate():
    meta=json.loads((OUT/'panzer.json').read_text());atlas=Image.open(OUT/'panzer.webp').convert('RGBA')
    report=json.loads((REVIEW/'panzer-pack.json').read_text())
    assert meta['version']==2 and meta['trimmed'] and meta['frame']==FRAME
    assert (OUT/'panzer.webp').stat().st_size<=200000 and report['quality']>=75
    assert report['atlas_sha256']==digest(OUT/'panzer.webp')
    assert len({r['grade_sha256'] for r in report['renders'].values()})==1
    assert next(iter(report['renders'].values()))['grade_sha256']==digest(M/'grade.json')
    occupied=Image.new('L',atlas.size);motion={};restored={}
    for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
        c=meta['clips'][clip]
        assert report['renders'][clip]['blend_sha256']==digest(M/'clips'/f'{clip}.blend'), 'Stale clip master'
        assert report['renders'][clip]==json.loads((M/'renders'/f'e-{clip}'/'render.json').read_text()), 'Stale render metadata'
        assert (c['row'],c['frames'],c['fps'],c['loop'])==(row,count,fps,loop)
        assert len(c['rects'])==count
        restored[clip]=[];seen=set()
        for i,r in enumerate(c['rects']):
            x,y,w,h,ox,oy=(r[k] for k in ('x','y','w','h','ox','oy'))
            assert all(isinstance(v,int) for v in r.values())
            assert x>=2 and y>=2 and x+w<=atlas.width-2 and y+h<=atlas.height-2
            assert 0<=ox and 0<=oy and ox+w<=160 and oy+h<=160
            rectangle=(x,y,w,h)
            if rectangle not in seen:
                assert not occupied.crop((x-1,y-1,x+w+1,y+h+1)).getbbox(),'Overlapping rectangles'
                occupied.paste(255,(x,y,x+w,y+h));seen.add(rectangle)
            im=restore(atlas,r); assert im.getchannel('A').getbbox()
            p=M/'renders'/f'e-{clip}'/f'{i:02}.png'
            assert report['source_sha256'][f'{clip}/{i}']==digest(p),'Stale delivery'
            expected=Image.open(p).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS).getchannel('A').point(lambda v:0 if v<3 else v)
            assert expected.tobytes()==im.getchannel('A').tobytes(), 'Trimmed alpha reconstruction mismatch'
            restored[clip].append(im)
        motion[clip]=any(ImageChops.difference(restored[clip][0],im).getbbox(alpha_only=False) for im in restored[clip][1:]);assert motion[clip]
    assert not ImageChops.multiply(atlas.getchannel('A'),ImageChops.invert(occupied)).getbbox(),'Nontransparent padding'
    assert restored['death'][-1].tobytes()==restored['death'][-2].tobytes(), 'Decoded death must hold exactly'
    terminal=M/'renders/e-death'
    assert Image.open(terminal/'08.png').convert('RGBA').tobytes()==Image.open(terminal/'09.png').convert('RGBA').tobytes()
    result=dict(contract='PASS',bytes=(OUT/'panzer.webp').stat().st_size,quality=report['quality'],frames=40,cell=160,atlas_size=atlas.size,trimmed=True,motion=motion,held_death=True)
    (REVIEW/'panzer-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
    return restored

def review_delivery(restored):
    from PIL import ImageDraw
    source=Image.open('app/src/assets/units/panzer-256.png').convert('RGBA')
    rendered=Image.open(M/'renders/c/three-quarter.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
    decoded=restored['idle'][0].resize((256,256),Image.Resampling.LANCZOS)
    report=json.loads((REVIEW/'panzer-pack.json').read_text())
    sheet=Image.new('RGB',(816,380),(224,215,191));draw=ImageDraw.Draw(sheet)
    for k,(label,im) in enumerate([('Painting',source),('Rest render',rendered),
                                  (f"Decoded 160px atlas, quality {report['quality']}",decoded)]):
        draw.text((8+k*272,10),label,fill=(40,34,27))
        sheet.paste(im,(8+k*272,36),im)
        small=im.resize((64,64),Image.Resampling.LANCZOS)
        sheet.paste(small,(104+k*272,302),small)
    sheet.save(REVIEW/'panzer-g-delivery.png')

if __name__=='__main__':
    if '--validate-only' not in sys.argv:pack()
    review_delivery(validate())
