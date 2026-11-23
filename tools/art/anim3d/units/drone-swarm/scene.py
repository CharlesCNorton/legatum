"""Three complete volumetric drones, calibrated in rest-camera screen coordinates.
Pixel landmarks are drafting constraints only: every body is a closed solid,
rotors are solid airfoils, lenses are spheres and all parts articulate in 3D.
"""
import bpy,bmesh,math,os,json,random
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/drone-swarm';A=R/'assets/drone-swarm'
reg=json.loads((M/'registration.json').read_text());S=reg['scale'];OX,OY=reg['offset'];K=6/256
UP=Vector((0,.28,math.sqrt(1-.28**2)));VIEW=Vector((0,-UP.z,UP.y));RIGHT=Vector((1,0,0));CENTER=Vector((0,0,2.55))
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.device='CPU';sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
world=bpy.data.worlds.new('WORLD-soft studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.86,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;sc.world=world
camdata=bpy.data.cameras.new('CAM-painting');cam=bpy.data.objects.new('CAM-painting',camdata);sc.collection.objects.link(cam);cam.location=CENTER+VIEW*14;cam.rotation_euler=(-VIEW).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=6;sc.camera=cam
for name,pos,power,size,color in [('key',(-4,-5,9),650,4,(1,.88,.69)),('fill',(5,-3,5),160,5,(.84,.91,1)),('rim',(2,4,7),420,3,(.72,.83,1))]:
 d=bpy.data.lights.new('LGT-'+name,'AREA');o=bpy.data.objects.new('LGT-'+name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(CENTER-o.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.size=size;d.color=color

def linear(c):return ((c+.055)/1.055)**2.4 if c>.04045 else c/12.92

def material(name,color,metal=0,rough=.6):
 m=bpy.data.materials.new('MAT-'+name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');b.inputs['Base Color'].default_value=(*[linear(c) for c in color],1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180;noise.inputs['Roughness'].default_value=.72
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.17;bump.inputs['Distance'].default_value=.007;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],b.inputs['Normal'])
 return m
bronze=material('worn bronze alloy',(.54,.49,.35),1,.52);steel=material('polished edge alloy',(.72,.68,.54),1,.3);dark=material('recess graphite',(.14,.14,.12),0,.77);blade=material('carbon propeller',(.24,.23,.21),0,.57);glass=material('purple optical coating',(.12,.12,.20),1,.16);stone=material('cream stone E9CFA0',(233/255,207/255,160/255),0,.84)
# Generated material artwork supplies hidden/back surfaces, with true metal only on metal.
fill=bpy.data.images.load(str(A/'painted-fill.png'))
for mat in (bronze,steel):
 n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF');t=n.new('ShaderNodeTexImage');t.image=fill;t.projection='BOX';t.projection_blend=.25;tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],t.inputs[0]);l.new(t.outputs['Color'],b.inputs['Base Color'])

def P(x,y,d=0):return CENTER+RIGHT*((OX+x*5*S-128)*K)+UP*((128-OY-y*5*S)*K)+VIEW*d

def finish(o,name,mat,bevel=.012):
 o.name='GEO-'+name;o.data.materials.append(mat)
 if bevel:
  m=o.modifiers.new('Machined edge roundover','BEVEL');m.width=bevel;m.segments=3
 for p in o.data.polygons:p.use_smooth=False
 return o

def solid(name,verts,faces,mat,bevel=.012):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();return finish(o,name,mat,bevel)

def ellipsoid(name,pos,size,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=pos);o=bpy.context.object;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,name,mat,0)
 for p in o.data.polygons:p.use_smooth=True
 return o

def cylinder(name,a,b,radius,mat,vertices=32):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,.008)

def rod(name,a,b,r,mat):return cylinder(name,a,b,r,mat,16)

def empty(name,pos):
 o=bpy.data.objects.new('RIG-'+name,None);sc.collection.objects.link(o);o.location=pos;return o

def parent(o,p):
 bpy.context.view_layer.update();mw=o.matrix_world.copy();o.parent=p;o.matrix_world=mw

