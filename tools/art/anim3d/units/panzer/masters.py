"""Retain true rendered 512px masters and downsampled 256px masters; refuse previews."""
import os,shutil
from pathlib import Path
from PIL import Image
m=Path(os.environ['ANIM_ROOT'])/'masters/panzer'
for src in (m/'renders').glob('*/*.png'):
    if src.parent.name=='ungraded':continue
    im=Image.open(src).convert('RGBA');assert im.size==(512,512),(src,im.size)
    for size in [512,256]:
        dst=m/str(size)/src.parent.name/src.name;dst.parent.mkdir(parents=True,exist_ok=True)
        if size==512:shutil.copyfile(src,dst)
        else:im.resize((size,size),Image.Resampling.LANCZOS).save(dst)
print('MASTERS: actual 512 and downsampled 256 retained')
