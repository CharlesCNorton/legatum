"""One bounded RGB quantile grade from rest pose, reused across all clip frames.
Never warp silhouettes or replace rendered pixels with the painting. Preserve alpha.
"""
from pathlib import Path
from PIL import Image
import os,sys,json,shutil,hashlib
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tank';stage=sys.argv[1];folder=M/'renders'/stage
if stage=='b':raise SystemExit(0)
def samples(im):
    channels=[[],[],[]]
    for r,g,b,a in im.convert('RGBA').getdata():
        if a>240:
            for c,value in zip(channels,(r,g,b)):c.append(value)
    return [[sorted(c)[int((len(c)-1)*q)] for q in (.1,.5,.9)] for c in channels]
if stage=='c':
    source=samples(Image.open('app/src/assets/units/tank-256.png'))
    before=samples(Image.open(folder/'three-quarter.png'));luts=[]
    for src,dst in zip(before,source):
        pairs=[(0,0)]+list(zip(src,dst))+[(255,255)];lut=[]
        for value in range(256):
            a,b=next((a,b) for a,b in zip(pairs,pairs[1:]) if a[0]<=value<=b[0])
            target=a[1]+(b[1]-a[1])*(value-a[0])/max(1,b[0]-a[0])
            lut.append(round(max(0,min(255,max(value-32,min(value+32,target))))))
        luts.append(lut)
    (M/'grade.json').write_text(json.dumps({'method':'bounded per-channel 10/50/90 percentile map from alpha>240 pixels; max 32 levels; one rest grade for every clip','source_quantiles':source,'render_quantiles':before,'luts':luts},indent=2))
else:luts=json.loads((M/'grade.json').read_text())['luts']
raw=M/'renders/ungraded'/stage;raw.mkdir(parents=True,exist_ok=True)
for p in folder.glob('*.png'):
    shutil.copyfile(p,raw/p.name);im=Image.open(p).convert('RGBA');channels=im.split()
    graded=Image.merge('RGBA',tuple(channels[i].point(luts[i]) for i in range(3))+(channels[3],));graded.save(p)
metadata=json.loads((folder/'render.json').read_text());metadata['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest();(folder/'render.json').write_text(json.dumps(metadata,indent=2))
print('GRADED',stage,'alpha preserved; ungraded frames retained')
