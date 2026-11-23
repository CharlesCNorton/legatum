"""Five authored scouting clips on the crouched MPFB bind pose."""
import bpy,os,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
source=M/'barbarian-scout.blend';sha=hashlib.sha256(source.read_bytes()).hexdigest()
for clip,(count,fps,loop) in CLIPS.items():
    if os.environ.get('CLIP') and clip!=os.environ['CLIP']:continue
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Scout • MPFB rig'];loc=rig.location.copy()
    axe=[o for o in sc.objects if o.name in ('GEO-axe-haft','GEO-forged-axe-head')]
    rest={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
    hand0=(rig.matrix_world@rig.pose.bones['hand_r'].matrix).copy()
    axe0={o.name:o.matrix_world.copy() for o in axe}
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
    for i in range(count+int(loop)):
        t=i/count if loop else min(i/(count-1),1)
        for p in rig.pose.bones:p.matrix_basis=rest[p.name]
        rig.location=loc;rig.rotation_euler=(0,0,0)
        if clip=='idle':
            v=math.sin(t*2*math.pi);turn('spine_03',0,.018*v);turn('head',2,.035*v);turn('lowerarm_l',0,.018*v)
        elif clip=='move':
            v=math.sin(t*2*math.pi)
            # Crouched reconnaissance shuffle; alternating support, small travel.
            turn('thigh_l',0,.13*v);turn('calf_l',0,-.13*v)
            turn('thigh_r',0,-.12*v);turn('calf_r',0,.12*v)
            turn('spine_03',2,.05*v);turn('upperarm_r',0,-.10*v);rig.location.z+=.012*(1-math.cos(t*4*math.pi))
        elif clip=='attack':
            a=[0,.15,.55,1,.78,.32,-.12,-.06,0,0][i]
            turn('spine_03',2,-.15*a);turn('upperarm_r',0,-1.1*a);turn('lowerarm_r',0,-.45*a)
            turn('upperarm_l',0,.22*a);turn('head',2,-.08*a)
            # Belt axe is gripped during the attack, and returns to its carrier.
            bpy.context.view_layer.update()
            hand=rig.matrix_world@rig.pose.bones['hand_r'].matrix
            for o in axe:
                original=axe0[o.name].copy()
                draw=min(1,i/2) if i<7 else max(0,(9-i)/2)
                original.translation.y-=.16*draw
                o.matrix_world=hand@hand0.inverted()@original
                o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
        elif clip=='hit':
            a=[0,1,.45,0][i];turn('spine_03',0,-.18*a);turn('head',0,-.13*a);turn('upperarm_l',2,-.20*a)
        else:
            # Sideways collapse around pelvis; settle fully for final two frames.
            a=min(1,t/.78);a=a*a*(3-2*a)
            turn('pelvis',2,1.48*a);turn('spine_03',2,.18*a);turn('head',0,.2*a)
            turn('upperarm_l',0,1.65*a);turn('lowerarm_l',0,-.8*a)
            turn('thigh_l',0,-.3*a);turn('calf_l',0,.6*a)
            rig.location+=Vector((.08*a,.015*a,-.28*a))
            bpy.context.view_layer.update()
            if a>0:
                for side,target,pole in [('l',(.40,-.10,.16),(.24,-.30,.30)),('r',(.18,.20,.16),(.02,-.30,.28))]:
                    limb('thigh_'+side,'calf_'+side,targets0['foot_'+side].lerp(Vector(target),a),targets0['calf_'+side].lerp(Vector(pole),a))
                for side,target,pole in [('l',(-.25,-.25,.20),(-.38,-.08,.30)),('r',(-.05,-.32,.20),(-.25,-.32,.28))]:
                    limb('upperarm_'+side,'lowerarm_'+side,targets0['hand_'+side].lerp(Vector(target),a),targets0['lowerarm_'+side].lerp(Vector(pole),a))
                # Ground actual anatomy, rather than rotating a bounding box into
                # the base. Correct root only; the cream disc never moves.
                bpy.context.view_layer.update();ob=bpy.data.objects['GEO-anatomy'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
                zmin=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
                rig.location.z+=max(0,.105-zmin)
                bpy.context.view_layer.update()
                # Preserve the fixed camera while containing the horn and pelt.
                xs=[]
                for ob in sc.objects:
                    if ob.type=='MESH' and ob.name!='GEO-stationary-cream-base':
                        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());xs.extend((ev.matrix_world@Vector(v)).x for v in ev.bound_box)
                if min(xs)<-.76:rig.location.x+=-.76-min(xs)

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
    (out/'clip.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':sha},indent=2))
print('CLIPS_READY',os.environ.get('CLIP','idle move attack hit death'))
