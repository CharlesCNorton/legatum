"""Native-size coverage A/B with one frozen round-9 grade and explicit ROIs."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from grade import apply

ROOT = Path.home()/'LegatumRuns/anim-pilot'
WORK = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'lanes/spearman-r10b'
OUT = ROOT/'review/3d-v2'
AB = WORK/'coverage-ab'
BG = (224, 215, 191)


def resize(image, size):
    """Linear-light, premultiplied RGBA resize for native sprite inspection."""
    p = np.asarray(image, dtype=float)/255
    a = p[:, :, 3]
    c = np.where(p[:, :, :3] <= .04045, p[:, :, :3]/12.92, ((p[:, :, :3]+.055)/1.055)**2.4)
    def channel(x):
        return np.asarray(Image.fromarray(x.astype(np.float32)).resize((size, size), Image.Resampling.LANCZOS))
    alpha = np.clip(channel(a), 0, 1)
    rgb = np.stack([channel(c[:, :, i]*a) for i in range(3)], axis=-1)
    rgb = np.clip(rgb/np.maximum(alpha[:, :, None], 1e-8), 0, 1)
    rgb = np.where(rgb <= .0031308, rgb*12.92, 1.055*rgb**(1/2.4)-.055)
    return Image.fromarray(np.rint(np.dstack([rgb, alpha])*255).astype(np.uint8))


def main():
    painting_path = Path('app/src/assets/units/spearman-256.png')
    painting = Image.open(painting_path).convert('RGBA')
    lut_path = ROOT/'lanes/spearman-r9-merge/masters/spearman-3d-v2/painting-grade.json'
    luts = json.loads(lut_path.read_text())['luts']
    receipt = json.loads((AB/'receipt.json').read_text())
    poses = list(receipt['poses'])
    poses.sort(key=lambda p: (p != 'rest', p.startswith('death'), p))
    metrics = {'coverage_script_sha256': receipt['coverage_script_sha256'], 'grade_policy': 'Identical frozen round-9 LUT for all before/after poses; no per-frame fit.',
               'grade_sha256': hashlib.sha256(lut_path.read_bytes()).hexdigest(), 'poses': {}}
    for pose in poses:
        before_raw = Image.open(AB/(pose+'-before.png')).convert('RGBA')
        after_raw = Image.open(AB/(pose+'-after.png')).convert('RGBA')
        before, after = [apply(im, luts) for im in [before_raw, after_raw]]
        images = [('Painting', painting), ('Round 9 | CPU', before), ('R10b | CPU', after)]
        sheet = Image.new('RGB', (816, 604), BG); draw = ImageDraw.Draw(sheet)
        for row, (size, y) in enumerate([(256, 28), (160, 320), (64, 524)]):
            for col, (label, im) in enumerate(images):
                x = col*272+(272-size)//2
                draw.text((col*272+8, y-20), f'{label} | {size}px | {pose}', fill=(40,34,27))
                scaled = resize(im, size); sheet.paste(scaled, (x,y), scaled)
        sheet.save(OUT/f'spearman-r10b-{pose}-compare.png')
        # Preserve separately named raw comparisons: colour gain cannot be
        # attributed to refitting a histogram grade or denoiser.
        rawsheet = Image.new('RGB', (816, 284), BG); d = ImageDraw.Draw(rawsheet)
        for col, (label, im) in enumerate([('Painting', painting), ('Round 9 raw CPU', before_raw), ('R10b raw CPU', after_raw)]):
            d.text((col*272+8, 7), label+' | '+pose, fill=(40,34,27)); rawsheet.paste(im,(col*272+8,28),im)
        rawsheet.save(OUT/f'spearman-r10b-{pose}-raw.png')
        b, a = np.array(before_raw), np.array(after_raw)
        opaque = (b[:,:,3]>240)&(a[:,:,3]>240)
        diff = np.max(np.abs(a[:,:,:3].astype(int)-b[:,:,:3].astype(int)), axis=2)
        report = {'alpha_identical': bool(np.array_equal(a[:,:,3], b[:,:,3])),
                  'changed_opaque_pixels_gt8': int(((diff>8)&opaque).sum())}
        if pose == 'rest':
            box = (93,94,130,143); x0,y0,x1,y1=box
            p = np.array(painting); shared=opaque[y0:y1,x0:x1]&(p[y0:y1,x0:x1,3]>240)
            report['shoulder_roi_xyxy'] = box
            report['shoulder_rgb_mae_to_painting'] = {label: float(np.abs(np.asarray(im).astype(float)[y0:y1,x0:x1,:3]-p[y0:y1,x0:x1,:3])[shared].mean()) for label,im in [('before',before),('after',after)]}
        # Fixed shoulder-shell ROI for the peak hit. This measures lost pale
        # exposure, not colour agreement with a nonexistent painted hit pose.
        if pose == 'hit-1':
            box=(138,103,162,140);x0,y0,x1,y1=box
            report['pale_patch_roi_xyxy']=box
            report['pale_low_chroma_pixels']={}
            for label,im in [('before',before),('after',after)]:
                rgb=np.array(im)[y0:y1,x0:x1,:3].astype(float)
                valid=np.array(im)[y0:y1,x0:x1,3]>240
                pale=(rgb.mean(axis=2)>145)&((rgb.max(axis=2)-rgb.min(axis=2))<80)&valid
                report['pale_low_chroma_pixels'][label]=int(pale.sum())
            report['pale_low_chroma_pixels_160']={}
            small_box=tuple(round(v*160/256) for v in box)
            report['pale_patch_roi_160_xyxy']=small_box
            for label, im in [('before', before), ('after', after)]:
                data=np.asarray(resize(im,160).crop(small_box)).astype(float)
                rgb=data[:,:,:3]
                pale=(rgb.mean(axis=2)>145)&((rgb.max(axis=2)-rgb.min(axis=2))<80)&(data[:,:,3]>240)
                report['pale_low_chroma_pixels_160'][label]=int(pale.sum())
        metrics['poses'][pose]=report
    (OUT/'spearman-r10b-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(json.dumps(metrics,indent=2))


if __name__ == '__main__':
    main()
