"""One gated Blender process for a complete CPU round; publish each stage immediately."""
import os,runpy,sys,subprocess
from pathlib import Path
root=Path(os.environ['ANIM_ROOT']);scripts=Path(__file__).resolve().parent
# Useful when the global gate is busy: each operation remains sequential in this one process.
steps=['animate'] if os.environ.get('SIEGE_REUSE_MASTER')=='1' else ['scene','materials','bake','paint','finish','animate']
for name in steps:
 print('ROUND_STAGE',name,flush=True);runpy.run_path(str(scripts/(name+'.py')),run_name='__main__')
for stage in ['c','detail','d','e-idle','e-move','e-attack','e-hit','e-death']:
 print('ROUND_RENDER',stage,flush=True);os.environ['RESOLUTION']='512' if stage=='detail' else '256';os.environ['SAMPLES']='16' if stage in ['c','detail'] else '12'
 sys.argv=['render.py','--',stage];runpy.run_path(str(scripts/'render.py'),run_name='__main__')
 subprocess.run([str(root/'venv/bin/python'),str(scripts/'review.py'),stage],check=True)
runpy.run_path(str(scripts/'audit.py'),run_name='__main__')
print('ROUND_COMPLETE',flush=True)
