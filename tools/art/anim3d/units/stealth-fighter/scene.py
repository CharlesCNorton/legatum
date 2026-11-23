"""Closed, faceted stealth airframe; dimensional wings, intakes, fins and exhaust.
Source landmarks register the rest camera while per-part depth builds real volume.
No cards, alpha-clipped geometry or camera constraints on the moving aircraft.
"""
import bpy,bmesh,math,json,os,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/stealth-fighter';A=R/'assets/stealth-fighter'
reg=json.loads((M/'registration.json').read_text());S=6.4
UP=Vector((0,.36,math.sqrt(1-.36**2)));FRONT=Vector((0,-UP.z,UP.y));RIGHT=Vector((1,0,0))
def p(x,y,d=0):
 u=(x-reg['box'][0])*reg['scale']+reg['offset'][0];v=(y-reg['box'][1])*reg['scale']+reg['offset'][1]
 return RIGHT*((u/1024-.5)*S)+UP*((.5-v/1024)*S)+FRONT*d
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.render.film_transparent=True
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.32
cam=bpy.data.objects.new('CAM-painting',bpy.data.cameras.new('CAM-painting'));bpy.context.collection.objects.link(cam);cam.location=FRONT*15;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=S;sc.camera=cam
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
for name,loc,power,color,size in [('key',(-3,-5,7),430,(1,.96,.88),4),('fill',(4,-4,3),110,(.92,.95,1),5),('rim',(0,5,5),260,(.82,.90,1),3)]:
 o=bpy.data.objects.new('LGT-'+name,bpy.data.lights.new(name,'AREA'));bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.color=color;o.data.size=size

