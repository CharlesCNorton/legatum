"""Rest-view diagnostics at delivery/review sizes; never automatic art approval."""
import hashlib
import json
import os
from pathlib import Path
from PIL import Image

root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/cavalry'
reference = Path('app/src/assets/units/cavalry-256.png')
render = master/'renders/c/00.png'
report = {'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
          'render_sha256': hashlib.sha256(render.read_bytes()).hexdigest(),
          'render_provenance': json.loads((master/'renders/c/render.json').read_text()),
          'art_approved': False, 'sizes': {}}
for size in (256, 64):
    a = Image.open(reference).convert('RGBA').resize((size,size), Image.Resampling.LANCZOS)
    b = Image.open(render).convert('RGBA').resize((size,size), Image.Resampling.LANCZOS)
    pairs = list(zip(a.get_flattened_data(), b.get_flattened_data()))
    union = sum(x[3] > 128 or y[3] > 128 for x,y in pairs)
    intersection = [(x,y) for x,y in pairs if x[3] > 128 and y[3] > 128]
    report['sizes'][str(size)] = {
        'silhouette_iou': round(len(intersection)/union, 4),
        'rgb_mae_on_opaque_overlap': round(sum(abs(x[c]-y[c]) for x,y in intersection for c in range(3))/(3*len(intersection)), 3),
        'painting_bounds': a.getchannel('A').getbbox(),
        'render_bounds': b.getchannel('A').getbbox(),
    }
report['limitations'] = 'Whole-token silhouette includes base; overlap colour excludes missing/extra silhouette. Neither measures animation or establishes painting parity.'
(root/'review/3d-v2/cavalry-look.json').write_text(json.dumps(report,indent=2)+'\n')
print('REST_DIAGNOSTICS', report['sizes'])
