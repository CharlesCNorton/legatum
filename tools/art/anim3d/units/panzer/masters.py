"""Retain actual rendered masters with renderer/source provenance; never upscale."""
import hashlib,json,os,shutil,sys
from pathlib import Path
from PIL import Image
m=Path(os.environ['ANIM_ROOT'])/'masters/panzer'
preview='--cpu-preview' in sys.argv
expected=256 if preview else 512
stages=['b','c','details','d','e-idle','e-move','e-attack','e-hit','e-death','g']
records={}
for stage in stages:
    folder=m/'renders'/stage
    manifest=json.loads((folder/'render.json').read_text())
    assert manifest['resolution']==expected,(stage,manifest)
    for src in folder.glob('*.png'):
        im=Image.open(src).convert('RGBA');assert im.size==(expected,expected),(src,im.size)
        for size in ([256] if preview else [512,256]):
            dst=m/str(size)/stage/src.name;dst.parent.mkdir(parents=True,exist_ok=True)
            if size==expected:shutil.copyfile(src,dst)
            else:im.resize((size,size),Image.Resampling.LANCZOS).save(dst)
    records[stage]=manifest
report=dict(source_sha256=hashlib.sha256((m/'panzer.blend').read_bytes()).hexdigest(),
            source_resolution=expected,stages=records,preview=preview)
for size in ([256] if preview else [512,256]):
    (m/str(size)/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('MASTERS:', 'actual 256px CPU previews retained' if preview else 'actual 512 and downsampled 256 retained')
