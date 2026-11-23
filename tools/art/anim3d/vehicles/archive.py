"""Keep untouched 512 and downsampled 256 masters outside git after a final pass."""
import os, sys, json, shutil
from pathlib import Path
from PIL import Image
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tank'
for stage in ('b','c','details','d','e-idle','e-move','e-attack','e-hit','e-death'):
    folder=M/'renders'/stage
    report=json.loads((folder/'render.json').read_text())
    size=report['resolution']
    if '--require-512' in sys.argv:
        assert size==512 and report['device']=='GPU',(stage,report)
    assert size>=256
    for destsize in (512,256):
        if size<destsize:continue
        dest=M/str(destsize)/stage;dest.mkdir(parents=True,exist_ok=True)
        for p in folder.glob('*.png'):
            im=Image.open(p);assert im.size==(size,size)
            if size==destsize:shutil.copy2(p,dest/p.name)
            else:im.resize((destsize,destsize),Image.Resampling.LANCZOS).save(dest/p.name)
        (dest/'render.json').write_text(json.dumps({**report,'archived_resolution':destsize},indent=2))
print('ARCHIVED: actual source-sized and 256px master sets')
