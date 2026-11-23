"""Curved Corinthian faceplate with genuine eye and mouth openings."""
import bpy,os,sys,math
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=Path(os.environ.get('ANIM_MASTER', str(R/'masters/spearman-3d-v2')))
paths=sorted((M/'clips').glob('*/*.blend')) if '--clips' in sys.argv else [M/'spearman.blend']
for path in paths:
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
 if not sc.get('corinthian_faceplate_v2'):
  crown=bpy.data.objects['Corinthian helmet crown'];vs=[v.co for v in crown.data.vertices]
  cy=(min(v.y for v in vs)+max(v.y for v in vs))/2;cz=max(v.z for v in vs)-.15
  bronze=bpy.data.materials['Bronze • hammered'];gold=bpy.data.materials['Bronze • polished edges'];dark=bpy.data.materials['Incised bronze patina']
  for ob in list(sc.objects):
   if any(ob.name.startswith(p) for p in ['Corinthian cheek guard','Cheek engraved border','Cheek breathing rivet','Nasal guard']):bpy.data.objects.remove(ob,do_unlink=True)
  def parent(ob):
   bpy.context.collection.objects.link(ob);ob.parent=crown.parent;ob.parent_type=crown.parent_type;ob.parent_bone=crown.parent_bone
   ob.matrix_parent_inverse=crown.matrix_parent_inverse;ob.matrix_basis=crown.matrix_basis
  def surface(x,z):
   y=cy-.135*math.sqrt(max(.1,1-(x/.12)**2))
   if -.13<z<.015 and abs(x)<.012:y-=.021*(1-abs(x)/.012)
   return (x,y,cz+z)
  def hole(x,z):
   eye=((abs(x)-.046)/.031)**2+((z+.018)/.0115)**2<1
   mouth=z<-.060 and abs(x)<(.009 if z>-.128 else .021)
   return eye or mouth
  n=72;verts=[surface(-.104+.208*i/n,-.172+.205*j/n) for j in range(n+1) for i in range(n+1)];faces=[]
  for j in range(n):
   for i in range(n):
    x=-.104+.208*(i+.5)/n;z=-.172+.205*(j+.5)/n
    if hole(x,z):continue
    a=j*(n+1)+i;faces.append((a,a+1,a+n+2,a+n+1))
  mesh=bpy.data.meshes.new('Corinthian continuous faceplate');mesh.from_pydata(verts,[],faces);mesh.update()
  ob=bpy.data.objects.new(mesh.name,mesh);parent(ob);mesh.materials.append(bronze)
  for p in mesh.polygons:p.use_smooth=True
  sol=ob.modifiers.new('Forged plate thickness','SOLIDIFY');sol.thickness=.004
  bevel=ob.modifiers.new('Rounded aperture edges','BEVEL');bevel.width=.0015;bevel.segments=2
  def line(name,pts,r,mat):
   d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2
   sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
   for p,v in zip(sp.points,pts):p.co=(*v,1)
   o=bpy.data.objects.new(name,d);parent(o);d.materials.append(mat)
  for sign in [-1,1]:
   pts=[]
   for i in range(49):
    a=i*2*math.pi/48;x=sign*(.046+.0325*math.cos(a));z=-.018+.013*math.sin(a)
    xx,y,zz=surface(x,z);pts.append((xx,y-.002,zz))
   line('Corinthian eye rolled rim',pts,.0023,gold)
   pts=[surface(sign*x,z) for x,z in [(.098,-.050),(.091,-.105),(.080,-.153),(.024,-.170),(.022,-.13),(.013,-.070)]]
   line('Corinthian cheek rolled rim',[(x,y-.002,z) for x,y,z in pts],.0027,gold)
  sc['corinthian_faceplate_v2']=True
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
