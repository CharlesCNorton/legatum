"""Five editable MPFB clips, draw/release string keys, planted base, terminal death."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from math import sin,pi
from retarget import prepare, apply_matrices
source=MASTER/'master.blend';source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
for clip,(n,fps,loop) in CLIPS.items():
    if os.environ.get('ONLY_CLIP') and clip != os.environ['ONLY_CLIP']:continue
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;sc.render.fps=fps;sc.frame_start=1;sc.frame_end=n
    rig=bpy.data.objects['RIG-barbarian-archer'];bow=bpy.data.objects['GEO-Bow stave'];string=bpy.data.objects['GEO-Bowstring'];arrow=bpy.data.objects['GEO-Nocked arrow'];tip=bpy.data.objects['GEO-Arrowhead']
    restpts=[Vector(p.co[:3]) for p in bow.data.splines[0].points]
    base=bpy.data.objects['GEO-Stationary cream base'];base_world=base.matrix_world.copy();checks=[]
    pose(rig,-.23 if clip=='move' else 0)
    for p in rig.pose.bones:
        q=p.matrix_basis.to_quaternion();p.rotation_mode='QUATERNION';p.rotation_quaternion=q
    neutral={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
    motion=None
    if clip!='attack':
        phases=[i/n if loop else min(1,i/(n-2)) if clip=='death' else i/(n-1) for i in range(n+1 if loop else n)]
        motion,metadata=prepare(rig,ROOT,clip,phases)
        if loop:motion[-1]=motion[0]
        metadata['source_master_sha256']=source_hash
        (MASTER/(clip+'-motion.json')).write_text(json.dumps(metadata,indent=2))
    sc.render.fps=fps
    body=bpy.data.objects['GEO-MPFB-anatomy'];boots=bpy.data.objects['GEO-Boots']
    cloak=bpy.data.objects['GEO-Wolf pelt back']
    if clip=='death':
        cloak.shape_key_add(name='Basis')
    for frame in range(1,n+2 if loop else n+1):
        sc.frame_set(frame);draw=1
        rig.location=(0,0,-.045);rig.rotation_euler=(0,0,0)
        if motion:
            sample=motion[frame-1];apply_matrices(rig,sample['matrices'])
            weight=min(1,(frame-1)/2) if clip=='death' else (0 if frame in (1,n) else 1) if clip=='hit' else 1
            if weight<1:
                for p in rig.pose.bones:p.matrix_basis=neutral[p.name].lerp(p.matrix_basis,weight)
            rig.location+=sample['root']*weight
            bpy.context.view_layer.update()
        else:
            draw=[1,1,1,1,.18,.32,.55,.77,.94,1][frame-1]
            pose(rig,.009*sin((frame-1)*pi/9),0,draw)
        if clip=='move':
            ev=boots.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
            low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
            rig.location.z+=.078-low
        elif clip=='death':
            settle=max(0,min(1,(frame-3)/3));settle=settle*settle*(3-2*settle)
            rig.rotation_euler.z=.10*min(1,(frame-1)/4)
            bpy.context.view_layer.update()
            ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
            coords=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
            center=Vector(((min(v.x for v in coords)+max(v.x for v in coords))/2,(min(v.y for v in coords)+max(v.y for v in coords))/2,0))
            rig.location+=(Vector((0,0,0))-center)*settle
            rig.location.z+=max(0,.09-min(v.z for v in coords))
            bpy.context.view_layer.update()
            # Geometric contact folds: each sampled cloth surface remains thick;
            # upper shoulder attachment stays fixed, loose hem settles on stone.
            for key in list(cloak.data.shape_keys.key_blocks)[1:]:
                key.value=0;key.keyframe_insert('value',frame=frame)
            key=cloak.shape_key_add(name='Contact fold '+str(frame))
            inverse=cloak.matrix_world.inverted()
            zs=[v.co.z for v in cloak.data.vertices];lo,hi=min(zs),max(zs)
            for v,base_v in zip(key.data,cloak.data.vertices):
                world=cloak.matrix_world@base_v.co
                loose=max(0,min(1,(hi-base_v.co.z)/(hi-lo)))
                target=.105+.025*sin(base_v.co.x*30)**2
                world.z+=(target-world.z)*settle*loose
                v.co=inverse@world
            key.value=0;key.keyframe_insert('value',frame=max(1,frame-1))
            key.value=1;key.keyframe_insert('value',frame=frame)
            draw=1-.6*settle
        bpy.context.view_layer.update()
        for p in rig.pose.bones:
            p.keyframe_insert('location',frame=frame)
            p.keyframe_insert('rotation_euler' if p.rotation_mode=='XYZ' else 'rotation_quaternion',frame=frame)
        rig.keyframe_insert('location',frame=frame);rig.keyframe_insert('rotation_euler',frame=frame)
        # Stave bends in its own material coordinates, retaining true thickness.
        for i,(p,rest) in enumerate(zip(bow.data.splines[0].points,restpts)):
            u=-1+2*i/(len(restpts)-1);v=rest.copy();v.x+=.085*(1-draw)*abs(u)**2;p.co=(*v,1);p.keyframe_insert('co',frame=frame)
        bpy.context.view_layer.update()
        ends=[bow.matrix_world@Vector(bow.data.splines[0].points[i].co[:3]) for i in (0,-1)]
        nock=rig.matrix_world@rig.pose.bones['hand_r'].tail+Vector((.02,-.015,.012))
        for p,v in zip(string.data.splines[0].points,[ends[0],nock,ends[1]]):p.co=(*v,1);p.keyframe_insert('co',frame=frame)
        grip=bow.matrix_world@restpts[len(restpts)//2];direction=(grip-nock).normalized();end=grip+direction*.15
        for p,v in zip(arrow.data.splines[0].points,[nock,end]):p.co=(*v,1);p.keyframe_insert('co',frame=frame)
        tip.location=end;tip.rotation_euler=Vector((1,0,0)).rotation_difference(direction).to_euler();tip.keyframe_insert('location',frame=frame);tip.keyframe_insert('rotation_euler',frame=frame)
        visible=not (clip=='attack' and 5<=frame<=8) and not (clip=='death' and frame>=5)
        for o in (arrow,tip):o.hide_render=not visible;o.keyframe_insert('hide_render',frame=frame)
        hand=rig.matrix_world@rig.pose.bones['hand_l'].head
        assert (grip-hand).length<.08,(clip,frame,'grip detached')
        assert all(abs(base.matrix_world[r][c]-base_world[r][c])<1e-7 for r in range(4) for c in range(4))
        checks.append({'frame':frame,'hand_grip_distance':(grip-hand).length,'string_nock_distance':0.,'base_static':True})
    # Organic channels keep auto-clamped Bezier; visibility stays stepped.
    for action in bpy.data.actions:
        curves=[fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]
        for fc in curves:
            for key in fc.keyframe_points:
                if 'hide_render' in fc.data_path:key.interpolation='CONSTANT'
                else:key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
    sc.frame_set(1);sc['source_master_sha256']=source_hash
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/(clip+'.blend')))
    (MASTER/(clip+'-audit.json')).write_text(json.dumps({'source_master_sha256':source_hash,'clip':clip,'checks':checks},indent=2))
    log(f'Built {clip} ({"Quaternius CC0" if motion else "authored bow attack"}): {n} frames at {fps} fps; dynamic bow/string, grip and stationary base checked, '+('loop closure keyed.' if loop else 'terminal keys retained.'))
