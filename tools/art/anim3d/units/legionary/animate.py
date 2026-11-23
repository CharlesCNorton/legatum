"""CC0 skeletal motion with a weapon-carry layer and original shield attack."""
import bpy, os, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0,str(Path(__file__).parent))
from retarget import prepare, apply_matrices
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/legionary';out=M/'clips';out.mkdir(exist_ok=True)
CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
source=M/'legionary.blend'
selected=os.environ.get('CLIP');assert selected is None or selected in CLIPS,selected
for clip,(count,fps) in CLIPS.items():
    if selected and clip!=selected:continue
    (out/f'{clip}.json').unlink(missing_ok=True)
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
        p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q @ Vector((0,1,0))).rotation_difference(Vector(direction).normalized());mat=(delta @ q).to_matrix().to_4x4();mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
    def limb(u,l,target,pole):
        a=rig.pose.bones[u].head.copy();v=Vector(target)-a;d=min(v.length,rig.data.bones[u].length+rig.data.bones[l].length-.0001);v.normalize();l1=rig.data.bones[u].length;l2=rig.data.bones[l].length;along=(l1*l1-l2*l2+d*d)/(2*d)
        side=Vector(pole)-a;side=(side-v*side.dot(v)).normalized();elbow=a+along*v+max(0,l1*l1-along*along)**.5*side;aim(u,elbow-a);aim(l,Vector(target)-elbow)
    def turn(name,axis,angle):
        p=rig.pose.bones[name];mat=p.matrix.copy();pos=mat.translation.copy();mat=Matrix.Rotation(angle,4,axis) @ mat;mat.translation=pos;p.matrix=mat;bpy.context.view_layer.update()
    def guard(dy=0,dz=0):
        limb('upperarm_r','lowerarm_r',(-.365,-.19+dy,1.28+dz),(-.60,0,.80))
        limb('upperarm_l','lowerarm_l',(.30,-.24+dy,1.10+dz),(.44,-.02,1.12))
        for side in ['r','l']:aim('hand_'+side,(0,-.025,.09))
    def floor(objects):
        dg=bpy.context.evaluated_depsgraph_get();low=100
        for ob in objects:
            if ob.type not in ['MESH','CURVE'] or ob.hide_render:continue
            ev=ob.evaluated_get(dg);me=ev.to_mesh()
            if me.vertices:low=min(low,min((ev.matrix_world @ v.co).z for v in me.vertices))
            ev.to_mesh_clear()
        return low
    samples=[1+round(i*24/fps) for i in range(count)];end=samples[-1]
    key_end=round(count*24/fps)+1 if clip in ['idle','move'] else end
    phases=[(f-1)/(count*24/fps) if clip in ['idle','move'] else min(1,(f-1)/(end-1)) for f in range(1,key_end+1)]
    reset();neutral_world={p.name:p.matrix.copy() for p in rig.pose.bones}
    motion,provenance=prepare(rig,R,clip,phases) if clip!='attack' else (None,{'provider':'Original weapon-specific shield bash'})
    reset();released=set(controls)
    for o in controls:released.update(o.children_recursive)
    worn=[o for o in rig.children_recursive if o not in released]
    feet=[o for o in worn if o.name.startswith(('GEO-sandal','GEO-ankle'))]
    reference_floor=floor(feet)
    contact=[]
    sc.frame_start=1;sc.frame_end=end;sc.render.fps=24
    for index,t in enumerate(phases):
        f=index+1;sc.frame_set(f);reset()
        if motion:
            matrices=motion[index]['matrices']
            if clip=='death':
                # A short guard-to-source blend before release avoids a T-pose pop.
                blend=min(1,t/.22);blend=blend*blend*(3-2*blend)
                matrices={n:neutral_world[n].lerp(mat,blend) for n,mat in matrices.items()}
            apply_matrices(rig,matrices);rig.location=base+motion[index]['root'];bpy.context.view_layer.update()
            if clip in ['idle','move','hit']:
                # Translation only: captured foot direction/roll remain untouched.
                rig.location.z+=reference_floor-floor(feet);bpy.context.view_layer.update()
            hem.value=.25+.2*math.sin(2*math.pi*t-.7)
        else:
            strength=[0,-.15,-.30,.35,1,.9,.45,.16,.04,0][min(9,round(t*9))]
            rig.location=base+Vector((0,-.075*strength,-.035*max(0,strength)));turn('spine_03','X',.09*strength)
            for side,sg in [('l',1),('r',-1)]:
                limb('thigh_'+side,'calf_'+side,(sg*.17,(-.06 if side=='r' else .035)+.075*strength,.082+.035*max(0,strength)),(sg*.25,-.37,.48))
            guard(-.075*strength,.018*strength)
            limb('upperarm_l','lowerarm_l',(.30,-.24-.12*strength,1.10+.035*strength),(.44,-.06,1.12));aim('hand_l',(0,-.025+.085*max(0,strength),.09));hem.value=max(0,strength)*.8
            for side in ['r','l']:aim('foot_'+side,(0,-.12,-.025));aim('ball_'+side,(0,-1,0))
        if clip=='death':
            release=max(0,min(1,(t-.04)/.50));release=release*release*(3-2*release)
            start=control_world[pilum.name];endmat=Matrix.Rotation(-math.pi/2,4,'Y');endmat.translation=Vector((-.33,-.48,.13))
            mat=start.to_quaternion().slerp(endmat.to_quaternion(),release).to_matrix().to_4x4();mat.translation=start.translation.lerp(endmat.translation,release);pilum.matrix_world=mat
            for digit in ['index','middle','ring','pinky','thumb']:
                for k in range(1,4):
                    p=rig.pose.bones[f'{digit}_{k:02d}_r'];p.rotation_quaternion=p.rotation_quaternion.slerp(Quaternion(),release)
            release2=max(0,min(1,(t-.18)/.50));release2=release2*release2*(3-2*release2)
            start=control_world[shield.name];mat=start.to_quaternion().slerp(Matrix.Rotation(-math.pi/2,4,'X').to_quaternion(),release2).to_matrix().to_4x4();mat.translation=start.translation.lerp(Vector((.23,.20,.16)),release2);shield.matrix_world=mat
            bpy.context.view_layer.update()
            for o in controls:
                low=floor(o.children_recursive)
                if low<.095:
                    mat=o.matrix_world.copy();mat.translation.z+=.095-low;o.matrix_world=mat
            worlds={o.name:o.matrix_world.copy() for o in controls}
            low=floor(worn);rig.location.z+=max(0,.09-low)
            bpy.context.view_layer.update()
            for o in controls:o.matrix_world=worlds[o.name]
        bpy.context.view_layer.update()
        contact.append({'frame':f,'phase':t,'root':list(rig.location),'feet':{s:list(rig.matrix_world @ rig.pose.bones['foot_'+s].head) for s in ['l','r']},'toes':{s:list(rig.matrix_world @ rig.pose.bones['ball_'+s].tail) for s in ['l','r']}})
        rig.keyframe_insert('location',frame=f)
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
    (out/f'{clip}.json').write_text(json.dumps({'clip':clip,'samples':samples,'fps':fps,'frames':count,'loop':clip in ['idle','move'],'source_master_sha256':sc['source_master_sha256'],'motion':provenance,'contact_samples':contact},indent=2))
    print('CLIP_READY',clip,samples)
