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
report = {'max_channel_error': int(np.abs(a-b).max()), 'identical': bool(np.array_equal(a,b))}
(master/'look-parity/parity.json').write_text(json.dumps(report, indent=2)+'\n')
assert report['identical'], 'Look CLI and delivered render differ: '+str(report)
print('RENDER_PARITY_OK', report)
