"""Review, frozen histogram grade, trimmed 160 atlas, validation and driver MP4."""
import argparse, hashlib, io, json, os, subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=ROOT/'masters/gaesatae';R=ROOT/'review/3d-v2';R.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(233,207,160,255);BG=(241,232,215,255)
REF=Image.open('app/src/assets/units/gaesatae-256.png').convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def thumb(im,n=256):return im.convert('RGBA').resize((n,n),Image.Resampling.LANCZOS)
def sheet(images,labels,size=256):
    out=Image.new('RGBA',(size*len(images),size+26),BG);d=ImageDraw.Draw(out)
    for i,(im,label) in enumerate(zip(images,labels)):
        out.alpha_composite(thumb(im,size),(i*size,26));d.text((i*size+6,7),label,fill='#493d2d')
    return out

def raw(stage):
    # Highest completed resolution wins. Never upsample a preview into a master.
    sizes=(int(os.environ['RESOLUTION']),) if 'RESOLUTION' in os.environ else (512,256,128)
    for size in sizes:
        p=M/'renders'/str(size)/stage
        if (p/'render.json').exists():
            meta=json.loads((p/'render.json').read_text())
            paths=[p/f'{i:02}.png' for i in range(len(meta['frames']))]
            assert all(sha(f)==h for f,h in zip(paths,meta['frames'])),f'Incomplete {stage}'
            blend=M/'clips'/f'{stage[2:]}.blend' if stage.startswith('e-') else M/'clips/attack.blend' if stage=='d' else M/('finished-plain.blend' if stage=='b' else 'gaesatae.blend')
            if sha(blend)!=meta['blend_sha256']:continue
            return [Image.open(f).convert('RGBA') for f in paths],meta
    raise FileNotFoundError(stage)

def fit_grade(im):
    # One conservative channel-affine histogram fit; frozen for every animation.
    def stats(src):
        src=thumb(src);mask=src.getchannel('A').point(lambda a:255 if a>200 else 0)
        s=ImageStat.Stat(src.convert('RGB'),mask);return s.mean,s.stddev
    a,sd=stats(im);b,td=stats(REF)
    scales=[max(.85,min(1.15,t/max(s,1))) for s,t in zip(sd,td)]
    offsets=[max(-12,min(12,(bb-aa*ss)*.65)) for aa,bb,ss in zip(a,b,scales)]
    return {'scale':scales,'offset':offsets,'method':'bounded masked RGB mean/std fit; frozen from rest','source_sha256':sha(M/'gaesatae.blend')}
def graded(im,g):
    rgb=im.convert('RGB');lut=[]
    for s,o in zip(g['scale'],g['offset']):lut += [round(max(0,min(255,i*s+o))) for i in range(256)]
    rgb=rgb.point(lut).convert('RGBA');rgb.putalpha(im.getchannel('A'));return rgb

