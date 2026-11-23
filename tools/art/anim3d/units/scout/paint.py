"""Real AO/curvature bakes and fixed-camera painting UVs on deformable geometry."""
import bpy,os,json,math
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/scout';A=R/'assets/scout';out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'scout-unpainted.blend'));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.margin=6
records=[]
for name in ['GEO-Scout MPFB anatomy','GEO-Folded short tunic','GEO-Leather satchel','GEO-Wind folded olive cloak']:
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 if not o.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 o.data.uv_layers.active.name='SurfaceUV';m=o.data.materials[0].copy();o.data.materials.clear();o.data.materials.append(m);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');output=n.get('Material Output')
 mods=[(v,v.show_render,v.show_viewport) for v in o.modifiers if v.type=='SOLIDIFY']
 for v,_,_ in mods:v.show_render=False;v.show_viewport=False
 maps={}
 for mode in ['AO','curvature']:
  im=bpy.data.images.new(name+' '+mode,256,256,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex
  uv=n.new('ShaderNodeUVMap');uv.uv_map='SurfaceUV';l.new(uv.outputs[0],tex.inputs['Vector']);old=output.inputs['Surface'].links[0].from_socket
  if mode=='curvature':
   g=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(g.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
  if mode=='curvature':l.new(old,output.inputs['Surface']);n.remove(em);n.remove(g)
  im.filepath_raw=str(out/(name+'-'+mode+'.png'));im.file_format='PNG';im.save();maps[mode]=tex
 base=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
 if base is None:
  rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=p.inputs['Base Color'].default_value;base=rgb.outputs[0]
 ao=n.new('ShaderNodeMixRGB');ao.blend_type='MULTIPLY';ao.inputs[0].default_value=.33;l.new(base,ao.inputs[1]);l.new(maps['AO'].outputs[0],ao.inputs[2]);l.new(ao.outputs[0],p.inputs['Base Color'])
 ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.45;ramp.inputs['From Max'].default_value=.55;ramp.inputs['To Min'].default_value=.88;ramp.inputs['To Max'].default_value=.61;l.new(maps['curvature'].outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Roughness'])
 for v,r,w in mods:v.show_render=r;v.show_viewport=w
 records.append({'object':name,'size':256,'maps':[maps[k].image.filepath_raw for k in maps]})
(out/'manifest.json').write_text(json.dumps(records,indent=2))
# Finish rigid surfaces before registering their final, rendered geometry.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 if o.type=='MESH' and not o.data.shape_keys:
  bpy.context.view_layer.objects.active=o
  for mod in list(o.modifiers):
   if mod.type in ['BEVEL','SOLIDIFY','SUBSURF'] and not any(m.type=='ARMATURE' for m in o.modifiers):
    bpy.ops.object.modifier_apply(modifier=mod.name)
# Freeze the actual MPFB macro mix and apply helper masks. Previously the
# differing evaluated vertex count silently skipped the entire skin projection.
body=bpy.data.objects['GEO-Scout MPFB anatomy']
if body.data.shape_keys:
 mixed=body.shape_key_add(name='Frozen macros',from_mix=True)
 coords=[tuple(v.co) for v in mixed.data]
 body.shape_key_clear()
 for v,co in zip(body.data.vertices,coords):v.co=co
bpy.context.view_layer.objects.active=body
for mod in list(body.modifiers):
 if mod.type=='MASK':bpy.ops.object.modifier_apply(modifier=mod.name)
painting=bpy.data.images.load(str(A/'projection.png'))
masked={k:bpy.data.images.load(str(A/('projection-'+k+'.png'))) for k in ['wool','linen','skin']}
projection=[]
# The source already contains painted illumination. Only camera rays see this
# pigment layer; shadows and indirect rays still see the original physical BSDF.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
for ob in sc.objects:
 if ob.type=='LIGHT':ob.data.energy*=.55
bpy.data.objects['Warm upper left'].data.color=(1,.96,.89)
bpy.data.objects['Cool rim'].data.energy*=.65
bpy.context.view_layer.update()
for o in list(sc.objects):
 if o.type!='MESH' or 'Stationary' in o.name or not o.data.materials or 'eyes' in o.name:continue
 if any(s in o.name for s in ['buckle','stud','fastener','grain ridge','Staff','staff','stitch','sewn','hem','lacing','clasp','Draped cowl fold','Hair curl','Beard curl','headband']):continue
 disabled=[(mod,mod.show_viewport) for mod in o.modifiers if mod.type in ['SUBSURF','SOLIDIFY','BEVEL']]
 for mod,_ in disabled:mod.show_viewport=False
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(deps);me=ev.to_mesh()
 assert len(me.vertices)==len(o.data.vertices),o.name
 coords=[o.matrix_world@v.co for v in me.vertices];normals=[(o.matrix_world.to_3x3()@v.normal).normalized() for v in me.vertices]
 screen=[world_to_camera_view(sc,sc.camera,c) for c in coords];ev.to_mesh_clear()
 for mod,val in disabled:mod.show_viewport=val
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 uv=o.data.uv_layers.new(name='PaintingUV');attr=o.data.attributes.new('PaintingFacing','FLOAT','POINT')
 for i,(c,n) in enumerate(zip(coords,normals)):
  towards=(sc.camera.location-c).normalized();dot=n.dot(towards)
  if any(k in o.name for k in ['cloak','cowl','tunic','sleeve']):dot=abs(dot)
  # A ray from just above the surface rejects hidden/occluded source paint.
  hit,loc,normal,index,hitob,matrix=sc.ray_cast(deps,c+towards*.012,towards,distance=20)
  visible=not hit or (loc-c).length<.025
  attr.data[i].value=max(0,min(1,(dot-.08)*3.5))*.94 if visible else 0
 for loop in o.data.loops:
  p=screen[loop.vertex_index];uv.data[loop.index].uv=(p.x,p.y)
 m=o.data.materials[0].copy();o.data.materials.clear();o.data.materials.append(m);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 if p is None:continue
 tex=n.new('ShaderNodeTexImage');tex.image=masked['wool'] if any(k in o.name for k in ['cloak','cowl']) else masked['linen'] if any(k in o.name for k in ['tunic','sleeve']) else masked['skin'] if 'MPFB anatomy' in o.name else painting;tex.extension='CLIP'
 uvn=n.new('ShaderNodeUVMap');uvn.uv_map='PaintingUV';l.new(uvn.outputs[0],tex.inputs['Vector'])
 at=n.new('ShaderNodeAttribute');at.attribute_name='PaintingFacing';weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';l.new(at.outputs['Fac'],weight.inputs[0]);l.new(tex.outputs['Alpha'],weight.inputs[1])
 pigment=n.new('ShaderNodeEmission');pigment.name='Frozen painted illumination';l.new(tex.outputs['Color'],pigment.inputs['Color'])
 camera=n.new('ShaderNodeLightPath');camera.name='Camera-only pigment'
 mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(camera.outputs['Is Camera Ray'],mask.inputs[0]);l.new(weight.outputs[0],mask.inputs[1])
 mix=n.new('ShaderNodeMixShader');l.new(mask.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
 projection.append({'object':o.name,'source_box_256':None,'method':'single frozen rest-camera UV; visibility, facing and source material alpha; camera-only pigment'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'scout.blend'));(M/'projection.json').write_text(json.dumps(projection,indent=2));print('SCOUT_PROJECTED',len(projection),flush=True)
