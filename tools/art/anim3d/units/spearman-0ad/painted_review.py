"""Package the delivered-GLB CPU renders, with three loops at game sampling fps."""
import json,os,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
UNIT=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'lanes/spearman-0ad-painted-r2';OUT=ROOT/'review/3d-v2';OUT.mkdir(parents=True,exist_ok=True)
PREFIX='spearman-0ad-painted-r2';frames=WORK/'frames'
asset=UNIT/'spearman.glb'
assert (WORK/'render.json').stat().st_mtime>=asset.stat().st_mtime,'Render has not completed for this GLB'
manifest=json.loads((WORK/'render.json').read_text());receipts={}
def fresh(path):
    assert path.stat().st_mtime>=asset.stat().st_mtime,f'Stale render: {path}'
    return path
def cream(path,size=None):
    if str(path).startswith(str(frames)):fresh(path)
    im=Image.open(path).convert('RGBA')
    if size:im=im.resize(size,Image.Resampling.LANCZOS)
    bg=Image.new('RGBA',im.size,'#f8f4e8');bg.alpha_composite(im);return bg.convert('RGB')
for name,clip in manifest['clips'].items():
    count=clip['count'];fps=clip['fps'];encoded=WORK/'cream-frames'/name;encoded.mkdir(parents=True,exist_ok=True)
    for i in range(count):cream(frames/name/f'{i:03}.png').save(encoded/f'{i:03}.png')
    output=OUT/f'{PREFIX}-{name}-160.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-stream_loop','2','-i',str(encoded/'%03d.png'),'-frames:v',str(count*3),'-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,pix_fmt,nb_read_frames,r_frame_rate,duration','-of','json',str(output)]))['streams'][0]
    assert stream['width']==stream['height']==160 and int(stream['nb_read_frames'])==count*3
    assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
    assert stream['r_frame_rate']==f'{fps}/1'
    receipts[name]={'path':str(output),'source_frames':count,'game_fps':fps,'glb_duration':clip['duration'],'sampled_loop_duration':count/fps,**stream}
small=[('idle',0),('attack',0),('attack',4),('attack',8),('attack',12)]
sheet=Image.new('RGB',(320,24+len(small)*184),'#f8f4e8');draw=ImageDraw.Draw(sheet)
draw.text((4,5),'160 px sprite',fill='#493b2a');draw.text((164,5),'48 px figure / LOD1',fill='#493b2a')
for row,(name,i) in enumerate(small):
    for col,folder in enumerate([name,'map48-'+name]):
        sheet.paste(cream(frames/folder/f'{i:03}.png'),(col*160,24+row*184))
        draw.text((col*160+4,24+row*184+162),f'{name} {i:02}',fill='#493b2a')
sheet.save(OUT/f'{PREFIX}-readability-48.png')
repo=UNIT.parents[4]
sheet=Image.new('RGB',(1024,552),'#f8f4e8');draw=ImageDraw.Draw(sheet)
sheet.paste(cream(repo/'app/src/assets/units/spearman-panel.png',(512,512)),(0,32))
sheet.paste(cream(frames/'still-idle/000.png'),(512,32))
draw.text((16,12),'Reference painting | 512 px',fill='#493b2a');draw.text((528,12),'Painted r2 | delivered LOD0 | Cycles CPU / AgX',fill='#493b2a')
sheet.save(OUT/f'{PREFIX}-vs-panel.png')
sheet=Image.new('RGB',(1536,552),'#f8f4e8');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['shield','helmet','crest']):
    sheet.paste(cream(frames/f'{name}-close.png'),(i*512,32));draw.text((i*512+16,12),name.title()+' | delivered LOD0',fill='#493b2a')
sheet.save(OUT/f'{PREFIX}-closeups.png')
# Representative motion strip for visual checking; this is not a playing-speed review.
sheet=Image.new('RGB',(640,5*184),'#f8f4e8');draw=ImageDraw.Draw(sheet)
for row,(name,clip) in enumerate(manifest['clips'].items()):
    for col in range(4):
        i=round((clip['count']-1)*col/3);sheet.paste(cream(frames/name/f'{i:03}.png'),(col*160,row*184));draw.text((col*160+4,row*184+162),f'{name} {i:02}',fill='#493b2a')
sheet.save(OUT/f'{PREFIX}-motion-sheet.png')
report={'asset_sha256':hashlib.sha256((UNIT/'spearman.glb').read_bytes()).hexdigest(),'render':'Cycles CPU, AgX; browser ACES recording is a separate lead handoff','clips':receipts}
(OUT/f'{PREFIX}-video-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
