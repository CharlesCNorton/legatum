"""Data-only COLLADA reader for pinned 0 A.D. triangles and native weights."""
import bpy
import xml.etree.ElementTree as ET
from mathutils import Matrix, Vector
NS={'c':'http://www.collada.org/2005/11/COLLADASchema'}
def find(e,p):return e.find(p,NS)
def all(e,p):return e.findall(p,NS)
def mat(s):
 v=list(map(float,s.split()));return Matrix([v[i:i+4] for i in range(0,16,4)])
def matrix(e):
 q=find(e,'c:matrix');return mat(q.text) if q is not None else Matrix.Identity(4)
def parse(p):return ET.parse(p).getroot()
def sources(e):
 out={}
 for s in all(e,'c:source'):
  a=find(s,'c:float_array');a=a if a is not None else find(s,'c:Name_array')
  stride=int(find(s,'c:technique_common/c:accessor').get('stride','1'))
  vals=a.text.split();vals=list(map(float,vals)) if a.tag.endswith('float_array') else vals
  out[s.get('id')]=[vals[i:i+stride] for i in range(0,len(vals),stride)]
 return out

def geometry(tree,name,material,transform=None):
 ge=find(tree,'c:library_geometries/c:geometry/c:mesh');src=sources(ge)
 vert=find(ge,'c:vertices/c:input');verts=src[vert.get('source')[1:]]
 faces=[];uvs=[]
 for tri in all(ge,'c:triangles')+all(ge,'c:polylist'):
  inputs=all(tri,'c:input');stride=max(int(i.get('offset')) for i in inputs)+1
  vi=next(int(i.get('offset')) for i in inputs if i.get('semantic')=='VERTEX')
  ui=next((i for i in inputs if i.get('semantic')=='TEXCOORD'),None)
  indices=list(map(int,find(tri,'c:p').text.split()))
  counts=list(map(int,find(tri,'c:vcount').text.split())) if find(tri,'c:vcount') is not None else [3]*(len(indices)//(3*stride))
  i=0
  for count in counts:
   faces.append(tuple(indices[i+j*stride+vi] for j in range(count)))
   if ui is not None:uvs.extend(src[ui.get('source')[1:]][indices[i+j*stride+int(ui.get('offset'))]][:2] for j in range(count))
   i+=count*stride
 transform=transform or Matrix.Identity(4)
 me=bpy.data.meshes.new(name);me.from_pydata([transform @ Vector(v[:3]) for v in verts],[],faces);me.update()
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(material)
 if uvs:
  uv=me.uv_layers.new(name='UVMap')
  for item,co in zip(uv.data,uvs):item.uv=co
 for p in me.polygons:p.use_smooth=True
 return ob

def bind(ob, tree, rig):
 skin=find(tree,'.//c:skin');src=sources(skin)
 shape=find(skin,'c:bind_shape_matrix')
 if shape is not None:
  transform=mat(shape.text)
  for v in ob.data.vertices:v.co=transform @ v.co
 weights=find(skin,'c:vertex_weights');inputs=all(weights,'c:input')
 joint=next(i for i in inputs if i.get('semantic')=='JOINT')
 weight=next(i for i in inputs if i.get('semantic')=='WEIGHT')
 names=[i[0] for i in src[joint.get('source')[1:]]]
 values=[i[0] for i in src[weight.get('source')[1:]]]
 for n in names:ob.vertex_groups.new(name=n)
 counts=list(map(int,find(weights,'c:vcount').text.split()))
 indices=list(map(int,find(weights,'c:v').text.split()));cursor=0
 for idx,count in enumerate(counts):
  for _ in range(count):
   j,w=indices[cursor:cursor+2];cursor+=2
   if values[w]>0:ob.vertex_groups[names[j]].add([idx],values[w],'REPLACE')
 ob.parent=rig
 mod=ob.modifiers.new('Native skin weights','ARMATURE');mod.object=rig
