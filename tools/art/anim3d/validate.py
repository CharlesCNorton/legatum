"""Validate decoded deliverables, exact cadence, stationary stone and held death."""
import json
from pathlib import Path
from PIL import Image, ImageChops
from pack import ROOT, MASTER, CLIPS


def main():
    path=ROOT/'app/src/assets/units/anim/spearman-3d.webp'
    meta=json.loads(path.with_suffix('.json').read_text())
    assert path.stat().st_size<=200_000, 'atlas exceeds 200 KB'
    assert meta['frame']==dict(w=256,h=256,ax=127,ay=221)
    atlas=Image.open(path).convert('RGBA');assert atlas.size==(2560,1280)
    for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
        assert meta['clips'][clip]==dict(row=row,frames=n,fps=fps,loop=loop)
        for i in range(n):
            frame=atlas.crop((i*256,row*256,(i+1)*256,(row+1)*256))
            alpha=frame.getchannel('A');bbox=alpha.getbbox()
            assert bbox and min(bbox[:2])>1 and max(bbox[2:])<255,(clip,i,'clipped',bbox)
            assert alpha.getextrema()==(0,255),(clip,i,'missing transparency/opaque surface')
            # Compare coverage at both exposed front edges, not RGB: real
            # contact shadows must be allowed to change as the body collapses.
            for box in ((85,235,96,246),(155,235,168,246)):
                expected=atlas.crop(box).getchannel('A')
                observed=frame.crop(box).getchannel('A')
                assert ImageChops.difference(expected,observed).getbbox() is None,(clip,i,'moving stone edge')
            assert frame.crop((82,230,87,233)).getchannel('A').getextrema()==(255,255),(clip,i,'stone rim absent')
        if n<10:
            assert atlas.crop((n*256,row*256,2560,(row+1)*256)).getchannel('A').getbbox() is None
    source=Image.open(ROOT/'app/src/assets/units/spearman-256.png').convert('RGBA')
    source_bounds=source.getchannel('A').getbbox()
    neutral_bounds=atlas.crop((0,0,256,256)).getchannel('A').getbbox()
    assert max(abs(a-b) for a,b in zip(source_bounds,neutral_bounds))<=10,('neutral framing',source_bounds,neutral_bounds)
    # Raw last three poses must be identical (not merely similar encoded cells).
    death=[Image.open(MASTER/'frames/death'/f'{i:02}.png').tobytes() for i in (7,8,9)]
    assert death[0]==death[1]==death[2],'death does not remain planted'
    # Idle/move/hit must actually move, independently of WebP artefacts.
    for clip,(n,_,_) in CLIPS.items():
        raw=[Image.open(MASTER/'frames'/clip/f'{i:02}.png').convert('RGBA') for i in range(n)]
        diffs=[ImageChops.difference(raw[0],im).convert('RGB').getbbox() for im in raw[1:]]
        assert any(diffs),(clip,'still frames')
    print('PASS: 40 frames; exact metadata; <=200 KB; alpha; bounds; padding; stationary stone; source framing; held death; all clips move')


if __name__=='__main__':main()
