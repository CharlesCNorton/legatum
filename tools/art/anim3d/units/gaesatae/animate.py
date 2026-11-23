"""Five authored skeletal clips on MPFB anatomy; fixed camera and static base."""
import bpy, hashlib, json, math, os
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from math import sin,pi
ROOT=Path(os.environ['ANIM_ROOT']);M=ROOT/'masters/gaesatae';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def aim(rig,name,direction):
    p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q@Vector((0,1,0));delta=v.rotation_difference(Vector(direction).normalized());mat=(delta@q).to_matrix().to_4x4();mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
def limb(rig,u,l,target,pole):
    a=rig.pose.bones[u].head.copy();axis=Vector(target)-a;l1=rig.data.bones[u].length;l2=rig.data.bones[l].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*max(0,l1*l1-along*along)**.5;aim(rig,u,elbow-a);aim(rig,l,Vector(target)-elbow)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def floor_correct(rig,obs):
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();lowest=100
    for o in obs:
        ev=o.evaluated_get(dg);me=ev.to_mesh()
        if me.vertices:lowest=min(lowest,min((o.matrix_world@v.co).z for v in me.vertices))
        ev.to_mesh_clear()
    if lowest<.103:rig.location.z+=.103-lowest
for name,(count,fps,loop) in CLIPS.items():
    if os.environ.get('CLIP') and name!=os.environ['CLIP']:continue
    bpy.ops.wm.open_mainfile(filepath=str(M/'gaesatae.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Gaesatae • MPFB game_engine']
    neutral={p.name:p.matrix_basis.copy() for p in rig.pose.bones};loc=rig.location.copy();weapon=bpy.data.objects['RIG-spear'];shield=bpy.data.objects['RIG-shield'];weapon.rotation_mode=shield.rotation_mode='QUATERNION'
    # Rest grip and tip remain named geometric points, rigidly attached except intentional death release.
    rest_weapon=weapon.matrix_world.copy();rest_shield=shield.matrix_world.copy()
    hand=rig.pose.bones['hand_r'];rest_hand=rig.matrix_world@((hand.head+hand.tail)*.5)
    geometry=[o for o in sc.objects if o.type=='MESH' and 'stationary cream' not in o.name]
    body=[o for o in geometry if not (o.parent==weapon or o.parent==shield)]
    cam=sc.camera;q=cam.matrix_world.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));normal=q@Vector((0,0,1))
    feet={side:rig.pose.bones['foot_'+side].matrix.copy() for side in ('r','l')}
    ankles={side:rig.pose.bones['calf_'+side].tail.copy() for side in ('r','l')}
    audit=[];total=count+1 if loop else count
    for i in range(total):
        sc.frame_set(i+1);t=i/count if loop else i/max(1,count-2);t=min(t,1);phase=2*pi*t
        rig.location=loc;rig.rotation_euler=(0,0,0)
        for p in rig.pose.bones:p.matrix_basis=neutral[p.name];p.rotation_mode='QUATERNION'
        # Parent attachment is restored before calculating each sample.
        bpy.context.view_layer.update()
        weapon.matrix_world=rest_weapon;shield.matrix_world=rest_shield
        bpy.context.view_layer.update()
        def turn(bone,axis,amount):
            p=rig.pose.bones[bone];p.rotation_quaternion=p.rotation_quaternion@Quaternion(axis,amount)
        if name=='idle':
            turn('spine_03',(0,1,0),.018*sin(phase));turn('head',(0,1,0),.022*sin(phase+.3))
            turn('upperarm_r',(1,0,0),.018*sin(phase));turn('lowerarm_l',(0,0,1),.025*sin(phase))
        elif name=='move':
            rig.location.z+=.012*(1-math.cos(phase*2))
            for side,sg,x in [('r',1,-.50),('l',-1,.34)]:
                swing=sg*sin(phase);lift=.075*max(0,swing)
                target=ankles[side]+Vector((0,.09*math.cos(phase+(0 if sg==1 else pi)),lift))
                limb(rig,'thigh_'+side,'calf_'+side,target,(x,-.50,.50))
                foot=rig.pose.bones['foot_'+side];mat=feet[side].copy();mat.translation+=rig.pose.bones['calf_'+side].tail-ankles[side];foot.matrix=mat
            turn('spine_03',(0,1,0),.035*sin(phase));turn('upperarm_r',(0,1,0),.025*sin(phase))
        elif name=='attack':
            # Anticipation -> extension -> recovery. Spear hand thrusts above head, no blade hiding.
            strength=sin(pi*smooth((t-.12)/.76)) if .12<t<.88 else 0
            if t<.28:strength=-.16*sin(pi*t/.28)
            delta=right*(.32*strength)+up*(.025*max(0,strength))+normal*(.16*strength)
            if abs(strength)>1e-6:
                elbow=rig.pose.bones['lowerarm_r'].head.copy()
                limb(rig,'upperarm_r','lowerarm_r',rig.pose.bones['lowerarm_r'].tail+delta,elbow)
            turn('spine_03',(0,1,0),-.14*strength);turn('spine_02',(0,0,1),-.09*strength)
        elif name=='hit':
            strength=sin(pi*t)
            turn('spine_01',(1,0,0),-.20*strength);turn('head',(0,0,1),-.14*strength);turn('upperarm_l',(0,1,0),-.13*strength)
        else:
            drop=smooth((t-.12)/.76)
            # Root rolls backward onto the stone while knees fold and the weapon is released.
            pivot=rig.pose.bones['pelvis'].head.copy()
            root=rig.pose.bones['Root'];root.matrix=Matrix.Translation(pivot)@Matrix.Rotation(-1.43*drop,4,'X')@Matrix.Rotation(-.45*drop,4,'Z')@Matrix.Translation(-pivot)@root.matrix
            rig.location.z-=.67*drop
            turn('calf_r',(1,0,0),.65*drop);turn('calf_l',(1,0,0),.50*drop);turn('upperarm_l',(0,0,1),.20*drop)
            for digit in ('index','middle','ring','pinky'):
                for j in range(1,4):
                    p=rig.pose.bones[f'{digit}_{j:02d}_r'];p.rotation_quaternion=p.rotation_quaternion.slerp(Quaternion(),smooth((t-.14)/.20))
            bpy.context.view_layer.update()
            # Settle limbs toward the stone instead of leaving the braced legs
            # pointing upward when the pelvis rolls onto its back.
            settle=smooth((t-.30)/.55)
            if settle>1e-6:
                inv=rig.matrix_world.inverted()
                for side,sg in [('r',-1),('l',1)]:
                    calf=rig.pose.bones['calf_'+side]
                    target=calf.tail.lerp(inv@Vector((sg*.36,-.28,.18)),settle)
                    pole=rig.pose.bones['calf_'+side].head.lerp(inv@Vector((sg*.50,-.10,.38)),settle)
                    limb(rig,'thigh_'+side,'calf_'+side,target,pole)
                    foot=rig.pose.bones['foot_'+side];mat=feet[side].copy()
                    mat.translation+=rig.pose.bones['calf_'+side].tail-ankles[side]
                    foot.matrix=mat
                for side,x in [('r',-.40),('l',.38)]:
                    arm=rig.pose.bones['lowerarm_'+side]
                    target=arm.tail.lerp(inv@Vector((x,.12,.19)),settle)
                    pole=arm.head.lerp(inv@Vector((x,.28,.28)),settle)
                    limb(rig,'upperarm_'+side,'lowerarm_'+side,target,pole)
            floor_correct(rig,body)
        bpy.context.view_layer.update()
        if name!='death':
            for side,sg in [('r',1),('l',-1)]:
                boot=bpy.data.objects['GEO-soft leather boot '+side]
                ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
                low=min((boot.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
                target=.103+(.075*max(0,sg*sin(phase)) if name=='move' else 0)
                foot=rig.pose.bones['foot_'+side];mat=foot.matrix.copy();mat.translation.z+=target-low;foot.matrix=mat
                bpy.context.view_layer.update()
        # Spear follows the fist as a rigid assembly, including full 3D depth.
        current_hand=rig.matrix_world@((rig.pose.bones['hand_r'].head+rig.pose.bones['hand_r'].tail)*.5)
        weapon.matrix_world=Matrix.Translation(current_hand-rest_hand)@rest_weapon
        if name=='death':
            release=smooth((t-.20)/.50)
            # Lay the long shaft in the base's front tangent; keep the whole spear in frame.
            start=rest_weapon.copy();rotation=Matrix.Rotation(-.34*release,4,'Y')@Matrix.Rotation(-.40*release,4,'Z')
            pivot=Vector((-.2,0,1.6));transform=Matrix.Translation(pivot+Vector((.12,-.23,-1.37))*release)@rotation@Matrix.Translation(-pivot)
            weapon.matrix_world=transform@rest_weapon
            # Equipment contact correction, independent from the settled body.
            def settle(obj):
                dg=bpy.context.evaluated_depsgraph_get();lo=100
                for child in obj.children:
                    if child.type!='MESH':continue
                    ev=child.evaluated_get(dg);me=ev.to_mesh();lo=min(lo,min((child.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
                if lo<.108:
                    mat=obj.matrix_world.copy();mat.translation.z+=.108-lo;obj.matrix_world=mat
            bpy.context.view_layer.update();settle(weapon)
            pivot=Vector((.5,-.2,.9));transform=Matrix.Translation(pivot+Vector((-.24,.14,-.48))*release)@Matrix.Rotation(1.27*release,4,'X')@Matrix.Translation(-pivot)
            shield.matrix_world=transform@rest_shield;bpy.context.view_layer.update();settle(shield)
        for p in rig.pose.bones:
            p.keyframe_insert('location',frame=i+1);p.keyframe_insert('rotation_quaternion',frame=i+1);p.keyframe_insert('scale',frame=i+1)
        rig.keyframe_insert('location',frame=i+1)
        for o in (weapon,shield):o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_quaternion',frame=i+1);o.keyframe_insert('scale',frame=i+1)
        audit.append({'frame':i+1,'root':list(rig.location),'spear_grip_distance':(current_hand-rest_hand-(weapon.matrix_world.translation-rest_weapon.translation)).length if name!='death' else None})
    # Blender 5 layered action API: natural keys with auto-clamped easing.
    for ob in (rig,weapon,shield):
        act=ob.animation_data.action;act.name=f'Gaesatae {name} | {ob.name}'
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
    frames=list(range(1,count+1))
    if name=='death':frames[-1]=frames[-2]
    sc.frame_start=1;sc.frame_end=total;sc.render.fps=fps;sc['sample_frames']=json.dumps(frames);sc['source_sha256']=hashlib.sha256((M/'gaesatae.blend').read_bytes()).hexdigest();sc['clip']=name
    sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{name}.blend'))
    (M/'clips'/f'{name}.json').write_text(json.dumps({'frames':frames,'fps':fps,'loop':loop,'source_sha256':sc['source_sha256'],'audit':audit,'authored':'MPFB skeleton, no mocap used'},indent=2)+'\n')
    print('CLIP_READY',name,flush=True)
