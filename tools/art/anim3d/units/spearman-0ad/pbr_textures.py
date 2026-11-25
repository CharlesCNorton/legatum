"""Encode Blender-authored maps; no repainting or colour transform.

WebP uses the glTF EXT_texture_webp extension supported by the viewer.
Lossless 2048 masters remain outside git. Report decoded errors, not just bytes.
"""
import json, sys
from pathlib import Path
from PIL import Image
import numpy as np
work,unit=map(Path,sys.argv[1:3]);report={}
for name,quality in [('basecolor',85),('normal',90),('orm',88)]:
    source=Image.open(work/f'{name}-1024.png').convert('RGB')
    assert source.size==(1024,1024)
    out=unit/f'spearman-{name}.webp'
    source.save(out,quality=quality,method=6)
    decoded=Image.open(out).convert('RGB')
    error=np.abs(np.asarray(source,dtype=float)-np.asarray(decoded,dtype=float))
    report[name]={'bytes':out.stat().st_size,'size':list(decoded.size),'quality':quality,
                  'encoding':'WebP','mean_channel_error_255':error.mean(axis=(0,1)).tolist(),
                  'p99_absolute_channel_error_255':float(np.percentile(error,99))}
(work/'texture-encoding.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
