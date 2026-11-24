"""Composite all actual game frames and encode three repeats without interpolation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
parser=argparse.ArgumentParser();parser.add_argument('clips',nargs='+');args=parser.parse_args()
review=root/'review/3d-v2';review.mkdir(parents=True,exist_ok=True)
for clip in args.clips:
    folder=root/'lanes/spearman-q/frames'/clip
    receipt=json.loads((folder/'receipt.json').read_text())
    count,fps=receipt['frames'],receipt['fps']
    frames=[];opaque=folder/'cream';opaque.mkdir(exist_ok=True)
    for i in range(count):
        im=Image.open(folder/f'{i:02}.png').convert('RGBA')
        assert im.size==(160,160)
        bg=Image.new('RGBA',im.size,(248,244,231,255));bg.alpha_composite(im)
        bg=bg.convert('RGB');bg.save(opaque/f'{i:02}.png');frames.append(bg)
    dest=review/f'spearman-q-{clip}-160.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-stream_loop','2','-framerate',str(fps),'-i',str(opaque/'%02d.png'),
                    '-frames:v',str(count*3),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
    result=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries',
                  'stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,duration','-of','json',str(dest)]))['streams'][0]
    assert result['codec_name']=='h264' and result['pix_fmt']=='yuv420p'
    assert (result['width'],result['height'])==(160,160) and int(result['nb_read_frames'])==count*3
    assert result['r_frame_rate']==f'{fps}/1'
    receipt['video']=result
    (review/f'spearman-q-{clip}-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    strip=Image.new('RGB',(count*160,160),(248,244,231))
    for i,im in enumerate(frames):strip.paste(im,(i*160,0))
    strip.save(review/f'spearman-q-{clip}-fullrate.png')
    sheet=Image.new('RGB',(640,180*((count+3)//4)),(248,244,231));draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(frames):
        x=i%4*160;y=i//4*180;sheet.paste(im,(x,y+20));draw.text((x+5,y+3),f'{clip} {i+1}/{count}',fill='#302820')
    sheet.save(root/f'lanes/spearman-q/{clip}-contact.png')
    print(dest,result)
