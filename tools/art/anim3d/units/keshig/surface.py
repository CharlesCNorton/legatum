# Convert bevelled equipment to finished 3D meshes before freezing UVs.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
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
# Rest-view sculpture retains all depth and inverse-transforms skin deltas.
right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0));up=sc.camera.matrix_world.to_quaternion() @ Vector((0,1,0))
def fit_objects(objects, landmarks, radius):
 for o in objects:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  assert len(me.vertices)==len(o.data.vertices),o.name
  arm=next((m.object for m in o.modifiers if m.type=='ARMATURE'),None)
  Ato=arm.matrix_world.inverted() @ o.matrix_world if arm else None
  for v,pv in zip(o.data.vertices,me.vertices):
   world=o.matrix_world @ pv.co;q=world_to_camera_view(sc,sc.camera,world);x,y=q.x*256,(1-q.y)*256
   weights=[math.exp(-((x-a[0])**2+(y-a[1])**2)/(2*radius**2)) for a,b in landmarks]
   total=max(1.,sum(weights));dx=sum(w*(b[0]-a[0]) for w,(a,b) in zip(weights,landmarks))/total;dy=sum(w*(b[1]-a[1]) for w,(a,b) in zip(weights,landmarks))/total
   local=o.matrix_world.to_3x3().inverted() @ ((right*dx-up*dy)*(sc.camera.data.ortho_scale/256))
   if arm:
    weighted=Matrix(((0.,0.,0.,0.),)*4);total=0
    for g in v.groups:
     name=o.vertex_groups[g.group].name
     if name not in arm.pose.bones:continue
     bone=arm.pose.bones[name];weighted+=(bone.matrix @ bone.bone.matrix_local.inverted())*g.weight;total+=g.weight
    if total>.001:local=(Ato.inverted() @ (weighted*(1/total)) @ Ato).to_3x3().inverted_safe() @ local
   v.co+=local
  ev.to_mesh_clear();o.data.update()
 bpy.context.view_layer.update()

rider_objects=[];horse_objects=[]
for o in sc.objects:
 if o.type!='MESH' or o.name=='Stationary cream stone':continue
 p=o
 while p is not None and p!=rig:p=p.parent
 (rider_objects if p==rig else horse_objects).append(o)
# Broader cap/face and a longer bow arm match the painting's adult proportions.
fit_objects(rider_objects,[((147,48),(140,48)),((160,48),(169,48)),((154,32),(157,35))],7)
arm_objects=[o for o in rider_objects if not o.name.startswith('GEO-')]
fit_objects(arm_objects,[((107,65),(89,65)),((122,70),(116,70)),((149,150),(157,164))],14)
for o in rider_objects:
 if o.name.startswith(('GEO-composite','GEO-bow','GEO-drawn','GEO-nocked','GEO-arrow iron')):
  for v in o.data.vertices:
   w=o.matrix_world @ v.co;q=world_to_camera_view(sc,sc.camera,w)
   # Bow/string/arrow remain solid attached meshes; move pigment-bearing grip
   # together with the newly tailored sleeve and hand.
   t=1. if o.name.startswith(('GEO-composite','GEO-bow')) else max(0,min(1,(148-q.x*256)/40))
   if o.name.startswith('GEO-drawn') and (q.y*256<171 or q.y*256>211):t=1.
   v.co+=o.matrix_world.to_3x3().inverted() @ (-right*(sc.camera.data.ortho_scale/256)*18*t)
fit_objects([horse],[((124,159),(124,168)),((88,143),(86,149))],13)

base=bpy.data.objects['Stationary cream stone'];base.location+=right*(-.18)+up*.16;base.scale.x*=1.07;base.scale.y*=1.07
# Physical painted stone: no figure/hoof pixels projected onto stationary geometry.
base=bpy.data.objects['Stationary cream stone'];stone=base.data.materials[0];n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF')
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
s.inputs['Base Color'].default_value=tuple(linear(v/255) for v in (233,207,160))+(1,)
s.inputs['Roughness'].default_value=.86
# Standard is deliberate here: the projected source already contains painted light.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,power,color in [('Warm key',360,(1,.95,.86)),('Cool fill',72,(.88,.93,1)),('Warm rim',108,(.83,.91,1))]:
 light=bpy.data.objects[name];light.data.energy=power;light.data.color=color

# Camera-only pigment opens the cream top/rim while preserving physical contact
# shadows. No source figure or static painted shadow enters this base material.
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],sep.inputs[0])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.1;ramp.color_ramp.elements[0].color=tuple(linear(v/255) for v in (211,174,121))+(1,);ramp.color_ramp.elements[1].position=.9;ramp.color_ramp.elements[1].color=tuple(linear(v/255) for v in (250,224,181))+(1,);l.new(sep.outputs['Z'],ramp.inputs[0])
em=n.new('ShaderNodeEmission');l.new(ramp.outputs[0],em.inputs['Color'])
ray=n.new('ShaderNodeLightPath');fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.72;l.new(ray.outputs['Is Camera Ray'],fac.inputs[0])
blend=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(em.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],n.get('Material Output').inputs['Surface'])
sc['support_height']=base.location.z+.05

# Camera-visible fine grain and contact AO remain in the stone pigment branch.
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180
nr=n.new('ShaderNodeMapRange');nr.inputs['To Min'].default_value=.92;nr.inputs['To Max'].default_value=1.035;l.new(noise.outputs['Fac'],nr.inputs['Value'])
grain=n.new('ShaderNodeMixRGB');grain.blend_type='MULTIPLY';grain.inputs[0].default_value=1;l.new(ramp.outputs[0],grain.inputs[1]);l.new(nr.outputs[0],grain.inputs[2])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.13
contact=n.new('ShaderNodeMixRGB');contact.blend_type='MULTIPLY';contact.inputs[0].default_value=.18;l.new(grain.outputs[0],contact.inputs[1]);l.new(ao.outputs['Color'],contact.inputs[2]);l.new(contact.outputs[0],em.inputs['Color'])
