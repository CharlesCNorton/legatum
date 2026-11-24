"""Require the independent look CLI and atlas path to produce identical pixels."""
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
master = Path(os.environ['ANIM_ROOT'])/'masters/spearman-3d-v2'
a = np.asarray(Image.open(master/'renders/c/three-quarter.png').convert('RGBA')).astype(int)
b = np.asarray(Image.open(master/'look-parity/rest.png').convert('RGBA')).astype(int)
assert a.shape == b.shape, (a.shape, b.shape)
d = np.abs(a-b)
# Eevee on the GPU is not bit-exact between runs (round 13: 142 of 262,144 pixels differed, 1 by more
# than 2 levels, mean 0.0002), so the gate allows sample noise but fails on a second render path.
over2 = float((d.max(axis=2) > 2).mean())
report = {'max_channel_error': int(d.max()), 'mean_error': float(d.mean()), 'pixels_over_2_levels': over2,
          'identical': bool(np.array_equal(a,b))}
report['ok'] = report['mean_error'] < 0.01 and over2 < 0.0005
(master/'look-parity/parity.json').write_text(json.dumps(report, indent=2)+'\n')
assert report['ok'], 'Look CLI and delivered render differ beyond GPU sample noise: '+str(report)
print('RENDER_PARITY_OK', report)
