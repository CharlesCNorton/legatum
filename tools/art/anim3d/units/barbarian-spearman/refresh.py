"""Serial render batch under one gate acquisition; no child Blender processes."""
import os,sys,runpy,subprocess
from pathlib import Path
T=Path('tools/art/anim3d/units/barbarian-spearman');R=Path(os.environ['ANIM_ROOT']);py=str(R/'venv/bin/python')
for stage in os.environ.get('STAGES','b,c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death,g-feet').split(','):
 sys.argv=['render.py','--',stage];runpy.run_path(str(T/'render.py'),run_name='__main__')
 subprocess.run([py,str(T/'grade.py'),stage],check=True)
 subprocess.run([py,str(T/'review.py'),stage],check=True)
