"""Check external masters, source binding, real bakes, reviews and delivered contract."""
from pathlib import Path
import os,json,hashlib,sys
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=ROOT/'masters/barbarian-archer';R=ROOT/'review/3d-v2';S='barbarian-archer'
expected=json.loads((Path(__file__).parent/'inputs.json').read_text())
for name,digest in expected.items():
    assert hashlib.sha256((ROOT/'assets'/S/name).read_bytes()).hexdigest()==digest,('input changed',name)
model=json.loads((M/'model-info.json').read_text());assert model['body_vertices']>10000 and model['bones']>=50
finish=json.loads((M/'finish-info.json').read_text());assert len(finish['projected_meshes'])>10 and len(finish['baked'])==4
for name in finish['baked']:
    for kind in ('AO','CURVATURE'):
        im=Image.open(M/'textures'/f'{name}-{kind}.png');assert im.size==(256,256)
        assert im.convert('L').getextrema()[0]<im.convert('L').getextrema()[1],(name,kind,'constant bake')
res=os.environ.get('RESOLUTION','256')
for stage in ('b','c','d','e-idle','e-move','e-attack','e-hit','e-death'):
    manifest=json.loads((M/'renders'/res/stage/'manifest.json').read_text())
    assert manifest['device']==os.environ.get('CYCLES_DEVICE','CPU'),('wrong device',stage)
source=hashlib.sha256((M/'master.blend').read_bytes()).hexdigest()
for name,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    audit=json.loads((M/(name+'-audit.json')).read_text());assert audit['source_master_sha256']==source
    assert all(c['hand_grip_distance']<.08 and c['base_static'] for c in audit['checks'])
    assert (R/f'{S}-e-{name}-strip.png').exists() and (R/f'{S}-e-{name}.webp').exists()
    for size in (256,512):
        paths=list((M/str(size)/name).glob('*.png'));assert len(paths)==n,(size,name,'missing masters')
        assert all(Image.open(p).size==(size,size) for p in paths)
for stage in ['b-plain','c-textured-lit','c-details','d-rig-poses','f-restpose-compare']:assert (R/f'{S}-{stage}.png').exists()
sys.path.insert(0,str(Path(__file__).resolve().parent))
from deliver import validate
validate()
print('PASS: MPFB geometry/rig, 8 real AO/curvature maps, projected 3D surfaces, source hashes, grip/base audits, all review artifacts and 512/256 masters')
