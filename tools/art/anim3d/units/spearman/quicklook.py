"""Fast pose look: render chosen frames of a clip/diagnostic blend from the
painting camera plus optional orthographic helper views. Review only; saves nothing
back to the blend.

blender -b --factory-startup --python quicklook.py -- <blend> <outdir> <frames|samples> [views] [clay]
views: comma list of cam,top,front,side (default cam).
"""
import bpy,sys,json,os
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
blend,out=args[0],Path(args[1]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene
frames=json.loads(sc['sample_frames']) if args[2]=='samples' else [int(v) for v in args[2].split(',')]
views=(args[3] if len(args)>3 else 'cam').split(',')
clay=len(args)>4 and args[4]=='clay'
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=int(os.environ.get('SAMPLES','6'))
sc.cycles.use_denoising=True;sc.cycles.seed=17
sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
sc.render.threads_mode='FIXED';sc.render.threads=3
if not sc.get('cloth_baked'):
 for ob in sc.objects:
  for m in ob.modifiers:
   if m.type=='CLOTH':m.show_render=False;m.show_viewport=False
if clay:
 plain=bpy.data.materials.new('Quicklook clay');plain.use_nodes=True
 plain.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.42,.36,.26,1)
 sc.view_layers[0].material_override=plain
cam=sc.camera;base=cam.matrix_world.copy();scale=cam.data.ortho_scale
POS={'top':((0,0,9),(0,0,0)),'front':((0,-9,1.0),(0,0,1.0)),'side':((9,0,1.0),(0,0,1.0)),'back':((0,9,1.0),(0,0,1.0))}
for i,frame in enumerate(frames):
 sc.frame_set(frame)
 for view in views:
  cam.matrix_world=base;cam.data.ortho_scale=scale
  if view!='cam':
   pos,look=POS[view];cam.location=pos
   cam.rotation_euler=(Vector(look)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
   cam.data.ortho_scale=3.2
  sc.render.filepath=str(out/f'{view}-{i:02d}.png');bpy.ops.render.render(write_still=True)
print('QUICKLOOK_READY',out)
