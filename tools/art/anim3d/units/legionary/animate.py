"""Five authored skeletal actions, grounded gait, shield bash and held collapse."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/legionary';out=M/'clips';out.mkdir(exist_ok=True)
CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
source=M/'legionary.blend'
selected=os.environ.get('CLIP');assert selected is None or selected in CLIPS,selected
for clip,(count,fps) in CLIPS.items():
    if selected and clip!=selected:continue
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Legionary MPFB game_engine'];neutral=json.loads(rig['neutral_pose']);base=rig.location.copy()
    shield=bpy.data.objects['Scutum control'];pilum=bpy.data.objects['Pilum control'];controls=[shield,pilum]
    control_basis={o.name:o.matrix_basis.copy() for o in controls};control_world={o.name:o.matrix_world.copy() for o in controls}
    for o in controls:o.rotation_mode='QUATERNION'
    for p in rig.pose.bones:p.rotation_mode='QUATERNION'
    skirt=bpy.data.objects['GEO-folded red wool tunic'];skirt.shape_key_add(name='Basis');hem=skirt.shape_key_add(name='Hem follow through')
    for v,p in zip(skirt.data.vertices,hem.data):
        weight=max(0,min(1,(1.12-v.co.z)/.32));p.co.y+=.025*weight*math.sin(v.co.x*13);p.co.x+=.008*weight
    def reset():
        rig.location=base.copy()
        for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
        for o in controls:o.matrix_basis=control_basis[o.name]
        hem.value=0;bpy.context.view_layer.update()
    def aim(name,direction):
        p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized());mat=(delta@q).to_matrix().to_4x4();mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
    def limb(u,l,target,pole):
        a=rig.pose.bones[u].head.copy();v=Vector(target)-a;d=min(v.length,rig.data.bones[u].length+rig.data.bones[l].length-.0001);v.normalize();l1=rig.data.bones[u].length;l2=rig.data.bones[l].length;along=(l1*l1-l2*l2+d*d)/(2*d)
        side=Vector(pole)-a;side=(side-v*side.dot(v)).normalized();elbow=a+along*v+max(0,l1*l1-along*along)**.5*side;aim(u,elbow-a);aim(l,Vector(target)-elbow)
    def turn(name,axis,angle):
        p=rig.pose.bones[name];mat=p.matrix.copy();pos=mat.translation.copy();mat=Matrix.Rotation(angle,4,axis)@mat;mat.translation=pos;p.matrix=mat;bpy.context.view_layer.update()
    def guard(dy=0,dz=0):
        limb('upperarm_r','lowerarm_r',(-.43,-.19+dy,1.28+dz),(-.38,-.12,1.02))
        limb('upperarm_l','lowerarm_l',(.30,-.32+dy,1.10+dz),(.44,-.02,1.12))
        for side in ['r','l']:aim('hand_'+side,(0,-.025,.09))
    def floor(o):
        dg=bpy.context.evaluated_depsgraph_get();low=100
        children=list(o.children_recursive) if o.type=='EMPTY' else [o]
        for child in children:
            if child.type not in ['MESH','CURVE']:continue
            ev=child.evaluated_get(dg);mesh=ev.to_mesh()
            low=min(low,min((ev.matrix_world@v.co).z for v in mesh.vertices));ev.to_mesh_clear()
        return low
    def pose(t):
        reset();phase=2*math.pi*t
        if clip=='idle':
            turn('spine_03','Y',.012*math.sin(phase));turn('head','Z',.025*math.sin(phase));guard(0,.006*math.sin(phase));hem.value=.15+.1*math.sin(phase)
        elif clip=='move':
            # In-place march: each foot advances while lifted and travels back while planted.
            for side,sg,offset in [('l',1,0),('r',-1,math.pi)]:
                a=phase+offset;y=-.04+.16*math.cos(a);z=.082+.105*max(0,math.sin(a));x=sg*.17
                limb('thigh_'+side,'calf_'+side,(x,y,z),(sg*.24,-.38,.48));aim('foot_'+side,(0,-.12,-.025));aim('ball_'+side,(0,-1,0))
            turn('spine_03','Z',.035*math.sin(phase));guard(0,.025+.010*math.cos(phase*2));hem.value=.45+.4*math.sin(phase-.7)
        elif clip=='attack':
            # Anticipation, forward shield impact, then recovery. Pilum stays gripped outside torso.
            strength=[0,-.15,-.30,.35,1,.9,.45,.16,.04,0][min(9,round(t*9))]
            rig.location=base+Vector((0,-.075*strength,-.035*max(0,strength)));turn('spine_03','X',.09*strength)
            for side,sg in [('l',1),('r',-1)]:
                limb('thigh_'+side,'calf_'+side,(sg*.17,(-.06 if side=='r' else .035)+.075*strength,.082+.035*max(0,strength)),(sg*.25,-.37,.48))
            guard(-.075*strength,.018*strength)
            limb('upperarm_l','lowerarm_l',(.30,-.32-.12*strength,1.10+.035*strength),(.44,-.06,1.12));aim('hand_l',(0,-.025,.09));hem.value=max(0,strength)*.8
        elif clip=='hit':
            a=[0,1,.45,0][min(3,round(t*3))];turn('spine_03','X',-.17*a);turn('head','X',-.12*a);rig.location.y=.025*a;guard(.045*a,.015*a);hem.value=.65*a
        elif clip=='death':
            a=min(1,t/.78);s=a*a*(3-2*a);rig.location=base+Vector((-.22*s,.03*s,-.78*s));turn('pelvis','Y',1.32*s);turn('spine_03','Y',.18*s);turn('head','X',.25*s)
            for side,sg in [('l',1),('r',-1)]:
                x=sg*.17*(1-s)+(-.10+sg*.06)*s;y=(.035 if side=='l' else -.06)*(1-s)+sg*.10*s
                limb('thigh_'+side,'calf_'+side,(x,y,.082*(1-s)+.88*s),(-.4,-.3,.55+.55*s))
            limb('upperarm_r','lowerarm_r',(-.43+.46*s,-.19+.08*s,1.28-.40*s),(-.35,-.25,.85))
            limb('upperarm_l','lowerarm_l',(.30+.06*s,-.32+.05*s,1.10-.30*s),(.4,-.15,.9))
            for side in ['r','l']:aim('hand_'+side,(0,-.025,.09))
            # Release before the collapse: a physical weapon falls beside the stone.
            release=max(0,min(1,(t-.04)/.50));release=release*release*(3-2*release)
            start=control_world[pilum.name];end=Matrix.Rotation(-math.pi/2,4,'Y');end.translation=Vector((-.35,-.48,.13))
            # Control is at the hand, not shaft centre; final offset keeps its 1.9m span inside the camera.
            end.translation=Vector((-.33,-.48,.13))
            loc=start.translation.lerp(end.translation,release);q=start.to_quaternion().slerp(end.to_quaternion(),release);mat=q.to_matrix().to_4x4();mat.translation=loc;pilum.matrix_world=mat
            for digit in ['index','middle','ring','pinky']:
                for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_r'];p.rotation_quaternion=p.rotation_quaternion.slerp(Quaternion(),release)
            release2=max(0,min(1,(t-.28)/.48));release2=release2*release2*(3-2*release2)
            start=shield.matrix_world.copy();q=start.to_quaternion().slerp(Matrix.Rotation(-math.pi/2,4,'X').to_quaternion(),release2);mat=q.to_matrix().to_4x4();mat.translation=start.translation.lerp(Vector((.23,.20,.16)),release2);shield.matrix_world=mat
            bpy.context.view_layer.update()
            for o in controls:
                low=floor(o)
                if low<.095:
                    mat=o.matrix_world.copy();mat.translation.z+=.095-low;o.matrix_world=mat
            hem.value=.45*s
        if clip in ['attack','death']:
            for side in ['r','l']:aim('foot_'+side,(0,-.12,-.025));aim('ball_'+side,(0,-1,0))
        bpy.context.view_layer.update()
        if clip=='death':
            # Resolve the actual evaluated worn geometry against the disc, rather
            # than guessing a root Z from ankle bones. Keep released props in world space.
            released=set(controls)
            for o in controls:released.update(o.children_recursive)
            worn=[o for o in rig.children_recursive if o not in released and o.type in ['MESH','CURVE'] and not o.hide_render]
            low=min(floor(o) for o in worn)
            blend=max(0,min(1,(t-.50)/.28))
            correction=(.09-low)*(1 if low<.09 else blend)
            if abs(correction)>1e-6:
                worlds={o.name:o.matrix_world.copy() for o in controls};rig.location.z+=correction;bpy.context.view_layer.update()
                for o in controls:o.matrix_world=worlds[o.name]
                bpy.context.view_layer.update()
    samples=[1+round(i*24/fps) for i in range(count)];end=samples[-1]
    sc.frame_start=1;sc.frame_end=end;sc.render.fps=24
    for f in range(1,end+2):
        sc.frame_set(f);t=(f-1)/(count*24/fps) if clip in ['idle','move'] else min(1,(f-1)/(end-1))
        pose(t);rig.keyframe_insert('location',frame=f)
        for p in rig.pose.bones:
            for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
        for o in controls:
            for prop in ['location','rotation_quaternion','scale']:o.keyframe_insert(prop,frame=f)
        hem.keyframe_insert('value',frame=f)
    if clip=='death':samples[-2]=samples[-1]
    for action in bpy.data.actions:
        action.use_fake_user=True
        for layer in action.layers:
            for strip in layer.strips:
                for bag in getattr(strip,'channelbags',[]):
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
    sc['clip']=clip;sc['sample_frames']=json.dumps(samples);sc['source_master_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{clip}.blend'))
    (out/f'{clip}.json').write_text(json.dumps({'clip':clip,'samples':samples,'fps':fps,'frames':count,'loop':clip in ['idle','move'],'source_master_sha256':sc['source_master_sha256'],'motion':'authored MPFB skeletal keys; tunic hem shape-key follow through'},indent=2))
    print('CLIP_READY',clip,samples)
