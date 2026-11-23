"""Decode trimmed atlas offsets, show five clips at 2x on cream for eight seconds."""
import json
import os
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
REVIEW = ROOT/'review/3d-v2'
ATLAS = Path('app/src/assets/units/anim/archer.webp')
ORDER = ['idle', 'move', 'attack', 'hit', 'death']


def reconstruct(atlas, rect):
    x,y,w,h,ox,oy = (rect[k] for k in ('x','y','w','h','ox','oy'))
    frame = Image.new('RGBA',(160,160))
    frame.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy))
    return frame


def main():
    meta = json.loads(ATLAS.with_suffix('.json').read_text())
    atlas = Image.open(ATLAS).convert('RGBA')
    frames = {name: [reconstruct(atlas, r) for r in meta['clips'][name]['rects']] for name in ORDER}
    sheet = Image.new('RGB',(1600,5*188),'#eee4d2')
    draw = ImageDraw.Draw(sheet)
    for row,name in enumerate(ORDER):
        for col,frame in enumerate(frames[name]):
            sheet.paste(frame,(col*160,row*188+24),frame)
            draw.text((col*160+5,row*188+5),f'{name} {col+1}',fill='#3c3023')
    sheet.save(REVIEW/'archer-g-decoded-atlas.png')
    comparison=Image.new('RGB',(640,270),'#eee4d2');draw=ImageDraw.Draw(comparison)
    painting=Image.open('app/src/assets/units/archer-256.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
    for k,(label,frame) in enumerate(zip(['painting 160','atlas idle','atlas release','atlas death'],[painting,frames['idle'][0],frames['attack'][4],frames['death'][-1]])):
        draw.text((k*160+5,8),label,fill='#3c3023');comparison.paste(frame,(k*160,30),frame)
        small=frame.resize((64,64),Image.Resampling.LANCZOS);comparison.paste(small,(k*160+48,200),small)
    comparison.save(REVIEW/'archer-g-atlas-check.png')
    movie = REVIEW/f'archer-round{os.environ.get("ROUND","3")}.mp4'
    proc = subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s','1600x348','-r','30','-i','-','-an','-c:v','libx264','-threads','3',
        '-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE)
    enlarged = {name:[f.resize((320,320),Image.Resampling.LANCZOS) for f in frames[name]] for name in ORDER}
    try:
        for t in range(240):
            canvas = Image.new('RGBA',(1600,348),'#eee4d2')
            draw = ImageDraw.Draw(canvas)
            for k,name in enumerate(ORDER):
                c = meta['clips'][name]
                i = int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1)
                canvas.alpha_composite(enlarged[name][i],(k*320,28))
                draw.text((k*320+8,6),name,fill='#3c3023')
            proc.stdin.write(canvas.convert('RGB').tobytes())
    finally:
        proc.stdin.close()
    assert proc.wait()==0,'FFmpeg failed'
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
        '-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(movie)]))['streams'][0]
    assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'],int(probe['nb_frames']))==('h264','yuv420p',1600,348,240),probe
    assert abs(float(probe['duration'])-8)<.01,probe
    (REVIEW/'archer-video.json').write_text(json.dumps({'path':str(movie),**probe},indent=2))
    print('VIDEO_PASS',movie,probe)

if __name__=='__main__':
    main()
