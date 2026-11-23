"""Pack all forty frames without changing the relief atlas contract or cadence."""
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HOME = Path.home() / 'LegatumRuns/anim-pilot'
MASTER = HOME / 'masters/spearman-3d'
CLIPS = {'idle': (8,10,True), 'move': (8,12,True), 'attack': (10,14,False), 'hit': (4,12,False), 'death': (10,10,False)}


def clean_alpha(im):
    im=im.copy()
    a=im.getchannel('A').point([round(round(x*31/255)*255/31) for x in range(256)])
    im.putalpha(a)
    im.paste((0,0,0,0),mask=a.point(lambda x:255 if x==0 else 0))
    return im


def main():
    output=ROOT/'app/src/assets/units/anim';output.mkdir(parents=True,exist_ok=True)
    review=HOME/'review';review.mkdir(parents=True,exist_ok=True)
    atlas=Image.new('RGBA',(2560,1280))
    frames={}
    for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
        frames[clip]=[]
        for i in range(n):
            im=Image.open(MASTER/'frames'/clip/f'{i:02}.png').convert('RGBA')
            assert im.size==(256,256)
            frames[clip].append(im)
            atlas.paste(clean_alpha(im),(256*i,256*row))
        frames[clip][0].save(review/f'spearman-3d-{clip}.webp',save_all=True,append_images=frames[clip][1:],duration=[round(1000/fps)]*(n-1)+[round(1000/fps) if loop else 850],loop=0,quality=85,method=6)
    attempts=[]
    for q in (80,70,60):
        stream=io.BytesIO();atlas.save(stream,format='WEBP',quality=q,method=6)
        data=stream.getvalue();attempts.append({'quality':q,'bytes':len(data)})
        if len(data)<=200_000:break
    else:raise RuntimeError(f'All forty frames exceed the budget: {attempts}; existing atlas not replaced')
    meta={'frame':{'w':256,'h':256,'ax':127,'ay':221},'clips':{c:dict(row=r,frames=n,fps=fps,loop=loop) for r,(c,(n,fps,loop)) in enumerate(CLIPS.items())}}
    temp=output/'.spearman-3d.webp.tmp';temp.write_bytes(data);temp.replace(output/'spearman-3d.webp')
    (output/'spearman-3d.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    report={'bytes':len(data),'quality':q,'frames':40,'attempts':attempts}
    (review/'spearman-3d-pack.json').write_text(json.dumps(report,indent=2)+'\n')
    # Review the DECODED delivery alongside the actual relief atlas, at equal sizes.
    delivered=Image.open(output/'spearman-3d.webp').convert('RGBA')
    relief=Image.open(output/'spearman.webp').convert('RGBA')
    rm=json.loads((output/'spearman.json').read_text())
    painting=Image.open(ROOT/'app/src/assets/units/spearman-256.png').convert('RGBA')
    selected={'idle':[0,2],'move':[2,6],'attack':[3,5],'hit':[1,2],'death':[4,9]}
    sheet=Image.new('RGB',(5*264,5*352),'#f2ead8');d=ImageDraw.Draw(sheet)
    for row,(clip,indices) in enumerate(selected.items()):
        y=row*352;d.text((8,y+5),f'{clip.upper()} | Painting / Relief / 3D / Relief / 3D | 256 px, with 64 px below',fill='#30251b')
        images=[('Painting',painting)]
        for i in indices:
            m=rm['clips'][clip];j=round(i/(CLIPS[clip][0]-1)*(m['frames']-1))
            images.append((f'Relief {j}',relief.crop((j*256,m['row']*256,(j+1)*256,(m['row']+1)*256))))
            images.append((f'3D {i}',delivered.crop((i*256,row*256,(i+1)*256,(row+1)*256))))
        for col,(label,im) in enumerate(images):
            x=col*264;yy=y+24
            d.rectangle((x,yy,x+263,yy+319),fill='#ded4bd')
            sheet.paste(im,(x+4,yy),im)
            tiny=im.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(tiny,(x+100,yy+254),tiny)
            d.text((x+4,yy+259),label,fill='#201a14')
    sheet.save(review/'spearman-3d-vs-relief.png')
    print(json.dumps(report))


if __name__=='__main__':main()
