"""Review, frozen histogram grade, true-size masters, trimmed atlas, validation/video."""
import hashlib,io,json,os,sys,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/landship';REV=R/'review/3d-v2';OUT=Path('app/src/assets/units/anim');UNIT=Path(__file__).parent
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(233,207,160,255)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def log(s):
    with (REV/'landship-log.md').open('a') as f:f.write(s+'\n')
def read(p,size=256):return Image.open(p).convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
def sheet(images,labels,path,size=256):
    canvas=Image.new('RGBA',(len(images)*size,size+30),CREAM);d=ImageDraw.Draw(canvas)
    for i,(im,label) in enumerate(zip(images,labels)):
        canvas.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS),(i*size,30));d.text((i*size+6,8),label,fill=(48,34,22))
    canvas.convert('RGB').save(path)
def quantiles(im):
    opaque=im.getchannel('A').point(lambda a:255 if a>230 else 0)
    out=[]
    for channel in im.convert('RGB').split():
        h=channel.histogram(mask=opaque);n=sum(h);vals=[]
        for frac in (.1,.5,.9):
            total=0
            for x,v in enumerate(h):
                total+=v
                if total>=n*frac:vals.append(x);break
        out.append(vals)
    return out
def grade(stage):
    folder=M/'renders'/stage;receipt=json.loads((folder/'render.json').read_text())
    raw=M/'renders/ungraded'/stage;raw.mkdir(parents=True,exist_ok=True)
    for p in folder.glob('*.png'):(raw/p.name).write_bytes(p.read_bytes())
    if stage=='c':
        ref=quantiles(read(Path('app/src/assets/units/landship-256.png')));src=quantiles(read(raw/'hero.png'))
        tables=[]
        for a,b in zip(src,ref):
            pairs=[(0,0)]+[(x,max(0,min(255,x+max(-18,min(18,y-x))))) for x,y in zip(a,b)]+[(255,255)]
            table=[]
            for x in range(256):
                j=next((j for j in range(4) if x<=pairs[j+1][0]),3);x0,y0=pairs[j];x1,y1=pairs[j+1];table.append(round(y0+(y1-y0)*(x-x0)/max(1,x1-x0)))
            tables.append(table)
        (M/'grade.json').write_text(json.dumps({'source_quantiles':src,'painting_quantiles':ref,'tables':tables,'max_adjustment':18},indent=2))
    if not (M/'grade.json').exists():raise RuntimeError('Render c before other painted stages')
    tables=json.loads((M/'grade.json').read_text())['tables']
    for p in raw.glob('*.png'):
        im=Image.open(p).convert('RGBA');channels=im.split();im=Image.merge('RGBA',tuple(channels[i].point(tables[i]) for i in range(3))+(channels[3],));im.save(folder/p.name)
        for size in (512,256):
            if im.width<size:continue # never fabricate higher resolution masters
            target=M/str(size)/stage;target.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(target/p.name)
    receipt['grade_sha256']=digest(M/'grade.json');receipt['frame_sha256']={p.name:digest(p) for p in folder.glob('*.png')};(folder/'render.json').write_text(json.dumps(receipt,indent=2))
