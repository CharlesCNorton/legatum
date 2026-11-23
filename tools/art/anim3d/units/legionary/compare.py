"""Reference metrics complement, never replace, the 256/64px visual verdict."""
import json, os
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
root=Path(os.environ['ANIM_ROOT']);master=root/'masters/legionary'
ref=Image.open('app/src/assets/units/legionary-256.png').convert('RGBA')
result={}
for name,path in [('gpu_round1',master/'driver-r1-gpu/renders/c/256/rest.png'),('current',master/'renders/c/256/rest.png')]:
    if not path.exists():continue
    render=Image.open(path).convert('RGBA');sizes={}
    for size in [256,64]:
        a=ref.resize((size,size),Image.Resampling.LANCZOS);b=render.resize((size,size),Image.Resampling.LANCZOS)
        ma=a.getchannel('A').point(lambda x:255 if x>=128 else 0);mb=b.getchannel('A').point(lambda x:255 if x>=128 else 0)
        intersection=ImageChops.darker(ma,mb);union=ImageChops.lighter(ma,mb)
        sizes[str(size)]={'silhouette_iou':sum(intersection.get_flattened_data())/sum(union.get_flattened_data()),'foreground_rgb_mae':ImageStat.Stat(ImageChops.difference(a.convert('RGB'),b.convert('RGB')),intersection).mean}
    result[name]=sizes
(root/'review/3d-v2/legionary-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
