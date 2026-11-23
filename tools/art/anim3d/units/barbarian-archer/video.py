"""Decode trimmed atlas frames and verify the driver's eight-second review movie."""
import json
import os
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw
from deliver import A, C, R, SLUG


def movie():
    meta = json.loads((A / f'{SLUG}.json').read_text())
    atlas = Image.open(A / f'{SLUG}.webp').convert('RGBA')
    clips = {}
    for name in C:
        frames = []
        for r in meta['clips'][name]['rects']:
            cell = Image.new('RGBA', (160, 160))
            crop = atlas.crop((r['x'], r['y'], r['x']+r['w'], r['y']+r['h']))
            cell.paste(crop, (r['ox'], r['oy']))
            frames.append(cell.resize((320, 320), Image.Resampling.LANCZOS))
        clips[name] = frames
    out = R / f'{SLUG}-round{os.environ.get("ROUND", "2")}.mp4'
    command = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', '1600x348', '-r', '30', '-i', '-', '-an', '-c:v', 'libx264',
               '-threads', '3', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', str(out)]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for frame in range(240):
            canvas = Image.new('RGBA', (1600, 348), (240,232,214,255))
            draw = ImageDraw.Draw(canvas)
            for column, (name, (n, fps, loop)) in enumerate(C.items()):
                index = int(frame/30*fps) % n if loop else min(int((frame%60)/30*fps),n-1)
                canvas.alpha_composite(clips[name][index], (column*320,28))
                draw.text((column*320+8,6),name,fill=(60,50,40,255))
            encoder.stdin.write(canvas.convert('RGB').tobytes())
        encoder.stdin.close()
        assert encoder.wait() == 0, 'Movie encoding failed'
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams',
                                                '-show_format','-of','json',str(out)]))
    stream = probe['streams'][0]
    assert (stream['codec_name'], stream['pix_fmt'], stream['width'], stream['height']) == ('h264','yuv420p',1600,348)
    assert int(stream['nb_frames']) == 240 and abs(float(probe['format']['duration'])-8)<.01
    (R/f'{SLUG}-video-validation.json').write_text(json.dumps(probe,indent=2))
    print(f'PASS: {out}: H.264 yuv420p, 1600x348, 240 frames, 8 seconds')


if __name__ == '__main__':
    movie()