def review(stage):
    folder=M/'renders'/stage
    if stage not in ('b','g'):grade(stage)
    painting=read(Path('app/src/assets/units/landship-256.png'))
    if stage=='b':
        sheet([painting]+[read(folder/f'{n}.png') for n in ('hero','front','side')],['Painting','Plain hero','Plain front','Plain side'],REV/'landship-b-plain.png')
    elif stage=='c':
        hero=read(folder/'hero.png');sheet([painting,hero],['Painting','Textured / lit'],REV/'landship-c-textured-lit.png')
        sheet([painting,hero,Image.blend(painting,hero,.5)],['Painting','3D rest','50/50 crossfade'],REV/'landship-f-restpose-compare.png')
        # Details are actual 256/512 pixels enlarged for inspection, not fabricated detail.
        crops=[(57,87,127,145),(138,95,198,166),(24,151,159,187)]
        ims=[];labels=[]
        for name,box in zip(('Sponson','Track nose','Lower armour'),crops):
            ims.extend([painting.crop(box),hero.crop(box)]);labels.extend([name+' painting',name+' 3D'])
        sheet(ims,labels,REV/'landship-c-details.png',192)
        small=Image.new('RGBA',(3*96,96),CREAM)
        for i,im in enumerate((painting,hero,Image.blend(painting,hero,.5))):small.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*96+16,16))
        small.convert('RGB').save(REV/'landship-f-restpose-64.png')
    elif stage=='d':sheet([read(p) for p in sorted(folder.glob('*.png'))],['Ready','Fire preparation','Recoil','Recovered'],REV/'landship-d-rig-poses.png')
    elif stage=='g':
        canvas=Image.new('RGBA',(8*160,2*190),CREAM);d=ImageDraw.Draw(canvas)
        for row,view in enumerate(('top','front')):
            for i in range(8):canvas.alpha_composite(read(folder/f'{view}-{i+1:02}.png',160),(160*i,190*row+25))
            d.text((5,row*190+6),view+' — +X travel, track contact cycle (no human feet)',fill=(40,30,20))
        canvas.convert('RGB').save(REV/'landship-g-feet-check.png')
    elif stage.startswith('e-'):
        name=stage[2:];count,fps,_=CLIPS[name];ims=[read(folder/f'{i:02}.png') for i in range(count)]
        sheet(ims,[f'{name} {i+1}' for i in range(count)],REV/f'landship-e-{name}-strip.png')
        ims[0].save(REV/f'landship-e-{name}.webp',save_all=True,append_images=ims[1:],duration=round(1000/fps),loop=0,quality=88,method=6)
    log(f'{stage}: review saved immediately; '+(folder/'render.json').read_text().replace('\n',' ')[:220])
def restore(atlas,r):
    im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));return im
