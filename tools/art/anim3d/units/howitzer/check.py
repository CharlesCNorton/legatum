"""Independent provenance/inventory gate before GPU delivery and its success receipt."""
import argparse, hashlib, json, os
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parent
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/howitzer';V=R/'review/3d-v2'
CLIPS={'idle':8,'move':8,'attack':10,'hit':4,'death':10}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(require_gpu=False):
    man=json.loads((M/'render-manifest.json').read_text())
    assert man['source_sha256']==sha(M/'howitzer.blend'),'stale model'
    assert man['inputs_sha256']==sha(M/'inputs.json'),'changed input manifest'
    inputs=json.loads((M/'inputs.json').read_text())
    assert inputs['source_sha256']==sha(R/'assets/howitzer/painting-source.png'),'changed painting'
    assert inputs['fill_sha256']==sha(R/'assets/howitzer/painted-olive.png'),'changed generated fill'
    # Packing/auditing do not render pixels; their own output receipts bind their code.
    render_scripts={'scene.py','prepare.py','refine.py','bake.py','projection.py','review.py'}
    for name,value in man['pipeline_sha256'].items():
        if name in render_scripts:assert sha(P/name)==value,'changed render pipeline: '+name
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
        assert sha(M/f'howitzer-{clip}.blend')==man['clip_blends'][clip],'stale clip'
        for i in range(count):
            p=M/'renders'/clip/f'{i:02}.png'
            assert sha(p)==man['clips'][clip]['hashes'][i]
            assert Image.open(M/'256'/clip/f'{i:02}.png').size==(256,256)
            if require_gpu:assert sha(M/'512'/clip/f'{i:02}.png')==sha(p)
    assert len(man['ground_audit'])==42
    assert min(a['minimum_z'] for a in man['ground_audit'])>=.1279
    assert all(abs(z-.13)<.0001 for a in man['ground_audit'] for z in a['wheel_contact_z']),'floating wheel'
    assert (M/'renders/death/08.png').read_bytes()==(M/'renders/death/09.png').read_bytes()
    for stage in ['b-plain','c-textured-lit','c-details','d-rig-poses','f-restpose-compare']:
        assert (V/f'howitzer-{stage}.png').is_file()
    print('PASS: render-pipeline/model/clip/grade/gallery hashes, 40 frames, ground clearance, held death'+('; GPU512 provenance' if require_gpu else '; CPU preview permitted'))
    return man
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--require-gpu',action='store_true');parser.add_argument('--receipt',action='store_true');a=parser.parse_args()
    man=check(a.require_gpu)
    if a.receipt:
        assert a.require_gpu,'only verified GPU runs receive a receipt'
        atlas=Path('app/src/assets/units/anim/howitzer.webp')
        report=json.loads((V/'howitzer-validation.json').read_text())
        assert report['provenance']==man
        assert report['delivery_sha256']==sha(P/'deliver.py'),'changed packer after delivery'
        audit=json.loads((M/'geometry-audit.json').read_text())
        assert all(audit['clips'][clip]['sha256']==sha(M/f'howitzer-{clip}.blend') for clip in CLIPS),'stale geometry audit'
        assert report['bytes']==atlas.stat().st_size<=200000 and report['quality']>=75
        video=V/f'howitzer-round{os.environ["ROUND"]}.mp4';assert video.is_file()
        (V/f'howitzer-gpu-receipt-r{os.environ["ROUND"]}.json').write_text(json.dumps({'round':os.environ['ROUND'],'master_sha256':man['source_sha256'],'atlas_sha256':sha(atlas),'video_sha256':sha(video),'bytes':report['bytes'],'quality':report['quality'],'geometry_audit_sha256':sha(M/'geometry-audit.json'),'delivery_sha256':sha(P/'deliver.py'),'check_sha256':sha(P/'check.py'),'art_approved':False},indent=2))
