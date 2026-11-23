"""Open crouched motion on the MPFB rig, plus original axe attack."""
import bpy,os,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from motion import Motion,MAP
motion=Motion(R)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
source=M/'barbarian-scout.blend';sha=hashlib.sha256(source.read_bytes()).hexdigest()
for clip,(count,fps,loop) in CLIPS.items():
    if os.environ.get('CLIP') and clip!=os.environ['CLIP']:continue
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Scout • MPFB rig'];loc=rig.location.copy()
    axe=[o for o in sc.objects if o.name in ('GEO-axe-haft','GEO-forged-axe-head')]
    rest={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
    neutral={p.name:(rig.matrix_world@p.matrix).copy() for p in rig.pose.bones}
    reference=motion.sample(clip,0) if clip!='attack' else None
    provenance=motion.provenance(clip) if clip!='attack' else {'method':'original weapon-specific axe attack'}
    hand0=(rig.matrix_world@rig.pose.bones['hand_r'].matrix).copy()
    axe0={o.name:o.matrix_world.copy() for o in axe}
    haft=bpy.data.objects['GEO-axe-haft']
    verts=[haft.matrix_world@v.co for v in haft.data.vertices]
    low=min(v.z for v in verts);high=max(v.z for v in verts)
    lower=[v for v in verts if v.z<low+.035]
    upper=[v for v in verts if v.z>high-.035]
    grip0=(sum(lower,Vector())/len(lower)).lerp(sum(upper,Vector())/len(upper),.72)
    palm0=hand0@Vector((0,.035,0))
    haft['grip_local']=list(haft.matrix_world.inverted()@grip0)
    targets0={n:(rig.matrix_world@rig.pose.bones[n].head).copy() for n in ('hand_l','hand_r','foot_l','foot_r','calf_l','calf_r','lowerarm_l','lowerarm_r')}
    def aim(name,direction):
        p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion()
        delta=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized())
        mat=(delta@q).to_matrix().to_4x4();mat.translation=p.head.copy();p.matrix=mat;bpy.context.view_layer.update()
    def limb(upper,lower,target,pole):
        inv=rig.matrix_world.inverted();target=inv@Vector(target);pole=inv@Vector(pole)
        start=rig.pose.bones[upper].head.copy();axis=target-start;l1=rig.data.bones[upper].length;l2=rig.data.bones[lower].length
        d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d)
        side=pole-start;side=(side-axis*side.dot(axis)).normalized()
        joint=start+axis*along+side*max(0,l1*l1-along*along)**.5
        aim(upper,joint-start);aim(lower,target-joint)
    def turn(name,axis,angle):
        p=rig.pose.bones[name];p.rotation_mode='XYZ';p.rotation_euler[axis]+=angle
    for i in range(count+int(loop)-int(clip=='death')):
        t=i/count if loop else min(i/(count-1),1)
        for p in rig.pose.bones:p.matrix_basis=rest[p.name]
        rig.location=loc;rig.rotation_euler=(0,0,0)
        for ob in sc.objects:
            if ob.type=='MESH' and ob.data.shape_keys:
                for key in ob.data.shape_keys.key_blocks:key.value=0
        if clip=='attack':
            a=[0,.15,.55,1,.78,.32,-.12,-.06,0,0][i]
            turn('spine_03',2,-.15*a);turn('upperarm_r',0,-1.1*a);turn('lowerarm_r',0,-.45*a)
            turn('upperarm_l',0,.22*a);turn('head',2,-.08*a)
            draw=min(1,i/2) if i<7 else max(0,(9-i)/2)
            for finger in ('index','middle','ring','pinky'):
                for joint in ('01','02','03'):
                    name=f'{finger}_{joint}_r'
                    if name in rig.pose.bones:turn(name,0,.65*draw)
            # The measured haft grip seats in the palm during the strike.
            # Belt axe is gripped during the attack, and returns to its carrier.
            bpy.context.view_layer.update()
            hand=rig.matrix_world@rig.pose.bones['hand_r'].matrix
            for o in axe:
                original=axe0[o.name].copy()
                draw=min(1,i/2) if i<7 else max(0,(9-i)/2)
                original.translation+=(palm0-grip0)*draw
                o.matrix_world=hand@hand0.inverted()@original
                o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
        else:
            # Source world rotations contain complete source hierarchy/roll.
            # Delta cancellation maps onto the kneeling bind without any foot
            # yaw edits. This is a reference-pose retarget with contact adaptation.
            phase=(i%count)/count if loop else min(1,t/.82) if clip=='death' else [0,.38,.66,0][i]
            sample=motion.sample(clip,phase)
            for p in rig.pose.bones:
                if p.name not in MAP:continue
                origin=MAP[p.name]
                delta=sample[origin].to_quaternion()@reference[origin].to_quaternion().inverted()
                baseq=neutral[p.name].to_quaternion()
                if clip=='death' and p.name.startswith(('thigh_','calf_','foot_','ball_','upperarm_','lowerarm_','hand_')):
                    # Blend out the kneeling support pose into the open fall's
                    # limb axes, preserving target roll and full source delta.
                    axis=baseq@Vector((0,1,0));srcaxis=reference[origin].to_quaternion()@Vector((0,1,0))
                    aligned=axis.rotation_difference(srcaxis)@baseq
                    baseq=baseq.slerp(aligned,min(1,phase*2))
                rotation=delta@baseq
                mat=rotation.to_matrix().to_4x4()
                mat.translation=rig.matrix_world@p.head
                p.matrix=rig.matrix_world.inverted()@mat
                bpy.context.view_layer.update()
            hip=sample['DEF-hips'].translation-reference['DEF-hips'].translation
            if clip in ('idle','move','hit'):
                # Kneeling support is a contact constraint. Captured ankle
                # positions drive the lead step; source rotations remain intact.
                feet_rotation={side:rig.pose.bones['foot_'+side].matrix.to_quaternion().copy() for side in ('l','r')}
                for side,suffix in (('l','L'),('r','R')):
                    target=targets0['foot_'+side].copy()
                    if clip=='move':
                        d=sample['DEF-foot.'+suffix].translation-reference['DEF-foot.'+suffix].translation
                        lift=max(0,d.z)*.45
                        gate=min(1,lift/.015)
                        # The rear knee remains the primary support. Translation
                        # is applied only while the lead foot is airborne.
                        if side=='l':target+=Vector((d.x*.15*gate,d.y*.25*gate,lift))
                    limb('thigh_'+side,'calf_'+side,target,targets0['calf_'+side])
                    pb=rig.pose.bones['foot_'+side];mat=feet_rotation[side].to_matrix().to_4x4();mat.translation=pb.head;pb.matrix=mat
                    bpy.context.view_layer.update()
            else:
                rig.location+=Vector((hip.x*.5,hip.y*.5,hip.z*.5))
                bpy.context.view_layer.update()
                # Let the cape and tunic fold against the body's support plane,
                # instead of propping the fallen torso up on rigid fur spikes.
                body=bpy.data.objects['GEO-anatomy'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
                floor=min((ev.matrix_world@v.co).z for v in me.vertices)-.012;ev.to_mesh_clear()
                if phase>0:
                    for ob in sc.objects:
                        if ob.name not in ('GEO-folded-pelt-cape','GEO-layered-fur-tufts.001','GEO-folded-tunic-hem','GEO-wolf-pelt-cowl','GEO-layered-fur-tufts'):continue
                        if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
                        key=ob.shape_key_add(name=f'Contact fold {i}');inv=ob.matrix_world.inverted()
                        for v,outv in zip(ob.data.vertices,key.data):
                            world=ob.matrix_world@v.co
                            if world.z<floor:
                                world.z=floor-.008+.008*math.exp((world.z-floor)/.05)
                                outv.co=inv@world
                        for frame,value in ((1,0),(max(1,i),0),(i+1,1),(i+2,0)):
                            key.value=value;key.keyframe_insert('value',frame=frame)
                        if i==count-2:
                            key.value=1;key.keyframe_insert('value',frame=count)
                        key.value=1
                    bpy.context.view_layer.update()
                # Ground the visible whole sculpture and centre its fall over
                # the disc; anatomy hidden inside a boot is not a contact point.
                points=[]
                for ob in sc.objects:
                    if ob.type=='MESH' and ob.name!='GEO-stationary-cream-base' and not ob.hide_render:
                        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
                        points.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
                a=min(1,phase*2)
                cx=(min(v.x for v in points)+max(v.x for v in points))*.5
                cy=(min(v.y for v in points)+max(v.y for v in points))*.5
                rig.location+=Vector((-cx*a,(.12-cy)*a,(.105-min(v.z for v in points))*a))
                bpy.context.view_layer.update()

        rig.keyframe_insert('location',frame=i+1)
        for p in rig.pose.bones:
            p.rotation_mode='XYZ'
            p.keyframe_insert('rotation_euler',frame=i+1);p.keyframe_insert('location',frame=i+1)
    # Explicit layered Action traversal for Blender 5.x.
    for action in bpy.data.actions:
        curves=list(action.fcurves) if hasattr(action,'fcurves') else [f for l in action.layers for s in l.strips if hasattr(s,'channelbags') for b in s.channelbags for f in b.fcurves]
        for f in curves:
            for k in f.keyframe_points:k.interpolation='BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
    sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['clip']=clip;sc['source_sha256']=sha
    sc['clip_count']=count;sc['loop']=loop;sc.frame_set(1)
    out=M/'clips'/clip;out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(clip+'.blend')))
    (out/'clip.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':sha,'motion':provenance},indent=2))
print('CLIPS_READY',os.environ.get('CLIP','idle move attack hit death'))
