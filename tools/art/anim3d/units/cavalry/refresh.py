"""Sequential review batch under one Blender gate; never spawn a second Blender."""
import os,sys,runpy,subprocess
from pathlib import Path
U=Path('tools/art/anim3d/units/cavalry');R=Path(os.environ['ANIM_ROOT']);python=R/'venv/bin/python'
for stage in os.environ.get('STAGES','b,c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death').split(','):
 previous=os.environ.get('RESOLUTION','256')
 if stage=='c-details':os.environ['RESOLUTION']='512'
 sys.argv=['render.py','--',stage];runpy.run_path(str(U/'render.py'),run_name='__main__')
 for name in ['grade.py','review.py']:subprocess.run([str(python),str(U/name),stage],check=True)
 os.environ['RESOLUTION']=previous
print('CAVALRY_REFRESH_DONE')
