"""Source registration and per-material painting extension; no synthetic geometry."""
from pathlib import Path
import os,json,hashlib
from PIL import Image,ImageDraw,ImageFilter
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/settler'
im=Image.open(A/'painting-source.png').convert('RGBA');box=im.getchannel('A').getbbox();fig=im.crop(box);k=928/fig.height;fig=fig.resize((round(fig.width*k),928),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(1024,1024));canvas.alpha_composite(fig,((1024-fig.width)//2,48));canvas.save(A/'projection.png')
# Expand material regions into nearby unseen coordinates to avoid painting a hand on cloth.
regions={
'ivory':[(112,66),(136,69),(153,86),(155,99),(141,105),(128,99),(115,92),(104,162),(99,188),(115,198),(144,194),(148,185),(136,155),(122,135),(111,166)],
'olive':[(111,94),(146,99),(150,136),(168,182),(153,177),(131,158),(117,139),(110,121)],
'rust':[(110,58),(148,49),(162,57),(170,80),(176,117),(187,159),(171,169),(154,134),(152,98),(145,70),(108,82),(94,90)],
'hood':[(117,20),(133,13),(145,16),(130,25),(119,42),(116,54),(140,51),(150,43),(151,57),(139,64),(114,66),(109,51)],
'skin':[(127,24),(142,22),(149,29),(146,43),(139,51),(129,48),(123,39)],
}
# Masked source colour is blended by alpha; generated material fills cover uncovered regions.
for name,points in regions.items():
    mask=Image.new('L',(1024,1024));ImageDraw.Draw(mask).polygon([(x*4,y*4) for x,y in points],fill=255);
    if name=='skin':
        d=ImageDraw.Draw(mask);d.ellipse((83*4,78*4,104*4,100*4),fill=255);d.polygon([(139*4,64*4),(152*4,77*4),(157*4,85*4),(148*4,88*4),(137*4,72*4)],fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(3));out=canvas.copy();out.putalpha(mask);out.save(A/f'projection-{name}.png')
fill=Image.open(A/'painted-fills.png').convert('RGB');w,h=fill.size
for name,rect in {'ivory':(0,0,w//2,h//2),'olive':(w//2,0,w,h//2),'rust':(0,h//2,w//2,h),'leather':(w//2,h//2,w,h)}.items():fill.crop(rect).save(A/f'fill-{name}.png')
(A/'source-manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