def pack():
    meta={'version':2,'trimmed':True,'frame':{'w':160,'h':160,'ax':77.5,'ay':119.375},'clips':{}};rows=[];y=2;width=0;receipts={};sourcehash={}
    for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
        folder=M/'renders'/f'e-{clip}';receipt=json.loads((folder/'render.json').read_text());assert receipt['resolution']>=256
        assert receipt['blend_sha256']==digest(M/'clips'/f'{clip}.blend');assert receipt['grade_sha256']==digest(M/'grade.json');receipts[clip]=receipt
        x=2;rh=0;rects=[];crops=[];seen={}
        for i in range(count):
            p=folder/f'{i:02}.png';assert receipt['frame_sha256'][p.name]==digest(p);sourcehash[f'{clip}/{i}']=digest(p)
            im=read(p,160);a=im.getchannel('A').point(lambda v:0 if v<3 else v);im.putalpha(a);box=a.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<160 and box[3]<160,(clip,i,box)
            im.paste((0,0,0,0),mask=a.point(lambda v:255 if v==0 else 0));key=hashlib.sha256(im.tobytes()).hexdigest()
            if key in seen:r=dict(seen[key]);crop=None
            else:
                crop=im.crop(box);w,h=crop.size;r=dict(x=x,y=y,w=w,h=h,ox=box[0],oy=box[1]);seen[key]=r;x+=w+4;rh=max(rh,h)
            rects.append(r);crops.append(crop)
        rows.append((rects,crops));width=max(width,x);y+=rh+4;meta['clips'][clip]=dict(row=row,frames=count,fps=fps,loop=loop,rects=rects)
    atlas=Image.new('RGBA',(width,y))
    for rects,crops in rows:
        for r,crop in zip(rects,crops):
            if crop is not None:atlas.paste(crop,(r['x'],r['y']))
    for q in (95,90,85,80,75):
        buffer=io.BytesIO();atlas.save(buffer,format='WEBP',quality=q,alpha_quality=100,method=6,exact=True)
        if len(buffer.getvalue())<=200000:break
    else:raise RuntimeError('Atlas exceeds 200KB at quality75; no reduced quality or frame removal allowed')
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'landship.webp').write_bytes(buffer.getvalue());(OUT/'landship.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    report={'quality':q,'bytes':len(buffer.getvalue()),'renders':receipts,'source_sha256':sourcehash,'atlas_sha256':digest(OUT/'landship.webp'),'grade_sha256':digest(M/'grade.json')};(REV/'landship-pack.json').write_text(json.dumps(report,indent=2));validate()
def validate():
    meta=json.loads((OUT/'landship.json').read_text());report=json.loads((REV/'landship-pack.json').read_text());atlas=Image.open(OUT/'landship.webp').convert('RGBA');occupied=Image.new('L',atlas.size);restored={}
    assert report['bytes']<=200000 and report['quality']>=75;assert report['atlas_sha256']==digest(OUT/'landship.webp');assert report['grade_sha256']==digest(M/'grade.json')
    assert meta['version']==2 and meta['trimmed'] and meta['frame']['w']==meta['frame']['h']==160
    for row,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
        c=meta['clips'][name];assert (c['frames'],c['fps'],c['loop'],c['row'])==(count,fps,loop,row);assert len(c['rects'])==count;restored[name]=[];seen=set()
        receipt=report['renders'][name];assert receipt==json.loads((M/'renders'/f'e-{name}'/'render.json').read_text());assert receipt['blend_sha256']==digest(M/'clips'/f'{name}.blend')
        for i,r in enumerate(c['rects']):
            assert all(isinstance(v,int) for v in r.values());x,y,w,h,ox,oy=[r[k] for k in ('x','y','w','h','ox','oy')];assert x>=2 and y>=2 and x+w<=atlas.width-2 and y+h<=atlas.height-2;assert ox>=0 and oy>=0 and ox+w<=160 and oy+h<=160
            key=(x,y,w,h)
            if key not in seen:assert not occupied.crop((x-1,y-1,x+w+1,y+h+1)).getbbox();occupied.paste(255,(x,y,x+w,y+h));seen.add(key)
            im=restore(atlas,r);p=M/'renders'/f'e-{name}'/f'{i:02}.png';assert report['source_sha256'][f'{name}/{i}']==digest(p)
            expected=read(p,160).getchannel('A').point(lambda v:0 if v<3 else v);assert im.getchannel('A').tobytes()==expected.tobytes();restored[name].append(im)
        assert any(ImageChops.difference(restored[name][0],im).getbbox(alpha_only=False) for im in restored[name][1:]),name+' has no motion'
    assert restored['death'][-1].tobytes()==restored['death'][-2].tobytes();assert not ImageChops.multiply(atlas.getchannel('A'),ImageChops.invert(occupied)).getbbox()
    result={'contract':'PASS','frames':40,'quality':report['quality'],'bytes':report['bytes'],'atlas_size':atlas.size,'alpha_reconstruction':'exact','held_death':True,'art_approval':False};(REV/'landship-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return restored

def video():
    frames={n:[im.resize((320,320),Image.Resampling.LANCZOS) for im in ims] for n,ims in validate().items()};label=os.environ.get('ROUND','1-cpu');assert all(c.isalnum() or c in '-_' for c in label);path=REV/f'landship-round{label}.mp4'
    p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x348','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
    try:
        for t in range(240):
            im=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(im)
            for j,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
                i=int(t/30*fps)%count if loop else min(int((t%60)/30*fps),count-1);im.alpha_composite(frames[name][i],(j*320,28));d.text((j*320+8,8),name,fill=(45,32,20))
            p.stdin.write(im.convert('RGB').tobytes())
        p.stdin.close();assert p.wait()==0
    except BaseException:p.kill();p.wait();raise
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(path)]))['streams'][0]
    assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'],int(probe['nb_frames']),float(probe['duration']))==('h264','yuv420p',1600,348,240,8)
    path.with_suffix('.json').write_text(json.dumps(probe,indent=2));print('VIDEO PASS',path)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','0.4','-i',str(path),'-frames:v','1',str(REV/f'landship-round{label}-video-check.png')],check=True)
if __name__=='__main__':
    if sys.argv[1]=='review':review(sys.argv[2])
    elif sys.argv[1]=='pack':pack()
    elif sys.argv[1]=='validate':validate()
    elif sys.argv[1]=='video':video()
