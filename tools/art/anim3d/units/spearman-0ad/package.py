"""Encode three repeats at existing 2D game rates; verify the decoded streams."""
import json, os, subprocess, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'oad/r5';OUT=ROOT/'review/3d-v2';OUT.mkdir(parents=True,exist_ok=True)
FPS={'idle':4,'walk':6,'attack':14,'hit':12,'death':4}
COUNTS={'idle':12,'walk':16,'attack':18,'hit':8,'death':16}
report={}
for name,fps in FPS.items():
    frames=WORK/'frames'/name
    files=sorted(frames.glob('*.png'));assert len(files)==COUNTS[name]
    encoded=WORK/'cream-frames'/name;encoded.mkdir(parents=True,exist_ok=True)
    for frame in files:
        image=Image.open(frame).convert('RGBA');cream=Image.new('RGBA',image.size,'#f8f4e8');cream.alpha_composite(image);cream.convert('RGB').save(encoded/frame.name)
    output=OUT/f'spearman-0ad-r5-{name}-160.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-stream_loop','2','-i',str(encoded/'%03d.png'),'-frames:v',str(len(files)*3),'-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,pix_fmt,nb_read_frames,r_frame_rate,duration','-of','json',str(output)]))['streams'][0]
    assert probe['codec_name']=='h264' and probe['pix_fmt']=='yuv420p'
    assert probe['width']==probe['height']==160 and int(probe['nb_read_frames'])==len(files)*3
    report[name]={'path':str(output),'source_frames':len(files),'game_fps':fps,**probe}
files=sorted((WORK/'frames/attack-fullrate').glob('*.png'));assert len(files)==36
sheet=Image.new('RGB',(6*160,6*180),'#f8f4e8');draw=ImageDraw.Draw(sheet)
for i,p in enumerate(files):
    img=Image.open(p).convert('RGBA');x=i%6*160;y=i//6*180;sheet.paste(img,(x,y),img)
    draw.text((x+5,y+162),f'{i:02d}  {i/30:.3f}s',fill='#493b2a')
sheet.save(OUT/'spearman-0ad-r5-attack-fullrate.png')
small=[('idle',0),('attack',0),('attack',6),('attack',9),('attack',13)]
sheet=Image.new('RGB',(320,24+len(small)*184),'#f8f4e8');draw=ImageDraw.Draw(sheet)
draw.text((4,5),'160 px sprite',fill='#493b2a');draw.text((164,5),'48 px figure',fill='#493b2a')
for row,(name,i) in enumerate(small):
    for col,folder in enumerate([name,'map48-'+name]):
        img=Image.open(WORK/'frames'/folder/f'{i:03}.png').convert('RGBA')
        sheet.paste(img,(col*160,24+row*184),img)
        draw.text((col*160+4,24+row*184+162),f'{name} {i:02}',fill='#493b2a')
sheet.save(OUT/'spearman-0ad-r5-readability-48.png')
(OUT/'spearman-0ad-r5-video-validation.json').write_text(json.dumps({'asset_sha256':hashlib.sha256(Path(__file__).with_name('spearman.glb').read_bytes()).hexdigest(),'clips':report},indent=2)+'\n')
print(json.dumps(report,indent=2))
