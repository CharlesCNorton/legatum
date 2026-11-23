"""Independent complete-stage provenance gate; CPU previews cannot pass as GPU."""
import argparse, hashlib, json, os
from pathlib import Path
from PIL import Image

STAGES={'b-plain':1,'c-textured-lit':1,'c-details':1,'d-rig-poses':4,
        'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(root, resolution, gpu=False):
    master=root/'masters/eagle-warrior'
    modes=set()
    for stage,count in STAGES.items():
        folder=master/'renders'/str(resolution)/stage
        report=json.loads((folder/'render.json').read_text())
        blend=master/'clips'/f'{stage[2:]}.blend' if stage.startswith('e-') else master/'clips/attack.blend' if stage=='d-rig-poses' else master/('plain.blend' if stage=='b-plain' else 'eagle-warrior.blend')
        assert report['blend_sha256']==sha(blend),(stage,'stale blend')
        assert report['frames']==count and report['resolution']==resolution
        if gpu:assert report['device']=='GPU' and report['engine']=='CYCLES' and resolution==512,(stage,'GPU512 required')
        modes.add((report['engine'],report['device'],report['samples'],report['resolution']))
        for i in range(count):
            with Image.open(folder/f'{i:02}.png') as im:assert im.size==(resolution,resolution) and im.mode=='RGBA'
            for size in sorted({256,resolution}):
                with Image.open(master/'graded'/str(size)/stage/f'{i:02}.png') as im:assert im.size==(size,size)
    assert len(modes)==1,'Mixed render configurations'
    return {'stages':len(STAGES),'clip_frames':40,'mode':list(next(iter(modes))),'master_sha256':sha(master/'eagle-warrior.blend')}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gpu',action='store_true');p.add_argument('--receipt',action='store_true');p.add_argument('--resolution',type=int,default=512);args=p.parse_args()
    root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
    result=check(root,args.resolution,args.gpu)
    if args.receipt:
        review=root/'review/3d-v2';rnd=os.environ.get('ROUND','2')
        validation=json.loads((review/'eagle-warrior-validation.json').read_text());audit=json.loads((review/'eagle-warrior-audit.json').read_text())
        assert validation['ok'] and validation['gpu'] and audit['ok']
        feet=json.loads((root/'masters/eagle-warrior/feet.json').read_text())
        assert feet['source_sha256']==sha(root/'masters/eagle-warrior/clips/move.blend'),'stale foot review'
        assert feet['device']=='GPU' and len(feet['files'])==16
        for entry in feet['files']:
            assert sha(root/'masters/eagle-warrior'/entry['path'])==entry['sha256'],'stale foot frame'
        assert (review/'eagle-warrior-g-feet-check.png').stat().st_size>0
        movie=review/f'eagle-warrior-round{rnd}.mp4';assert movie.stat().st_size>0
        result.update(validation=validation,audit_ok=True,feet_device=feet['device'],movie_sha256=sha(movie),round=rnd,art_approved=False)
        (review/f'eagle-warrior-gpu-round{rnd}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
