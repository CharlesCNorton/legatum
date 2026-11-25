"""Encode the actual GLB renders at existing game rates and assemble review sheets."""
import hashlib, json, os, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'oad/pbr-r3';OUT=ROOT/'review/3d-v2';UNIT=Path(__file__).resolve().parent
PREFIX='spearman-0ad-pbr-r3'
FPS={'idle':4,'walk':6,'attack':14,'hit':12,'death':4};COUNTS={'idle':12,'walk':16,'attack':18,'hit':8,'death':16}
OUT.mkdir(parents=True,exist_ok=True)
def cream(path):
    im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,'#f8f4e8');bg.alpha_composite(im);return bg.convert('RGB')
report={}
for name,fps in FPS.items():
    files=sorted((WORK/'frames'/name).glob('*.png'));assert len(files)==COUNTS[name]
    frames=WORK/'cream-frames'/name;frames.mkdir(parents=True,exist_ok=True)
    for p in files:cream(p).save(frames/p.name)
    output=OUT/f'{PREFIX}-{name}-160.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-stream_loop','2','-i',str(frames/'%03d.png'),'-frames:v',str(len(files)*3),'-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,pix_fmt,nb_read_frames,r_frame_rate,duration','-of','json',str(output)]))['streams'][0]
    assert stream['width']==stream['height']==160 and int(stream['nb_read_frames'])==len(files)*3 and stream['pix_fmt']=='yuv420p'
    report[name]={'game_fps':fps,'source_frames':len(files),**stream}
small=[('idle',0),('attack',0),('attack',6),('attack',9),('attack',13)]
sheet=Image.new('RGB',(320,24+len(small)*184),'#f8f4e8');draw=ImageDraw.Draw(sheet)
draw.text((4,5),'160 px sprite',fill='#493b2a');draw.text((164,5),'48 px figure | LOD1',fill='#493b2a')
for row,(name,i) in enumerate(small):
    for col,folder in enumerate([name,'map48-'+name]):
        sheet.paste(cream(WORK/'frames'/folder/f'{i:03}.png'),(col*160,24+row*184));draw.text((col*160+4,24+row*184+162),f'{name} {i:02}',fill='#493b2a')
sheet.save(OUT/f'{PREFIX}-readability-48.png')
panel=UNIT.parents[4]/'app/src/assets/units/spearman-panel.png'
sheet=Image.new('RGB',(1024,544),'#f8f4e8');sheet.paste(cream(panel),(0,0));sheet.paste(cream(WORK/'hero.png'),(512,0));draw=ImageDraw.Draw(sheet);draw.text((16,520),'Reference painting | 512 px',fill='#493b2a');draw.text((528,520),'PBR r3 | delivered GLB | Cycles CPU',fill='#493b2a');sheet.save(OUT/f'{PREFIX}-vs-panel.png')
sheet=Image.new('RGB',(1536,544),'#f8f4e8');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['shield','helmet','crest']):
    sheet.paste(cream(WORK/f'{name}-close.png'),(i*512,0));draw.text((i*512+16,520),name+' | LOD0, shipped 1024 textures',fill='#493b2a')
sheet.save(OUT/f'{PREFIX}-closeups.png')
# Inspect motion without relying on identical animation data to imply collision safety.
sheet=Image.new('RGB',(5*160,4*184),'#f8f4e8');draw=ImageDraw.Draw(sheet)
for col,name in enumerate(FPS):
    files=sorted((WORK/'frames'/name).glob('*.png'))
    for row in range(4):
        i=round((len(files)-1)*row/3)
        sheet.paste(cream(files[i]),(col*160,row*184));draw.text((col*160+8,row*184+162),f'{name} | sample {i}',fill='#493b2a')
sheet.save(OUT/f'{PREFIX}-motion-contact.png')
receipt={'asset_sha256':hashlib.sha256((UNIT/'spearman.glb').read_bytes()).hexdigest(),'clips':report,'render':'Cycles CPU, AgX, actual shipped GLB; browser ACES evidence is a separate host capture','timing':'Legacy game sprite rates, three loops. GLB clip timings remain round-6 exact.'}
(OUT/f'{PREFIX}-video-validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if (WORK/'deformation.json').exists() and (WORK/'joints').exists():
    audit=json.loads((WORK/'deformation.json').read_text())
    sheet=Image.new('RGB',(960,5*352),'#f8f4e8');draw=ImageDraw.Draw(sheet)
    for row,name in enumerate(FPS):
        for col,group in enumerate(('shoulders','elbows','knees')):
            sample=audit['clips'][name][group]
            sheet.paste(cream(WORK/'joints'/f'{name}-{group}.png'),(col*320,row*352))
            draw.text((col*320+4,row*352+323),f"{name} {group} | {sample['sample_time_s']:.3f}s",fill='#493b2a')
            draw.text((col*320+4,row*352+337),f"minimum LBS axis scale {sample['minimum_axis_scale']:.3f}",fill='#493b2a')
    sheet.save(OUT/f'{PREFIX}-joint-check.png')
turn=sorted((WORK/'cycles-turntable').glob('*.png'))
if turn:
    assert len(turn)==96
    directory=WORK/'cream-turntable';directory.mkdir(exist_ok=True)
    for p in turn:cream(p).save(directory/p.name)
    output=OUT/f'{PREFIX}-cycles-turntable.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','8','-i',str(directory/'%03d.png'),'-frames:v','96','-c:v','libx264','-crf','16','-pix_fmt','yuv420p',str(output)],check=True)
    stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,nb_read_frames,r_frame_rate,duration,pix_fmt','-of','json',str(output)]))['streams'][0]
    assert int(stream['nb_read_frames'])==96 and stream['width']==stream['height']==256
    (OUT/f'{PREFIX}-cycles-turntable-validation.json').write_text(json.dumps({'asset_sha256':receipt['asset_sha256'],'render':'Cycles CPU, AgX, delivered GLB',**stream},indent=2)+'\n')
