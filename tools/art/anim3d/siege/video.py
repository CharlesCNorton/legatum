"""Eight-second review from the actual decoded v2 atlas, including trim offsets."""
import hashlib,json,os,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from validate import reconstruct
from pack import CLIPS,REVIEW

def sample_index(clip, tick, fps=30):
    # One-shots replay every two seconds and hold their final pose in between.
    elapsed=tick/fps if clip['loop'] else (tick % (2*fps))/fps
    sample=int(elapsed*clip['fps'])
    return sample % clip['frames'] if clip['loop'] else min(sample,clip['frames']-1)

def main():
    path=Path('app/src/assets/units/anim/field-cannon.webp')
    meta=json.loads(path.with_suffix('.json').read_text());assert meta['version']==2
    atlas=Image.open(path).convert('RGBA');cell=meta['frame']['w'];assert cell==meta['frame']['h']==160
    frames={name:[reconstruct(atlas,rect,cell).resize((320,320),Image.Resampling.LANCZOS) for rect in meta['clips'][name]['rects']] for name in CLIPS}
    out=REVIEW/f"field-cannon-round{os.environ.get('ROUND','3')}.mp4"
    # Stream RGB to one bounded encoder instead of 240 temporary PNG files.
    cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x348','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for tick in range(240):
            canvas=Image.new('RGBA',(1600,348),(240,232,214,255));draw=ImageDraw.Draw(canvas)
            for col,name in enumerate(CLIPS):
                index=sample_index(meta['clips'][name],tick)
                canvas.alpha_composite(frames[name][index],(col*320,28));draw.text((col*320+8,6),name,fill=(60,50,40,255))
            proc.stdin.write(canvas.convert('RGB').tobytes())
        proc.stdin.close()
        assert proc.wait()==0,'Video encoder failed'
    except BaseException:
        proc.kill();proc.wait();raise
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames:format=duration','-of','json',str(out)]))
    stream=probe['streams'][0]
    assert (stream['codec_name'],stream['pix_fmt'],stream['width'],stream['height'],int(stream['nb_frames']))==('h264','yuv420p',1600,348,240)
    assert abs(float(probe['format']['duration'])-8)<.04
    probe['atlas_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    (REVIEW/f'field-cannon-round{os.environ.get("ROUND","3")}-video.json').write_text(json.dumps(probe,indent=2))
    print('PASS: decoded trimmed atlas video, five clips, H.264 yuv420p, 1600x348, 240 frames / 8 seconds',out)
if __name__=='__main__':main()
