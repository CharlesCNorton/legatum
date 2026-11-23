"""Keep untouched 512 and downsampled 256 masters outside git after a final pass."""
import os, sys, json, shutil, hashlib
from pathlib import Path
from PIL import Image
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/main-battle-tank'
for stage in ('b','c','details','d','e-idle','e-move','e-attack','e-hit','e-death','g'):
    folder=M/'renders'/stage
    report=json.loads((folder/'render.json').read_text())
    size=report['resolution']
    clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g' else None
    master=M/'clips'/f'{clip}.blend' if clip else M/('main-battle-tank-plain.blend' if stage=='b' else 'main-battle-tank.blend')
    assert report['blend_sha256']==hashlib.sha256(master.read_bytes()).hexdigest(), 'Stale master'
    if stage!='b':assert report['grade_sha256']==hashlib.sha256((M/'grade.json').read_bytes()).hexdigest(), 'Stale grade'
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
