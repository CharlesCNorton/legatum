"""Five authored actions on the original MPFB skeleton; keyed weapon grip and held death."""
import ast,bpy,hashlib,json,math,os
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/crossbowman';out=M/'clips';out.mkdir(exist_ok=True)
CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<infantry IK>','exec'))
def turn(name,axis,a):
    p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(a,4,axis) @ m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
def contact():
    # Exact evaluated surface bounds prevent floor penetration after collapse.
    dg=bpy.context.evaluated_depsgraph_get();pts=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or o.name=='GEO-stationary cream stone' or o.parent==weapon or o.parent==shield:continue
        ev=o.evaluated_get(dg);me=ev.to_mesh();pts.extend(ev.matrix_world @ v.co for v in me.vertices);ev.to_mesh_clear()
    return min(p.z for p in pts),min(p.x for p in pts),max(p.x for p in pts)
for clip,(count,fps) in CLIPS.items():
    if os.environ.get('CLIP') and os.environ['CLIP']!=clip:continue
    (out/f'{clip}.json').unlink(missing_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(M/'model.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-crossbowman'];weapon=bpy.data.objects['CTRL-crossbow'];shield=bpy.data.objects['CTRL-pavise'];sloc=shield.location.copy();shield.rotation_mode='XYZ';neutral=json.loads(rig['neutral']);rigloc=rig.location.copy();wloc=weapon.location.copy();weapon.rotation_mode='QUATERNION';rig.rotation_mode='XYZ';sc.render.fps=fps
    for p in rig.pose.bones:p.rotation_mode='QUATERNION'
    for i in range(count+(1 if clip in ['idle','move'] else 0)):
        f=i+1;sc.frame_set(f);phase=i/count;wave=math.sin(2*math.pi*phase)
        for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
        rig.location=rigloc;rig.rotation_euler=(0,0,0);weapon.location=wloc;weapon.rotation_quaternion=Quaternion();shield.location=sloc;shield.rotation_euler=(0,0,0);bpy.context.view_layer.update()
        if clip=='idle':
            turn('spine_03','Y',.012*wave);turn('head','Z',.025*wave);weapon.location.z+=.004*wave
        elif clip=='move':
            # In-place guarded walk, legs exchange support; weapon carried clear of stone.
            for side,sg in [('l',1),('r',-1)]:
                p=phase+(0 if sg==1 else .5);s=math.sin(2*math.pi*p);lift=.085*max(0,s)
                target=(sg*(.17 if side=='l' else .12),-.015+.14*math.cos(2*math.pi*p),.10+lift)
                limb('thigh_'+side,'calf_'+side,target,(sg*.21,-.3,.5));aim_bone('foot_'+side,(sg*.025,-1,0))
            turn('spine_02','Z',.035*wave);turn('head','Z',-.035*wave)
            weapon.location.z+=.10+.009*math.cos(4*math.pi*phase)
            shield.location.z+=.09+.008*math.cos(4*math.pi*phase)
            shield.rotation_euler.y=.025*wave
            limb('upperarm_l','lowerarm_l',(.455,-.25,1.49),(.30,-.80,1.44))
            limb('upperarm_r','lowerarm_r',tuple(rig.matrix_world.inverted() @ (weapon.location+Vector((.05,.035,.04)))),(-.29,-.80,1.18))
        elif clip=='attack':
            lift=[0,.35,.80,1,1,.98,.95,.65,.25,0][i];kick=[0,0,0,0,1,.35,0,0,0,0][i]
            direction=Vector((.85,-.52,.13)).normalized();q=Vector((0,0,-1)).rotation_difference(direction);weapon.rotation_quaternion=Quaternion().slerp(q,lift)
            weapon.location=wloc+Vector((.10,-.08,.36))*lift+Vector((-.025,.04,-.01))*kick
            # Hands follow the same rigid stock transform; support reaches onto the forestock.
            right=weapon.location+weapon.rotation_quaternion @ Vector((.05,.035,.04))
            leftrest=Vector((.455,-.25,1.40));lefttarget=rig.matrix_world.inverted() @ (weapon.location+weapon.rotation_quaternion @ Vector((.05,.025,-.40)))
            limb('upperarm_r','lowerarm_r',tuple(rig.matrix_world.inverted() @ right),(-.29,-.80,1.18))
            limb('upperarm_l','lowerarm_l',tuple(leftrest.lerp(lefttarget,lift)),(.30,-.80,1.44))
            turn('head','Z',.12*lift);turn('spine_03','X',-.04*kick)
            # Released bolt visibility is keyed, never hidden by zero scale.
            bolt=bpy.data.objects['GEO-loaded bolt'];bolt.hide_render=i in [4,5,6];bolt.keyframe_insert('hide_render',frame=f)
        elif clip=='hit':
            a=[0,1,.45,0][i];turn('spine_02','X',-.22*a);turn('head','X',-.12*a);turn('upperarm_l','Z',-.18*a);weapon.rotation_quaternion=Quaternion((0,1,0),-.11*a)
        elif clip=='death':
            t=min(1,i/7);a=t*t*(3-2*t)
            # Fold knees, roll onto the side and let the released crossbow settle in front.
            turn('thigh_l','X',-.65*a);turn('calf_l','X',1.15*a);turn('thigh_r','X',-.40*a);turn('calf_r','X',.85*a);turn('spine_02','X',.25*a);turn('head','X',.17*a)
            rig.rotation_euler=(.12*a,1.47*a,.12*a);rig.location=rigloc+Vector((-.7*a,.10*a,-.06*a));bpy.context.view_layer.update()
            base=bpy.data.objects['GEO-stationary cream stone']
            floor=max((base.matrix_world @ Vector(corner)).z for corner in base.bound_box)+.004
            low,x0,x1=contact();rig.location.z+=max(0,floor-low);rig.location.x-=(x0+x1)*.6*a
            release=min(1,i/5)
            # Roll around the fallen stock axis as it lands: the prod must lie
            # flat rather than turn vertical and stab through the stone.
            flat=Quaternion((1,0,0),math.pi/2) @ Vector((0,0,-1)).rotation_difference(Vector((1,0,0)))
            weapon.rotation_quaternion=Quaternion().slerp(flat,release)
            weapon.location=wloc.lerp(Vector((-.58,-.36,.19)),release)
            bpy.context.view_layer.update()
            dg=bpy.context.evaluated_depsgraph_get();lowest=float('inf')
            for part in weapon.children:
                if part.type!='MESH':continue
                ev=part.evaluated_get(dg);me=ev.to_mesh()
                lowest=min(lowest,min((ev.matrix_world @ v.co).z for v in me.vertices))
                ev.to_mesh_clear()
            weapon.location.z+=max(0,floor-lowest)
        if clip in ['idle','hit']:
            grip=weapon.location+weapon.rotation_quaternion @ Vector((.05,.035,.04))
            limb('upperarm_r','lowerarm_r',tuple(rig.matrix_world.inverted() @ grip),(-.29,-.80,1.18))
        bowstring=bpy.data.objects['GEO-taut bowstring']
        if bowstring.data.shape_keys:
            draw=bowstring.data.shape_keys.key_blocks['Draw'];draw.value=([0,.3,.8,1,0,0,.2,.4,.2,0][i] if clip=='attack' else 0);draw.keyframe_insert('value',frame=f)
        if clip=='attack':
            aim_bone('hand_r',weapon.rotation_quaternion @ Vector((0,0,-1)))
            aim_bone('hand_l',Vector((0,-.2,-1)).lerp(weapon.rotation_quaternion @ Vector((0,0,-1)),lift))
        bpy.context.view_layer.update()
        shield.keyframe_insert('location',frame=f);shield.keyframe_insert('rotation_euler',frame=f)
        for p in rig.pose.bones:
            for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
        rig.keyframe_insert('location',frame=f);rig.keyframe_insert('rotation_euler',frame=f);weapon.keyframe_insert('location',frame=f);weapon.keyframe_insert('rotation_quaternion',frame=f)
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in getattr(strip,'channelbags',[]):
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
    rig.animation_data.action.name=clip+' MPFB skeleton';weapon.animation_data.action.name=clip+' crossbow grip'
    sc.frame_start=1;sc.frame_end=count;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{clip}.blend'))
    (out/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':clip in ['idle','move'],'model_sha256':hashlib.sha256((M/'model.blend').read_bytes()).hexdigest(),'motion':'authored MPFB skeletal keys; no cloth physics claimed'},indent=2))
print('ANIMATED',list(CLIPS))
