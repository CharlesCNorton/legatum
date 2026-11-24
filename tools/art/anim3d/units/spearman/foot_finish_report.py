"""Assemble CPU or host-GPU A/B; never mix engines in an improvement claim."""
import json
import os
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.images import resize_rgba
from kit.regions import region_stats, luminance
from kit.critique import painting_mask, best_iou, rgb_to_lab, blurred_rgb


def main():
    mode = sys.argv[1]
    assert mode in ('proxy', 'beauty')
    root = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
    folder = Path(sys.argv[2]) if len(sys.argv)>2 else root/'lanes/spearman-r15b'/mode
    review = root/'review/3d-v2'; review.mkdir(parents=True, exist_ok=True)
    prefix = 'spearman-r15b-' + ('cpu' if mode=='proxy' else 'gpu')
    receipt = json.loads((folder/'receipt.json').read_text())
    assert receipt['mode'] == mode
    painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
    def frame(variant, clip, i=0):
        return Image.open(folder/variant/clip/f'{i:02}.png').convert('RGBA')
    def paste(sheet, im, pos, size):
        im = resize_rgba(im, (size,size), space='display')
        sheet.paste(im, pos, im)
    painting256 = painting
    for size in (256,160,64):
        painting = Image.open('app/src/assets/units/spearman-64.png').convert('RGBA') if size == 64 else painting256
        sheet = Image.new('RGB',(size*3,size+36),(248,244,230)); draw = ImageDraw.Draw(sheet)
        for i,(label,im) in enumerate([('Painting',painting),('R14 look',frame('before','rest')),('R15b look',frame('after','rest'))]):
            draw.text((i*size+3,3),label,fill='black'); paste(sheet,im,(i*size,30),size)
        sheet.save(review/f'{prefix}-rest-{size}.png')
        if 'pools' in receipt['clips']['rest']['variants']:
            draw.rectangle((2*size,0,3*size,size+36),fill=(248,244,230))
            draw.text((2*size+3,3),'Pools: candidate',fill='black')
            paste(sheet,frame('pools','rest'),(2*size,30),size)
            sheet.save(review/f'{prefix}-pools-rest-{size}.png')
        for clip in receipt['clips']:
            if clip == 'rest': continue
            count = len(receipt['clips'][clip]['variants']['after']['frames'])
            sheet = Image.new('RGB',((count+1)*size,2*(size+28)),(248,244,230)); draw=ImageDraw.Draw(sheet)
            for row,variant in enumerate(('before','after')):
                draw.text((4,row*(size+28)+4),variant+' | '+receipt['engine'],fill='black')
                for i in range(count): paste(sheet,frame(variant,clip,i),(i*size,row*(size+28)+28),size)
                paste(sheet,painting,(count*size,row*(size+28)+28),size)
            sheet.save(review/f'{prefix}-{clip}-{size}.png')
    painting = painting256
    boxes = {1:(154,198,166,211),5:(120,198,133,212)}
    stats = {'engine': receipt['engine'], 'flash_boxes_at_256': boxes, 'move': {}, 'rest': {},
             'shadow_strength': {'before': 1., 'after_rest': 1., 'after_move': .4, 'rest_pools_candidate': .4}, 'anchor_error_max_m': 0.,
             'geometry_weights_uvs_pose_actions_unchanged': True}
    for i,box in boxes.items():
        stats['move'][i] = {v: region_stats(frame(v,'move',i),box) for v in ('before','after')}
        a = np.asarray(frame('before','move',i).crop(box))
        # Fixed BEFORE mask excludes cream base/bright greave in the foot box;
        # use the identical selected pixels on both sides, not the after colour.
        selected = (a[...,3] > 240) & (luminance(a[...,:3]) < 145)
        stats['move'][i]['foot_pixels'] = int(selected.sum())
        stats['move'][i]['foot_mask'] = 'before alpha > 240 and display luma < 145, same pixels for both'
        stats['move'][i]['foot_luminance'] = {}
        for variant in ('before','after'):
            values = luminance(np.asarray(frame(variant,'move',i).crop(box))[...,:3])[selected]
            stats['move'][i]['foot_luminance'][variant] = {'mean': float(values.mean()), 'p90': float(np.percentile(values,90))}
    for variant in ('before','after'):
        stats['rest'][variant] = region_stats(frame(variant,'rest'),(105,214,172,219))
    coords = {side: [] for side in 'lr'}
    for item in receipt['clips']['move']['variants']['after']['frames']:
        for side in 'lr':
            c = item['feet'][side]['sole_center']; m = item['markers'][side]
            stats['anchor_error_max_m'] = max(stats['anchor_error_max_m'],max(abs(a-b) for a,b in zip(c,m)))
            coords[side].append(m)
    stats['shadow_anchor_travel_m'] = {s: np.ptp(np.array(points),axis=0).tolist() for s,points in coords.items()}
    # Enlarged crops disclose the region actually changed, including regressions.
    sheet=Image.new('RGB',(3*512,200),(248,244,230)); draw=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate([('Painting',painting),('R14 look',frame('before','rest')),('R15b look',frame('after','rest'))]):
        draw.text((i*512+5,4),label,fill='black')
        crop=im.crop((75,200,180,239)).resize((504,156),Image.Resampling.NEAREST)
        sheet.paste(crop,(i*512,28),crop)
    sheet.save(review/f'{prefix}-feet-shadow-crop.png')
    stats['rest_critique'] = {}
    p = np.asarray(painting)
    pm, _ = painting_mask(painting)
    for variant in receipt['clips']['rest']['variants']:
        r = np.asarray(frame(variant,'rest'))
        mask = pm & (r[...,3] > 8)
        delta = np.linalg.norm(rgb_to_lab(blurred_rgb(p[...,:3],mask)) - rgb_to_lab(blurred_rgb(r[...,:3],mask)),axis=2)
        stats['rest_critique'][variant] = {'silhouette_iou': float(best_iou(pm,r[...,3]>8)[0]),
            'blurred_delta_e': float(delta[mask].mean()),
            'feet_blurred_delta_e': float(delta[206:222,60:200][mask[206:222,60:200]].mean()),
            'base_blurred_delta_e': float(delta[222:244,60:200][mask[222:244,60:200]].mean())}
    (review/f'{prefix}-metrics.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats,indent=2))

if __name__ == '__main__': main()
