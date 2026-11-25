"""Composite all actual game frames and encode three repeats without interpolation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from kit.images import resize_rgba
from PIL import Image, ImageDraw

root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
parser=argparse.ArgumentParser();parser.add_argument('clips',nargs='+');parser.add_argument('--gpu',action='store_true');args=parser.parse_args()
review=root/'review/3d-v2';review.mkdir(parents=True,exist_ok=True)
for clip in args.clips:
    lane=root/'lanes/spearman-q-r2'
    folder=(lane/'gpu' if args.gpu else lane)/'frames'/clip
    prefix='spearman-q-r2-gpu' if args.gpu else 'spearman-q-r2'
    receipt=json.loads((folder/'receipt.json').read_text())
    count,fps=receipt['frames'],receipt['fps']
    frames=[];opaque=folder/'cream';opaque.mkdir(exist_ok=True)
    for i in range(count):
        im=Image.open(folder/f'{i:02}.png').convert('RGBA')
        if im.size!=(160,160):im=resize_rgba(im,(160,160),'display')
        bg=Image.new('RGBA',im.size,(248,244,231,255));bg.alpha_composite(im)
        bg=bg.convert('RGB');bg.save(opaque/f'{i:02}.png');frames.append(bg)
    dest=review/f'{prefix}-{clip}-160.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-stream_loop','2','-framerate',str(fps),'-i',str(opaque/'%02d.png'),
                    '-frames:v',str(count*3),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(dest.with_suffix('.part.mp4'))],check=True)
    dest.with_suffix('.part.mp4').replace(dest)
    result=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries',
                  'stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration','-of','json',str(dest)]))['streams'][0]
    assert result['codec_name']=='h264' and result['pix_fmt']=='yuv420p'
    assert (result['width'],result['height'])==(160,160) and int(result['nb_read_frames'])==count*3
    assert result['r_frame_rate']==f'{fps}/1'
    receipt['video']=result
    (review/f'{prefix}-{clip}-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    strip=Image.new('RGB',(count*160,160),(248,244,231))
    for i,im in enumerate(frames):strip.paste(im,(i*160,0))
    strip.save(review/f'{prefix}-{clip}-fullrate.png')
    sheet=Image.new('RGB',(640,180*((count+3)//4)),(248,244,231));draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(frames):
        x=i%4*160;y=i//4*180;sheet.paste(im,(x,y+20));draw.text((x+5,y+3),f'{clip} {i+1}/{count}',fill='#302820')
    sheet.save((lane/'gpu' if args.gpu else lane)/f'{clip}-contact.png')
    print(dest,result)