def material(name,color,metal=0,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=130;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.004;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal']);return m
paint=material('MAT-grey painted composite',(.18,.19,.19));silver=material('MAT-worn titanium edges',(.56,.58,.59),1,.46);dark=material('MAT-exhaust ceramic',(.027,.030,.030),0,.8);glass=material('MAT-amber canopy',(.38,.31,.13),0,.26)
stone=material('MAT-cream stone E9CFA0',(.815,.624,.352),0,.86)
objects=[]
def mesh(name,verts,faces,mat,parent=True):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('GEO-'+name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 if parent:objects.append(ob)
 return ob

def solid(name,coords,depth,thickness,mat=paint,parent=True,ridge=None):
 # Closed faceted body: finished roof, bottom and side walls with real depth.
 ds=depth if isinstance(depth,list) else [depth]*len(coords);vs=[p(x,y,d) for (x,y),d in zip(coords,ds)];n=len(vs)
 vs += [v-FRONT*thickness for v in vs]
 fs=[tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 if ridge is None:fs.append(tuple(range(n-1,-1,-1)))
 else:
  vs.append(p(*ridge));fs += [(i,(i+1)%n,2*n) for i in range(n)]
 ob=mesh(name,vs,fs,mat,parent);b=ob.modifiers.new('Machined edge roundover','BEVEL');b.width=.008 if mat!=stone else .018;b.segments=3;return ob
# Main lifting body includes two raised engine spines and a tapered radar nose.
fuselage=solid('fuselage',[(200,634),(266,561),(409,460),(615,320),(812,237),(902,227),(1040,153),(1101,154),(1244,126),(1197,182),(1040,327),(1043,374),(993,418),(774,542),(600,637),(372,712),(291,683)],[-.02,.08,.14,.12,.06,.10,.16,.18,.08,.12,.25,.26,.24,.25,.25,.26,.20],.28,ridge=(717,370,.48))
far=solid('far wing',[(215,345),(185,232),(289,196),(617,316),(808,258),(624,440),(390,519)],[-.13,-1.28,-1.34,-.60,-.13,-.12,.03],.065)
near=solid('near wing',[(469,658),(695,478),(813,405),(899,466),(979,735),(932,770),(595,688)], [.32,.20,.13,.35,1.28,1.29,.63],.075)
solid('far stabilizer',[(213,474),(66,469),(10,506),(65,598),(217,607),(332,541)],[-.02,-.65,-.71,-.57,.02,.12],.065)
solid('near stabilizer',[(360,697),(401,804),(520,837),(592,692),(638,633)], [.32,.94,1.06,.69,.35],.065)
# Engine fairings with substantial cross section, no flat extrusion of the silhouette.
solid('far engine spine',[(199,635),(267,571),(664,314),(762,288),(698,385),(306,671)], [.14,.31,.26,.20,.32,.22],.18,ridge=(462,475,.58))
solid('near engine spine',[(291,683),(356,614),(704,358),(818,321),(759,423),(373,713)], [.30,.43,.38,.29,.38,.31],.18,ridge=(535,511,.68))
solid('far vertical fin',[(215,589),(176,348),(246,306),(410,462),(302,543)], [.30,.37,.40,.39,.38],.060)
solid('near vertical fin',[(382,693),(505,499),(585,456),(629,567),(479,655)], [.56,.68,.70,.69,.64],.065)
# Separate raised cockpit and faceted gold canopy.
solid('cockpit sill',[(832,327),(854,279),(937,200),(1024,151),(1100,155),(1119,171),(1057,241),(947,275),(888,302)], [.36,.42,.45,.42,.33,.30,.40,.49,.46],.18,ridge=(991,225,.63))
solid('gold canopy',[(914,232),(955,192),(997,161),(1023,153),(1047,181),(1056,224),(951,248)], [.57,.59,.57,.50,.52,.57,.64],.14,glass,ridge=(999,195,.79))
solid('canopy rear window',[(1030,153),(1097,156),(1113,171),(1060,217)], [.48,.35,.38,.57],.10,glass)
# Apertures are recessed dark solids inside bevelled lips.
for label,coords,d in [('near',[(832,335),(879,344),(878,374),(847,359)],.55),('far',[(819,264),(853,254),(837,281),(808,290)],.25)]:
 solid(label+' intake lip',coords,d,.13,silver)
 cx=sum(x for x,y in coords)/len(coords);cy=sum(y for x,y in coords)/len(coords)
 solid(label+' intake throat',[(cx+(x-cx)*.77,cy+(y-cy)*.75) for x,y in coords],d+.004,.06,dark)
# Two rectangular vectoring nozzle tunnels: four walls and recessed back, visible flutes.
for label,poly,d in [('far',[(262,582),(315,603),(273,667),(199,636)],.45),('near',[(342,620),(397,642),(373,712),(291,684)],.62)]:
 cx=sum(x for x,y in poly)/4;cy=sum(y for x,y in poly)/4;inner=[(cx+(x-cx)*.75,cy+(y-cy)*.75) for x,y in poly]
 vs=[p(x,y,d+off) for off,points in [(0,poly),(0,inner),(-.20,inner)] for x,y in points]
 fs=[]
 for i in range(4):j=(i+1)%4;fs.extend([(i,j,4+j,4+i),(4+i,4+j,8+j,8+i)])
 ob=mesh(label+' exhaust shroud',vs,fs,silver);sol=ob.modifiers.new('Nozzle wall thickness','SOLIDIFY');sol.thickness=.018;b=ob.modifiers.new('Exhaust bevel','BEVEL');b.width=.006;b.segments=2
 solid(label+' exhaust recess',inner,d-.20,.06,dark)
# Physical base and sculpted stand. Keep one plain round disc.
center=p(640,1027,-.50)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.13,depth=.20,location=center);base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);b=base.modifiers.new('Rounded stone lip','BEVEL');b.width=.025;b.segments=4
support=solid('curved stationary stone support',[(504,971),(531,887),(577,789),(636,696),(679,710),(659,765),(646,821),(654,879),(683,931),(732,985),(672,1011)],[-.30]*11,.25,stone,False,ridge=(609,894,-.12))
root=bpy.data.objects.new('RIG-airframe',None);bpy.context.collection.objects.link(root);root.location=p(665,450,.10)
bpy.context.view_layer.update()
for ob in objects:
 mat=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=mat
# Elevon hinges are separate rigid pivots; neutral surface position is preserved.
for side,name in [('near','GEO-near stabilizer'),('far','GEO-far stabilizer')]:
 ob=bpy.data.objects[name];pivot=bpy.data.objects.new('RIG-'+side+' elevon',None);bpy.context.collection.objects.link(pivot);pivot.location=ob.matrix_world @ sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);bpy.context.view_layer.update();mat=pivot.matrix_world.copy();pivot.parent=root;pivot.matrix_world=mat;bpy.context.view_layer.update();mat=ob.matrix_world.copy();ob.parent=pivot;ob.matrix_world=mat
# Small solid missile for one attack run, hidden by keyed visibility only.
missile=solid('missile',[(794,421),(855,385),(860,388),(805,432)],.65,.045,silver,False);missile.hide_render=True
sc['unit']='stealth-fighter';sc['projection_method']='frozen UV on finished closed aircraft';sc['base_hex']='#E9CFA0'
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
for ob in list(bpy.data.objects):
 if ob.type!='MESH':continue
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update();ob['surface_finished']=True
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(M/'surface.blend'))
sys.path.insert(0,str(Path(__file__).resolve().parent));from project import apply_projection
apply_projection(sc,cam,A,FRONT)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'stealth-fighter.blend'))
(M/'geometry.json').write_text(json.dumps({'blender':bpy.app.version_string,'meshes':len([o for o in bpy.data.objects if o.type=='MESH']),'rig':'airframe, two elevons, released missile','volumetric_smoke':False},indent=2))
