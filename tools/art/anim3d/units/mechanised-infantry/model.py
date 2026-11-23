"""Eight-wheel APC, open rear cabin and ramp, plus articulated MPFB infantryman."""
import bpy,bmesh,json
from mathutils import Vector
from math import sin,cos,pi

def build(g):
 globals().update(g)
 sc=bpy.context.scene
 bpy.ops.object.camera_add(location=(6,-10,3.1));cam=bpy.context.object;cam.name='CAM-painting';target=Vector((0,0,.81));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4;sc.camera=cam
 right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0));view=cam.rotation_euler.to_matrix()@Vector((0,0,1))
 def point(x,y,d=0):return target+right*((x-128)/64)-up*((y-128)/64)+view*d
 root=empty('chassis');upper=empty('body suspension',(0,0,0),root)
 def solid(name,outline,shift=(22,-17),depth=.9,front=.35,m=None,p=None):
  n=len(outline)
  def d(x):return front-(x-170)*.025 if name.startswith('Rear ') else front
  v=[point(x,y,d(x)) for x,y in outline]+[point(x+shift[0],y+shift[1],d(x)-depth) for x,y in outline];f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
  return bevel(mesh(name,v,f,m or olive,p or upper),.009)
 # Single cream disc closely matches the painted support ellipse.
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.80,depth=.13,location=(0,0,.085));base=bpy.context.object;base.name='GEO-stationary cream disc';base.data.materials.append(stone);bevel(base,.018)
 # Near side, glacis and top: closed sloped hull with substantial cross-section.
 solid('Armoured hull',[(18,105),(27,94),(152,95),(173,111),(161,123),(28,113)],(30,-14),.96,.25)
 solid('Lower hull',[(28,111),(158,119),(158,128),(30,120)],(30,-16),.91,.14)
 # Hollow rear opening: frame jambs and top rail surround a deep interior.
 solid('Rear opening shadow',[(170,99),(207,94),(207,143),(173,151)],(-7,-4),.12,.08,m=black)
 solid('Rear left jamb',[(165,98),(173,98),(177,149),(168,146)],(3,-3),.14,.48)
 solid('Rear right jamb',[(208,94),(215,96),(213,145),(206,146)],(2,-2),.14,.46)
 solid('Rear lintel',[(166,94),(211,89),(215,95),(170,101)],(2,-3),.14,.48)
 ramp=empty('rear ramp hinge',point(186,146,.48),upper)
 solid('Lowered loading ramp',[(174,144),(208,139),(229,165),(183,173)],(0,2),.07,.52,p=ramp)
 for i in range(7):
  y=149+i*3;rod('Ramp traction rib',point(179+i*.9,y,.56),point(210+i*1.6,y-3,.56),.008,edge,ramp)
 # Small autocannon turret, real hatches, vision blocks and fasteners.
 turn=empty('turret traverse',point(118,79,-.12),upper);lift=empty('autocannon elevation',point(132,70,.12),turn)
 solid('Turret shell',[(92,77),(102,65),(127,64),(139,75),(131,83),(99,84)],(5,-3),.34,.16,p=turn)
 solid('Turret hatch',[(104,64),(123,63),(127,66),(105,68)],(2,-1),.045,.18,p=turn)
 for x,y in [(101,71),(122,69)]:solid('Turret vision glass',[(x,y),(x+7,y),(x+7,y+4),(x,y+4)],(0,0),.02,.22,m=black,p=turn)
 a=point(129,72,.22);b=point(161,76,.20);rod('Slim autocannon',a,b,.018,steel,lift);rod('Muzzle collar',b-(b-a).normalized()*.045,b,.023,steel,lift)
 for x,y in [(36,95),(75,90),(146,94),(158,110)]:
  solid('Hull service hatch',[(x,y),(x+11,y-1),(x+11,y+6),(x,y+7)],(1,-1),.035,.29)
  rod('Hatch handle',point(x+3,y+1,.34),point(x+8,y,.34),.009,steel,upper)
 for x in range(31,162,15):rod('Hull edge bolt',point(x,110,.29),point(x,110,.31),.010,steel,upper,verts=6)
 for x,y in [(24,109),(155,112)]:solid('Protected headlight',[(x,y),(x+6,y),(x+6,y+5),(x,y+5)],(0,0),.03,.32,m=edge)
 wheels=[]
 # Four independent physical axles, eight full rubber tires with hub bolts/tread.
 for i,(px,py,side) in enumerate([(36,139,-1),(65,143,-1),(94,147,-1),(124,150,-1),(73,125,1),(102,129,1),(131,133,1),(160,136,1)]):
  r=.318;center=point(px,py,0);center+=view*((.15+r+.008-center.z)/view.z)
  w=empty('wheel '+str(i),center,root);w['radius']=r+.008;w['side']=side;wheels.append(w)
  profiles=[(-.12,.68*r),(-.14,.84*r),(-.11,.97*r),(-.075,r),(.075,r),(.11,.97*r),(.14,.84*r),(.12,.68*r)];v=[];f=[];N=48
  for yy,rr in profiles:
   for j in range(N):a=j*2*pi/N;v.append(center+Vector((rr*cos(a),yy,rr*sin(a))))
  for k in range(8):
   for j in range(N):f.append((k*N+j,k*N+(j+1)%N,((k+1)%8)*N+(j+1)%N,((k+1)%8)*N+j))
  mesh('Dusty tire '+str(i),v,f,rubber,w,True)
  rod('Wheel dish',center+Vector((0,-.13,0)),center+Vector((0,.13,0)),r*.67,olive,w)
  for sy in [-1,1]:
   yy=center.y+sy*.14;ring('Wheel rolled bead',(center.x,yy,center.z),r*.66,.008,edge,w)
   rod('Hub cap',(center.x,yy,center.z),(center.x,yy+sy*.025,center.z),r*.25,olive,w)
   for j in range(8):
    a=j*2*pi/8;x=center.x+r*.40*cos(a);z=center.z+r*.40*sin(a);rod('Wheel nut',(x,yy,z),(x,yy+sy*.012,z),.009,steel,w,verts=6)
  for j in range(32):
   a=j*2*pi/32
   for sy in [-1,1]:
    o=cube('Chevron tire tread',center+Vector(((r+.003)*cos(a),sy*.065,(r+.003)*sin(a))),(.04,.115,.014),rubber,w);o.rotation_euler=(0,pi/2-a,0)
 for i in range(4):rod('Axle',wheels[i].matrix_world.translation,wheels[i+4].matrix_world.translation,.045,steel,root)
 # Finish vehicle geometry before projection.
 for o in list(sc.objects):
  if o.type not in {'MESH','CURVE'}:continue
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  if o.type=='CURVE':bpy.ops.object.convert(target='MESH')
  for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));edges=[e for e in bm.edges if e.calc_length()>.12]
  if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
  bm.to_mesh(o.data);bm.free()
 from human import build as soldier_build
 soldier=soldier_build(point,view)
 bpy.context.view_layer.update()
 (M/'motion-sources.json').write_text(json.dumps(soldier['sources'],indent=2))
 return dict(root=root,upper=upper,turn=turn,lift=lift,wheels=wheels,base=base,cam=cam,view=view,right=right,up=up,ramp=ramp,soldier=soldier,muzzle=b,point=point)
