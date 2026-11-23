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
# Curves become actual meshes so their projected UVs move with the rig.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
painting=bpy.data.images.load(str(A/'projection.png'));masked={k:bpy.data.images.load(str(A/('projection-'+k+'.png'))) for k in ['wool','linen','skin']};projection=[]
# Source boxes at native 256 pixels; these correct individual kit registration, not silhouette.
regions={'Folded short tunic':(116,69,189,181),'Folded sleeve l':(181,61,198,87),'Folded sleeve r':(119,68,144,94),'Wind folded olive cloak':(57,66,155,188),'Draped cowl fold':(139,65,180,84),'Draped shoulder cowl':(135,51,188,78),'Leather satchel':(119,109,147,146),'Satchel overlapping flap':(121,112,144,130),'Travellers felt hat brim':(126,26,160,78)}
for o in list(sc.objects):
 if o.type!='MESH' or 'Stationary' in o.name or not o.data.materials or 'eyes' in o.name:continue
 if any(s in o.name for s in ['buckle','stud','fastener','grain ridge','Staff','staff','stitch','sewn','hem','lacing','clasp','Draped cowl fold','Hair curl','Beard curl','headband']):continue
 disabled=[(mod,mod.show_viewport) for mod in o.modifiers if mod.type in ['SUBSURF','SOLIDIFY','BEVEL']]
 for mod,_ in disabled:mod.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 if len(me.vertices)!=len(o.data.vertices):
  ev.to_mesh_clear()
  for mod,val in disabled:mod.show_viewport=val
  continue
 coords=[o.matrix_world@v.co for v in me.vertices];normals=[(o.matrix_world.to_3x3()@v.normal).normalized() for v in me.vertices];screen=[world_to_camera_view(sc,sc.camera,c) for c in coords]
 ev.to_mesh_clear()
 for mod,val in disabled:mod.show_viewport=val
 uv=o.data.uv_layers.new(name='PaintingUV');attr=o.data.attributes.new('PaintingFacing','FLOAT','POINT')
 box=next((b for k,b in regions.items() if k in o.name),None)
 xs=[v.x for v in screen];ys=[v.y for v in screen];lo=(min(xs),min(ys));hi=(max(xs),max(ys))
 headids=[v.index for v in o.data.vertices if any(o.vertex_groups[g.group].name=='head' and g.weight>.2 for g in v.groups)] if 'MPFB anatomy' in o.name else []
 if headids:
  hx=[screen[i].x for i in headids];hy=[screen[i].y for i in headids];hb=(min(hx),min(hy),max(hx),max(hy))
 for i,(c,n) in enumerate(zip(coords,normals)):
  dot=n.dot((sc.camera.location-c).normalized());dot=abs(dot) if any(k in o.name for k in ['cloak','cowl','tunic','sleeve']) else dot;attr.data[i].value=max(0,min(1,(dot-.05)*2.3))*.86
 for loop in o.data.loops:
  i=loop.vertex_index;u,v=screen[i].x,screen[i].y
  if box:
   x0,y0,x1,y1=box;u=(x0+(u-lo[0])/max(.001,hi[0]-lo[0])*(x1-x0))/256;v=1-(y1-(v-lo[1])/max(.001,hi[1]-lo[1])*(y1-y0))/256
  elif headids and i in headids:
   u=(163+(u-hb[0])/max(.001,hb[2]-hb[0])*32)/256;v=1-(64-(v-hb[1])/max(.001,hb[3]-hb[1])*45)/256
  uv.data[loop.index].uv=(u,v)
 m=o.data.materials[0].copy();o.data.materials.clear();o.data.materials.append(m);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 if p is None:continue
 tex=n.new('ShaderNodeTexImage');tex.image=masked['wool'] if any(k in o.name for k in ['cloak','cowl']) else masked['linen'] if any(k in o.name for k in ['tunic','sleeve']) else masked['skin'] if 'MPFB anatomy' in o.name else painting;tex.extension='CLIP';uvn=n.new('ShaderNodeUVMap');uvn.uv_map='PaintingUV';l.new(uvn.outputs[0],tex.inputs['Vector'])
 at=n.new('ShaderNodeAttribute');at.attribute_name='PaintingFacing';mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(at.outputs['Fac'],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1])
 mix=n.new('ShaderNodeMixRGB');l.new(mul.outputs[0],mix.inputs[0]);base=p.inputs['Base Color'];mix.inputs[1].default_value=base.default_value
 if base.is_linked:l.new(base.links[0].from_socket,mix.inputs[1])
 l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],base)
 # A restrained emission component avoids lighting the painting highlights twice.
 l.new(mix.outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.18
 projection.append({'object':o.name,'source_box_256':box,'method':'fixed rest-camera UV, facing and source-alpha blend'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'scout.blend'));(M/'projection.json').write_text(json.dumps(projection,indent=2));print('SCOUT_PROJECTED',len(projection),flush=True)
