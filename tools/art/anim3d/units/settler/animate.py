"""CC0 retargeted traveller actions, authored staff check, fixed base and held death."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from math import sin,cos,pi
from retarget import prepare,apply_matrices
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler';V=R/'review/3d-v2';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,6,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}

def aim(rig,name,d):
    p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q @ Vector((0,1,0));rot=(v.rotation_difference(Vector(d).normalized()) @ q).to_matrix().to_4x4();rot.translation=p.head.copy();p.matrix=rot;bpy.context.view_layer.update()
def limb(rig,a,b,t,pole):
    h=rig.pose.bones[a].head.copy();t=Vector(t);axis=t-h;l1=rig.data.bones[a].length;l2=rig.data.bones[b].length;dist=max(.01,min(axis.length,l1+l2-.0001));axis.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);v=Vector(pole)-h;v=(v-axis*v.dot(axis)).normalized();joint=h+axis*along+v*max(0,l1*l1-along*along)**.5
    aim(rig,a,joint-h);aim(rig,b,t-joint)
def rotate(rig,name,angle,axis='X'):
    p=rig.pose.bones[name];p.matrix_basis=p.matrix_basis @ Matrix.Rotation(angle,4,axis);bpy.context.view_layer.update()
def loaded_stride(rig, drop=.12):
    """Native IK lowers a pack carrier while retaining captured ankle paths/rotations."""
    bpy.context.view_layer.update();helpers=[];constraints=[]
    for side in ['l','r']:
        foot=rig.pose.bones['foot_'+side]
        target=bpy.data.objects.new('CTRL-captured ankle '+side,None)
        bpy.context.scene.collection.objects.link(target)
        target.matrix_world=rig.matrix_world @ foot.matrix
        helpers.append(target)
        ik=rig.pose.bones['calf_'+side].constraints.new('IK')
        ik.target=target;ik.chain_count=2;ik.use_stretch=False
        constraints.append((rig.pose.bones['calf_'+side],ik))
        orientation=foot.constraints.new('COPY_ROTATION');orientation.target=target
        orientation.owner_space=orientation.target_space='WORLD'
        constraints.append((foot,orientation))
    rig.location.z-=drop;bpy.context.view_layer.update()
    matrices={p.name:p.matrix.copy() for p in rig.pose.bones}
    for bone,constraint in constraints:bone.constraints.remove(constraint)
    for ob in helpers:bpy.data.objects.remove(ob,do_unlink=True)
    apply_matrices(rig,matrices)

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
    frames=count+1 if loop else count
    for name,rows in neutral.items():rig.pose.bones[name].matrix_basis=Matrix(rows)
    bpy.context.view_layer.update()
    phases=[i/count if loop else min(i,count-2)/(count-2) if clip=='death' else i/(count-1) for i in range(frames)]
    captured=motion=None
    if clip!='attack':
        captured,motion=prepare(rig,R,clip,phases)
        (M/f'motion-{clip}.json').write_text(json.dumps(motion,indent=2))
    for i in range(frames):
        sc.frame_set(i+1);t=i/count if loop else min(i,count-2)/(count-2) if clip=='death' else i/(count-1)
        for name,rows in neutral.items():rig.pose.bones[name].matrix_basis=Matrix(rows)
        rig.location=base_loc;rig.rotation_euler=(0,0,0);sway.value=0;bpy.context.view_layer.update()
        if captured:
            apply_matrices(rig,captured[i]['matrices'])
            rig.location=base_loc+captured[i]['root']
            sway.value=(.55 if clip=='move' else .15)*sin(2*pi*t)
        if clip=='move':
            rig.location.y+=.20
            # Translate the root to the supporting sole; captured rotations stay intact.
            side='l' if 1<=i<=4 else 'r'
            ob=bpy.data.objects['GEO-sandal sole '+side]
            bpy.context.view_layer.update()
            ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
            low=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
            rig.location.z+=.079-low
            loaded_stride(rig)
        if clip=='attack':
            # Brief backward anticipation, forward staff check, recovery; no violent civilian lunge.
            envelope=sin(pi*t)**2;advance=sin(pi*max(0,min(1,(t-.16)/.70)))**2
            rotate(rig,'spine_03',-.08*envelope,'X');rotate(rig,'spine_01',-.05*envelope,'Z')
            if advance>1e-8:
                limb(rig,'upperarm_r','lowerarm_r',(-.30-.12*advance,-.22-.18*advance,1.12+.06*envelope),(-.34-.11*advance,-.04-.06*advance,1.10+.03*advance))
            rotate(rig,'hand_r',-.25*advance,'X');sway.value=.4*sin(pi*t)
        elif clip=='death':
            # Complete library fall: pelvis/spine/limbs retain captured rotations.
            # Only root translation supplies support contact, never a foot rotation fix.
            center=max(0,min(1,(t-.15)/.55));center=center*center*(3-2*center)
            rig.location.x-=.42*center
            bpy.context.view_layer.update()
            if t>.12:
                lowest=10
                for o in sc.objects:
                    if o.type!='MESH' or o in staff or 'stationary' in o.name:continue
                    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
                    if me.vertices:lowest=min(lowest,min((ev.matrix_world @ v.co).z for v in me.vertices))
                    ev.to_mesh_clear()
                rig.location.z+=.085-lowest
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
    (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':sc['source_sha256'],'motion':motion or {'method':'Authored civilian staff-check attack'},'cloth':'Authored folded garment with hem follow-through; no cloth simulation'},indent=2))
    with (V/'settler-log.md').open('a') as f:f.write(f'- Saved {clip}: {count} frames at {fps} fps, editable MPFB rig, stationary base; CC0 library motion or authored staff attack.\n')
