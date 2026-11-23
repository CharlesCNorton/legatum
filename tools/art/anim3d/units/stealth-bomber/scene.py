"""Closed, cambered flying-wing sculpture with intake wells and a convex cockpit.
Source coordinates register its geometry; depth is retained in every view.
"""
import bpy,bmesh,math,json,os,sys
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/stealth-bomber';A=R/'assets/stealth-bomber'
reg=json.loads((M/'registration.json').read_text());S=6.4
UP=Vector((0,.28,math.sqrt(1-.28**2)));FRONT=Vector((0,-UP.z,UP.y));RIGHT=Vector((1,0,0))
def p(x,y,d=0):
 u=(x-reg['box'][0])*reg['scale']+reg['offset'][0];v=(y-reg['box'][1])*reg['scale']+reg['offset'][1]
 return RIGHT*((u/1024-.5)*S)+UP*((.5-v/1024)*S)+FRONT*d
def depth(x,y):return .0014*(x-650)+.0018*(y-450)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.render.film_transparent=True
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
cam=bpy.data.objects.new('CAM-painting',bpy.data.cameras.new('CAM-painting'));bpy.context.collection.objects.link(cam);cam.location=FRONT*15;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=S;sc.camera=cam
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
for name,loc,power,color,size in [('key',(-3,-5,7),470,(1,.97,.91),4),('fill',(4,-4,3),125,(.92,.95,1),5),('rim',(0,5,5),300,(.85,.91,1),3)]:
 o=bpy.data.objects.new('LGT-'+name,bpy.data.lights.new(name,'AREA'));bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.color=color;o.data.size=size

