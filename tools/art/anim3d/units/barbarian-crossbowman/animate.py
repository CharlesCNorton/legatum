"""CC0 Quaternius motion on MPFB; original crossbow attack and released equipment."""
import ast,bpy,hashlib,json,math,os
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
import sys
sys.path.insert(0,str(Path(__file__).parent))
from retarget import prepare, apply_matrices
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-crossbowman';out=M/'clips';out.mkdir(exist_ok=True)
CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<infantry IK>','exec'))
def turn(name,axis,a):
    p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(a,4,axis)@m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
def contact():
    # Exact evaluated surface bounds prevent floor penetration after collapse.
    dg=bpy.context.evaluated_depsgraph_get();pts=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or o.name=='GEO-stationary cream stone' or o.parent==weapon:continue
        ev=o.evaluated_get(dg);me=ev.to_mesh();pts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    base=bpy.data.objects['GEO-stationary cream stone']
    return min(p.z-(.051 if ((p.x-base.location.x)/.52)**2+(p.y/.52)**2<1 else 0) for p in pts),min(p.x for p in pts),max(p.x for p in pts)
for clip,(count,fps) in CLIPS.items():
    if os.environ.get('CLIP') and os.environ['CLIP']!=clip:continue
    (out/f'{clip}.json').unlink(missing_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(M/'model.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-barbarian-crossbowman'];weapon=bpy.data.objects['CTRL-crossbow'];neutral=json.loads(rig['neutral']);rigloc=rig.location.copy();wloc=weapon.location.copy();weapon.rotation_mode='QUATERNION';rig.rotation_mode='XYZ';sc.render.fps=fps
    wrists={side:rig.pose.bones['hand_'+side].head.copy() for side in ['r','l']}
    poles={side:rig.pose.bones['lowerarm_'+side].head.copy() for side in ['r','l']}
    grip=weapon.matrix_world.inverted()@(rig.matrix_world@wrists['r'])
    weapon['grip_local']=list(grip)
    handrot={side:rig.pose.bones['hand_'+side].matrix.to_quaternion() for side in ['r','l']}
    pouches=[o for o in sc.objects if o.name.startswith(('GEO-bolt leather case','GEO-spare bolt'))]
    pouchrest={o.name:o.matrix_basis.copy() for o in pouches}
    for p in rig.pose.bones:p.rotation_mode='QUATERNION'
    samples=count+(1 if clip in ['idle','move'] else 0)
    phases=[i/count if clip in ['idle','move'] else min(1,i/7) if clip=='death' else i/(count-1) for i in range(samples)]
    motion,provenance=prepare(rig,R,clip,phases) if clip!='attack' else (None,{'provider':'Original crossbow-specific attack'})
    # Save complete source evidence, including calibrated rolls and action hashes.
    (out/f'{clip}-motion.json').write_text(json.dumps(provenance,indent=2))
    for i in range(samples):
        f=i+1;sc.frame_set(f);phase=i/count;wave=math.sin(2*math.pi*phase)
        for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
        for o in pouches:o.matrix_basis=pouchrest[o.name]
        rig.location=rigloc;rig.rotation_euler=(0,0,0);weapon.location=wloc;weapon.rotation_quaternion=Quaternion();bpy.context.view_layer.update()
        if clip!='attack':
            apply_matrices(rig,motion[i]['matrices'])
            rig.location=rigloc+motion[i]['root']
            bpy.context.view_layer.update()
            if clip in ['idle','move','hit']:
                # Translation-only ground adaptation keeps source ankle/foot rotations intact.
                dg=bpy.context.evaluated_depsgraph_get();boot=bpy.data.objects['GEO-leather boots'];ev=boot.evaluated_get(dg);me=ev.to_mesh()
                low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
                rig.location.z+=.052-low
                bpy.context.view_layer.update()
                if clip=='move':
                    hand=rig.pose.bones['hand_r'].head.copy()+Vector((0,0,.12))
                    limb('upperarm_r','lowerarm_r',tuple(hand),tuple(poles['r']))
                # Weapon is rigidly carried by the right wrist; retain neutral stock orientation.
                if clip=='hit':weapon.rotation_quaternion=Quaternion((0,1,0),-.09*math.sin(math.pi*phases[i]))
                weapon.location=(rig.matrix_world@rig.pose.bones['hand_r'].head)-(weapon.rotation_quaternion@Vector((grip.x*weapon.scale.x,grip.y*weapon.scale.y,grip.z*weapon.scale.z)))
                bpy.context.view_layer.update()
            else:
                a=phases[i]*phases[i]*(3-2*phases[i])
                # Retargeted full-body fall; softly move the belt case out from beneath the body.
                for o in pouches:
                    mat=o.matrix_world.copy();mat.translation+=Vector((.08,.03,.04))*a;o.matrix_world=mat
                bpy.context.view_layer.update()
                gap,x0,x1=contact()
                rig.location.x-=(x0+x1)*.45*a
                bpy.context.view_layer.update();gap,_,_=contact();rig.location.z-=gap*a if gap>0 else gap
                release=min(1,i/5)
                weapon.rotation_quaternion=Quaternion().slerp(Quaternion((1,0,0),math.pi/2)@Vector((0,0,-1)).rotation_difference(Vector((1,0,0))),release)
                weapon.location=wloc.lerp(Vector((-.55,-.4,.14)),release)
        elif clip=='attack':
            lift=[0,.35,.80,1,1,.98,.95,.65,.25,0][i];kick=[0,0,0,0,1,.35,0,0,0,0][i]
            direction=Vector((.58,-.81,.04)).normalized();q=Vector((0,0,-1)).rotation_difference(direction);weapon.rotation_quaternion=Quaternion().slerp(q,lift)
            weapon.location=wloc+Vector((.02,-.04,.22))*lift+Vector((-.025,.04,-.01))*kick
            turn('spine_03','X',-.04*kick)
            # Hands follow the same rigid stock transform; support reaches onto the forestock.
            bpy.context.view_layer.update()
            right=weapon.matrix_world@grip
            leftrest=wrists['l'];lefttarget=rig.matrix_world.inverted()@(weapon.location+weapon.rotation_quaternion@Vector((0,.025,-.40)))
            limb('upperarm_r','lowerarm_r',tuple(rig.matrix_world.inverted()@right),tuple(poles['r'].lerp(Vector((-.39,-.08,1.35)),lift)))
            limb('upperarm_l','lowerarm_l',tuple(leftrest.lerp(lefttarget,lift)),tuple(poles['l'].lerp(Vector((.37,-.2,1.35)),lift)))
            for side in ['r','l']:
                p=rig.pose.bones['hand_'+side];loc=p.head.copy();mat=(weapon.rotation_quaternion@handrot[side]).to_matrix().to_4x4();mat.translation=loc;p.matrix=mat
            bpy.context.view_layer.update()
            turn('head','Z',.12*lift)
            # Released bolt visibility is keyed, never hidden by zero scale.
            bolt=bpy.data.objects['GEO-loaded bolt'];bolt.hide_render=i in [4,5,6];bolt.keyframe_insert('hide_render',frame=f)
        bpy.context.view_layer.update()
        for p in rig.pose.bones:
            for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
        if clip=='death':
            for o in pouches:o.keyframe_insert('location',frame=f)
        rig.keyframe_insert('location',frame=f);rig.keyframe_insert('rotation_euler',frame=f);weapon.keyframe_insert('location',frame=f);weapon.keyframe_insert('rotation_quaternion',frame=f)
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in getattr(strip,'channelbags',[]):
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
    rig.animation_data.action.name=clip+' MPFB skeleton';weapon.animation_data.action.name=clip+' crossbow grip'
    sc.frame_start=1;sc.frame_end=count;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{clip}.blend'))
    (out/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':clip in ['idle','move'],'model_sha256':hashlib.sha256((M/'model.blend').read_bytes()).hexdigest(),'motion':provenance['provider']+'; no cloth physics claimed'},indent=2))
print('ANIMATED',list(CLIPS))
