"""CC0 quadruped retarget with fitted contacts; original elephant attack."""
import hashlib
import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from motion import sample, move_targets, ACTIONS, SHA
from rider_motion import sample_rider

ROOT = Path(os.environ['ANIM_ROOT'])
M = ROOT/'masters/war-elephant'
CLIPS = {'idle':(8,10,True), 'move':(8,12,True), 'attack':(10,14,False),
         'hit':(4,12,False), 'death':(10,10,False)}
source = M/'war-elephant.blend'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
source_motion = sample(ROOT, CLIPS)


def rotate(bone, axis, angle):
    basis = bone.bone.matrix_local.to_quaternion()
    bone.rotation_mode = 'QUATERNION'
    bone.rotation_quaternion = basis.inverted() @ Quaternion(axis, angle) @ basis


requested=set(os.environ.get('CLIPS', ','.join(CLIPS)).split(','))
assert requested <= set(CLIPS), 'Unknown clip requested'
for clip, (count, fps, loop) in CLIPS.items():
    if clip not in requested:
        continue
    out = M/'clips'/clip
    out.mkdir(parents=True, exist_ok=True)
    (out/'clip.json').unlink(missing_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    sc = bpy.context.scene
    rig = bpy.data.objects['RIG-Elephant']
    sc.render.fps = fps
    rest = {p.name:p.matrix.copy() for p in rig.pose.bones}
    rest_location = rig.pose.bones['body'].location.copy()
    riders = [bpy.data.objects[f'RIG-{role} MPFB'] for role in ['Officer', 'Mahout']]
    rider_action, rider_samples = sample_rider(riders[0], clip, count, loop)
    rider_rest = {r.name: {name: r.pose.bones[name].matrix_basis.to_quaternion()
                          for name in rider_samples[0]} for r in riders}
    # Fitted knee/sole locations come from the actual mesh, not the pre-fit rig.
    anatomy = bpy.data.objects['GEO-Elephant continuous sculpt']
    evaluated = anatomy.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    centres = {}
    for leg in ['front.near','front.far','back.near','back.far']:
        group = anatomy.vertex_groups[leg+'.lower'].index
        points = [evaluated.matrix_world@v.co for v in mesh.vertices
                  if any(g.group==group and g.weight>.95 for g in v.groups)]
        centres[leg] = sum(points,Vector())/len(points)
    evaluated.to_mesh_clear()
    # An extra key is the exact loop closure, excluded from the delivery samples.
    sc.frame_start, sc.frame_end = 0, count if loop else count-1
    for i in range(count+int(loop)):
        t = i/count if loop else min(i,count-2)/(count-2) if clip=='death' else i/(count-1)
        phase = 2*math.pi*t
        for p in rig.pose.bones:
            p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion()
            p.location = (0,0,0)
        body = rig.pose.bones['body']
        for rider_rig in riders:
            for name, delta in rider_samples[i].items():
                bone = rider_rig.pose.bones[name]
                bone.rotation_mode = 'QUATERNION'
                bone.rotation_quaternion = rider_rest[rider_rig.name][name] @ delta
        rise, surge, roll, pitch = 0., 0., 0., 0.
        if clip == 'idle':
            source_frames = source_motion['idle']
            rise = (source_frames[i]['Back'][2]-source_frames[0]['Back'][2])*.12
            pitch = (source_frames[i]['Head'][0]-source_frames[0]['Head'][0])*.025
        elif clip == 'move':
            source_frames = source_motion['move']
            rise = (source_frames[i]['Back'][2]-source_frames[0]['Back'][2])*.20
            pitch = (source_frames[i]['Back'][0]-source_frames[0]['Back'][0])*.025
        elif clip == 'attack':
            # Anticipation, two-foot braced surge, tusk/head strike, recovery.
            surge = [0,-.025,-.055,-.035,.035,.06,.04,.02,.0,.0][i]
            pitch = [0,-.01,-.02,-.01,.055,.075,.05,.015,0,0][i]
            rotate(rig.pose.bones['head'], (0,1,0), pitch*1.2)
            for side in ['near','far']:
                rotate(rig.pose.bones['front.'+side], (0,1,0), pitch*1.2)
        elif clip == 'hit':
            sf = source_motion['hit']
            recoil = (sf[i]['Back'][2]-sf[0]['Back'][2])
            surge = recoil*.10
            rotate(rig.pose.bones['head'], (0,1,0), recoil*.32)
        else:
            # Knees fold, torso settles onto its side; final two samples held.
            sf = source_motion['death']
            drop = sf[0]['Back'][2]-sf[i]['Back'][2]
            full = sf[0]['Back'][2]-min(f['Back'][2] for f in sf)
            ease = min(1,max(0,drop/full))
            u = ease
            roll = ease*1.48
            rise = -.98*ease
            pitch = -.10*math.sin(math.pi*u)
            for name in ['front.near','front.far','back.near','back.far']:
                rotate(rig.pose.bones[name], (0,1,0), .65*ease)
                rotate(rig.pose.bones[name+'.lower'], (0,1,0), -1.35*ease)
                if name.endswith('near'):
                    leg=rig.pose.bones[name]
                    local=leg.bone.matrix_local.to_quaternion()
                    leg.rotation_quaternion @= local.inverted() @ Quaternion((1,0,0),.30*ease) @ local
                elif name == 'back.far':
                    # The fitted rear sole is farther into camera depth than
                    # the original rig. Fold that thigh inward as the body
                    # rolls, rather than leaving the calf hooked above it.
                    leg=rig.pose.bones[name]
                    local=leg.bone.matrix_local.to_quaternion()
                    leg.rotation_quaternion @= local.inverted() @ Quaternion((1,0,0),-.80*ease) @ local
            rotate(rig.pose.bones['head'], (0,1,0), .18*ease)
        rotate(body, (1,0,0), roll)
        basis=body.bone.matrix_local.to_quaternion()
        body.rotation_quaternion @= basis.inverted() @ Quaternion((0,1,0),pitch) @ basis
        body.location = rest_location + basis.inverted() @ Vector((surge,0,rise))
        for j in range(7):
            angle = .022*math.sin(phase-j*.40) if clip in ['idle','move'] else -.10*math.sin(math.pi*t)*(1-j/9)
            rotate(rig.pose.bones[f'trunk{j}'],(0,1,0),angle)
        for sign,side in [(-1,'near'),(1,'far')]:
            if clip=='death' and side=='near':
                rotate(rig.pose.bones['ear.'+side],(1,0,0),.50*ease)
            else:
                rotate(rig.pose.bones['ear.'+side],(0,0,1),sign*.045*math.sin(phase+.4))
        rotate(rig.pose.bones['tail'],(1,0,0),.06*math.sin(phase-.5))
        if clip == 'attack':
            rider = bpy.data.objects['RIG-Officer MPFB'].pose.bones['spine_02']
            rider.rotation_quaternion @= Quaternion((1,0,0), .45*math.sin(math.pi*t))
        elif clip == 'death':
            for role in ['Officer','Mahout']:
                rider=bpy.data.objects[f'RIG-{role} MPFB'].pose.bones['spine_02']
                rider.rotation_quaternion @= Quaternion((1,0,0), .20*ease)
        for rider_rig in riders:
            for name in rider_samples[i]:
                rider_rig.pose.bones[name].keyframe_insert('rotation_quaternion', frame=i)
        bpy.context.view_layer.update()
        if clip == 'move':
            # Absolute lower-segment transforms preserve sole direction and
            # pin contact; upper segments follow the open source swing arc.
            for leg, delta in move_targets(source_motion['move'],i).items():
                upper = rig.pose.bones[leg]
                hip = rig.matrix_world @ rest[leg].translation
                ankle = centres[leg]
                before = ankle-hip
                after = ankle+delta-hip
                rotation = before.rotation_difference(after).to_matrix().to_4x4()
                deform = Matrix.Translation(hip)@rotation@Matrix.Translation(-hip)
                upper.matrix = rig.matrix_world.inverted()@deform@rig.matrix_world@rest[leg]
                bpy.context.view_layer.update()
                lower = rig.pose.bones[leg+'.lower']
                lower.matrix = rig.matrix_world.inverted()@Matrix.Translation(delta)@rig.matrix_world@rest[leg+'.lower']
                bpy.context.view_layer.update()
        # Every stance must land above the base; this is not a physics solver.
        ev=bpy.data.objects['GEO-Elephant continuous sculpt'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        me=ev.to_mesh();low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
        if clip=='death':
            # The body alone is insufficient: the ear, fringe and straps also
            # have thickness and must not pass through the stationary stone.
            for ob in sc.objects:
                if ob.type!='MESH' or ob.name=='GEO-Stationary cream stone base':continue
                ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
                me=ev.to_mesh()
                low=min(low,min((ev.matrix_world@v.co).z for v in me.vertices))
                ev.to_mesh_clear()
        if low<.13:
            body.location += basis.inverted() @ Vector((0,0,.13-low))
        for p in rig.pose.bones:
            p.keyframe_insert('location',frame=i)
            p.keyframe_insert('rotation_quaternion',frame=i)
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(clip+'.blend')))
    (out/'clip.json').write_text(json.dumps({'clip':clip,'frames':count,'fps':fps,'loop':loop,
        'source_master_sha256':source_hash,'authored':clip=='attack',
        'rider_action':rider_action,'rider_retarget':'reference/roll compensated torso and head; seated limbs constrained',
        'motion_source':ACTIONS.get(clip,'Original weapon attack'),
        'motion_source_sha256':SHA if clip!='attack' else None},indent=2)+'\n')
    print('ANIMATED',clip,count)