def material(name,color,metal=0,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=140;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.004;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal']);return m
paint=material('MAT-painted composite',(.12,.115,.11));metal=material('MAT-worn edge alloy',(.52,.51,.48),1,.48);black=material('MAT-intake shadow',(.017,.017,.016),0,.85);glass=material('MAT-smoked canopy',(.065,.073,.075),0,.28)
stone=material('MAT-cream stone E9CFA0',(.815,.624,.352),0,.86)
objects=[]
def mesh(name,verts,faces,mat,parent=True,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('GEO-'+name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=smooth
 if parent:objects.append(ob)
 return ob

def shell(name,poly,mat,thick=.08,crown=.15,parent=True):
 # Dense true cambered solid: distinct upper/lower surfaces, welded perimeter.
 pts=[Vector((x,y,0)) for x,y in poly];faces=[]
 for tri in tessellate_polygon([pts]):faces.append(tuple((v if isinstance(v,int) else pts.index(v)) for v in tri))
 me=bpy.data.meshes.new('temporary');me.from_pydata(pts,[],faces);bm=bmesh.new();bm.from_mesh(me)
 bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=6,use_grid_fill=True);bm.verts.ensure_lookup_table();bm.verts.index_update()
 verts=[(v.co.x,v.co.y) for v in bm.verts];topfaces=[tuple(v.index for v in f.verts) for f in bm.faces];edges=[(e.verts[0].index,e.verts[1].index) for e in bm.edges if e.is_boundary];N=len(verts)
 # Distance to boundary controls airfoil thickness and prevents blunt tip caps.
 def dist(x,y):
  q=Vector((x,y));vals=[]
  for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
   a=Vector((ax,ay));b=Vector((bx,by));v=b-a;t=max(0,min(1,(q-a).dot(v)/v.length_squared));vals.append((q-a-v*t).length)
  return min(vals)
 vv=[]
 for side in (1,-1):
  for x,y in verts:
   w=min(1,dist(x,y)/90);d=depth(x,y)+side*(.012+thick*w)+(crown*w if side==1 else 0)
   vv.append(p(x,y,d))
 ff=topfaces+[tuple(i+N for i in reversed(f)) for f in topfaces]+[(i,j,j+N,i+N) for i,j in edges]
 o=mesh(name,vv,ff,mat,parent,True);bm.free();bpy.data.meshes.remove(me)
 b=o.modifiers.new('Airfoil edge radius','BEVEL');b.width=.006;b.segments=2;return o
outline=[(8,761),(125,623),(297,599),(352,484),(465,474),(446,410),(608,385),(635,336),(786,329),(778,296),(1013,281),(1002,235),(1166,153),(1245,171),(1146,384),(1114,512),(1180,631),(1011,624),(744,660),(689,665),(280,728),(45,770)]
body=shell('fuselage',outline,paint,.10,.23)
# Sculpted centre spine and distinct bevelled intakes carry relief in other views.
spine=shell('centre crown',[(535,415),(682,393),(842,413),(1012,468),(1116,544),(1150,611),(1013,621),(847,551),(777,464)],paint,.025,.12)

def tube(name,points,r,mat,parent=True):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2;cu.use_fill_caps=True;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for dst,pt in zip(sp.points,points):dst.co=(*pt,1)
 ob=bpy.data.objects.new('GEO-'+name,cu);bpy.context.collection.objects.link(ob);cu.materials.append(mat)
 if parent:objects.append(ob)
 return ob
for name,poly in [('near intake',[(703,507),(779,488),(846,550),(732,547)]),('far intake',[(900,397),(949,383),(1022,427),(947,431)])]:
 # Rim walls, a recessed floor, and an outer ramp; every part has thickness.
 center=Vector((sum(x for x,y in poly)/4,sum(y for x,y in poly)/4));inner=[tuple(center+(Vector(v)-center)*.83) for v in poly]
 # Remove the underlying airfoil before adding real recessed walls.
 cutverts=[p(x,y,depth(x,y)+d) for d in (.065,.95) for x,y in inner]
 cutfaces=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 cutter=mesh(name+' cutter',cutverts,cutfaces,black,False)
 for target in (body,spine):
  bpy.context.view_layer.objects.active=target
  mod=target.modifiers.new('Recess '+name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
  bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(cutter,do_unlink=True)
 vv=[p(x,y,depth(x,y)+d) for ring,d in [(poly,.47),(inner,.47),(inner,.075)] for x,y in ring]
 ff=[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]+[(i+4,(i+1)%4+4,(i+1)%4+8,i+8) for i in range(4)]+[(8,9,10,11)]
 ob=mesh(name,vv,ff,paint);solid=ob.modifiers.new('Intake wall thickness','SOLIDIFY');solid.thickness=.025;be=ob.modifiers.new('Intake lip bevel','BEVEL');be.width=.012;be.segments=3
# Canopy is a convex closed shell with real low-profile framing.
canopy=shell('cockpit',[(935,520),(966,486),(995,466),(1042,480),(1098,521),(1121,561),(1088,566),(989,545)],glass,.03,.22)
canopy.location+=FRONT*.27
for i,line in enumerate([[(935,520),(966,486),(995,466),(1042,480),(1098,521),(1121,561),(1088,566),(989,545),(935,520)],[(966,486),(987,503),(979,537)],[(995,466),(1015,479),(1026,547)],[(1042,480),(1068,512),(1108,555)]]):
 tube('canopy frame '+str(i),[p(x,y,depth(x,y)+.49) for x,y in line],.006,metal)
# Stationary limestone disc in the painting's world plane.
basecenter=p(655,1022,-.7)
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.025,depth=.15,location=basecenter);base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);be=base.modifiers.new('Rounded limestone lip','BEVEL');be.width=.025;be.segments=4
coords=[(550,978),(563,900),(581,837),(613,777),(657,716),(691,671),(698,649),(739,646),(705,705),(684,753),(675,801),(679,845),(701,893),(736,944),(773,986),(747,1002)]
# Carved support is a tapered solid wedge, not an alpha card.
vv=[p(x,y,d) for d in (-.6,-.35) for x,y in coords];n=len(coords);ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
support=mesh('curved stationary stone support',vv,ff,stone,False);be=support.modifiers.new('Carved support bevel','BEVEL');be.width=.018;be.segments=3
root=bpy.data.objects.new('RIG-airframe',None);bpy.context.collection.objects.link(root);root.location=p(760,470,depth(760,470));bpy.context.view_layer.update()
for ob in objects:
 mat=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=mat
bpy.context.view_layer.update()
for i in range(3):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=p(830+i*24,585,.4));ob=bpy.context.object;ob.name='GEO-bomb-'+str(i);ob.scale=(.042,.042,.115);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(black);ob.hide_render=True
sc['unit']='stealth-bomber';sc['projection_method']='frozen camera UV on closed cambered volumes';sc['base_hex']='#E9CFA0'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
for ob in list(bpy.data.objects):
 if ob.type not in ('MESH','CURVE'):continue
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 if ob.type=='CURVE':bpy.ops.object.convert(target='MESH')
 for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 if 'support' in ob.name or 'intake' in ob.name:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True);bm.to_mesh(ob.data);bm.free();ob.data.update()
 ob['surface_finished']=True
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(M/'surface.blend'))
sys.path.insert(0,str(Path(__file__).resolve().parent));from project import apply_projection
apply_projection(sc,cam,A,FRONT)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'stealth-bomber.blend'))
(M/'geometry.json').write_text(json.dumps({'blender':bpy.app.version_string,'mesh_count':len([o for o in bpy.data.objects if o.type=='MESH']),'rig':'airframe rigid hierarchy and released bombs','volumetric_smoke':False},indent=2))
