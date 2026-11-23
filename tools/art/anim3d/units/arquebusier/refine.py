"""Repeatable full-depth rest fitting from the original unpainted checkpoint."""
import bpy, bmesh, math, json, os, shutil, sys
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/arquebusier'
checkpoint=M/'refinement-input.blend'
if not checkpoint.exists():
 source=M/'round1-cpu/plain.blend'
 shutil.copy2(source if source.exists() else M/'plain.blend',checkpoint)
bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:
  image.filepath=bpy.path.abspath(image.filepath,start=str(M))
  assert Path(image.filepath).exists(),image.filepath
  image.reload();image.pack()
sc=bpy.context.scene;rig=bpy.data.objects['RIG-Arquebusier MPFB'];cam=sc.camera
right=cam.matrix_world.to_quaternion() @ Vector((1,0,0));up=cam.matrix_world.to_quaternion() @ Vector((0,1,0));ray=cam.matrix_world.to_quaternion() @ Vector((0,0,-1));unit=cam.data.ortho_scale/256
# Pixel landmarks are measured in the native 256px token, not independently warped UVs.
controls=[((95,86),(90,76),18),((102,64),(103,60),17),((160,87),(158,84),20),((152,108),(150,102),18),((114,154),(113,147),20),((146,154),(141,149),20),((109,205),(110,199),27),((151,212),(143,203),25),((128,46),(127,44),15)]
def delta(x,y):
 weights=[math.exp(-((x-a[0])**2+(y-a[1])**2)/(2*r*r)) for a,b,r in controls]
 den=max(1,sum(weights))
 return (sum(w*(b[0]-a[0]) for w,(a,b,r) in zip(weights,controls))/den,sum(w*(b[1]-a[1]) for w,(a,b,r) in zip(weights,controls))/den)
# Freeze MPFB macro mix while preserving its native topology and weights.
for o in list(sc.objects):
 if o.type=='MESH' and o.data.shape_keys:
  bpy.context.view_layer.objects.active=o
  o.shape_key_add(name='Frozen macro mix',from_mix=True)
  for k in list(o.data.shape_keys.key_blocks)[:-1]:o.shape_key_remove(k)
  o.shape_key_remove(o.data.shape_keys.key_blocks[0])
