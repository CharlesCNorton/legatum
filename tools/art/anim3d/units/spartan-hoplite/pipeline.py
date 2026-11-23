"""Unit-owned sequential entry point. All Blender work stays inside one gated process."""
import os, sys, runpy
from pathlib import Path
BASE=Path('tools/art/anim3d')
UNIT=BASE/'units/spartan-hoplite'
ROOT=Path(os.environ['ANIM_ROOT'])
M=Path(os.environ['ANIM_MASTER']);M.mkdir(parents=True,exist_ok=True)
LOG=ROOT/'review/3d-v2/spartan-hoplite-log.md'
def log(s):
 with LOG.open('a') as f:f.write(s+'\n')
def run(path):runpy.run_path(str(path),run_name='__main__')
stage=sys.argv[sys.argv.index('--')+1]
if stage=='build':
 log('Build: used blender-modeling/materials/lighting/cameras/animation/rendering skills: bevels, cloth thickness, physical pigments, fixed orthographic camera, keyed rig, Cycles previews.')
 run(BASE/'scene.py');run(BASE/'helmet.py');run(UNIT/'kit.py')
 log('Built original MPFB anatomy, 53-bone rig and hoplite-specific linen/lambda kit; saved separately from old master.')
elif stage=='mantle-finish':run(UNIT/'mantle_finish.py')
elif stage=='clearance':run(UNIT/'shield_clearance.py')
elif stage=='probe':run(UNIT/'contact_probe.py')
elif stage=='finalize':run(UNIT/'finalize.py')
elif stage=='sync-finish':run(UNIT/'sync_finish.py')
elif stage=='audit':
 os.environ['ANIM_AUDIT_PREFIX']='spartan-hoplite-';run(UNIT/'contact_probe.py');run(BASE/'audit.py')
elif stage=='paint':run(UNIT/'paint.py')
elif stage=='materials':
 (M/'unpainted.blend').unlink(missing_ok=True)
 run(BASE/'materials.py');run(BASE/'bake.py');run(UNIT/'paint.py')
 log('Textured: CC0 scans, 512 AO/curvature bakes, fixed painting UVs, generated unseen linen/bronze fills, cream pigment and product lighting.')
elif stage.startswith('animate-'):
 sys.argv=['animate.py','--',stage.removeprefix('animate-')];run(BASE/'animate.py')
 log('Baked '+stage+' with authored combat/CMU locomotion and real cloth simulation.')
elif stage=='all-clips':
 for clip in ['idle','move','attack','hit','death']:
  sys.argv=['animate.py','--',clip];run(BASE/'animate.py');log('Baked clip '+clip)
else:
 os.environ['HOPLITE_STAGE']=stage;run(UNIT/'render.py')
