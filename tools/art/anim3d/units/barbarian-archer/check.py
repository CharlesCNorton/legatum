"""Check external masters, source binding, real bakes, reviews and delivered contract."""
from pathlib import Path
import os,json,hashlib,sys
from PIL import Image
from deliver import read, grade, tile
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
for stage in ('b','c','d','e-idle','e-move','e-attack','e-hit','e-death','g-feet'):
    _,manifest=read(stage)
    assert manifest['device']==os.environ.get('CYCLES_DEVICE','CPU'),('wrong device',stage)
    assert manifest['resolution']==int(res)
    if os.environ.get('CYCLES_DEVICE')=='GPU':assert manifest['samples']==64 and int(res)==512
source=hashlib.sha256((M/'master.blend').read_bytes()).hexdigest()
scene_audit=json.loads((M/'scene-audit.json').read_text())
assert scene_audit['source_master_sha256']==source and scene_audit['frames']==40
for name,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    audit=json.loads((M/(name+'-audit.json')).read_text());assert audit['source_master_sha256']==source
    assert all(c['hand_grip_distance']<.08 and c['base_static'] for c in audit['checks'])
    assert (R/f'{S}-e-{name}-strip.png').exists() and (R/f'{S}-e-{name}.webp').exists()
    for size in ((256,512) if int(res)==512 else (256,)):
        paths=sorted((M/str(size)/name).glob('*.png'));assert len(paths)==n,(size,name,'missing masters')
        assert all(Image.open(p).size==(size,size) for p in paths)
        raw,_=read('e-'+name)
        assert all(Image.open(p).convert('RGBA').tobytes()==tile(grade(frame),size).tobytes()
                   for p,frame in zip(paths,raw)), (size,name,'stale exported masters')
for stage in ['b-plain','c-textured-lit','c-details','d-rig-poses','f-restpose-compare','g-feet-check']:assert (R/f'{S}-{stage}.png').exists()
feet=json.loads((M/'feet-check.json').read_text())
assert feet['source_sha256']==hashlib.sha256((M/'move.blend').read_bytes()).hexdigest()
assert len(feet['samples'])==8
for name in ('idle','move','hit','death'):
    motion=json.loads((M/(name+'-motion.json')).read_text())
    assert motion['source_master_sha256']==source and motion['license']=='CC0-1.0'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from deliver import validate
validate()
print('PASS: MPFB geometry/rig, 8 real AO/curvature maps, projected 3D surfaces, source hashes, grip/base audits, all review artifacts and masters at the actual render resolution')
