"""Serial mounted refresh within one shared Blender slot.

Optional CLIP regenerates only that clip; STAGES selects comma-separated reviews.
Defaults rerender existing masters. Invoke only through blender-slot in background.
"""
import os,sys,runpy,subprocess
from pathlib import Path
root=Path(os.environ['ANIM_ROOT']);scripts=Path('tools/art/anim3d/mounted')
if os.environ.get('MARKINGS')=='1':runpy.run_path(str(scripts/'markings.py'),run_name='__main__')
if os.environ.get('CLIP'):runpy.run_path(str(scripts/'animate.py'),run_name='__main__')
runpy.run_path(str(scripts/'audit.py'),run_name='__main__')
resolution=os.environ.get('RESOLUTION','256')
stages=os.environ.get('STAGES','c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death').split(',')
for stage in stages:
 os.environ['RESOLUTION']='512' if stage=='c-details' else resolution
 sys.argv=['render.py','--',stage];runpy.run_path(str(scripts/'render.py'),run_name='__main__')
 for helper in ['grade.py','review.py']:subprocess.run([str(root/'venv/bin/python'),str(scripts/helper),stage],check=True)
print('MOUNTED_REFRESH_READY',','.join(stages))
