"""Serial batch under one Blender gate; publish each stage before proceeding."""
import os,sys,runpy,subprocess
from pathlib import Path
here=Path(__file__).parent;root=Path(os.environ['ANIM_ROOT'])
steps=os.environ.get('STAGES','build,b,paint,c,animate,d,e-idle,e-move,e-attack,e-hit,e-death,audit').split(',')
for step in steps:
    print('ROUND_STAGE',step,flush=True)
    if step in ['build','paint','animate','audit']:runpy.run_path(str(here/f'{step}.py'),run_name='__main__')
    else:
        sys.argv=['render.py','--',step];runpy.run_path(str(here/'render.py'),run_name='__main__')
        subprocess.run([str(root/'venv/bin/python'),str(here/'review.py'),step],check=True)
print('ROUND_COMPLETE',flush=True)
