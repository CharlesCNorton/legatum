"""Review sheets, one stable colour grade, trimmed atlas, checks and MP4.

Trim format v2: frame is the untrimmed logical 160 px canvas. Each clip has
rects [{x,y,w,h,ox,oy}]; crop atlas (x,y,w,h), then paste at (ox,oy). The anchor
remains in the logical canvas. Never use the legacy row stride for these files.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=ROOT/'masters/war-elephant';R=ROOT/'review/3d-v2'
OUT=Path('app/src/assets/units/anim');SLUG='war-elephant'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(240,232,214,255)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path,size=None):
    im=Image.open(path).convert('RGBA')
    return im.resize((size,size),Image.Resampling.LANCZOS) if size else im


def grade_lut(ref,render):
    """One restrained histogram transfer, never independently fit each frame."""
    def quantiles(im,ch):
        hist=im.getchannel(ch).histogram(mask=im.getchannel('A').point(lambda a:255 if a>240 else 0))
        total=sum(hist);out=[];acc=0;idx=0
        for k in range(17):
            target=total*k/16
            while idx<255 and acc+hist[idx]<target:acc+=hist[idx];idx+=1
            out.append(idx)
        return out
    tables=[]
    for ch in ['R','G','B']:
        a,b=quantiles(render,ch),quantiles(ref,ch);lut=[]
        for value in range(256):
            k=next((j for j in range(15) if value<a[j+1]),15)
            f=min(1,max(0,(value-a[k])/max(1,a[k+1]-a[k])))
            mapped=b[k]+f*(b[k+1]-b[k])
            lut.append(round(.70*value+.30*mapped))
        tables.append(lut)
    return tables


def graded(im):
    tables=json.loads((M/'grade.json').read_text())['lut']
    return Image.merge('RGBA',tuple(im.getchannel(ch).point(lut) for ch,lut in zip('RGB',tables))+(im.getchannel('A'),))


def sheet(images,labels,path,cell=256):
    out=Image.new('RGBA',(cell*len(images),cell+28),CREAM)
    d=ImageDraw.Draw(out)
    for i,(im,label) in enumerate(zip(images,labels)):
        out.alpha_composite(im.resize((cell,cell),Image.Resampling.LANCZOS),(i*cell,28))
        d.text((i*cell+8,8),label,fill=(60,48,32,255))
    out.convert('RGB').save(path)


def review(stage):
    folder=M/'renders'/stage
    report=json.loads((folder/'render.json').read_text())
    images=[rgba(folder/f['path']) for f in report['frames']]
    ref=rgba('app/src/assets/units/war-elephant-256.png',images[0].width)
    if stage=='c':
        (M/'grade.json').write_text(json.dumps({'lut':grade_lut(ref,images[0]),'rest_sha256':sha(folder/'00.png')}))
    if stage!='b':images=[graded(im) for im in images]
    gallery=folder/'256';gallery.mkdir(exist_ok=True)
    for i,im in enumerate(images):im.resize((256,256),Image.Resampling.LANCZOS).save(gallery/f'{i:02}.png')
    if stage=='b':
        sheet([ref]+images,['Painting','Three-quarter','Side','Front'],R/f'{SLUG}-b-plain.png')
    elif stage=='c':
        label=f'3D {report["device"]} / {report["resolution"]} px'
        sheet([ref,images[0]],['Painting',label],R/f'{SLUG}-c-textured-lit.png')
        detail_ref=rgba(ROOT/'assets/war-elephant/painting-aligned.png',images[0].width)
        sheet([detail_ref,images[0]],['Painting',f'3D {report["resolution"]} px {report["device"]}'],R/f'{SLUG}-c-details.png',min(512,images[0].width))
        size=ref.width;half=size//2
        split=ref.copy();split.paste(images[0].crop((half,0,size,size)),(half,0))
        sheet([ref,images[0],split,Image.blend(ref,images[0],.5)],
              ['Painting',label,'Half split','50% crossfade'],R/f'{SLUG}-f-restpose-compare.png')
        sheet([ref,images[0]],['Painting','3D'],R/f'{SLUG}-64-compare.png',64)
    elif stage=='d':sheet(images,['Anticipation','Brace','Strike','Recover'],R/f'{SLUG}-d-rig-poses.png')
    elif stage=='g':
        # Two complete views of the same move cycle, not proxy foot markers.
        canvas=Image.new('RGB',(8*256,2*284),CREAM[:3])
        for row,label in enumerate(['Top cutaway; travel right','Front cutaway; travel toward viewer']):
            path=folder/f'view-{row}.png'
            sheet(images[row*8:(row+1)*8],[f'{label} / {i}' for i in range(8)],path)
            canvas.paste(Image.open(path),(0,row*284))
        canvas.save(R/f'{SLUG}-g-feet-check.png')
    else:
        sheet(images,[str(i) for i in range(len(images))],R/f'{SLUG}-{stage}-strip.png')
        clip=stage[2:];count,fps,loop=CLIPS[clip]
        ims=[im.resize((256,256),Image.Resampling.LANCZOS) for im in images]
        ims[0].save(R/f'{SLUG}-{stage}.webp',save_all=True,append_images=ims[1:],duration=round(1000/fps),loop=0,quality=90)
    report['grade_sha256']=sha(M/'grade.json') if stage!='b' else None
    (folder/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('REVIEW',stage)


def token(raw):
    # Premultiplied bicubic reduction retains smooth coverage without Lanczos
    # ringing. WebP alpha stays full 8-bit; no palette or alpha quantization.
    return graded(raw.resize((160,160),Image.Resampling.BICUBIC))


def masters():
    """Require real GPU512 evidence; never upscale a preview into a master."""
    for stage in ['b','c','d','g']+['e-'+c for c in CLIPS]:
        folder=M/'renders'/stage
        report=json.loads((folder/'review.json').read_text())
        assert report['resolution']==512 and report['device']=='GPU',(stage,'Not a GPU512 master')
        assert report['engine'] in ['CYCLES','BLENDER_EEVEE']
        blend=M/('plain.blend' if stage=='b' else 'war-elephant.blend')
        if stage=='d':blend=M/'clips/attack/attack.blend'
        if stage=='g':blend=M/'clips/move/move.blend'
        if stage.startswith('e-'):blend=M/'clips'/stage[2:]/(stage[2:]+'.blend')
        assert report['blend_sha256']==sha(blend),(stage,'Stale blend')
        if stage!='b':assert report['grade_sha256']==sha(M/'grade.json')
        for size in [512,256]:(M/str(size)/stage).mkdir(parents=True,exist_ok=True)
        for frame in report['frames']:
            path=folder/frame['path'];im=rgba(path)
            assert im.size==(512,512) and sha(path)==frame['sha256']
            if stage!='b':im=graded(im)
            im.save(M/'512'/stage/path.name)
            im.resize((256,256),Image.Resampling.LANCZOS).save(M/'256'/stage/path.name)
    print('MASTERS verified GPU512 and exported 512/256')


def pack():
    preview='--preview' in sys.argv
    assert json.loads((M/'grade.json').read_text())['rest_sha256']==sha(M/'renders/c/00.png'),'Stale rest grade'
    OUT.mkdir(parents=True,exist_ok=True)
    meta={'version':2,'layout':'trimmed','frame':{'w':160,'h':160,'ax':79,'ay':138},'clips':{}}
    atlas=Image.new('RGBA',(1600,1000));y=2;source_hashes={};sources={}
    for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
        folder=M/'renders'/('e-'+clip)
        info=json.loads((folder/'review.json').read_text())
        blend=M/'clips'/clip/(clip+'.blend')
        assert info['blend_sha256']==sha(blend),f'{clip}: stale render'
        assert info['grade_sha256']==sha(M/'grade.json'),f'{clip}: stale grade'
        assert json.loads((blend.parent/'clip.json').read_text())['source_master_sha256']==sha(M/'war-elephant.blend')
        if not preview:
            assert info['resolution']==512 and info['device']=='GPU','Final delivery requires GPU512; use --preview for CPU review'
        rest=json.loads((M/'renders/c/review.json').read_text())
        for key in ['engine','device','resolution','samples']:
            assert info[key]==rest[key],f'{clip}: rest and clip {key} differ'
        sources[clip]=info
        x=2;maxh=0;rects=[];seen={}
        for i in range(n):
            source=folder/f'{i:02}.png'
            assert sha(source)==info['frames'][i]['sha256'],'Changed raw frame'
            source_hashes[f'{clip}/{i}']=sha(source)
            raw=rgba(source)
            im=token(raw)
            alpha=im.getchannel('A')
            im.paste((0,0,0,0),mask=alpha.point(lambda a:255 if a==0 else 0))
            key=hashlib.sha256(im.tobytes()).hexdigest()
            if key in seen:
                rects.append(seen[key]);continue
            bbox=alpha.getbbox();assert bbox
            ox,oy,right,bottom=bbox;w,h=right-ox,bottom-oy
            assert x+w<1600
            atlas.paste(im.crop(bbox),(x,y))
            rect=dict(x=x,y=y,w=w,h=h,ox=ox,oy=oy)
            rects.append(rect);seen[key]=rect
            x+=w+4;maxh=max(maxh,h)
        meta['clips'][clip]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':rects}
        y+=maxh+4
    atlas=atlas.crop((0,0,1600,y))
    for quality in [90,85,80,75]:
        buff=io.BytesIO();atlas.save(buff,format='WEBP',quality=quality,method=6,exact=True)
        if buff.tell()<=200000:break
    else:raise RuntimeError('Atlas exceeds 200 KB at quality 75; do not lower quality or drop frames')
    (OUT/f'{SLUG}.webp').write_bytes(buff.getvalue())
    (OUT/f'{SLUG}.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    report={'bytes':buff.tell(),'quality':quality,'frames':40,'logical_size':160,'preview':preview,
            'atlas_sha256':sha(OUT/f'{SLUG}.webp'),'metadata_sha256':sha(OUT/f'{SLUG}.json'),
            'source_hashes':source_hashes,'renders':sources}
    (R/f'{SLUG}-pack.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PACKED',buff.tell(),'bytes; quality',quality,'40 frames')


def unpack(meta,atlas,clip):
    frames=[]
    for r in meta['clips'][clip]['rects']:
        im=Image.new('RGBA',(160,160))
        im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']))
        frames.append(im)
    return frames


def validate():
    (R/f'{SLUG}-validation.json').unlink(missing_ok=True)
    path=OUT/f'{SLUG}.webp';atlas=rgba(path);meta=json.loads(path.with_suffix('.json').read_text())
    report=json.loads((R/f'{SLUG}-pack.json').read_text())
    assert path.stat().st_size<=200000 and report['quality']>=75
    assert sha(path)==report['atlas_sha256'] and sha(path.with_suffix('.json'))==report['metadata_sha256']
    assert meta['version']==2 and meta['layout']=='trimmed'
    assert set(meta['clips'])==set(CLIPS)
    result={}
    for clip,(count,fps,loop) in CLIPS.items():
        c=meta['clips'][clip]
        blend=M/'clips'/clip/(clip+'.blend')
        info=report['renders'][clip]
        assert info['blend_sha256']==sha(blend),f'{clip}: stale atlas render'
        assert info['grade_sha256']==sha(M/'grade.json'),f'{clip}: stale atlas grade'
        assert json.loads((blend.parent/'clip.json').read_text())['source_master_sha256']==sha(M/'war-elephant.blend')
        for i in range(count):
            assert report['source_hashes'][f'{clip}/{i}']==sha(M/'renders'/('e-'+clip)/f'{i:02}.png')
        assert (c['frames'],c['fps'],c['loop'])==(count,fps,loop)
        assert len(c['rects'])==count
        for r in c['rects']:
            assert min(r.values())>=0
            assert r['x']+r['w']<=atlas.width and r['y']+r['h']<=atlas.height
            assert r['ox']+r['w']<=160 and r['oy']+r['h']<=160
        frames=unpack(meta,atlas,clip)
        for i,im in enumerate(frames):
            a=im.getchannel('A');bounds=a.getbbox();assert bounds
            expected=token(rgba(M/'renders'/('e-'+clip)/f'{i:02}.png')).getchannel('A')
            assert a.tobytes()==expected.tobytes(),(clip,i,'Alpha reconstruction mismatch')
            assert a.getextrema()==(0,255)
            assert min(bounds[0],bounds[1],160-bounds[2],160-bounds[3])>=2,(clip,bounds,'clipped')
        hashes=[hashlib.sha256(im.tobytes()).hexdigest() for im in frames]
        assert len(set(hashes))>=3,(clip,'no motion')
        if clip=='death':
            # Reuse identical rectangles so the decoded held pose is exact as well.
            assert hashes[-1]==hashes[-2]
            assert sha(M/'renders/e-death/08.png')==sha(M/'renders/e-death/09.png')
        result[clip]={'frames':count,'distinct_decoded_frames':len(set(hashes)),'alpha_and_bounds':'pass'}
    result['bytes']=path.stat().st_size;result['quality']=report['quality']
    (R/f'{SLUG}-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('VALIDATED',json.dumps(result))


def video():
    path=OUT/f'{SLUG}.webp';atlas=rgba(path);meta=json.loads(path.with_suffix('.json').read_text())
    frames={c:[im.resize((320,320),Image.Resampling.LANCZOS) for im in unpack(meta,atlas,c)] for c in CLIPS}
    out=R/f'{SLUG}-round{os.environ.get("ROUND","2")}.mp4'
    with tempfile.TemporaryDirectory(prefix='war-elephant-',dir=ROOT/'tmp') as tmp:
        for tick in range(240):
            canvas=Image.new('RGBA',(1600,348),CREAM);draw=ImageDraw.Draw(canvas)
            for k,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
                frame=int(tick/30*fps)%n if loop else min(int((tick%60)/30*fps),n-1)
                canvas.alpha_composite(frames[clip][frame],(k*320,28))
                draw.text((k*320+8,8),clip,fill=(60,48,32,255))
            canvas.convert('RGB').save(Path(tmp)/f'{tick:04}.png')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',f'{tmp}/%04d.png',
                        '-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
        '-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(out)]))['streams'][0]
    assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'])==('h264','yuv420p',1600,348)
    assert int(probe['nb_frames'])==240 and abs(float(probe['duration'])-8)<.01
    (R/f'{SLUG}-video.json').write_text(json.dumps(probe,indent=2)+'\n')
    print('VIDEO verified',out)


if __name__=='__main__':
    command=sys.argv[1]
    if command=='review':review(sys.argv[2])
    else:{'pack':pack,'validate':validate,'video':video,'masters':masters}[command]()
