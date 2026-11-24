"""Repeatable finish from the baked checkpoint; frozen UVs on finished 3D surfaces."""
import bpy, os, json, math, shutil, sys
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

R=Path(os.environ['ANIM_ROOT']); M=R/'masters/byzantine-heir'
checkpoint=M/'projection-input.blend'
assert not (M/'bake-required').exists(), 'Bake the rebuilt master first'
if not checkpoint.exists():shutil.copy2(M/'byzantine-heir.blend',checkpoint)
bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
sc=bpy.context.scene;cam=sc.camera;rig=bpy.data.objects['Heir MPFB game_engine']
body=bpy.data.objects['Heir MPFB anatomy'];base=bpy.data.objects['Stationary cream stone']
# Freeze MPFB's current macro mix, retaining the anatomical topology and weights.
if body.data.shape_keys:
 mixed=body.shape_key_add(name='Frozen macro mix',from_mix=True)
 coords=[v.co.copy() for v in mixed.data]
 body.shape_key_clear()
 for v,co in zip(body.data.vertices,coords):v.co=co
# Fit the weighted anatomical feet inside the closed boots. Invert each
# vertex's blended rest-to-pose matrix so changes survive live articulation.
bpy.context.view_layer.update()
transforms={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted() for g in body.vertex_groups if g.name in rig.pose.bones}
local_to_rig=rig.matrix_world.inverted()@body.matrix_world
for vertex in body.data.vertices:
 weights=[(g.weight,transforms[g.group]) for g in vertex.groups if g.group in transforms]
 total=sum(w for w,_ in weights)
 if not total:continue
 blend=Matrix([[sum(w*mat[r][c] for w,mat in weights)/total for c in range(4)] for r in range(4)])
 transform=rig.matrix_world@blend@local_to_rig
 world=transform@vertex.co
 if world.z>1.80:
  world.x-=.028*min(1,(world.z-1.80)/.12)
  vertex.co=transform.inverted()@world
 if world.z<.55:
  world.y+=.16*max(0,min(1,(.55-world.z)/.35))
  # Skin toes must be enclosed by footwear rather than painted as limestone.
  if world.z<.18:world.z=.12+(world.z-.12)*.55
  vertex.co=transform.inverted()@world
# Fit full-depth rigid footwear through mesh coordinates, not object scale or alpha.
for ob in sc.objects:
 if ob.type!='MESH':continue
 if ob.name.startswith(('Leather toe','Tall leather boot')):
  inv=ob.matrix_world.inverted()
  for v in ob.data.vertices:
   w=ob.matrix_world@v.co
   if ob.name.startswith('Leather toe'):
    w.y+=.16
   else:
    w.y+=.16*max(0,min(1,(.55-w.z)/.35))
   v.co=inv@w
# Register crown and curls with the painted head, preserving their full volumes.
for ob in sc.objects:
 if ob.type=='MESH' and ob.name.startswith(('Sculpted hair','Sculpted chestnut','Gold crown','Crown cabochon')):
  inv=ob.matrix_world.inverted()
  for v in ob.data.vertices:
   w=ob.matrix_world@v.co;w.x-=.028;v.co=inv@w
# Keep the stationary disc round and its contact top unchanged.
base.location.y+=.22
base.modifiers[0].width=.012;base.modifiers[0].segments=5
# The source train has a fuller, longer trailing fold. Move the entire cloth
# cross-section and every shape key consistently, retaining physical depth.
ob=bpy.data.objects['Gathered purple train'];inv=ob.matrix_world.inverted()
for key in ob.data.shape_keys.key_blocks:
 for v in key.data:
  w=ob.matrix_world@v.co;q=world_to_camera_view(sc,cam,w);y=(1-q.y)*256
  t=max(0,min(1,(y-175)/44));w.x+=.020*t;w.z-=.045*t
  v.co=inv@w
# Finish every rigid kit surface before projection. Preserve the dense cloth
# deformation cages and original anatomy weights; their UV evaluation is below.
for ob in list(sc.objects):
 if ob.type!='MESH' or ob==base or ob.data.shape_keys or ob==body:continue
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 for mod in list(ob.modifiers):
  if mod.type in {'SOLIDIFY','BEVEL','SUBSURF'}:
   if mod.type=='SUBSURF' and mod.levels==0:ob.modifiers.remove(mod)
   else:bpy.ops.object.modifier_apply(modifier=mod.name)
