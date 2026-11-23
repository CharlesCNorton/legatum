"""Ten-second painting/animation comparison of the actual graded frame sequence."""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER=ROOT/'masters/spearman-3d-v2'
output=ROOT/'review/3d-v2/spearman-round3.mp4'
painting=Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
clips={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','544x380','-r','24','-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-threads','2','-crf','18','-pix_fmt','yuv420p',str(output)]
process=subprocess.Popen(command,stdin=subprocess.PIPE)
try:
 for clip,(count,fps,loop) in clips.items():
  frames=[Image.open(MASTER/'renders'/('e-'+clip)/f'{i:02}.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS) for i in range(count)]
  for i in range(48):
   t=i/24
   index=int(t*fps)%count if loop else min(count-1,int(t*fps))
   frame=Image.new('RGB',(544,380),(224,215,191));draw=ImageDraw.Draw(frame)
   for x,label,im in [(8,'Painting',painting),(280,'3D: '+clip,frames[index])]:
    draw.text((x,10),label,fill=(40,34,27));frame.paste(im,(x,36),im)
    small=im.resize((64,64),Image.Resampling.LANCZOS);frame.paste(small,(x+96,302),small)
   process.stdin.write(frame.tobytes())
finally:
 process.stdin.close()
assert process.wait()==0,'Video encoder failed'
print(output)
