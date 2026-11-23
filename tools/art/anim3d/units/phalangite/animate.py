"""Five authored clips on MPFB, with solved two-handed sarissa grip."""
import bpy,os,json,math,ast,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from math import sin,cos,pi
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/phalangite';master=M/'phalangite.blend';clips={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
# Reuse the lead's tested two-bone geometric pose solver, without executing its model build.
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared rig solver>','exec'))
requested=os.environ.get('CLIP')
report=json.loads((M/'animation-audit.json').read_text()) if requested and (M/'animation-audit.json').exists() else {}
if requested:clips={requested:clips[requested]}
for clip,(count,fps,loop) in clips.items():
    bpy.ops.wm.open_mainfile(filepath=str(master));sc=bpy.context.scene;rig=bpy.data.objects['Phalangite MPFB game_engine'];weapon=bpy.data.objects['CTRL-sarissa'];neutral={n:Matrix(v) for n,v in json.loads(rig['neutral_pose']).items()}
    initial=rig.location.copy();weapon0=weapon.matrix_world.copy();gr=Vector(weapon['grip_r']);gl=Vector(weapon['grip_l']);palm=Vector((.015,-.025,.035));base=bpy.data.objects['GEO-stationary-cream-base'];base_matrix=base.matrix_world.copy();grip_errors=[]
    rig.rotation_mode='QUATERNION';weapon.rotation_mode='QUATERNION';sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
    footrest={side:rig.pose.bones['calf_'+side].tail.copy() for side in ['l','r']}
    samples=count+1 if loop else count
    for i in range(samples):
        frame=i+1;u=i/count if loop else min(i,count-2)/max(1,count-2);phase=2*pi*u
        for p in rig.pose.bones:p.matrix_basis=neutral[p.name]
        rig.location=initial;rig.rotation_quaternion=(1,0,0,0);weapon.matrix_world=weapon0
        offset=Vector((0,0,0));angle=0
        if clip=='idle':
            offset.z=.008*sin(phase);rig.pose.bones['spine_02'].rotation_mode='XYZ';rig.pose.bones['spine_02'].rotation_euler.y+=.014*sin(phase)
        elif clip=='move':
            rig.location.z+=.012*(1-cos(phase*2));offset.z=.018*sin(phase*2)
            for side,sg in [('r',1),('l',-1)]:
                q=sin(phase)*sg;target=footrest[side].copy();target.y+=.15*q;target.z+=.075*max(0,cos(phase)*sg)
                limb('thigh_'+side,'calf_'+side,target,(-.35 if side=='r' else .35,-.4,.5))
        elif clip=='attack':
            # Gather, lower point, drive through the shoulders, recover.
            thrust=[0,-.025,-.04,.06,.11,.11,.08,.035,0,0][i];offset=Vector((thrust,-.02*thrust,-.025*sin(pi*u)));angle=-.045*sin(pi*u)
            rig.pose.bones['spine_02'].rotation_mode='XYZ';rig.pose.bones['spine_02'].rotation_euler.y+=.07*sin(pi*u)
            target=footrest['l']+Vector((.02,-.035*sin(pi*u),0));limb('thigh_l','calf_l',target,(.35,-.4,.5))
        elif clip=='hit':
            recoil=[0,1,.35,0][i];offset=Vector((-.025*recoil,0,.012*recoil));angle=.035*recoil
            rig.pose.bones['spine_02'].rotation_mode='XYZ';rig.pose.bones['spine_02'].rotation_euler.y-=.12*recoil
        elif clip=='death':
            t=max(0,min(1,(u-.10)/.80));smooth=t*t*(3-2*t)
            # Fall obliquely across the base so the long figure remains in the camera.
            rig.rotation_quaternion=Quaternion(Vector((-.60,.80,0)),1.50*smooth);rig.location=initial+Vector((-.43*smooth,-.38*smooth,.16*smooth))
            for side,sg in [('l',1),('r',-1)]:
                # Fold both real leg chains before grounding: a widely braced
                # low ankle otherwise holds the horizontal torso in mid-air.
                target=footrest[side].lerp(Vector((sg*.10,-.12,.52)),smooth)
                limb('thigh_'+side,'calf_'+side,target,(sg*.15,-.40,.75))
            offset=Vector((.08*smooth,0,-.68*smooth));angle=-.45*smooth
        # Rigid continuous weapon rotation preserves both endpoints and grip separation.
        pivot=gr;transform=Matrix.Translation(pivot+offset)@Matrix.Rotation(angle,4,'Y')@Matrix.Translation(-pivot);weapon.matrix_world=transform@weapon0
        bpy.context.view_layer.update()
        if clip=='death' and u>.15:
            # Intentional release; settle the complete shaft on the near edge of the stone.
            t=min(1,(u-.15)/.67);start=Vector(weapon['start']);end=Vector(weapon['end']);old=(end-start).normalized();direction=Vector((.40,.916,0)).normalized();rot=old.rotation_difference(direction).slerp(Quaternion(),1-t)
            oldcenter=(start+end)*.5;center=oldcenter.lerp(Vector((.45,.15,.13)),t)
            weapon.matrix_world=Matrix.Translation(center)@rot.to_matrix().to_4x4()@Matrix.Translation(-oldcenter)@weapon0
            for side in ['l','r']:
                for digit in ['index','middle','ring','pinky']:
                    for k in range(1,4):rig.pose.bones[f'{digit}_{k:02d}_{side}'].rotation_euler.x=.25
        else:
            # Solver works in rig local coordinates; use common wrist-to-palm offsets.
            for side,grip in [('r',gr),('l',gl)]:
                goal=rig.matrix_world.inverted()@(transform@grip-palm)
                limb('upperarm_'+side,'lowerarm_'+side,goal,(-.49,-.26,1.12) if side=='r' else (.15,-.28,.85))
                aim_bone('hand_'+side,(.04,-.02,.10))
            bpy.context.view_layer.update()
            for side,grip in [('r',gr),('l',gl)]:grip_errors.append((rig.matrix_world@rig.pose.bones['hand_'+side].head+palm-transform@grip).length)
        if clip=='death' and u>.6:
            bpy.context.view_layer.update();body=bpy.data.objects['MPFB anatomical male • original topology'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=(.105-low)*min(1,(u-.6)/.25);bpy.context.view_layer.update()
        # Key every bone as quaternion after matrix-space IK to avoid Euler flips.
        for p in rig.pose.bones:
            q=p.matrix_basis.to_quaternion();p.rotation_mode='QUATERNION';p.rotation_quaternion=q
            p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame)
        for ob in [rig,weapon]:
            for prop in ['location','rotation_quaternion']:ob.keyframe_insert(prop,frame=frame)
        assert (base.matrix_world.translation-base_matrix.translation).length<1e-8
    for ob in [rig,weapon]:
        action=ob.animation_data.action;action.name=f'Phalangite {clip} '+ob.name
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
    sc['clip']=json.dumps({'name':clip,'frames':count,'fps':fps,'loop':loop});sc['source_sha256']=hashlib.sha256(master.read_bytes()).hexdigest();sc.frame_set(1)
    assert max(grip_errors,default=0)<.08,(clip,max(grip_errors))
    (M/'clips').mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
    report[clip]={'frames':count,'max_grip_error_m':max(grip_errors,default=0),'stationary_base':True,'terminal_hold':clip=='death'}
(M/'animation-audit.json').write_text(json.dumps(report,indent=2));print('FIVE_CLIPS_READY',report)
