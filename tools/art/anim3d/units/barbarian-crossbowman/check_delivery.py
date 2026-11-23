"""Independent final-master and decoded-video checks, including stale-input rejection."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=R/'masters/barbarian-crossbowman'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gpu():
    for stage,count in {'b':3,'c':1,'d':4,'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}.items():
        source=M/('plain.blend' if stage=='b' else 'clips/attack.blend' if stage=='d' else 'clips/'+stage[2:]+'.blend' if stage.startswith('e-') else 'model.blend')
        for size in [256,512]:
            folder=M/'frames'/str(size)/stage;meta=json.loads((folder/'render.json').read_text())
            assert meta['engine']=='CYCLES' and meta['device']=='GPU', 'Final masters require GPU: '+stage
            assert meta['resolution']==512 and meta['derived_resolution']==size and meta['samples']>=64, 'Final settings: '+stage
            assert meta['source_sha256']==sha(source), 'Stale source: '+stage
            if stage!='b':assert meta['grade_sha256']==sha(M/'grade.json'), 'Stale grade: '+stage
            assert meta['frames']==count
            for i in range(count):assert Image.open(folder/f'{i:02d}.png').size==(size,size)
    print('GPU_MASTERS_OK all stages GPU64/512 and gallery256')
def video():
    p=R/'review/3d-v2'/f'barbarian-crossbowman-round{os.environ.get("ROUND","2")}.mp4'
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(p)]))['streams'][0]
    assert data['codec_name']=='h264' and data['pix_fmt']=='yuv420p'
    assert (data['width'],data['height'],int(data['nb_frames']))==(1600,348,240)
    assert abs(float(data['duration'])-8)<.01
    (M/'video-validation.json').write_text(json.dumps(data,indent=2));print('VIDEO_OK',data)
if __name__=='__main__':{'gpu':gpu,'video':video}[sys.argv[1]]()
