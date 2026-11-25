"""Export the saved painted Blender master without repeating Cycles bakes."""
import bpy,sys,os
from mathutils import Vector
from pathlib import Path
UNIT=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'lanes/spearman-0ad-painted-r2'
g=GLB(WORK/'approved-r6.glb');d=g.doc
bones=[d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
bpy.ops.wm.open_mainfile(filepath=str(WORK/'painted-master.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('GEO-')]
# The saved authoring file retains the high-poly masters. Export only needs the lows.
for ob in list(bpy.context.scene.objects):
    if ob not in objects:bpy.data.objects.remove(ob,do_unlink=True)
def triangles(ob):return sum(len(p.vertices)-2 for p in ob.data.polygons)
def apply(o,kind,**kw):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    m=o.modifiers.new(kind,kind)
    for k,v in kw.items():setattr(m,k,v)
    bpy.ops.object.modifier_apply(modifier=m.name)
# Serialize loop normals/UVs and the strongest four unchanged/interpolated weights.
def export_mesh(items,name):
    attrs={k:[] for k in ['POSITION','NORMAL','TANGENT','TEXCOORD_0','JOINTS_0','WEIGHTS_0','COLOR_0']};idx=[];regions=[]
    for ob in items:
        apply(ob,'TRIANGULATE');me=ob.data;me.calc_loop_triangles();me.calc_tangents();start=len(attrs['POSITION']);mapping={}
        for tri in me.loop_triangles:
            if tri.area<1e-12:continue
            for li in tri.loops:
                loop=me.loops[li];v=me.vertices[loop.vertex_index];uv=me.uv_layers.active.data[li].uv;n=me.corner_normals[li].vector.normalized();t=loop.tangent.normalized()
                # Opposing faces on a simplified thin edge can cancel a smooth normal.
                # Use that face's geometric normal, then rebuild an orthonormal tangent.
                if n.length<.5:n=tri.normal.normalized()
                t=(t-n*t.dot(n)).normalized()
                if t.length<.5:
                    t=n.cross(Vector((0,1,0)))
                    if t.length<.1:t=n.cross(Vector((1,0,0)))
                    t.normalize()
                ww=sorted([(bones.index(ob.vertex_groups[x.group].name),x.weight) for x in v.groups if x.weight>1e-6 and ob.vertex_groups[x.group].name in bones],key=lambda x:-x[1])[:4]
                assert ww,(ob.name,v.index)
                total=sum(w for _,w in ww);js=[j for j,_ in ww];ws=[w/total for _,w in ww];js+=[0]*(4-len(js));ws+=[0]*(4-len(ws))
                key=(v.index,tuple(round(x,6) for x in n),tuple(round(x,7) for x in uv),tuple(round(x,6) for x in t),loop.bitangent_sign)
                if key not in mapping:
                    mapping[key]=len(attrs['POSITION']);attrs['POSITION'].append(tuple(v.co));attrs['NORMAL'].append(tuple(n));attrs['TANGENT'].append((*t,-loop.bitangent_sign if loop.bitangent_sign else 1));attrs['TEXCOORD_0'].append((uv.x,1-uv.y));attrs['JOINTS_0'].append(js);attrs['WEIGHTS_0'].append(ws);attrs['COLOR_0'].append((int(bool(ob['team'])),0,0,1))
                idx.append((mapping[key],))
        regions.append({'part':ob['part'],'start':start,'count':len(attrs['POSITION'])-start,'bone':ob['bone'] or None,'team':ob['team'] or None})
    return {'name':name,'attrs':attrs,'indices':idx,'regions':regions}
mesh0=export_mesh(objects,'spearman_LOD0')
# Simplify by semantic region, not one tiny tuft/rivet at a time: otherwise
# minimum per-object triangle counts consume the entire map-LOD budget.
from collections import defaultdict
groups=defaultdict(list)
for ob in objects:groups[(ob['part'],ob['bone'],ob['team'])].append(ob)
lod1=[]
ratio=2550/sum(map(triangles,objects))
for group in groups.values():
    copies=[]
    for ob in group:
        x=ob.copy();x.data=ob.data.copy();bpy.context.collection.objects.link(x);copies.append(x)
    bpy.ops.object.select_all(action='DESELECT')
    for x in copies:x.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]
    if len(copies)>1:bpy.ops.object.join()
    x=bpy.context.object
    if triangles(x)>12:apply(x,'DECIMATE',ratio=ratio)
    lod1.append(x)
from painted_contact import fit
fit(lod1,g,bones)
mesh1=export_mesh(lod1,'spearman_LOD1')
from painted_package import package
package(g,[mesh0,mesh1],UNIT,WORK)