# Move body subdivision before armature and bake it into the weighted mesh so
# UVs are measured at exactly the same vertices used by the rendered surface.
bpy.context.view_layer.objects.active=body
for mod in list(body.modifiers):
 if mod.type=='SUBSURF':
  bpy.ops.object.modifier_move_up(modifier=mod.name)
  bpy.ops.object.modifier_apply(modifier=mod.name)
sys.path.insert(0,str(Path(__file__).parent))
from finish_geometry import finish
stone_grain=finish(sc,rig)
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
for name,power,color in [('Warm key',270,(1,.96,.88)),('Soft fill',65,(.90,.95,1)),('Cool rim',135,(.82,.90,1))]:
 light=bpy.data.objects[name];light.data.energy=power;light.data.color=color
sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.25
# Stone stays physical: no static painted feet/shadows. Fine pigment grain.
stone=base.data.materials[0];n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF')
noise=next(x for x in n if x.type=='TEX_NOISE');noise.inputs['Scale'].default_value=210
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.72,.53,.29,1);ramp.color_ramp.elements[1].color=(.90,.71,.44,1)
l.new(stone_grain,ramp.inputs[0]);mix=next(x for x in n if x.type=='MIX_RGB');l.new(ramp.outputs[0],mix.inputs[1])
for node in n:
 if node.type=='BUMP':node.inputs['Distance'].default_value=.0008;node.inputs['Strength'].default_value=.14
# Camera-only stone pigment opens the cream without lighting the figure.
out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
paint=n.new('ShaderNodeBsdfPrincipled');paint.inputs['Base Color'].default_value=(0,0,0,1);paint.inputs['Specular IOR Level'].default_value=0;paint.inputs['Emission Strength'].default_value=1
l.new(ramp.outputs[0],paint.inputs['Emission Color'])
# Register the unobstructed front stone rim to the original brushwork. The
# upper surface remains procedural and receives moving contact shadows;
# source feet and their shadows are excluded by a strict camera-space bound.
uv=base.data.uv_layers.new(name='Stone rest camera')
coords=[world_to_camera_view(sc,cam,base.matrix_world@v.co) for v in base.data.vertices]
for loop in base.data.loops:
 q=coords[loop.vertex_index];uv.data[loop.index].uv=(q.x,q.y)
tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name
tex=n.new('ShaderNodeTexImage');tex.image=next(im for im in bpy.data.images if 'painting-aligned' in im.name);tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs['Vector'])
axis=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs[0],axis.inputs[0])
rim=n.new('ShaderNodeMath');rim.operation='LESS_THAN';rim.inputs[1].default_value=1-230/256;l.new(axis.outputs['Y'],rim.inputs[0])
mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(rim.outputs[0],mask.inputs[0]);l.new(tex.outputs['Alpha'],mask.inputs[1])
geo=n.new('ShaderNodeNewGeometry');normal=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],normal.inputs[0])
side=n.new('ShaderNodeMapRange');side.inputs['From Min'].default_value=.15;side.inputs['From Max'].default_value=.85;side.inputs['To Min'].default_value=1;side.inputs['To Max'].default_value=0;side.clamp=True;l.new(normal.outputs['Z'],side.inputs['Value'])
side_mask=n.new('ShaderNodeMath');side_mask.operation='MULTIPLY';l.new(mask.outputs[0],side_mask.inputs[0]);l.new(side.outputs[0],side_mask.inputs[1]);mask=side_mask
pigment=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],pigment.inputs[0]);l.new(ramp.outputs[0],pigment.inputs[1]);l.new(tex.outputs['Color'],pigment.inputs[2]);l.new(pigment.outputs[0],paint.inputs['Emission Color'])
ray=n.new('ShaderNodeLightPath');fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.55;l.new(ray.outputs['Is Camera Ray'],fac.inputs[0])
blend=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(paint.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
# Frozen one-camera UVs; source opacity affects pigment only, never geometry.
view=(cam.matrix_world.to_quaternion()@Vector((0,0,1))).normalized()
records=[]
for ob in sc.objects:
 if ob.type!='MESH' or ob==base:continue
 mods=[(m,m.show_viewport) for m in ob.modifiers if m.type!='ARMATURE']
 for mod,_ in mods:mod.show_viewport=False
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(ob.data.vertices),ob.name
 uv=ob.data.uv_layers.get('Rest painting');attr=ob.data.color_attributes.get('Projection facing');coords=[];weights=[]
 points=[ev.matrix_world@v.co for v in me.vertices]
 normals=[(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized() for v in me.vertices]
 ev.to_mesh_clear()
 # The MPFB mask hides helper geometry around the face. Restore it before
 # scene ray casting; measuring raw indexed UVs with the mask disabled must
 # not make those non-rendered helpers into false occluders.
 for mod,state in mods:mod.show_viewport=state
 bpy.context.view_layer.update();ray_deps=bpy.context.evaluated_depsgraph_get()
 for w,normal in zip(points,normals):
  q=world_to_camera_view(sc,cam,w);coords.append((q.x,q.y))
  facing=max(0,min(1,(normal.dot(view)+.12)/.30))
  # Freeze source visibility too: a boot beneath the cloak must not borrow
  # purple pixels just because its normal points toward the source camera.
  if facing:
   hit,location,_,_,_,_=sc.ray_cast(ray_deps,w+view*10,-view,distance=11)
   visibility=max(0,min(1,(.035-(location-w).length)/.025)) if hit else 0
  else:visibility=0
  weights.append(facing*visibility)
 for loop in ob.data.loops:
  uv.data[loop.index].uv=coords[loop.vertex_index];attr.data[loop.index].color=(weights[loop.vertex_index],)*3+(1,)
 for material in ob.data.materials:
  n=material.node_tree.nodes;l=material.node_tree.links;s=n.get('Principled BSDF');out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
  tex=next(x for x in n if x.type=='TEX_IMAGE' and x.image and 'painting-aligned' in x.image.name)
  mask=next(x for x in n if x.type=='MATH' and x.operation=='MULTIPLY')
  # Remove paint from the old physical colour path; retain generated fills,
  # actual AO/curvature and the original material's physical response.
  pigment_mix=next(x for x in n if x.type=='MIX_RGB' and x.inputs[0].is_linked and x.inputs[0].links[0].from_node==mask)
  l.remove(pigment_mix.inputs[0].links[0]);pigment_mix.inputs[0].default_value=0
  for link in list(s.inputs['Emission Color'].links):l.remove(link)
  s.inputs['Emission Strength'].default_value=0
  paint=n.new('ShaderNodeBsdfPrincipled');paint.name='Camera painted pigment';paint.inputs['Base Color'].default_value=(0,0,0,1);paint.inputs['Roughness'].default_value=1;paint.inputs['Specular IOR Level'].default_value=0;paint.inputs['Emission Strength'].default_value=1;l.new(tex.outputs['Color'],paint.inputs['Emission Color'])
  # Boot pigment cannot borrow the painting's cream stone below the soles.
  if ob.name.startswith(('Leather toe','Tall leather boot')):
   lum=n.new('ShaderNodeRGBToBW');l.new(tex.outputs['Color'],lum.inputs[0])
   dark=n.new('ShaderNodeMath');dark.operation='LESS_THAN';dark.inputs[1].default_value=.28;l.new(lum.outputs[0],dark.inputs[0])
   bootmask=n.new('ShaderNodeMath');bootmask.operation='MULTIPLY';l.new(mask.outputs[0],bootmask.inputs[0]);l.new(dark.outputs[0],bootmask.inputs[1]);mask=bootmask
  lightpath=n.new('ShaderNodeLightPath');cam_mask=n.new('ShaderNodeMath');cam_mask.operation='MULTIPLY';l.new(mask.outputs[0],cam_mask.inputs[0]);l.new(lightpath.outputs['Is Camera Ray'],cam_mask.inputs[1])
  strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.96;l.new(cam_mask.outputs[0],strength.inputs[0])
  blend=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(paint.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
 records.append({'mesh':ob.name,'vertices':len(ob.data.vertices)})
sc['finish_version']=4
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'byzantine-heir.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
(M/'projection.json').write_text(json.dumps({'method':'Finished rigid surfaces and subdivided weighted anatomy, frozen rest-camera UVs; camera-ray visibility and camera-only 96% pigment; retained generated fills and AO/curvature','meshes':records,'checkpoint':str(checkpoint)},indent=2))
print('REFINE_READY',len(records),'meshes')
