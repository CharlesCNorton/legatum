"""Independent provenance/inventory gate before GPU delivery and its success receipt."""
import argparse, hashlib, json, os
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parent
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/mechanised-infantry';V=R/'review/3d-v2'
CLIPS={'idle':8,'move':8,'attack':10,'hit':4,'death':10}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(require_gpu=False):
    man=json.loads((M/'render-manifest.json').read_text())
    assert man['source_sha256']==sha(M/'mechanised-infantry.blend'),'stale model'
    assert man['inputs_sha256']==sha(M/'inputs.json'),'changed input manifest'
    inputs=json.loads((M/'inputs.json').read_text())
    assert inputs['source_sha256']==sha(R/'assets/mechanised-infantry/painting-source.png'),'changed painting'
    assert inputs['fill_sha256']==sha(R/'assets/mechanised-infantry/painted-olive.png'),'changed generated fill'
    for name,value in man['pipeline_sha256'].items():assert sha(P/name)==value,'changed pipeline: '+name
    assert man['grade_sha256']==sha(M/'grade.json'),'changed grade'
    for name,value in man['gallery_sha256'].items():assert sha(M/'256'/name)==value,'changed gallery: '+name
    if require_gpu:
        assert (man['device'],man['resolution'])==('GPU',512),'final delivery requires actual GPU512 masters'
        assert man['samples']>=48,'final delivery requires at least 48 samples'
    for name,proof in man['renders'].items():
        p=M/'renders'/name
        assert sha(p)==proof['sha256'],'changed render: '+name
        assert Image.open(p).size==(man['resolution'],)*2
        assert all(proof[k]==man[k] for k in ['resolution','engine','device','samples'])
        if require_gpu:assert sha(M/'512'/name)==sha(p),'stale 512 master: '+name
    for clip,count in CLIPS.items():
        assert sha(M/f'mechanised-infantry-{clip}.blend')==man['clip_blends'][clip],'stale clip'
        for i in range(count):
            p=M/'renders'/clip/f'{i:02}.png'
            assert sha(p)==man['clips'][clip]['hashes'][i]
            assert Image.open(M/'256'/clip/f'{i:02}.png').size==(256,256)
            if require_gpu:assert sha(M/'512'/clip/f'{i:02}.png')==sha(p)
    assert len(man['ground_audit'])==42
    import math
    move=[r for r in man['ground_audit'] if r['clip']=='move']
    for r in move:
        for radius,angle in zip(man['audit']['wheel_radii'],r['wheel_angle']):
            assert abs(angle+r['travel']/radius)<1e-5,'wheel slip'
    assert all(abs(a+2*math.pi)<1e-5 for a in move[-1]['wheel_angle']),'rolling loop mismatch'
    assert min(a['minimum_z'] for a in man['ground_audit'])>=.1499
    assert all(a['minimum_vehicle_z']>0 for a in man['ground_audit'])
    assert all(abs(z-.15)<.0001 for a in man['ground_audit'] for z in a['wheel_contact_z']),'floating wheel'
    assert (M/'renders/death/08.png').read_bytes()==(M/'renders/death/09.png').read_bytes()
    for stage in ['b-plain','c-textured-lit','c-details','d-rig-poses','f-restpose-compare','g-feet-check']:
        assert (V/f'mechanised-infantry-{stage}.png').is_file()
    print('PASS: pipeline/model/clip/grade/gallery hashes, 40 frames, ground clearance, held death'+('; GPU512 provenance' if require_gpu else '; CPU preview permitted'))
    return man
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--require-gpu',action='store_true');parser.add_argument('--receipt',action='store_true');a=parser.parse_args()
    man=check(a.require_gpu)
    if a.receipt:
        assert a.require_gpu,'only verified GPU runs receive a receipt'
        atlas=Path('app/src/assets/units/anim/mechanised-infantry.webp')
        report=json.loads((V/'mechanised-infantry-validation.json').read_text())
        assert report['provenance']==man
        assert report['bytes']==atlas.stat().st_size<=200000 and report['quality']>=75
        video=V/f'mechanised-infantry-round{os.environ["ROUND"]}.mp4';assert video.is_file()
        (V/f'mechanised-infantry-gpu-receipt-r{os.environ["ROUND"]}.json').write_text(json.dumps({'round':os.environ['ROUND'],'master_sha256':man['source_sha256'],'atlas_sha256':sha(atlas),'video_sha256':sha(video),'bytes':report['bytes'],'quality':report['quality'],'art_approved':False},indent=2))
