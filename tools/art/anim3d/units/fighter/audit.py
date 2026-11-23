"""Geometry and transform audit, independent of render/atlas contract checks."""
import bpy,bmesh,json,os,math
from pathlib import Path
from mathutils import Vector
M=Path(os.environ['ANIM_ROOT'])/'masters/fighter'
bpy.ops.wm.open_mainfile(filepath=str(M/'fighter.blend'))
geometry=[]
for name in ['Fuselage • elliptical riveted monocoque','Port wing • thick tapered airfoil','Starboard wing • thick tapered airfoil','Vertical stabilizer • tapered fin']:
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),name+' not closed';volume=abs(bm.calc_volume(signed=True));assert volume>.0001;bm.free();geometry.append({'mesh':name,'closed':True,'volume':volume})
for name in ('idle','move','attack','hit','death'):
    bpy.ops.wm.open_mainfile(filepath=str(M/(name+'.blend')));sc=bpy.context.scene;sc.frame_set(1);base=bpy.data.objects['BASE • stationary cream stone'];base_rest=base.matrix_world.copy();root=bpy.data.objects['RIG-flight'];root_rest=root.matrix_world.copy()
    for frame in range(1,sc.frame_end+1):
        sc.frame_set(frame);assert base.matrix_world==base_rest,'Moving stone base'
        for o in bpy.data.objects:
            if o.type=='MESH':assert min(abs(s) for s in o.scale)>.01,'Unsafe mesh scale'
    if name in ('idle','move'):
        sc.frame_set(sc.frame_end+1);assert max(abs(root.matrix_world[i][j]-root_rest[i][j]) for i in range(4) for j in range(4))<1e-5,'Flight loop discontinuity'
    if name=='death':
        sc.frame_set(sc.frame_end-1);previous=root.matrix_world.copy();sc.frame_set(sc.frame_end);assert previous==root.matrix_world,'Death not held'
report={'result':'PASS','geometry':geometry,'stationary_base':'all 40 samples','safe_mesh_scales':True,'flight_loops_close':True,'held_death':True,'bakes':len(list((M/'textures/baked').glob('*.png')))}
assert report['bakes']==6
(M/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
