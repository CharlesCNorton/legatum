"""Native-size comparisons and semantic pixel measurements for the R12b CPU A/B."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.images import resize_rgba
from look_textures import PARTS, ID_COLOURS

CREAM = (248, 244, 232, 255)


def sheet(images, labels, size, path, columns=None):
    columns = columns or len(images)
    rows = (len(images)+columns-1)//columns
    out = Image.new('RGBA', (columns*size, rows*(size+24)), CREAM)
    draw = ImageDraw.Draw(out)
    for i, (im, label) in enumerate(zip(images, labels)):
        x, y = (i % columns)*size, (i // columns)*(size+24)
        draw.text((x+4, y+5), label, fill=(40, 32, 24))
        out.alpha_composite(resize_rgba(im.convert('RGBA'), (size, size), space='display'), (x, y+24))
    out.convert('RGB').save(path)


def main():
    root, out = map(Path, sys.argv[1:3]); out.mkdir(exist_ok=True, parents=True)
    p = root/'preview'
    painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
    before, after = [Image.open(p/f'rest-00-{v}.png').convert('RGBA') for v in ('before', 'after')]
    gpu = Image.open(root/'round11-gpu-rest.png').convert('RGBA')
    for size in (256, 160, 64):
        reference = Image.open('app/src/assets/units/spearman-64.png') if size == 64 else painting
        labels = ['Paint', 'R11gpu', 'R11cpu', 'R12bcpu'] if size == 64 else ['Painting', 'R11 GPU', 'R11 CPU proxy', 'R12b CPU proxy']
        sheet([reference, gpu, before, after], labels, size,
              out/f'spearman-r12b-rest-{size}.png')
    cases = ('move-02', 'move-06', 'hit-01', 'death-04', 'death-07')
    for size in (256, 160):
        sheet([Image.open(p/f'{c}-{v}.png') for v in ('before', 'after') for c in cases],
              [f'{c} {v}' for v in ('before', 'after') for c in cases], size,
              out/f'spearman-r12b-motion-{size}.png', len(cases))
    metrics = {'label': 'Cycles CPU proxy; analytic sun, real AO, no cast shadows, no grade', 'regions': {}}
    yy, xx = np.indices((256, 256))
    for case in ('rest-00',)+cases:
        a, b, ids = [np.asarray(Image.open(p/f'{case}-{v}.png').convert('RGBA')).astype(float)
                     for v in ('before', 'after', 'id')]
        table = np.array([ID_COLOURS[q] for q in PARTS])
        distance = np.linalg.norm(ids[:, :, None, :3]-table[None, None], axis=-1)
        owner = distance.argmin(-1)
        valid = (distance.min(-1) < 30) & (ids[:, :, 3] > 240)
        masks = {
            'sandals': np.isin(owner, [PARTS.index('sandal_l'), PARTS.index('sandal_r')]),
            'skirt': owner == PARTS.index('skirt'),
            'shoulder': (owner == PARTS.index('tunic')) & (yy < 180),
            'base': np.isin(owner, [PARTS.index('base'), PARTS.index('rim')]),
        }
        assert np.array_equal(a[:, :, 3], b[:, :, 3]), (case, 'silhouette changed')
        rows = {}
        for name, mask in masks.items():
            mask &= valid
            if not mask.any():
                continue
            rows[name] = {'pixels': int(mask.sum()), 'changed_over_2_levels': int((np.max(abs(a[:, :, :3]-b[:, :, :3]), axis=-1)[mask] > 2).sum())}
            for label, data in [('before', a), ('after', b)]:
                lum = data[:, :, :3][mask] @ [.2126, .7152, .0722]
                rows[name][label] = {'mean_luminance': float(lum.mean()), 'p90': float(np.percentile(lum, 90)),
                                     'pixels_over_160': int((lum > 160).sum())}
        metrics['regions'][case] = rows
    no_contact = p/'rest-00-no-contact.png'
    if no_contact.exists():
        live = np.asarray(after).astype(float)
        off = np.asarray(Image.open(no_contact).convert('RGBA')).astype(float)
        ids = np.asarray(Image.open(p/'rest-00-id.png').convert('RGBA')).astype(float)
        codes = np.array([ID_COLOURS[q] for q in ('base', 'rim')])
        stone = (np.linalg.norm(ids[:, :, None, :3]-codes[None, None], axis=-1).min(-1) < 25) & (ids[:, :, 3] > 240)
        loss = (off[:, :, :3]-live[:, :, :3]) @ [.2126, .7152, .0722]
        dark = stone & (loss > 2)
        ys, xs = np.nonzero(dark)
        metrics['contact'] = {'stone_pixels_darkened_over_2_levels': int(dark.sum()),
                              'bbox_xyxy': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                              'mean_luminance_loss_in_shadow': float(loss[dark].mean()),
                              'limit': 'AO only; the Eevee cast shadow requires host GPU review'}
        images = [Image.open(no_contact), after, Image.open(p/'rest-00-id.png')]
        detail = Image.new('RGBA', (900, 150), CREAM)
        draw = ImageDraw.Draw(detail)
        for i, (im, label) in enumerate(zip(images, ('Contact off', 'Live Cycles contact', 'Material ID'))):
            draw.text((i*300+4, 5), label, fill=(40, 32, 24))
            crop = resize_rgba(im.convert('RGBA').crop((70, 200, 185, 246)), (300, 120), space='display')
            detail.alpha_composite(crop, (i*300, 28))
        detail.convert('RGB').save(out/'spearman-r12b-base-contact.png')
    (out/'spearman-r12b-continuity-metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
