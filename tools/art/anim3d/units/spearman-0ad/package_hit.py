"""Round 6 silhouette measurement and game-rate hit/idle comparison.

Uses lossless RGBA sprites, not H.264 colour thresholds. Both alpha-weighted
centroids and opaque-silhouette centroids must travel >=8 px; top is alpha>=128.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

UNIT = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
WORK = ROOT/'oad/r6'
OUT = ROOT/'review/3d-v2'
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB


def measure(folder):
    centres, weighted, tops = [], [], []
    for p in sorted(folder.glob('*.png')):
        a = np.array(Image.open(p).convert('RGBA'))[:,:,3]/255
        y,x = np.indices(a.shape); mask = a >= .5
        centres.append([float(x[mask].mean()),float(y[mask].mean())])
        weighted.append([float((x*a).sum()/a.sum()),float((y*a).sum()/a.sum())])
        tops.append(int(y[mask].min()))
    def diameter(points):
        return max(float(np.linalg.norm(np.array(a)-b)) for a,b in itertools.product(points,repeat=2))
    return {'frames':len(centres),'opaque_centroid_diameter_px':diameter(centres),
            'alpha_weighted_centroid_diameter_px':diameter(weighted),
            'top_range_px':max(tops)-min(tops),'opaque_centroids_xy':centres,'tops_y':tops}


def cream(path):
    im = Image.open(path).convert('RGBA')
    canvas = Image.new('RGBA',im.size,'#f8f4e8');canvas.alpha_composite(im)
    return canvas.convert('RGB')


def encode(folder, output, fps, count, loops=1):
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-stream_loop',str(loops-1),
                    '-i',str(folder/'%03d.png'),'-frames:v',str(count*loops),'-c:v','libx264',
                    '-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    stream = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
                       '-show_entries','stream=codec_name,width,height,pix_fmt,nb_read_frames,r_frame_rate,duration',
                       '-of','json',str(output)]))['streams'][0]
    assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
    assert int(stream['nb_read_frames'])==count*loops
    return stream


def frozen():
    old,new = GLB(WORK/'approved-r5.glb'),GLB(UNIT/'spearman.glb')
    clips = {}
    for a,b in zip(old.doc['animations'],new.doc['animations']):
        assert a==b
        if a['name']=='hit':continue
        for s in a['samplers']:
            for k in ['input','output']:assert old.accessor(s[k])==new.accessor(s[k])
        clips[a['name']]='identical sampler data'
    hit = next(a for a in new.doc['animations'] if a['name']=='hit')
    modified = {s['output'] for s in hit['samplers']}
    for i,a in enumerate(old.doc['accessors']):
        if i not in modified:assert a==new.doc['accessors'][i] and old.accessor(i)==new.accessor(i)
    for key in old.doc:
        if key!='accessors':assert old.doc[key]==new.doc[key]
    for im in old.doc['images']:
        v=old.doc['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);end=start+v['byteLength']
        assert old.bin[start:end]==new.bin[start:end]
    return {'approved_r5_sha256':hashlib.sha256((WORK/'approved-r5.glb').read_bytes()).hexdigest(),
            'clips':clips,'geometry_atlas_materials_skin_team_mask':'identical'}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'asset_sha256':hashlib.sha256((UNIT/'spearman.glb').read_bytes()).hexdigest(),'frozen':frozen()}
    report['hit_160']=measure(WORK/'frames/hit')
    report['idle_160']=measure(WORK/'frames/idle')
    report['r5_hit_160']=measure(ROOT/'oad/r5/frames/hit')
    metric=report['hit_160']
    assert metric['frames']==8
    assert min(metric['opaque_centroid_diameter_px'],metric['alpha_weighted_centroid_diameter_px'],metric['top_range_px'])>=8, metric
    hits=[cream(p) for p in sorted((WORK/'frames/hit').glob('*.png'))]
    idles=[cream(p) for p in sorted((WORK/'frames/idle').glob('*.png'))]
    sheet=Image.new('RGB',(640,360),'#f8f4e8');draw=ImageDraw.Draw(sheet)
    encoded=WORK/'cream-hit';encoded.mkdir(exist_ok=True)
    for i,im in enumerate(hits):
        im.save(encoded/f'{i:03}.png');sheet.paste(im,(i%4*160,i//4*180))
        draw.text((i%4*160+4,i//4*180+162),f'{i:02} | key {24*i/7:.2f}',fill='#493b2a')
    sheet.save(OUT/'spearman-0ad-r6-hit-contact.png')
    report['hit_video']=encode(encoded,OUT/'spearman-0ad-r6-hit-160.mp4',12,8,3)
    # One 3-second comparison cycle: an 8-frame hit at 12 fps, then idle-zero
    # recovery hold; the right plays its full 12-frame idle at 4 fps. Repeat 3x.
    comparison=WORK/'comparison';comparison.mkdir(exist_ok=True)
    for i in range(36):
        canvas=Image.new('RGB',(320,180),'#f8f4e8')
        canvas.paste(hits[min(i,7)],(0,0));canvas.paste(idles[i//3],(160,0))
        draw=ImageDraw.Draw(canvas);draw.text((4,164),'HIT | 12 fps',fill='#493b2a');draw.text((164,164),'IDLE | 4 fps',fill='#493b2a')
        canvas.save(comparison/f'{i:03}.png')
    report['comparison_video']=encode(comparison,OUT/'spearman-0ad-r6-hit-vs-idle-160.mp4',12,36,3)
    report['comparison_timing']='Three 3s cycles; 8 hit samples at 12 fps then idle-zero hold; idle 12 samples at 4 fps. Shared fixed camera, 160px panels.'
    # The accepted evidence is carried forward without re-rendering the clips.
    prior=json.loads((OUT/'spearman-0ad-r5-video-validation.json').read_text())
    assert prior['asset_sha256']==report['frozen']['approved_r5_sha256']
    for name in ['idle','walk','attack','death']:
        shutil.copyfile(OUT/f'spearman-0ad-r5-{name}-160.mp4',OUT/f'spearman-0ad-r6-{name}-160.mp4')
    for name in ['attack-fullrate.png','readability-48.png']:
        shutil.copyfile(OUT/f'spearman-0ad-r5-{name}',OUT/f'spearman-0ad-r6-{name}')
    (WORK/'hit-review.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'spearman-0ad-r6-hit-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