# Base is a horizontal real cylinder. Its projected ellipse matches the painting.
bcenter=P(119.5,215.5,0);radius=81*5*S*K
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=radius,depth=.29,location=bcenter);base=finish(bpy.context.object,'stationary cream base',stone,.045)
# Source base's top is about 36% as high as wide; camera elevation = asin(.28).
roots=[];hulls=[];rotors=[];gimbals=[]
# Offsets / scales drafted from each reference silhouette (source coordinates / 5).
for idx,(dx,dy,scale) in enumerate([(0,0,1),(-47,68,.94),(28,114,.88)]):
 tag=f'drone{idx+1}'
 def Q(x,y,d=0):return P(138+(x-138)*scale+dx,34+(y-34)*scale+dy,d*scale)
 root=empty(tag,Q(138,36));roots.append(root);parts=[]
 # Hand-drafted volumetric armour shell: broad side, bevelled bonnet, rear dome.
 contour=[(117,24,-.10),(124,16,-.22),(133,13,-.23),(143,16,-.13),(151,23,.03),(157,31,.22),(161,37,.40),(158,44,.44),(141,45,.42),(130,40,.24),(122,32,.05)]
 vs=[Q(*v) for v in contour]
 vs += [Q(132,23,-.03),Q(138,30,.20),Q(141,39,.40)]
 # A full curved underside closes the shell well behind its visible side plates.
 vs += [Q(135+(x-135)*.82,29+(y-29)*.82,d-.48) for x,y,d in contour]
 faces=[(0,1,11,12,13,8,9,10),(1,2,3,4,11),(11,4,5,6,13,12),(13,6,7,8),tuple(reversed(range(14,25)))]
 faces += [(i,(i+1)%11,(i+1)%11+14,i+14) for i in range(11)]
 hull=solid(tag+' hull',vs,faces,bronze,.022);parts.append(hull);hulls.append(hull)
 # Front sensor recess and thick protective lip, facing the source camera.
 def panel(name,x,y,w,h,d,mat):
  vs=[Q(x+sx*w/2,y+sy*h/2,d+dz) for dz in (-.025,.025) for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  return solid(tag+' '+name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,.012)
 parts.append(panel('sensor protective rim',149,39,17,8,.37,steel));parts.append(panel('inset sensor window',149,39,14,5,.41,dark))
 for x in (144,154):parts.append(ellipsoid(tag+' navigation optic',Q(x,39,.47),(.035,.035,.035),glass))
 # Gimbal has actual trunnions, yoke and a deep glass lens.
 gm=empty(tag+' gimbal',Q(147,56,.42));gimbals.append(gm);parent(gm,root)
 for sx in (-1,1):
  o=rod(tag+' gimbal yoke',Q(147+sx*7,46,.29),Q(147+sx*7,56,.42),.055*scale,bronze);parts.append(o)
  o=cylinder(tag+' gimbal pivot',Q(147+sx*7,53,.40),Q(147+sx*7,53,.49),.072*scale,steel);parts.append(o)
 body=ellipsoid(tag+' gimbal housing',Q(147,56,.43),(.27*scale,.24*scale,.27*scale),bronze);parent(body,gm)
 lens=cylinder(tag+' lens ring',Q(148,57,.58),Q(148,57,.72),.181*scale,steel);parent(lens,gm)
 iris=ellipsoid(tag+' lens glass',Q(148,57,.75),(.145*scale,.145*scale,.145*scale),glass);parent(iris,gm)
 # Two weighty articulated rotor pods and aerodynamically tapered solid blades.
 for side,(x,y) in enumerate(((98,19),(181,26))):
  parts.append(rod(tag+' rotor spar',Q(126 if side==0 else 153,27,.0),Q(x,y+5,.0),.075*scale,bronze))
  for zoff,r,depth,mat in [(5,.148,.17,bronze),(0,.12,.21,steel),(-5,.07,.09,dark)]:
   pos=Q(x,y+zoff,.0);parts.append(cylinder(tag+' motor casing',pos-Vector((0,0,depth*scale/2)),pos+Vector((0,0,depth*scale/2)),r*scale,mat))
  rp=Q(x,y-9,.025);rot=empty(tag+f' rotor{side}',rp);rotors.append(rot);parent(rot,root)
  # Rotor lies horizontally, with swept, rounded tips. Root and blade retain thickness.
  for sign in (-1,1):
   length=.59*scale;outline=[(.025,-.035),(.25,-.12),(.52,-.12),(.59,-.018),(.53,.08),(.22,.10)]
   verts=[rp+Vector((sign*a,sign*b,dz)) for dz in (-.012,.012) for a,b in outline];nf=len(outline)
   ob=solid(tag+f' rotor{side} blade{sign}',verts,[tuple(reversed(range(nf))),tuple(range(nf,2*nf))]+[(i,(i+1)%nf,(i+1)%nf+nf,i+nf) for i in range(nf)],blade,.008);parent(ob,rot)
  rot.rotation_euler.z=.65 if side==0 else -.65
  cap=ellipsoid(tag+' rotor hub',rp,(.09*scale,.09*scale,.045*scale),steel);parent(cap,rot)
 # Landing struts, no support columns down to the pedestal.
 for x,off in ((126,0),(140,.18)):
  parts.append(rod(tag+' landing strut',Q(x,39,-.03+off),Q(x-8,55,-.03+off),.067*scale,bronze));parts.append(rod(tag+' landing toe',Q(x-8,55,-.03+off),Q(x-6,57,.03+off),.066*scale,dark))
 # Panel seams, screw heads, vents and beveled edge rails are actual small geometry.
 for (a,b) in [((125,14),(137,26)),((140,16),(152,29)),((137,26),(152,29)),((130,36),(140,45))]:parts.append(rod(tag+' raised panel seam',Q(*a,.01),Q(*b,.33),.012*scale,steel))
 for x,y,d in [(128,20,-.18),(136,21,-.12),(140,29,.34),(151,31,.34),(155,42,.35),(138,40,.35),(100,23,.13),(180,30,.13)]:
  parts.append(ellipsoid(tag+' recessed fastener',Q(x,y,d),(.027*scale,.027*scale,.027*scale),dark))
  parts.append(ellipsoid(tag+' screw glint',Q(x-.35,y-.35,d+.025),(.013*scale,.013*scale,.013*scale),steel))
 for i in range(4):parts.append(rod(tag+' cooling vent',Q(125+i*.9,19+i*.35,-.20),Q(124+i*.9,21+i*.35,-.18),.013*scale,dark))
 for ob in parts:parent(ob,root)
# Plain stage is a persistent geometry snapshot before painting.
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
image=bpy.data.images.load(str(A/'projection.png'));records=[]
for ob in [o for o in sc.objects if o.type=='MESH']:
 me=ob.data;uv=me.uv_layers.new(name='PaintingProjection');weight=me.color_attributes.new(name='Paint confidence',type='FLOAT_COLOR',domain='CORNER');normalmatrix=ob.matrix_world.to_3x3().inverted().transposed()
 for loop in me.loops:
  vert=me.vertices[loop.vertex_index];pt=world_to_camera_view(sc,cam,ob.matrix_world@vert.co);uv.data[loop.index].uv=(pt.x,pt.y)
  facing=max(0,min(1,((normalmatrix@vert.normal).normalized().dot(VIEW)+.02)/.35));weight.data[loop.index].color=(facing,facing,facing,1)
 mat=ob.data.materials[0].copy();mat.name=ob.name+' painted';ob.data.materials.clear();ob.data.materials.append(mat);n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF');original=b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None
 coord=n.new('ShaderNodeUVMap');coord.uv_map='PaintingProjection';tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP';l.new(coord.outputs[0],tex.inputs[0]);conf=n.new('ShaderNodeVertexColor');conf.layer_name='Paint confidence';mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(conf.outputs['Color'],mask.inputs[0]);l.new(tex.outputs['Alpha'],mask.inputs[1]);mix=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mix.inputs[0]);mix.inputs[1].default_value=b.inputs['Base Color'].default_value
 if original:l.new(original,mix.inputs[1])
 l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],b.inputs['Base Color'])
 # Painting already contains light: use physical relief plus painted emission.
 em=n.new('ShaderNodeEmission');l.new(mix.outputs[0],em.inputs[0]);fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.68;l.new(mask.outputs[0],fac.inputs[0]);surf=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],surf.inputs[0]);l.new(b.outputs[0],surf.inputs[1]);l.new(em.outputs[0],surf.inputs[2]);l.new(surf.outputs[0],n.get('Material Output').inputs['Surface']);records.append(ob.name)
sc['unit']='drone-swarm';sc['rig']='3 independent rigid body roots, 6 rotor pivots, 3 gimbals';sc['projection']='frozen rest-camera UVs; back/underside generated bronze fill';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'drone-swarm.blend'));(M/'model.json').write_text(json.dumps({'meshes':len(records),'projected':records,'rig_roots':[o.name for o in roots],'rotors':[o.name for o in rotors]},indent=2));print('MODEL COMPLETE',len(records),flush=True)
