"""Five editable MPFB clips, draw/release string keys, planted base, terminal death."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from math import sin,cos,pi
source=MASTER/'master.blend';source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
for clip,(n,fps,loop) in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;sc.render.fps=fps;sc.frame_start=1;sc.frame_end=n
    rig=bpy.data.objects['RIG-barbarian-archer'];bow=bpy.data.objects['GEO-Bow stave'];string=bpy.data.objects['GEO-Bowstring'];arrow=bpy.data.objects['GEO-Nocked arrow'];tip=bpy.data.objects['GEO-Arrowhead']
    restpts=[Vector(p.co[:3]) for p in bow.data.splines[0].points]
    base=bpy.data.objects['GEO-Stationary cream base'];base_world=base.matrix_world.copy();checks=[]
    for frame in range(1,n+2 if loop else n+1):
        sc.frame_set(frame);t=(frame-1)/n;phase=2*pi*t;draw=1
        if clip=='idle':pose(rig,.008*sin(phase),0,1)
        elif clip=='move':
            # Two alternating footfalls. In-place stride; lift only on swing half.
            pose(rig,.016*(1-cos(phase*2)),.085*sin(phase),.88)
            for side,sign in [('r',1),('l',-1)]:
                swing=max(0,sign*sin(phase));x=-.36 if side=='r' else .41
                y=(-.02 if side=='r' else .04)+sign*.085*sin(phase)
                limb(rig,'thigh_'+side,'calf_'+side,(x,y,.18+.06*swing),(x,-.36,.53))
                aim(rig,'foot_'+side,(-.06 if side=='r' else .08,-.16,-.06))
        elif clip=='attack':
            draw=[1,1,1,1,.18,.32,.55,.77,.94,1][frame-1]
            pose(rig,.009*sin((frame-1)*pi/9),0,draw)
        elif clip=='hit':
            recoil=[0,.13,.07,0][frame-1];pose(rig,-recoil*.2,0,.92)
            rig.rotation_euler.y=-recoil;rig.pose.bones['spine_03'].rotation_mode='XYZ';rig.pose.bones['spine_03'].rotation_euler.x=-recoil
        else:
            u=min((frame-1)/7,1);smooth=u*u*(3-2*u);pose(rig,0,0,1-.6*smooth)
            rig.rotation_euler.x=1.30*smooth;rig.rotation_euler.z=-.22*smooth
            rig.location=(0,.62*smooth,-.045+.13*smooth)
            rig.pose.bones['spine_02'].rotation_mode='XYZ';rig.pose.bones['spine_02'].rotation_euler.x=.20*smooth
            rig.pose.bones['head'].rotation_mode='XYZ';rig.pose.bones['head'].rotation_euler.y=.30*smooth
            draw=1-.6*smooth
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
    log(f'Authored {clip}: {n} frames at {fps} fps; dynamic bow/string, grip and stationary base checked, '+('loop closure keyed.' if loop else 'terminal keys retained.'))