# Curves are real solid geometry too; finish before camera UV calibration.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
for o in list(sc.objects):
 if o.type!='MESH' or 'base' in o.name or 'muzzle' in o.name:continue
 bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):
  if mod.type!='ARMATURE' and 'MPFB' not in o.name:
   bpy.ops.object.modifier_apply(modifier=mod.name)
 # Long low-poly kit faces need interior visibility samples (not only occluded ends).
 if 'MPFB' not in o.name:
  bm=bmesh.new();bm.from_mesh(o.data)
  edges=[e for e in bm.edges if e.calc_length()>.09]
  if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=5,use_grid_fill=True)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  bm.to_mesh(o.data);bm.free()
 bpy.context.view_layer.update()
 # Body subdivision is disabled only for the inverse-skin solve; native topology remains.
 saved=[m for m in o.modifiers if m.type!='ARMATURE' and m.show_viewport]
 for m in saved:m.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(o.data.vertices)
 worlds=[ev.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
 arm=next((m for m in o.modifiers if m.type=='ARMATURE'),None)
 for v,w in zip(o.data.vertices,worlds):
  uv=world_to_camera_view(sc,cam,w);x,y=uv.x*256,(1-uv.y)*256
  dx,dy=delta(x,y)
  if any(s in o.name for s in ('morion','comb bright')):
   dx=-7.5;dy=0
   # Broader, taller swept side profile; retain every vertex's camera depth.
   dx+=(x-129)*.06;dy-=(max(0,35-y))*.08
  if 'slashed doublet' in o.name and y<67:
   # Lower and taper the open neckline around the actual neck.
   dy+=max(0,67-y)*.55
   dx+=(128-x)*max(0,67-y)/45
  if 'morion swept brim' in o.name or 'morion rolled brass lip' in o.name:
   fitted_x=x+dx
   target_y=45-.38*(fitted_x-108)-.025*(fitted_x-118)**2
   dy+=.80*(target_y-(y+dy))
   dx+=max(0,108-fitted_x)*.5
  if 'morion raised comb' in o.name or 'comb bright edge' in o.name:
   dx+=(116-(x+dx))*.30;dy+=2
  if 'shoe' in o.name:
   if o.parent_bone=='foot_l':dx+=(x-150)*.9+4;dy-=5
   else:dx+=4;dy-=2
  if 'matchlock' in o.name or o.parent and o.parent.name=='CTRL-matchlock':
   dx=((x-94)*.3+6)*max(0,min(1,(y-155)/50)) if 'fore-end' in o.name else 0;dy=-6 if y>160 else -8
  d=right*(dx*unit)-up*(dy*unit)
  # Move footwear onto the same physical contact plane along camera rays.
  if 'shoe' in o.name:
   d+=ray*(-d.z/ray.z)
  if arm:
   mats=[];total=0
   for g in v.groups:
    name=o.vertex_groups[g.group].name
    if name in rig.pose.bones:
     p=rig.pose.bones[name];mats.append((g.weight,p.matrix @ p.bone.matrix_local.inverted()));total+=g.weight
   skin=Matrix.Identity(4)
   if total:
    skin=Matrix([[sum(ww*mm[i][j] for ww,mm in mats)/total for j in range(4)] for i in range(4)])
   v.co+=skin.to_3x3().inverted() @ o.matrix_world.to_3x3().inverted() @ d
  else:v.co+=o.matrix_world.to_3x3().inverted() @ d
 for m in saved:m.show_viewport=True
 o.data.update()
 # Recompute outward normals after nonlinear fitting, before frozen UV projection.
 if 'MPFB' not in o.name:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
base=bpy.data.objects['GEO-stationary cream base'];base.location.y+=.25;base.location.x-=.012;base.scale.x=base.scale.y=.96
for mod in base.modifiers:
 if mod.type=='BEVEL':mod.width=.014;mod.segments=5
# Smoke remains a bounded real volume, never an opaque balloon or zero-scaled mesh.
smoke=bpy.data.objects['GEO-muzzle smoke'];ma=smoke.data.materials[0].copy();smoke.data.materials.clear();smoke.data.materials.append(ma)
n=ma.node_tree.nodes;l=ma.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.65,.60,.50,1)
tc=n.new('ShaderNodeTexCoord');dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE';dist.inputs[1].default_value=(.5,.5,.5);l.new(tc.outputs['Generated'],dist.inputs[0]);ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.1;ramp.inputs['From Max'].default_value=.5;ramp.inputs['To Min'].default_value=7;ramp.inputs['To Max'].default_value=0;ramp.clamp=True;l.new(dist.outputs['Value'],ramp.inputs['Value']);l.new(ramp.outputs[0],vol.inputs['Density']);l.new(vol.outputs[0],out.inputs['Volume'])
# Painted source has illumination already: Standard is intentional for camera pigment.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for o in sc.objects:
 if o.type=='LIGHT':o.data.energy*=.55
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.15
stone=base.data.materials[0];p=stone.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.72,.54,.31,1)
# Keep fine stone grain, with no static feet or source shadows projected onto it.
for n in stone.node_tree.nodes:
 if n.type=='BUMP':n.inputs['Distance'].default_value=.0007;n.inputs['Strength'].default_value=.09
# Camera-only warm stone pigment; live AO retains contact, no painted feet.
n=stone.node_tree.nodes;l=stone.node_tree.links;out=n.get('Material Output')
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],sep.inputs[0])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[0].color=(.79,.56,.30,1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(.94,.76,.50,1);l.new(sep.outputs['Z'],ramp.inputs[0])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.12;l.new(ramp.outputs[0],ao.inputs['Color'])
em=n.new('ShaderNodeEmission');l.new(ao.outputs['Color'],em.inputs['Color']);camera=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.8;l.new(camera.outputs['Is Camera Ray'],weight.inputs[0]);mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
sys.path.insert(0,str(Path(__file__).resolve().parent))
from bind_fit import calibrate
bind_joints=calibrate(rig)
rig['rest_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
(M/'bind-joints.json').write_text(json.dumps(bind_joints,indent=2))
bpy.context.view_layer.update()
sc['refinement']='round2 full-depth screen landmark fit; frozen MPFB macro mix and finished rigid surfaces'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
(M/'registration.json').write_text(json.dumps({'controls':controls,'camera':list(cam.location),'method':'full-depth mesh coordinates; UVs recalibrated only after fitting','exact_viewpoint':False},indent=2))
