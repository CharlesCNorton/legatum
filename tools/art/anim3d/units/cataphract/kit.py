"""Cataphract steel barding, jointed scale rows, red piping and riding cloak.
Executed by build.py with its anatomical meshes and attachment helpers in scope.
"""
red=material('Cataphract red leather',(.24,.034,.016),0,.68)
steel=bronze
# Remove the horseman's blanket, Greek trim, crest and bare-sandal equipment.
for o in list(bpy.context.scene.objects):
 if o.name.startswith(('Ivory woven','Blanket','Rider sandal','Sandal straps','Linen chest fold')):
  bpy.data.objects.remove(o,do_unlink=True)
# Curved steel scales are individual thick solids, combined by articulated region.
def scales(name, surface, rows, cols, bone):
 vs=[];fs=[]
 for j in range(rows):
  for i in range(cols):
   start=len(vs)
   for v,u in [(0,0),(0,1),(.68,1),(1,.8),(1,.2),(.68,0)]:
    # Stagger columns on alternating rows and raise the lower lip.
    a=(i+u+(j%2)*.48)/cols;b=(j+v*.96)/rows
    point=Vector(surface(a,b));point.x+=.003*sin(pi*v)
    vs.append(tuple(point))
   fs.append(tuple(range(start,start+6)))
 o=bevel(solid(mesh(name,vs,fs,steel),.007),.002,2)
 horse_attach(o,bone)
 # Scales are sewn onto a continuous thick backing, visible in the collapse.
 # Without this physical layer their undersides read as a perforated metal grid.
 backing=[];quads=[]
 for j in range(rows+1):
  for i in range(cols+1):
   p=Vector(surface(i/cols,j/rows));p.x-=.012 if p.x>=0 else -.012
   backing.append(tuple(p))
 for j in range(rows):
  for i in range(cols):
   k=j*(cols+1)+i;quads.append((k,k+1,k+cols+2,k+cols+1))
 lining=bevel(solid(mesh('GEO-barding lining '+name,backing,quads,red),.009),.002,2)
 horse_attach(lining,bone)
 return o
# Barrel covering: both sides curve smoothly over the horse's actual back.
for sg in [-1,1]:
 def surf(a,b,sg=sg):
  angle=.24+b*1.70
  return (sg*.385*sin(angle),-.47+a*1.35,1.23+.36*cos(angle))
 scales('GEO-barding barrel '+str(sg),surf,11,25,'Torso')
 edge=[surf(i/50,1) for i in range(51)]
 horse_attach(curve('GEO-red barding hem',edge,.019,red),'Torso')
 for i in range(24):
  x,y,z=surf((i+.5)/24,1)
  horse_attach(curve('GEO-red leather pendant',[(x,y,z),(x*1.04,y,z-.08)],.018,red),'Torso')
 # Chest and neck use three sections, each attached to its matching neck joint.
 for section in range(3):
  def surfneck(a,b,sg=sg,section=section):
   t=(section+b)/3
   cy=-.46-.47*t;cz=1.40+.57*t
   angle=.16+a*2.5;radius=.30-.14*t
   return (sg*radius*sin(angle),cy+radius*.6*cos(angle),cz+radius*.25*cos(angle))
  scales('GEO-articulated neck scales '+str(sg)+' '+str(section),surfneck,5,10,'Neck'+str(section+1))
# A weighted chain coif from head to shoulders, fitted before the rider was posed.
# Helm bowl and nasal remain physical steel geometry from the family build.
# Rider armor is the fitted MPFB shirt; raised bands catch the warm product light.
for j in range(8):
 z=1.09+j*.044
 pts=[(.207*sin(a),-.159*cos(a),z+.004*cos(6*a)) for a in [i*2*pi/64 for i in range(65)]]
 attach(curve('GEO-rider lamellar row',pts,.007,steel),'spine_03')
# Riding boots fitted around the seated calves and feet, with actual seams.
for side in ['l','r']:
 calf=rig.pose.bones['calf_'+side];foot=rig.pose.bones['foot_'+side]
 # The anatomical coordinates here are rider-local, transformed by the rider parent.
 ob=curve('GEO-riding boot '+side,[calf.tail,foot.head,foot.tail],.056,leather)
 attach(ob,'foot_'+side)
 # Curves made after the rider parent transform must be moved from rider local space.
 ob.matrix_world=rig.matrix_world@ob.matrix_world
# Thick pleated cloak, trailing down the horse's rear flank.
vs=[];fs=[]
for j in range(20):
 t=j/19
 for i in range(17):
  u=i/16;w=.20+.11*t
  vs.append(((u-.5)*2*w,.08+.28*t+.035*sin(u*pi*8)*sin(pi*t),1.44-.88*t+.018*cos(u*pi*6)*t))
for j in range(19):
 for i in range(16):k=j*17+i;fs.append((k,k+1,k+18,k+17))
cloak=solid(mesh('GEO-heavy rust riding cloak',vs,fs,red),.009)
sub=cloak.modifiers.new('Soft woven folds','SUBSURF');sub.levels=1
# Parenting a local-space cloak directly retains its coordinates under the rider.
cloak.parent=rig
vg=cloak.vertex_groups.new(name='spine_03');vg.add(list(range(len(vs))),1,'REPLACE')
ar=cloak.modifiers.new('Rider cloak attachment','ARMATURE');ar.object=rig
# Paired bronze buckles and saddle stirrups on a real leather strap.
for sg in [-1,1]:
 horse_attach(curve('GEO-stirrup leather',[(sg*.27,.04,1.53),(sg*.42,.04,.93)],.014,red),'Torso')
 horse_attach(curve('GEO-steel stirrup',[(sg*.42,-.01,.97),(sg*.46,-.01,.84),(sg*.46,.10,.84),(sg*.42,.10,.97)],.010,iron),'Torso')
# Make source actions survive independent blend saves.
for act in bpy.data.actions:act.use_fake_user=True
