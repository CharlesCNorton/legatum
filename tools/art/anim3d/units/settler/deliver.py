"""160 px logical cells, cropped top-left storage with explicit offsets; quality >=75."""
from pathlib import Path
import os,sys,json,hashlib,io
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/settler';OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CELL=160

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
    master=sha(M/'settler.blend');grade=sha(M/'grade.json');records={}
    for clip,(count,fps,loop) in CLIPS.items():
        manifest=json.loads((M/'renders'/('e-'+clip)/'render.json').read_text());meta=json.loads((M/'clips'/f'{clip}.json').read_text())
        assert manifest['master_sha256']==meta['source_sha256']==master,(clip,'stale master')
        assert manifest['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),(clip,'stale clip')
        assert manifest['grade_sha256']==grade,(clip,'stale grade')
        assert manifest['resolution']>=512,(clip,'512 master required')
        paths=sorted((M/'frames-256'/('e-'+clip)).glob('*.png'));masters=sorted((M/'frames-512'/('e-'+clip)).glob('*.png'));assert len(paths)==len(masters)==count
        for i,path in enumerate(sorted((M/'renders'/('e-'+clip)/'raw').glob('*.png'))):assert sha(path)==manifest['frames'][f'{i:02}'],(clip,'changed raw frame')
        records[clip]={'manifest':manifest,'frames_256':{p.name:sha(p) for p in paths},'frames_512':{p.name:sha(p) for p in masters}}
    return records

def pack():
    records=inputs();atlas=Image.new('RGBA',(1600,800));metadata={'version':2,'frame':{'w':160,'h':160,'ax':79,'ay':138},'clips':{}}
    for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
        trim=[]
        for i in range(count):
            im=Image.open(M/'frames-256'/('e-'+clip)/f'{i:02}.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
            alpha=im.getchannel('A').point(lambda a:0 if a<5 else round(a/17)*17);im.putalpha(alpha);box=alpha.getbbox();assert box
            l,t,r,b=box;crop=im.crop(box);atlas.paste(crop,(i*CELL,row*CELL));trim.append({'x':i*CELL,'y':row*CELL,'w':r-l,'h':b-t,'dx':l,'dy':t})
        metadata['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'trim':trim}
    trials=[]
    for q in [90,85,80,75]:
        buffer=io.BytesIO();atlas.save(buffer,format='WEBP',quality=q,method=6,exact=True);data=buffer.getvalue();trials.append({'quality':q,'bytes':len(data)})
        if len(data)<=200000:break
    assert len(data)<=200000,f'Atlas exceeds 200 KB at quality 75: {trials}'
    (OUT/'settler.webp').write_bytes(data);(OUT/'settler.json').write_text(json.dumps(metadata,separators=(',',':'))+'\n')
    (M/'pack.json').write_text(json.dumps({'bytes':len(data),'quality':q,'trials':trials,'atlas_sha256':sha(OUT/'settler.webp'),'json_sha256':sha(OUT/'settler.json'),'inputs':records,'status':'Round-1 CPU candidate, not art approval'},indent=2))
    validate()

def validate():
    records=inputs();metadata=json.loads((OUT/'settler.json').read_text());report=json.loads((M/'pack.json').read_text());assert records==report['inputs'],'Frames changed since pack'
    path=OUT/'settler.webp';assert sha(path)==report['atlas_sha256'];assert sha(OUT/'settler.json')==report['json_sha256'];assert path.stat().st_size<=200000 and report['quality']>=75
    atlas=Image.open(path).convert('RGBA');assert atlas.size==(1600,800);assert metadata['frame']=={'w':160,'h':160,'ax':79,'ay':138};assert atlas.getchannel('A').getextrema()==(0,255)
    result={};all_restored={}
    for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
        c=metadata['clips'][clip];assert c['row']==row and c['frames']==count and c['fps']==fps and c['loop']==loop and len(c['trim'])==count
        restored=[]
        for i,t in enumerate(c['trim']):
            assert t['x']==i*160 and t['y']==row*160
            assert 0<=t['dx']<160 and 0<=t['dy']<160 and 0<t['w']<=160-t['dx'] and 0<t['h']<=160-t['dy']
            im=Image.new('RGBA',(160,160));im.paste(atlas.crop((t['x'],t['y'],t['x']+t['w'],t['y']+t['h'])),(t['dx'],t['dy']));restored.append(im)
            unframed=Image.open(M/'renders'/('e-'+clip)/'raw'/f'{i:02}.png').convert('RGBA');raw_box=unframed.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()
            assert raw_box and raw_box[0]>0 and raw_box[1]>0 and raw_box[2]<unframed.width and raw_box[3]<unframed.height,(clip,i,'raw render clipped',raw_box)
            raw=Image.open(M/'frames-256'/('e-'+clip)/f'{i:02}.png').convert('RGBA');box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<256 and box[3]<256,(clip,i,'clipped',box)
            # Cropped storage must have no nontransparent payload outside its declared extent.
            cell=atlas.crop((i*160,row*160,(i+1)*160,(row+1)*160));assert cell.getchannel('A').getbbox()==(0,0,t['w'],t['h'])
        for i in range(count,10):assert atlas.crop((i*160,row*160,(i+1)*160,(row+1)*160)).getchannel('A').getbbox() is None
        assert any(restored[0].tobytes()!=im.tobytes() for im in restored[1:]),(clip,'decoded static')
        if clip=='death':assert restored[-1].tobytes()==restored[-2].tobytes(),'Decoded death hold differs'
        preview=Image.open(R/'review/3d-v2'/f'settler-e-{clip}.webp');assert preview.size==(256,256)
        duration=0
        for frame in range(preview.n_frames):preview.seek(frame);preview.load();duration+=preview.info.get('duration',0)
        assert duration==count*round(1000/fps),(clip,'preview timing',duration)
        result[clip]={'frames':count,'trim_offsets':True,'transparent_margins':True,'preview_duration_ms':duration};all_restored[clip]=restored
    result.update(bytes=path.stat().st_size,quality=report['quality'],masters_512=40,masters_256=40,hashes=True)
    (M/'validation.json').write_text(json.dumps(result,indent=2))
    print('VALIDATE_PASS',json.dumps(result))
    # Evidence decoded from the actual compressed atlas, with offsets restored.
    ims=[]
    for values in all_restored.values():ims.extend(values)
    sheet=Image.new('RGB',(1600,800),(224,215,191))
    for row,(clip,values) in enumerate(all_restored.items()):
        for i,im in enumerate(values):sheet.paste(im,(i*160,row*160),im)
    sheet.save(R/'review/3d-v2/settler-atlas-decoded.png')
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='validate':validate()
    else:pack()