def review(stage,g=None):
    ims,meta=raw(stage)
    ims=[graded(im,g) for im in ims] if g and stage!='b' else ims
    caption=f"Cycles {meta['device']} {meta['resolution']}px / {meta['samples']} samples"
    if stage=='b':
        sheet([REF,ims[0]],['Painting','Plain geometry | '+caption]).save(R/'gaesatae-b-plain.png')
    elif stage=='c':
        sheet([REF,ims[0],thumb(REF,64).resize((256,256)),thumb(ims[0],64).resize((256,256))],['Painting 256','Rest | '+caption,'Painting 64 x4','Rest 64 x4']).save(R/'gaesatae-c-textured-lit.png')
        rendered=thumb(ims[0]);blend=Image.blend(REF,rendered,.5)
        split=REF.copy();split.paste(rendered.crop((128,0,256,256)),(128,0))
        compare=Image.new('RGBA',(1024,372),BG)
        compare.alpha_composite(sheet([REF,rendered,split,blend],['Painting','3D rest | '+caption,'Half split','50/50 crossfade']),(0,0))
        small=sheet([REF,rendered,split,blend],['Source','Rest','Split','50/50'],64)
        compare.alpha_composite(small,(384,282));compare.save(R/'gaesatae-f-restpose-compare.png')
        crops=[];labels=[]
        for name,box in [('head / torc',(118,28,169,81)),('tattooed torso',(103,65,175,126)),('shield',(163,55,213,206)),('boots / stone',(60,185,212,248))]:
            for label,im in [('painting',REF),('3D',thumb(ims[0]))]:
                c=im.crop(box);c=c.resize((round(c.width*min(240/c.width,240/c.height)),round(c.height*min(240/c.width,240/c.height))),Image.Resampling.LANCZOS);pad=Image.new('RGBA',(256,256));pad.alpha_composite(c,((256-c.width)//2,(256-c.height)//2));crops.append(pad);labels.append(name+' '+label)
        sheet(crops,labels).save(R/'gaesatae-c-details.png')
    elif stage=='d':sheet(ims,[f'Attack pose {i}' for i in range(len(ims))]).save(R/'gaesatae-d-rig-poses.png')
    else:
        clip=stage[2:];n,fps,loop=CLIPS[clip]
        sheet(ims,[f'{clip} {i+1}' for i in range(n)]).save(R/f'gaesatae-e-{clip}-strip.png')
        frames=[thumb(im) for im in ims]
        frames[0].save(R/f'gaesatae-e-{clip}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=90,method=6)
    # True 512 outputs are retained as such; only downsample to 256.
    if meta['resolution']>=256:
        for size in (512,256):
            if size>meta['resolution']:continue
            d=M/'masters'/str(size)/stage;d.mkdir(parents=True,exist_ok=True)
            for i,im in enumerate(ims):thumb(im,size).save(d/f'{i:02}.png')
    print('REVIEW_READY',stage,caption)
    return ims,meta

def pack(sets,metas):
    meta={'version':2,'layout':'trimmed-rows','frame':{'w':160,'h':160,'ax':80,'ay':142},'clips':{},'provenance':{'master_sha256':sha(M/'gaesatae.blend'),'renders':metas}}
    rows=[];y=0;allframes={}
    for row,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
        crops=[];rects=[];x=1;rh=0;allframes[name]=[];unique={}
        for im in sets[name]:
            im=im.resize((160,160),Image.Resampling.BICUBIC)
            box=im.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<160 and box[3]<160,(name,'clipped',box)
            crop=im.crop(box);w,h=crop.size;key=hashlib.sha256(im.tobytes()).hexdigest()
            if key in unique:r=dict(unique[key]);crops.append(None)
            else:
                r={'x':x,'y':y+1,'w':w,'h':h,'ox':box[0],'oy':box[1]};unique[key]=r;crops.append(crop);x+=w+2
            rects.append(r);rh=max(rh,h);allframes[name].append(im)
        meta['clips'][name]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects};rows.append((crops,rects));y+=rh+2
    width=max(1+sum(im.width+2 for im in crops if im is not None) for crops,_ in rows);atlas=Image.new('RGBA',(width,y));meta['atlas']={'w':width,'h':y}
    for crops,rects in rows:
        for im,r in zip(crops,rects):
            if im is not None:atlas.alpha_composite(im,(r['x'],r['y']))
    best=None
    for q in (90,85,80,75):
        b=io.BytesIO();atlas.save(b,'WEBP',quality=q,method=6,exact=True)
        if len(b.getvalue())<=200000:best=b.getvalue();meta['quality']=q;break
    assert best is not None,'Atlas exceeds 200 KB at quality 75; do not reduce quality/frame counts'
    out=Path('app/src/assets/units/anim');out.mkdir(parents=True,exist_ok=True)
    (out/'gaesatae.webp').write_bytes(best);meta['bytes']=len(best);meta['atlas_sha256']=sha(out/'gaesatae.webp')
    (out/'gaesatae.json').write_text(json.dumps(meta,indent=2)+'\n')
    validate(out/'gaesatae.webp');return meta

def unpack(path,meta):
    atlas=Image.open(path).convert('RGBA');result={}
    for name,c in meta['clips'].items():
        result[name]=[]
        for r in c['rects']:
            im=Image.new('RGBA',(160,160));im.alpha_composite(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));result[name].append(im)
    return result

def validate(path):
    m=json.loads(path.with_suffix('.json').read_text());assert m['provenance']['master_sha256']==sha(M/'gaesatae.blend'),'Stale atlas master';assert path.stat().st_size<=200000 and m['quality']>=75
    assert sha(path)==m['atlas_sha256'];ims=unpack(path,m);atlas=Image.open(path)
    for name,(count,fps,loop) in CLIPS.items():
        source,render_meta=raw('e-'+name);assert render_meta==m['provenance']['renders'][name],'Stale atlas frames'
        for source_frame,decoded in zip(source,ims[name]):
            alpha=source_frame.resize((160,160),Image.Resampling.BICUBIC).getchannel('A')
            assert ImageChops.difference(alpha,decoded.getchannel('A')).getbbox() is None,'Alpha changed'
        c=m['clips'][name];assert c['frames']==count and len(c['rects'])==count and c['fps']==fps and c['loop']==loop
        for r in c['rects']:
            assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
            assert r['x']>=0 and r['y']>=0 and r['x']+r['w']<=atlas.width and r['y']+r['h']<=atlas.height
        assert any(ImageChops.difference(ims[name][0],f).convert('RGB').getbbox() for f in ims[name][1:]),name+' lacks motion'
    assert ims['death'][-1].tobytes()==ims['death'][-2].tobytes(),'Decoded death must hold exactly'
    assert atlas.size==(m['atlas']['w'],m['atlas']['h'])
    decoded=Image.new('RGBA',(1600,5*186),BG)
    for row,(name,frames) in enumerate(ims.items()):decoded.alpha_composite(sheet(frames,[name+' '+str(i+1) for i in range(len(frames))],160),(0,row*186))
    decoded.save(R/'gaesatae-g-decoded-atlas.png')
    # Also verify the lossless held source frame.
    assert sha(M/'renders'/str(m['provenance']['renders']['death']['resolution'])/'e-death/08.png')==sha(M/'renders'/str(m['provenance']['renders']['death']['resolution'])/'e-death/09.png')
    (M/'validation.json').write_text(json.dumps({'atlas_bytes':path.stat().st_size,'quality':m['quality'],'frames':40,'alpha':True,'rects_and_offsets':True,'motion':True,'lossless_held_death':True,'gpu':all(v['device']=='GPU' for v in m['provenance']['renders'].values())},indent=2)+'\n')
    print('VALIDATED',path.stat().st_size,'bytes, q',m['quality'],', 40 frames')

def movie(path):
    m=json.loads(path.with_suffix('.json').read_text());ims=unpack(path,m);out=R/f"gaesatae-round{os.environ.get('ROUND','1')}.mp4"
    command=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x348','-r','30','-i','-','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)]
    p=subprocess.Popen(command,stdin=subprocess.PIPE)
    for t in range(240):
        canvas=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(canvas)
        for k,(name,c) in enumerate(m['clips'].items()):
            i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1)
            canvas.alpha_composite(ims[name][i].resize((320,320),Image.Resampling.LANCZOS),(k*320,28));d.text((k*320+8,8),name,fill='#493d2d')
        p.stdin.write(canvas.convert('RGB').tobytes())
    p.stdin.close();assert p.wait()==0
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out)]));s=probe['streams'][0]
    assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p' and int(s['nb_frames'])==240
    print('MOVIE_READY',out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage');p.add_argument('--movie',action='store_true');p.add_argument('--validate',action='store_true');a=p.parse_args()
    if a.validate:validate(Path('app/src/assets/units/anim/gaesatae.webp'))
    elif a.stage=='b':review('b')
    else:
        rest,_=raw('c');g=fit_grade(rest[0]);(M/'grade.json').write_text(json.dumps(g,indent=2)+'\n')
        if a.stage:review(a.stage,g)
        else:
            for stage in ('b','c','d'):review(stage,g)
            sets={};metas={}
            for name in CLIPS:sets[name],metas[name]=review('e-'+name,g)
            _,restmeta=raw('c')
            for meta in metas.values():
                assert all(meta[k]==restmeta[k] for k in ('resolution','samples','device','source_sha256')),'Mixed render settings'
            pack(sets,metas)
            if a.movie:movie(Path('app/src/assets/units/anim/gaesatae.webp'))
