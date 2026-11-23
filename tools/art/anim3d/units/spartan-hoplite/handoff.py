"""GPU master gate and movie from decoded trimmed frames, never fixed cells."""
import json, os, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from deliver import M, R, REV, SLUG, CLIPS, OUT, sha

def verify_gpu():
 for stage,count in [('b',3),('c',1),('d',4)]+[('e-'+c,v[0]) for c,v in CLIPS.items()]:
  source=M/'clips'/stage[2:]/(stage[2:]+'.blend') if stage.startswith('e-') else M/'clips/attack/attack.blend' if stage=='d' else M/('plain.blend' if stage=='b' else 'spearman.blend')
  for size in [512,256]:
   folder=M/str(size)/stage
   assert (folder/'render.json').is_file(),('Missing fresh GPU master',stage,size)
   meta=json.loads((folder/'render.json').read_text())
   assert (meta['engine'],meta['device'],meta['resolution'],meta['samples'])==('CYCLES','GPU',512,64),('Not final GPU512/64',stage,meta)
   assert meta['source_master_sha256']==sha(M/'spearman.blend')
   assert meta['blend_sha256']==sha(source)
   if stage!='b':assert meta['grade_sha256']==sha(M/'grade.json')
   for i in range(count):assert Image.open(folder/f'{i:02}.png').size==(size,size)
 feet=json.loads((M/'feet/evidence.json').read_text())
 assert feet['device']=='GPU' and feet['samples']==64
 assert feet['clip_sha256']==sha(M/'clips/move/move.blend')
 assert len(feet['records'])==8
 assert feet['contact_check']['tested_stance_intervals']>0
 assert feet['contact_check']['max_support_yaw_deg']<20
 assert feet['contact_check']['max_sole_yaw_deg']<20
 assert feet['contact_check']['max_sole_ground_error_m']<.025
 for view in ['top','front']:
  for i in range(8):assert Image.open(M/f'feet/{view}-{i:02}.png').size==(256,256)
 assert (REV/(SLUG+'-g-feet-check.png')).is_file()
 print('GPU MASTER GATE PASSED: every stage GPU512/64, current hashes, 256 derivatives')

def video():
 meta=json.loads((OUT/(SLUG+'.json')).read_text());atlas=Image.open(OUT/(SLUG+'.webp')).convert('RGBA')
 frames={}
 for clip,(count,_,_) in CLIPS.items():
  frames[clip]=[]
  for r in meta['clips'][clip]['rects']:
   frame=Image.new('RGBA',(160,160));frame.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']))
   frames[clip].append(frame.resize((320,320),Image.Resampling.LANCZOS))
  assert len(frames[clip])==count
 out=REV/f'{SLUG}-round{os.environ.get("ROUND","3")}.mp4'
 proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x348','-framerate','30','-i','-','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for t in range(240):
  canvas=Image.new('RGBA',(1600,348),(240,232,214,255));draw=ImageDraw.Draw(canvas)
  for k,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
   i=int(t/30*fps)%count if loop else min(int((t%60)/30*fps),count-1)
   canvas.alpha_composite(frames[clip][i],(k*320,28));draw.text((k*320+8,6),clip,fill=(60,50,40,255))
  proc.stdin.write(canvas.convert('RGB').tobytes())
 proc.stdin.close();assert proc.wait()==0
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(out)]))['streams'][0]
 assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'],int(probe['nb_frames']),float(probe['duration']))==('h264','yuv420p',1600,348,240,8.0),probe
 (REV/f'{SLUG}-video-validation.json').write_text(json.dumps({'path':str(out),'probe':probe,'atlas_sha256':sha(OUT/(SLUG+'.webp'))},indent=2))
 print('VIDEO VERIFIED',out,probe)
