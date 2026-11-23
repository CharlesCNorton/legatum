"""One gated Blender process for a complete CPU round; publish each stage immediately."""
import os,runpy,sys,subprocess
from pathlib import Path
root=Path(os.environ['ANIM_ROOT']);scripts=Path(__file__).resolve().parent
# Useful when the global gate is busy: each operation remains sequential in this one process.
steps=['animate'] if os.environ.get('SIEGE_REUSE_MASTER')=='1' else ['scene','register','materials','bake','finish','paint','animate']
for name in steps:
 print('ROUND_STAGE',name,flush=True);runpy.run_path(str(scripts/(name+'.py')),run_name='__main__')
runpy.run_path(str(scripts/'audit.py'),run_name='__main__')
for stage in os.environ.get('SIEGE_STAGES','b,c,detail,d,e-idle,e-move,e-attack,e-hit,e-death').split(','):
 print('ROUND_RENDER',stage,flush=True);os.environ.setdefault('RESOLUTION','512');os.environ.setdefault('SAMPLES','12')
 sys.argv=['render.py','--',stage];runpy.run_path(str(scripts/'render.py'),run_name='__main__')
 subprocess.run([str(root/'venv/bin/python'),str(scripts/'review.py'),stage],check=True)
print('ROUND_COMPLETE',flush=True)
