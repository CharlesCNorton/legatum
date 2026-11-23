"""Full-depth six-wheel rocket truck; screen landmarks register solid mechanical parts.
Camera-depth is retained: no alpha cutout, displacement card or camera-facing subject plane.
"""
import bpy, bmesh, math, json
from math import sin,cos,pi
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

def build(g):
 globals().update(g)
 sc=bpy.context.scene
 bpy.ops.object.camera_add(location=(-6,-10,4.4));cam=bpy.context.object;cam.name='CAM-painting'
 target=Vector((0,0,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.0;sc.camera=cam
 right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0));view=cam.rotation_euler.to_matrix()@Vector((0,0,1))
 def point(px,py,depth=0):return target+right*((px-128)/64)-up*((py-128)/64)+view*depth
 def solid(name,outline,shift=(-27,-5),depth=.6,front=.25,m=olive,p=None):
  # Front contour plus a displaced back contour define a closed full-depth prism.
  n=len(outline)
  def surface_depth(x):
   if name in ['Front grille surround','Front bumper','Far front wheel fender']:
    return -.80+.026*x
   if name in ['Left windshield','Right windshield']:
    return -1.987+.023*x
   if p is None or p in [root,upper]:return front+.60-.0053*x
   return front
  v=[point(x,y,surface_depth(x)) for x,y in outline]+[point(x+shift[0],y+shift[1],surface_depth(x)-depth) for x,y in outline]
  faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
  return bevel(mesh(name,v,faces,m,p or root),.008)
 def spRod(name,a,b,r,m=olive,p=None):
  def attached(t):
   x,y,d=t
   if 'Grille' in name or 'Headlamp' in name:d=-.80+.026*x+.02
   elif 'Windscreen' in name:d=-1.987+.023*x+.012
   elif p==upper:d+=.60-.0053*x
   return point(x,y,d)
  return rod(name,attached(a),attached(b),r,m,p or root)
 root=empty('chassis');upper=empty('suspension body',(0,0,0),root)
 # Base is a single stationary cream disc, not part of the animated hierarchy.
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.76,depth=.15,location=(0,0,.075));base=bpy.context.object;base.name='GEO-stationary cream disc';base.data.materials.append(stone);bevel(base,.02)
 # Main rail and full cab volume. Separate raised panels retain thickness and joints.
 solid('Chassis box rails',[(52,145),(232,128),(233,133),(53,150)],(-24,-9),.42,-.32,p=root)
 solid('Cab full shell',[(101,96),(122,96),(125,145),(111,149),(99,146),(96,115)],(-31,-3),.72,.25,p=upper)
 solid('Cab rounded roof',[(100,94),(119,95),(123,97),(101,98)],(-34,0),.74,.27,p=upper)
 solid('Hood engine enclosure',[(53,122),(95,118),(98,138),(51,141)],(-23,-5),.62,.27,p=upper)
 solid('Front grille surround',[(30,122),(52,124),(52,147),(29,145)],(-1,-1),.10,.89,p=upper)
 solid('Cab near door',[(102,114),(123,114),(124,144),(102,147)],(-.4,-.4),.035,.28,p=upper)
 # Real inset smoked glazing, surrounds and windshield planes; painting maps onto them.
 glass=mat('Olive painted smoked glass',(.16,.18,.15),0,.34)
 solid('Near side window',[(104,99),(120,99),(121,113),(103,114)],(-.2,-.2),.025,.30,m=glass,p=upper)
 solid('Left windshield',[(68,98),(80,98),(77,112),(64,112)],(0,0),.025,.50,m=glass,p=upper)
 solid('Right windshield',[(82,99),(99,99),(96,113),(79,112)],(0,0),.025,.51,m=glass,p=upper)
 for a,b in [((79,112,.54),(89,109,.54)),((65,112,.54),(73,110,.54))]:spRod('Windscreen wiper',a,b,.008,black,upper)
 # Front guards and near front fender follow the arch; no full boxes filling wheel apertures.
 solid('Front wheel arched fender',[(55,137),(63,133),(97,133),(103,140),(112,158),(106,160),(97,139),(65,140),(60,148),(53,149)],(-20,-4),.52,.38,p=upper)
 solid('Far front wheel fender',[(18,137),(22,132),(29,133),(31,145),(18,146)],(-3,-3),.25,.36,p=upper)
 solid('Front bumper',[(13,146),(64,151),(63,159),(12,154)],(0,-3),.09,1.0,p=upper)
 solid('Rear bed flat deck',[(146,127),(225,124),(228,128),(146,132)],(-25,-5),.7,.22,p=upper)
 solid('Rear wheel fender',[(162,132),(167,127),(221,125),(224,128),(233,142),(229,144),(220,131),(170,133),(166,145),(159,144)],(-20,-5),.5,.33,p=upper)
 solid('Cab step',[(107,154),(126,152),(129,158),(111,161)],(-7,-2),.2,.35,p=upper)
 solid('Fuel tank',[(128,143),(152,141),(158,145),(158,157),(129,160)],(-6,-3),.35,.24,p=upper)
 for x in [131,153]:solid('Fuel tank strap',[(x,143),(x+1,143),(x+1,158),(x,158)],(-.1,-.1),.018,.28,m=edge,p=upper)
 solid('Side stowage chest',[(129,122),(144,123),(145,140),(129,140)],(-7,-3),.25,.27,p=upper)
 for x in [131,143]:solid('Chest strap',[(x,124),(x+1,124),(x+1,138),(x,138)],(0,0),.015,.29,m=edge,p=upper)
 spRod('Door grab handle',(117,118,.33),(121,118,.33),.012,steel,upper)
 spRod('Mirror stalk',(101,119,.36),(108,111,.40),.012,olive,upper)
 solid('Side mirror',[(106,105),(110,105),(110,111),(106,111)],(-.5,-.4),.035,.42,p=upper)
 for x in [234,240]:
  spRod('Retracted rear stabilizer',(x,130,.17),(x+1,155,.17),.035,olive,upper)
  solid('Stabilizer foot',[(x-2,155),(x+3,155),(x+4,157),(x-2,158)],(-2,-1),.11,.19,p=upper)
 # Grill apertures, ribs, protected headlights, towing hooks, louvers.
 for x in range(32,51,3):
  spRod('Grille dark recess',(x,126,.92),(x-.5,144,.92),.014,black,upper)
  spRod('Grille vertical rib',(x+.8,126,.94),(x+.2,144,.94),.008,edge,upper)
 for x in range(69,93,2):spRod('Engine vent rib',(x,125,.30),(x,130,.30),.007,edge,upper)
 for px,py in [(24,139),(57,142)]:
  c=point(px,py,-.80+.026*px+.02);rod('Headlamp housing',c-view*.045,c,.048,olive,upper)
  lamp=mat('Olive painted ivory headlamp',(.65,.62,.45),0,.28)
  rod('Headlamp lens',c,c+view*.008,.037,lamp,upper)
  spRod('Headlamp guard',(px-2,py,.98),(px+2,py,.98),.007,steel,upper)
 # Round rolling wheels. Near and far centers are fitted independently to the painting.
 wheels=[]
 for index,(px,py,r,side) in enumerate([(86,165,.315,-1),(180,157,.315,-1),(210,154,.315,-1),(43,162,.315,1),(140,161,.315,1),(170,150,.315,1)]):
  z=.15+r+.008
  center=point(px,py,0);center+=view*((z-center.z)/view.z)
  w=empty('wheel '+str(index),center,root);wheels.append(w);w['radius']=r+.008;w['side']=side
  # Cylinder axis is global Y; full tire ring has genuine open center and rounded sidewall.
  profiles=[(-.105,.68*r),(-.125,.84*r),(-.105,.96*r),(-.075,r),(.075,r),(.105,.96*r),(.125,.84*r),(.105,.68*r)]
  v=[];f=[];N=48
  for off,rr in profiles:
   for j in range(N):a=j*2*pi/N;v.append(center+Vector((rr*cos(a),off,rr*sin(a))))
  for k in range(len(profiles)):
   for j in range(N):f.append((k*N+j,k*N+(j+1)%N,((k+1)%len(profiles))*N+(j+1)%N,((k+1)%len(profiles))*N+j))
  tire=mesh('Dusty tire '+str(index),v,f,rubber,w,True)
  for j in range(32):
   a=j*2*pi/32
   for sy in [-1,1]:
    o=cube('Chevron tire tread',center+Vector(((r+.003)*cos(a),sy*.055,(r+.003)*sin(a))),(.036,.105,.014),rubber,w);o.rotation_euler=(0,pi/2-a,sy*.32)
  rod('Wheel pressed dish',center+Vector((0,-.112,0)),center+Vector((0,.112,0)),r*.69,olive,w)
  for sy in [-1,1]:
   yy=center.y+sy*.123;ring('Wheel bright bead',(center.x,yy,center.z),r*.67,.008,edge,w)
   rod('Wheel hub',(center.x,yy,center.z),(center.x,yy+sy*.025,center.z),r*.25,olive,w)
   for j in range(8):
    a=j*2*pi/8;xx=center.x+r*.39*cos(a);zz=center.z+r*.39*sin(a)
    rod('Hex hub nut',(xx,yy,zz),(xx,yy+sy*.015,zz),.009,steel,w,verts=6)
 # Near tire shapes stay circular; hidden/far front registered positions have separate actual axles.
 for i,j in [(0,3),(1,4),(2,5)]:rod('Full axle',wheels[i].matrix_world.translation,wheels[j].matrix_world.translation,.026,steel,root)
 # Rotating launcher pedestal and tilt cradle are distinct solid mechanical controls.
 turn=empty('launcher traverse',point(181,122,-.1),upper)
 lift=empty('launcher elevation',point(216,110,-.15),turn)
 solid('Pedestal',[(158,121),(198,119),(201,124),(157,126)],(-8,-3),.36,.15,p=turn)
 solid('Elevation support near',[(172,119),(186,95),(192,96),(179,122)],(-6,-2),.22,.20,p=turn)
 spRod('Hydraulic piston',(177,116,.28),(188,96,.28),.031,steel,turn)
 spRod('Hydraulic cylinder',(174,119,.28),(182,107,.28),.045,olive,turn)
 solid('Launcher near side panel',[(178,51),(230,91),(218,113),(169,78)],(-2,-1),.06,.13,p=lift)
 solid('Launcher underside',[(123,72),(169,80),(218,113),(173,105)],(-1,-1),.08,-.35,p=lift)
 solid('Launcher back plate',[(229,92),(217,112),(173,104),(185,84)],(-1,-1),.08,-.55,p=lift)
 # 40 hollow tubes: real bore walls, rolled mouth rims and dark recessed ends.
 # End rings live on a fully three-dimensional inclined launcher plane.
 mouths=[]
 for row in range(4):
  for col in range(10):
   px=132+col*5.25-row*1.85;py=43+col*.82+row*6.65
   c=point(px,py,.33+row*.018);end=c+right*(46/64)-up*(36/64)-view*.62
   axis=(end-c).normalized();u=(right-axis*right.dot(axis)).normalized();v=axis.cross(u).normalized()
   # World circular bores with full depth; proportional fitting of front rows.
   rad=.049
   vertices=[];faces=[];N=24
   for center,rr in [(c,rad),(end,rad),(end,rad*.79),(c,rad*.79)]:
    for j in range(N):a=2*pi*j/N;vertices.append(center+u*(rr*cos(a))+v*(rr*sin(a)))
   for k in range(4):
    for j in range(N):faces.append((k*N+j,k*N+(j+1)%N,((k+1)%4)*N+(j+1)%N,((k+1)%4)*N+j))
   tube=mesh('Rocket tube %02d'%(row*10+col),vertices,faces,olive,lift,True);tube.data.materials.append(black)
   for face in tube.data.polygons:
    if 2*N<=face.index<3*N:face.material_index=1
   rod('Deep tube shadow',end-axis*.09,end-axis*.08,rad*.78,black,lift,verts=24)
   mouths.append((c,axis,u,v))
 # Solid panel rims, raised seam rails, fasteners and a lifting hinge.
 for a,b in [((180,55,.2),(225,92,.2)),((173,77,.2),(216,108,.2)),((176,72,.2),(220,105,.2))]:spRod('Launcher raised reinforcement',a,b,.012,edge,lift)
 for j in range(6):
  c=point(179+j*8,56+j*6.5,.23);rod('Launcher rivet',c,c+view*.014,.012,steel,lift,verts=8)
 spRod('Elevation hinge',(207,110,.20),(216,112,.20),.04,olive,turn)
 # Convert and apply the actual surface finish before UV projection.
 for o in list(sc.objects):
  if o.type not in {'MESH','CURVE'}:continue
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  if o.type=='CURVE':bpy.ops.object.convert(target='MESH')
  for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  if any(k in o.name for k in ['shell','panel','enclosure','roof','window','windshield','door','fender','Wheel pressed dish']):
   bmesh.ops.triangulate(bm,faces=list(bm.faces));edges=[e for e in bm.edges if e.calc_length()>.12]
   if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
  bm.to_mesh(o.data);bm.free();o.data.update()
 bpy.context.view_layer.update()
 (M/'registration.json').write_text(json.dumps({'method':'closed polyhedral bodywork registered from screen landmarks with retained depth; physically round six tires and forty deep hollow tubes','camera_scale':4,'wheel_centers':[[w.name,*list(w.matrix_world.translation)] for w in wheels]},indent=2))
 return dict(root=root,upper=upper,turn=turn,lift=lift,wheels=wheels,base=base,cam=cam,mouths=mouths,view=view,right=right,up=up)
