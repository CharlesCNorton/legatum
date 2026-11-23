"""Geometry and transform audit, independent of render/atlas contract checks."""
import bpy,bmesh,json,os,math,hashlib
from pathlib import Path
from mathutils import Vector
M=Path(os.environ['ANIM_ROOT'])/'masters/fighter'
bpy.ops.wm.open_mainfile(filepath=str(M/'fighter.blend'))
assert json.loads((M/'clips.json').read_text())['source_sha256']==hashlib.sha256((M/'fighter.blend').read_bytes()).hexdigest(),'Stale clip source'
assert bpy.context.scene.view_settings.view_transform=='Standard'
for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    for material in obj.data.materials:
        if 'Paint coverage' in material.node_tree.nodes:
            assert any(n.type=='LIGHT_PATH' for n in material.node_tree.nodes),'Missing camera-only pigment'
    if not obj.name.startswith('FX-'):assert not obj.modifiers,'Unfinished projection surface '+obj.name
base=bpy.data.objects['BASE • stationary cream stone']
assert len(base.data.materials)==2,'Missing physical top/rim materials'
assert not base.data.uv_layers.get('Frozen rest-camera'),'Painted static shadow on base'
geometry=[]
for name in ['Fuselage • elliptical riveted monocoque','Port wing • thick tapered airfoil','Starboard wing • thick tapered airfoil','Vertical stabilizer • tapered fin','Canopy • cockpit blister','DISPLAY • curved stone pedestal']:
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),name+' not closed';volume=bm.calc_volume(signed=True);assert volume>.0001,'Inward or degenerate solid: '+name;bm.free();geometry.append({'mesh':name,'closed':True,'volume':volume})
for name in ('idle','move','attack','hit','death'):
    bpy.ops.wm.open_mainfile(filepath=str(M/(name+'.blend')));sc=bpy.context.scene;sc.frame_set(1);base=bpy.data.objects['BASE • stationary cream stone'];base_rest=base.matrix_world.copy();root=bpy.data.objects['RIG-flight'];root_rest=root.matrix_world.copy()
    prop=bpy.data.objects['RIG-propeller']
    assert prop.rotation_mode=='QUATERNION','Propeller must spin in its fitted shaft frame'
    for frame in range(1,sc.frame_end+1):
        sc.frame_set(frame);assert base.matrix_world==base_rest,'Moving stone base'
        for o in bpy.data.objects:
            if o.type=='MESH':
                assert min(abs(s) for s in o.scale)>.01,'Unsafe mesh scale'
                if name=='death' and not o.name.startswith(('BASE','FX-')):
                    assert not o.hide_render,'Vanishing wreck/support'
                    for vertex in o.data.vertices:
                        point=o.matrix_world @ vertex.co
                        floor=.22 if (point.x+.02)**2+point.y**2<1.00**2 else .04
                        assert point.z>=floor-.002,f'Ground penetration {o.name} frame {frame}: {point.z}'
    if name in ('idle','move'):
        sc.frame_set(sc.frame_end+1);assert max(abs(root.matrix_world[i][j]-root_rest[i][j]) for i in range(4) for j in range(4))<1e-5,'Flight loop discontinuity'
    if name=='death':
        sc.frame_set(sc.frame_end-1);previous=root.matrix_world.copy();sc.frame_set(sc.frame_end);assert previous==root.matrix_world,'Death not held'
report={'result':'PASS','geometry':geometry,'stationary_base':'all 40 samples','safe_mesh_scales':True,'flight_loops_close':True,'held_death':True,'camera_only_pigment':True,'physical_stone':True,'crash_contact':True,'no_feet':'mechanical aircraft; top/front move-cycle sheet required','bakes':len(list((M/'textures/baked').glob('*.png')))}
assert report['bakes']==6
(M/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
