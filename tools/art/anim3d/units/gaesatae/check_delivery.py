"""Independently check complete stage/master provenance and the decoded review movie."""
import argparse, json, os, subprocess
from pathlib import Path
from PIL import Image
import deliver as d
p=argparse.ArgumentParser();p.add_argument('--gpu',action='store_true');args=p.parse_args()
settings=[]
for stage in ['b','c','d']+['e-'+c for c in d.CLIPS]:
    images,meta=d.raw(stage)
    expected=d.CLIPS[stage[2:]][0] if stage.startswith('e-') else 4 if stage=='d' else 1
    assert len(images)==expected,(stage,len(images))
    if args.gpu:assert meta['device']=='GPU' and meta['resolution']==512,(stage,'not GPU512')
    settings.append((meta['resolution'],meta['samples'],meta['device']))
    for size in (256,512) if args.gpu else (256,):
        for i in range(expected):
            path=d.M/'masters'/str(size)/stage/f'{i:02}.png'
            with Image.open(path) as image:assert image.size==(size,size) and image.mode=='RGBA',path
assert len(set(settings))==1,'Mixed render settings'
d.validate(Path('app/src/assets/units/anim/gaesatae.webp'))
movie=d.R/f"gaesatae-round{os.environ.get('ROUND','2')}.mp4"
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(movie)]))['streams'][0]
assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'],int(probe['nb_frames']))==('h264','yuv420p',1600,348,240)
assert abs(float(probe['duration'])-8)<.01
for suffix in ['b-plain','c-textured-lit','c-details','d-rig-poses','f-restpose-compare','g-decoded-atlas']+['e-'+c+'-strip' for c in d.CLIPS]:
    assert (d.R/f'gaesatae-{suffix}.png').is_file(),suffix
print('DELIVERY_CHECK_OK',settings[0],'40 frames; masters; all reviews; 8s H.264/yuv420p MP4')
