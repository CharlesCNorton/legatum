"""Same-settings R10/R11b CPU review, fixed grade and broad-tone diagnostics."""
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from grade import apply
from kit.images import resize_rgba
from kit.critique import best_iou, rgb_to_lab, shift_array, on_cream

ROOT=Path.home()/'LegatumRuns/anim-pilot'
WORK=Path(os.environ.get('ANIM_ROOT',str(ROOT/'lanes/spearman-r11b')))
OUT=ROOT/'review/3d-v2'
AB=WORK/'fold-ab'
PAINT=Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
LUT=WORK/'round10-grade.json'
TABLES=json.loads(LUT.read_text())['luts']
BOXES={'shoulder':(93,94,130,143),'cloak':(98,120,113,176),
       'inner_thigh_cloak':(119,168,137,178),'shield_rim':(168,117,182,170),
       'shield':(136,107,181,172),'torso':(112,110,138,152),'legs':(93,172,164,221),'base':(76,224,180,242)}


def tone(image):
    p=np.asarray(image)
    cream=on_cream(image,p[:,:,3]>8)
    return np.asarray(cream.filter(ImageFilter.GaussianBlur(2)))


def rest_metrics(images):
    p=np.asarray(PAINT);pm=p[:,:,3]>8
    result={}
    for label,im in images:
        a=np.asarray(im);iou,dx,dy,mask=best_iou(pm,a[:,:,3]>8)
        shared=pm&mask
        rgb=shift_array(a[:,:,:3],dx,dy)
        raw=np.linalg.norm(rgb_to_lab(p[:,:,:3])-rgb_to_lab(rgb),axis=2)
        blurred=np.linalg.norm(rgb_to_lab(tone(PAINT))-rgb_to_lab(shift_array(tone(im),dx,dy)),axis=2)
        result[label]={'iou':iou,'offset':[dx,dy],'raw_delta_e':float(raw[shared].mean()),'sigma2_delta_e':float(blurred[shared].mean()),'regions':{}}
        for name,(x0,y0,x1,y1) in BOXES.items():
            valid=(p[y0:y1,x0:x1,3]>240)&(a[y0:y1,x0:x1,3]>240)
            pa=p[y0:y1,x0:x1,:3][valid].astype(float);ra=a[y0:y1,x0:x1,:3][valid].astype(float)
            lum=ra @ np.array([.2126,.7152,.0722]);plum=pa @ np.array([.2126,.7152,.0722])
            delta=np.linalg.norm(rgb_to_lab(tone(PAINT))[y0:y1,x0:x1]-rgb_to_lab(tone(im))[y0:y1,x0:x1],axis=2)
            result[label]['regions'][name]={'box':(x0,y0,x1,y1),'pixels':int(valid.sum()),'rgb_mae':float(np.abs(pa-ra).mean()),'sigma2_delta_e':float(delta[valid].mean()),'mean_luma':float(lum.mean()),'p90_luma':float(np.percentile(lum,90)),'painting_mean_luma':float(plum.mean()),'painting_p90_luma':float(np.percentile(plum,90))}
    return result


def main():
    receipt=json.loads((AB/'receipt.json').read_text())
    report={'settings':{k:v for k,v in receipt.items() if k!='poses'},'grade_policy':'Same frozen round-10 LUT for every A/B; no refit or per-frame fit.','grade_sha256':hashlib.sha256(LUT.read_bytes()).hexdigest(),'blur_policy':'Gaussian sigma 2 on cream-composited sRGB at 256; same silhouette offset for global raw/blurred values; opaque same-position overlap for regional metrics.','poses':{}}
    for pose in receipt['poses']:
        if not (AB/(pose+'-before.png')).exists():
            continue
        raw=[Image.open(AB/(pose+'-'+side+'.png')).convert('RGBA') for side in ['before','after']]
        before,after=[apply(im,TABLES) for im in raw]
        for side,im in [('before',before),('after',after)]:im.save(AB/(pose+'-'+side+'-graded.png'))
        sheet=Image.new('RGB',(816,604),(224,215,191));draw=ImageDraw.Draw(sheet)
        for size,y in [(256,28),(160,320),(64,524)]:
            for col,(label,im) in enumerate([('Painting (rest)',PAINT),('Round 10 CPU',before),('R11b CPU',after)]):
                x=col*272+(272-size)//2
                draw.text((col*272+8,y-20),f'{label} | {size}px | {pose}',fill=(40,34,27))
                thumb=resize_rgba(im,(size,size));sheet.paste(thumb,(x,y),thumb)
        sheet.save(OUT/f'spearman-r11b-{pose}-compare.png')
        b,a=[np.asarray(im) for im in raw]
        report['poses'][pose]={'alpha_identical':bool(np.array_equal(a[:,:,3],b[:,:,3])),'invariants_identical':receipt['poses'][pose]['invariants_before']==receipt['poses'][pose]['invariants_after']}
        if pose=='rest':
            report['rest']=rest_metrics([('before',before),('after',after)])
            report['rest_raw']=rest_metrics([('before',raw[0]),('after',raw[1])])
        if pose=='hit-1':
            box=(138,103,162,140)
            report['poses'][pose]['pale_shoulder_pixels']={}
            for label,im in [('before',before),('after',after)]:
                p=np.asarray(im.crop(box)).astype(float);rgb=p[:,:,:3]
                report['poses'][pose]['pale_shoulder_pixels'][label]=int(((rgb.mean(2)>145)&(np.ptp(rgb,axis=2)<80)&(p[:,:,3]>240)).sum())
    # Current material previews on the unchanged, baked round-10 motions.
    # These are lossless 160 reductions, not a decoded production atlas.
    for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
        for i in range(count):
            src=AB/f'{clip}-{i}-after.png'
            if not src.exists():
                continue
            dst=WORK/'frames-160'/clip/f'{i:02}.png'
            dst.parent.mkdir(parents=True,exist_ok=True)
            im=apply(Image.open(src).convert('RGBA'),TABLES)
            resize_rgba(im,(160,160)).save(dst)
    (OUT/'spearman-r11b-metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report.get('rest',{}),indent=2))

if __name__=='__main__':main()
