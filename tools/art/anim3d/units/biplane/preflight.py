"""Cheap input and final GPU-provenance gates; safe to run without Blender."""
import hashlib, json, os, sys
from pathlib import Path
from PIL import Image

ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=ROOT/'masters/biplane'
UNIT=Path(__file__).resolve().parent
STAGES={'b':1,'c':1,'d':4,'g':16,'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source(stage):
    return M/('unpainted.blend' if stage=='b' else 'attack.blend' if stage=='d' else 'move.blend' if stage=='g' else stage[2:]+'.blend' if stage.startswith('e-') else 'biplane.blend')

def inputs():
    for name in ('biplane.blend','unpainted.blend','inputs.json','build-inputs.json'):
        assert (M/name).is_file(),f'Missing {M/name}; rebuild/paint first'
    for name,digest in json.loads((M/'inputs.json').read_text()).items():
        assert sha(ROOT/'assets/biplane'/name)==digest,('changed asset',name)
    built=json.loads((M/'build-inputs.json').read_text())
    for name,digest in built['scripts'].items():
        assert sha(UNIT/name)==digest,('rebuild required; changed script',name)
    assert sha(M/'biplane.blend')==built['master_sha256'],'Master changed since paint'
    return built

def gpu():
    inputs()
    settings=None
    for stage,count in STAGES.items():
        raw=M/'raw'/stage
        r=json.loads((raw/'render.json').read_text())
        assert r['engine']=='CYCLES' and r['device']=='GPU' and r['resolution']==512,('not GPU512',stage,r)
        assert r['samples']>=64,('insufficient final samples',stage)
        cfg=(r['engine'],r['device'],r['resolution'],r['samples'])
        assert settings in (None,cfg),('mixed settings',stage)
        settings=cfg
        assert r['blend_sha256']==sha(source(stage)),('stale source',stage)
        assert r['frames']==count,('wrong stage count',stage)
        for size in (512,256):
            folder=M/str(size)/stage
            p=json.loads((folder/'processed.json').read_text())
            assert p['blend_sha256']==r['blend_sha256']
            assert p['raw_sha256']==[sha(raw/f'{i:02}.png') for i in range(count)]
            assert p['processed_sha256']==[sha(folder/f'{i:02}.png') for i in range(count)]
            if stage!='b':assert p['grade_sha256']==sha(M/'grade.json')
            for i in range(count):assert Image.open(folder/f'{i:02}.png').size==(size,size)
    print('Verified all GPU512 stages, current sources, fixed grade and 256 masters')

if __name__=='__main__':
    if sys.argv[1:] == ['--gpu']:gpu()
    else:inputs();print('Verified current biplane build and external assets')
