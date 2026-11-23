"""Five authored traveller actions, editable 53-bone rig, fixed base and held death."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from math import sin,cos,pi
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler';V=R/'review/3d-v2';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}

def aim(rig,name,d):
    p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q @ Vector((0,1,0));rot=(v.rotation_difference(Vector(d).normalized()) @ q).to_matrix().to_4x4();rot.translation=p.head.copy();p.matrix=rot;bpy.context.view_layer.update()
def limb(rig,a,b,t,pole):
    h=rig.pose.bones[a].head.copy();t=Vector(t);axis=t-h;l1=rig.data.bones[a].length;l2=rig.data.bones[b].length;dist=max(.01,min(axis.length,l1+l2-.0001));axis.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);v=Vector(pole)-h;v=(v-axis*v.dot(axis)).normalized();joint=h+axis*along+v*max(0,l1*l1-along*along)**.5
    aim(rig,a,joint-h);aim(rig,b,t-joint)
def rotate(rig,name,angle,axis='X'):
    p=rig.pose.bones[name];p.matrix_basis=p.matrix_basis @ Matrix.Rotation(angle,4,axis);bpy.context.view_layer.update()
def curves(action):
    if hasattr(action,'fcurves'):return list(action.fcurves)
    return [f for layer in action.layers for strip in layer.strips for bag in strip.channelbags for f in bag.fcurves]
for clip,(count,fps,loop) in CLIPS.items():
    if os.environ.get('CLIP') and os.environ['CLIP']!=clip:continue
    bpy.ops.wm.open_mainfile(filepath=str(M/'settler.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Settler MPFB'];neutral=json.loads(rig['neutral_pose']);base_loc=rig.location.copy();base_world=bpy.data.objects['GEO-stationary cream base'].matrix_world.copy()
    # Frame samples are contiguous; loop clips carry an extra exact closing key beyond delivery.
    for p in rig.pose.bones:p.rotation_mode='QUATERNION'
    sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count;sc['sample_frames']=json.dumps(list(range(1,count+1)));sc['clip']=clip;sc['source_sha256']=hashlib.sha256((M/'settler.blend').read_bytes()).hexdigest()
    staff=[o for o in sc.objects if 'staff' in o.name];hand=rig.matrix_world @ rig.pose.bones['hand_r'].matrix;staff_bind={o.name:hand.inverted() @ o.matrix_world for o in staff};staff_world={o.name:o.matrix_world.copy() for o in staff}
    if clip=='death':
        for o in staff:w=o.matrix_world.copy();o.parent=None;o.matrix_world=w
    skirt=bpy.data.objects['GEO-full length linen skirt'];sway=skirt.data.shape_keys.key_blocks['Hem sway']
    collapse_keys=[]
    if clip=='death':
        for ob in sc.objects:
            if ob.type!='MESH':continue
            is_pack=any(n in ob.name for n in ['ochre traveller pack','pack woven rib','rolled wool blanket','blanket visible spiral'])
            is_cloth=any(n in ob.name for n in ['full length linen skirt','olive diagonal overdrape','rust shawl long fringed tail','shawl fringe'])
            if not (is_pack or is_cloth):continue
            if ob.data.shape_keys is None:ob.shape_key_add(name='Basis')
            key=ob.shape_key_add(name='Authored fall compression')
            for v in key.data:
                if is_pack:v.co.x-=.25
                else:
                    weight=0 if any(n in ob.name for n in ['linen skirt','overdrape']) else 1
                    v.co.x*=1-.42*weight
            collapse_keys.append(key)
    frames=count+1 if loop else count
    for name,rows in neutral.items():rig.pose.bones[name].matrix_basis=Matrix(rows)
    bpy.context.view_layer.update()
    neutral_rot={name:rig.pose.bones[name].matrix.to_quaternion() for name in ['foot_r','foot_l','hand_r']}
    for i in range(frames):
        sc.frame_set(i+1);t=i/count if loop else min(i,count-2)/(count-2) if clip=='death' else i/(count-1)
        for name,rows in neutral.items():rig.pose.bones[name].matrix_basis=Matrix(rows)
        rig.location=base_loc;rig.rotation_euler=(0,0,0);sway.value=0;bpy.context.view_layer.update()
        if clip=='idle':
            rotate(rig,'spine_03',.014*sin(2*pi*t),'Y');rotate(rig,'head',.025*sin(2*pi*t),'Z');sway.value=.2*sin(2*pi*t)
        elif clip=='move':
            phase=2*pi*t
            for side,offset,x in [('r',0,-.065),('l',pi,.105)]:
                p=phase+offset;y=.30+.13*cos(p);z=.06+.055*max(0,sin(p));limb(rig,'thigh_'+side,'calf_'+side,(x,y,z),(x,-.40,.40))
                foot=rig.pose.bones['foot_'+side];fixed=neutral_rot[foot.name].to_matrix().to_4x4();fixed.translation=foot.head.copy();foot.matrix=fixed;bpy.context.view_layer.update()
            rotate(rig,'spine_03',.024*sin(phase),'Y');rotate(rig,'spine_01',.02*sin(phase),'Z');sway.value=.75*sin(phase-.5)
            # Staff advances with the hand; no false fixed-foot claim for in-place walk.
            limb(rig,'upperarm_r','lowerarm_r',(-.30,-.22+.045*cos(phase),1.12+.018*max(0,sin(phase))),(-.35,-.04,1.1))
            hand=rig.pose.bones['hand_r'];fixed=neutral_rot['hand_r'].to_matrix().to_4x4();fixed.translation=hand.head.copy();hand.matrix=fixed;bpy.context.view_layer.update()
        elif clip=='attack':
            # Brief backward anticipation, forward staff check, recovery; no violent civilian lunge.
            envelope=sin(pi*t)**2;advance=sin(pi*max(0,min(1,(t-.16)/.70)))**2
            rotate(rig,'spine_03',-.08*envelope,'X');rotate(rig,'spine_01',-.05*envelope,'Z')
            if advance>1e-8:
                limb(rig,'upperarm_r','lowerarm_r',(-.30-.12*advance,-.22-.18*advance,1.12+.06*envelope),(-.34-.11*advance,-.04-.06*advance,1.10+.03*advance))
            rotate(rig,'hand_r',-.25*advance,'X');sway.value=.4*sin(pi*t)
        elif clip=='hit':
            amount=[0,1,.45,0][i];rotate(rig,'spine_01',.10*amount,'X');rotate(rig,'spine_03',.13*amount,'Y');rotate(rig,'head',-.12*amount,'Z');sway.value=-.5*amount
        elif clip=='death':
            # Shallow knee relaxation within the complete robe, side collapse, exact terminal hold.
            fall=t*t*(3-2*t)
            for key in collapse_keys:key.value=fall;key.keyframe_insert('value')
            rig.rotation_euler.y=1.53*fall;rig.location.x=-.86*fall
            if fall>1e-8:
                limb(rig,'upperarm_l','lowerarm_l',(.18-.13*fall,-.25+.01*fall,1.37-.21*fall),(.38-.24*fall,-.02-.03*fall,1.12+.06*fall))
                limb(rig,'upperarm_r','lowerarm_r',(-.30+.35*fall,-.22,1.12+.06*fall),(-.34+.29*fall,-.04-.06*fall,1.10+.15*fall))
                for digit in ['index','middle','ring','pinky']:
                    for segment in range(1,4):rotate(rig,f'{digit}_{segment:02d}_r',-.8*fall,'X')
            rotate(rig,'thigh_l',.10*fall,'X');rotate(rig,'calf_l',-.15*fall,'X');rotate(rig,'thigh_r',.08*fall,'X');rotate(rig,'calf_r',-.12*fall,'X');rotate(rig,'spine_01',-.24*fall,'X');rotate(rig,'head',.18*fall,'Z');sway.value=.45*fall
            bpy.context.view_layer.update()
            # Ground the collapsed actual evaluated geometry, including robe/pack; never scale to hide.
            if t>.12:
                lowest=10
                for o in sc.objects:
                    if o.type!='MESH' or o in staff or 'stationary' in o.name:continue
                    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lowest=min(lowest,min((ev.matrix_world @ v.co).z for v in me.vertices));ev.to_mesh_clear()
                rig.location.z+=max(0,.085-lowest)
            bpy.context.view_layer.update();hw=rig.matrix_world @ rig.pose.bones['hand_r'].matrix
            release=max(0,min(1,(t-.30)/.40));release=release*release*(3-2*release)
            for o in staff:
                held=hw @ staff_bind[o.name];original=staff_world[o.name]
                # Fixed ground pose: staff spans x, lies in front of base, always inside 2.04m cell.
                target=Matrix.Translation(Vector((-.69,-.37,.105))) @ Matrix.Rotation(pi/2,4,'Y') @ Matrix.Translation(Vector((.365,.233,-.09))) @ original
                loc,q,scale=held.decompose();loc2,q2,scale2=target.decompose();o.matrix_world=Matrix.LocRotScale(loc.lerp(loc2,release),q.slerp(q2,release),scale)
                o.rotation_mode='QUATERNION';o.keyframe_insert('location');o.keyframe_insert('rotation_quaternion');o.keyframe_insert('scale')
        bpy.context.view_layer.update()
        for p in rig.pose.bones:
            p.rotation_mode='QUATERNION';p.keyframe_insert('location');p.keyframe_insert('rotation_quaternion');p.keyframe_insert('scale')
        rig.keyframe_insert('location');rig.keyframe_insert('rotation_euler');sway.keyframe_insert('value')
        assert all(abs(base_world[r][c]-bpy.data.objects['GEO-stationary cream base'].matrix_world[r][c])<1e-9 for r in range(4) for c in range(4))
    for action in bpy.data.actions:
        for fc in curves(action):
            for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
    sc.frame_set(1);bpy.context.view_layer.update()
    if clip in ['idle','attack','hit']:
        error=max(abs(p.matrix_basis[r][c]-neutral[p.name][r][c]) for p in rig.pose.bones for r in range(4) for c in range(4))
        assert error<1e-5,(clip,'first-frame rest mismatch',error)
    bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
    (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':sc['source_sha256'],'motion':'Authored MPFB rig keys; folded garment geometry and keyed hem; no mocap or cloth sim claim'},indent=2))
    with (V/'settler-log.md').open('a') as f:f.write(f'- Saved {clip}: {count} frames at {fps} fps, editable MPFB rig, stationary base; authored keys.\n')
