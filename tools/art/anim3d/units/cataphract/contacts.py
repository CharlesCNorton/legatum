"""Vertical support corrections over native quadruped motion, no foot yaw edits."""
import bpy
from mathutils import Vector, Matrix

FEET = ['FF.L','FF.R','FFB.L','FFB.R']

def foot_indices(horse):
    return {name:[v.index for v in horse.data.vertices
                  if any(g.group == horse.vertex_groups[name].index and g.weight > .5 for g in v.groups)]
            for name in FEET}

def evaluated(horse):
    ob=horse.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ob.to_mesh()
    points=[ob.matrix_world@v.co for v in me.vertices];ob.to_mesh_clear();return points

def corrections(horse, points, targets):
    arm=bpy.data.objects['AnimalArmature'];indices=foot_indices(horse)
    offsets={n:targets[n]-min(points[i].z for i in ids) for n,ids in indices.items()}
    Ato=arm.matrix_world.inverted()@horse.matrix_world
    result=[]
    for v,world in zip(horse.data.vertices,points):
        influences={}
        for g in v.groups:
            name=horse.vertex_groups[g.group].name
            for foot in FEET:
                side=foot.rsplit('.',1)[1]; back=foot.startswith('FFB')
                lower=('BackLowerLeg.' if back else 'FrontLowerLeg.')+side
                upper=('BackUpperLeg.' if back else 'FrontUpperLeg.')+side
                if name in (foot,lower,upper):
                    # Full correction at the hoof, smoothly fading to the knee.
                    low=min(points[i].z for i in indices[foot])
                    fade=max(0,min(1,(.8-world.z)/max(.1,.8-low-.035)))
                    if name==foot: fade=1
                    influences[foot]=influences.get(foot,0)+g.weight*fade
        dz=sum(offsets[n]*weight for n,weight in influences.items())
        local=horse.matrix_world.to_3x3().inverted()@Vector((0,0,dz))
        weighted=Matrix(((0.,0.,0.,0.),)*4);total=0
        for g in v.groups:
            name=horse.vertex_groups[g.group].name
            if name not in arm.pose.bones:continue
            bone=arm.pose.bones[name];weighted+=(bone.matrix@bone.bone.matrix_local.inverted())*g.weight;total+=g.weight
        if total>.001:local=(Ato.inverted()@(weighted*(1/total))@Ato).to_3x3().inverted_safe()@local
        result.append(v.co+local)
    return result

def fit_rest_contacts():
    horse=bpy.data.objects['Horse'];points=evaluated(horse)
    for v,co in zip(horse.data.vertices,corrections(horse,points,{n:.112 for n in FEET})):v.co=co
    horse.data.update();bpy.context.view_layer.update()

def key_contacts(count,loop,clip):
    if clip=='death':return  # whole-body collapse uses the existing floor solver
    scene=bpy.context.scene;horse=bpy.data.objects['Horse'];arm=bpy.data.objects['AnimalArmature']
    frames=range(1,count+int(loop)+1);native=[]
    for frame in frames:
        scene.frame_set(frame);bpy.context.view_layer.update()
        native.append({n:(arm.matrix_world@arm.pose.bones[n].head).z for n in FEET})
    floor={n:min(s[n] for s in native) for n in FEET}
    shapes=[]
    for frame,pose in zip(frames,native):
        scene.frame_set(frame);bpy.context.view_layer.update()
        targets={n:.112+max(0,pose[n]-floor[n]) for n in FEET}
        shapes.append(corrections(horse,evaluated(horse),targets))
    horse.shape_key_add(name='Basis');horse.data.shape_keys.use_relative=False
    for frame,coords in zip(frames,shapes):
        shape=horse.shape_key_add(name='Native gait support '+str(frame));shape.interpolation='KEY_LINEAR'
        for v,co in zip(shape.data,coords):v.co=co
        keys=horse.data.shape_keys;keys.eval_time=shape.frame;keys.keyframe_insert('eval_time',frame=frame)
    scene['contact_method']='Vertical mesh corrective over native foot lift; unchanged horizontal gait and foot rotations'
