"""Finish full-depth surfaces before frozen projection; executed by finish.py."""
# Freeze the existing MPFB macro mix, retaining weights and the clean input master.
for o in list(sc.objects):
 if o.type!='MESH':continue
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 if o.data.shape_keys:
  mixed=o.shape_key_add(name='Frozen macro mix',from_mix=True)
  coordinates=[v.co.copy() for v in mixed.data];o.shape_key_clear()
  for v,co in zip(o.data.vertices,coordinates):v.co=co
 arm_mods=[m for m in o.modifiers if m.type=='ARMATURE']
 states=[(m,m.show_viewport) for m in arm_mods]
 for m,_ in states:m.show_viewport=False
 for m in list(o.modifiers):
  if m.type=='ARMATURE':continue
  if m.type=='SUBSURF':m.levels=m.render_levels=1
  bpy.ops.object.modifier_apply(modifier=m.name)
 for m,state in states:m.show_viewport=state
 o['finished_before_projection']=True
bpy.context.view_layer.update()
# Remove inherited horseman white facial/pastern markings absent from this painting.
horse=bpy.data.objects['Horse']
for p in horse.data.polygons:
 if p.material_index==8:p.material_index=0
# Fine, local registration of full anatomical volumes. No depth flattening or alpha cuts.
def fit_objects(objects, landmarks, radius):
 for o in objects:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  assert len(me.vertices)==len(o.data.vertices),o.name
  arm=next((m.object for m in o.modifiers if m.type=='ARMATURE'),None)
  Ato=arm.matrix_world.inverted()@o.matrix_world if arm else None
  for v,pv in zip(o.data.vertices,me.vertices):
   world=o.matrix_world@pv.co;q=world_to_camera_view(sc,sc.camera,world);x,y=q.x*256,(1-q.y)*256
   weights=[math.exp(-((x-a[0])**2+(y-a[1])**2)/(2*radius**2)) for a,b in landmarks]
   total=max(1.,sum(weights));dx=sum(w*(b[0]-a[0]) for w,(a,b) in zip(weights,landmarks))/total;dy=sum(w*(b[1]-a[1]) for w,(a,b) in zip(weights,landmarks))/total
   local=o.matrix_world.to_3x3().inverted()@((right*dx-up*dy)*(sc.camera.data.ortho_scale/256))
   if arm:
    weighted=Matrix(((0.,0.,0.,0.),)*4);total=0
    for g in v.groups:
     name=o.vertex_groups[g.group].name
     if name not in arm.pose.bones:continue
     bone=arm.pose.bones[name];weighted+=(bone.matrix@bone.bone.matrix_local.inverted())*g.weight;total+=g.weight
    if total>.001:local=(Ato.inverted()@(weighted*(1/total))@Ato).to_3x3().inverted_safe()@local
   v.co+=local
  ev.to_mesh_clear();o.data.update()
 bpy.context.view_layer.update()
rider_objects=[];horse_objects=[]
for o in sc.objects:
 if o.type!='MESH' or o==base:continue
 p=o
 while p is not None and p!=rig:p=p.parent
 if p==rig:rider_objects.append(o)
 else:horse_objects.append(o)
# The far hand is high and the near shoulder narrow; lower the real forearm/hand,
# broaden the shoulder and seat the calf closer to the painted boot.
fit_objects(rider_objects,[((145,101),(138,101)),((131,93),(130,93)),((100,87),(96,87)),((118,101),(114,99)),((108,168),(116,171))],10)
# The crest of the neck is high and the throat is too hollow. These edits include
# articulated scale panels, mane curves, tack and anatomy, preserving their depth.
fit_objects(horse_objects,[((180,80),(182,88)),((159,105),(163,108)),((173,128),(175,131)),((190,106),(194,109))],12)
# Second registration pass from the native-size split review. Preserve depth and
# skin weights; fit the neck crest, chest and planted legs before freezing UVs.
fit_objects(horse_objects,[((183,76),(182,82)),((177,91),(178,95)),((204,114),(197,114)),((168,131),(162,133))],9)
fit_objects(rider_objects,[((103,92),(98,92)),((118,102),(111,101)),((140,109),(135,109)),((111,161),(115,165))],8)
fit_objects(rider_objects,[((145,121),(138,115)),((90,133),(86,133)),((91,156),(87,156))],9)
# Fit complete lower-leg volumes by their original anatomical weights. A tiny
# local RBF around each hoof pinches the fetlock; use a continuous section field.
exec(compile(Path(__file__).with_name('legs.py').read_text(), 'lower leg sculpture', 'exec'))
# Base: preserve one circular horizontal disc, sharpen the small rim bevel and
# move the footprint up to the reference. Contact height remains unchanged.
base.scale.x*=.98;base.scale.y*=.98
# Physical painted stone: no figure/hoof pixels projected onto stationary geometry.
stone=base.data.materials[0];n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF')
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
s.inputs['Base Color'].default_value=tuple(linear(v/255) for v in (233,207,160))+(1,)
s.inputs['Roughness'].default_value=.86
# Standard is deliberate here: the projected source already contains painted light.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,power,color in [('Warm key',360,(1,.95,.86)),('Cool fill',72,(.88,.93,1)),('Cool rim',108,(.83,.91,1))]:
 light=bpy.data.objects[name];light.data.energy=power;light.data.color=color

# Camera-only pigment opens the cream top/rim while preserving physical contact
# shadows. No source figure or static painted shadow enters this base material.
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],sep.inputs[0])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.1;ramp.color_ramp.elements[0].color=tuple(linear(v/255) for v in (211,174,121))+(1,);ramp.color_ramp.elements[1].position=.9;ramp.color_ramp.elements[1].color=tuple(linear(v/255) for v in (250,224,181))+(1,);l.new(sep.outputs['Z'],ramp.inputs[0])
em=n.new('ShaderNodeEmission');l.new(ramp.outputs[0],em.inputs['Color'])
ray=n.new('ShaderNodeLightPath');fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.72;l.new(ray.outputs['Is Camera Ray'],fac.inputs[0])
blend=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(em.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],n.get('Material Output').inputs['Surface'])
# Stone pigment keeps live contact occlusion and fine low-amplitude grain even
# on the camera branch, so the disc no longer looks like a flat cardboard oval.
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2
grain=n.new('ShaderNodeMapRange');grain.inputs['To Min'].default_value=.93;grain.inputs['To Max'].default_value=1.02;l.new(noise.outputs['Fac'],grain.inputs['Value'])
occlusion=n.new('ShaderNodeAmbientOcclusion');occlusion.inputs['Distance'].default_value=.17
pigment=n.new('ShaderNodeMixRGB');pigment.blend_type='MULTIPLY';pigment.inputs[0].default_value=.7;l.new(ramp.outputs[0],pigment.inputs[1]);l.new(occlusion.outputs['Color'],pigment.inputs[2])
grained=n.new('ShaderNodeMixRGB');grained.blend_type='MULTIPLY';grained.inputs[0].default_value=1;l.new(pigment.outputs[0],grained.inputs[1]);l.new(grain.outputs[0],grained.inputs[2]);l.new(grained.outputs[0],em.inputs['Color'])
