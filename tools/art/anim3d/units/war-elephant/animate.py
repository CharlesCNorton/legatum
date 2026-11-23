"""Five authored elephant clips, preserving fixed camera and stone base."""
import hashlib
import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(os.environ['ANIM_ROOT'])
M = ROOT/'masters/war-elephant'
CLIPS = {'idle':(8,10,True), 'move':(8,12,True), 'attack':(10,14,False),
         'hit':(4,12,False), 'death':(10,10,False)}
source = M/'war-elephant.blend'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()


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
    # An extra key is the exact loop closure, excluded from the delivery samples.
    sc.frame_start, sc.frame_end = 0, count if loop else count-1
    for i in range(count+int(loop)):
        t = i/count if loop else min(i, count-2)/(count-2)
        phase = 2*math.pi*t
        for p in rig.pose.bones:
            p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion()
            p.location = (0,0,0)
        body = rig.pose.bones['body']
        rise, surge, roll, pitch = 0., 0., 0., 0.
        if clip == 'idle':
            rise = .008*math.sin(phase)
        elif clip == 'move':
            rise = .014*(1-math.cos(2*phase))
            for name, offset in [('back.near',0),('front.near',.25),('back.far',.5),('front.far',.75)]:
                a = phase+offset*2*math.pi
                rotate(rig.pose.bones[name], (0,1,0), .13*math.sin(a))
                rotate(rig.pose.bones[name+'.lower'], (0,1,0), -.20*max(0,math.sin(a)))
            pitch = .009*math.sin(phase)
        elif clip == 'attack':
            # Anticipation, two-foot braced surge, tusk/head strike, recovery.
            surge = [0,-.025,-.055,-.035,.035,.06,.04,.02,.0,.0][i]
            pitch = [0,-.01,-.02,-.01,.055,.075,.05,.015,0,0][i]
            rotate(rig.pose.bones['head'], (0,1,0), pitch*1.2)
            for side in ['near','far']:
                rotate(rig.pose.bones['front.'+side], (0,1,0), pitch*1.2)
        elif clip == 'hit':
            surge = [0,-.035,-.02,0][i]
            rotate(rig.pose.bones['head'], (0,1,0), [0,-.12,-.06,0][i])
        else:
            # Knees fold, torso settles onto its side; final two samples held.
            u = min(1,max(0,(t-.12)/.72)); ease=u*u*(3-2*u)
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
            rotate(rig.pose.bones['head'], (0,1,0), .18*ease)
        rotate(body, (1,0,0), roll)
        basis=body.bone.matrix_local.to_quaternion()
        body.rotation_quaternion @= basis.inverted() @ Quaternion((0,1,0),pitch) @ basis
        body.location = basis.inverted() @ Vector((surge,0,rise))
        for j in range(7):
            angle = .022*math.sin(phase-j*.40) if clip in ['idle','move'] else -.10*math.sin(math.pi*t)*(1-j/9)
            rotate(rig.pose.bones[f'trunk{j}'],(0,1,0),angle)
        for sign,side in [(-1,'near'),(1,'far')]:
            rotate(rig.pose.bones['ear.'+side],(0,0,1),sign*.045*math.sin(phase+.4))
        rotate(rig.pose.bones['tail'],(1,0,0),.06*math.sin(phase-.5))
        if clip == 'attack':
            rider = bpy.data.objects['RIG-Officer MPFB'].pose.bones['spine_02']
            rider.rotation_mode = 'XYZ'
            rider.rotation_euler.x = .45*math.sin(math.pi*t)
            rider.keyframe_insert('rotation_euler', frame=i)
        elif clip == 'death':
            for role in ['Officer','Mahout']:
                rider=bpy.data.objects[f'RIG-{role} MPFB'].pose.bones['spine_02']
                rider.rotation_mode='XYZ'
                rider.rotation_euler.x=.42*ease
                rider.rotation_euler.y=-.18*ease
                rider.keyframe_insert('rotation_euler',frame=i)
        bpy.context.view_layer.update()
        # Every stance must land above the base; this is not a physics solver.
        ev=bpy.data.objects['GEO-Elephant continuous sculpt'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        me=ev.to_mesh();low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
        if low<.13:
            body.location += basis.inverted() @ Vector((0,0,.13-low))
        for p in rig.pose.bones:
            p.keyframe_insert('location',frame=i)
            p.keyframe_insert('rotation_quaternion',frame=i)
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(clip+'.blend')))
    (out/'clip.json').write_text(json.dumps({'clip':clip,'frames':count,'fps':fps,'loop':loop,
        'source_master_sha256':source_hash,'authored':True},indent=2)+'\n')
    print('ANIMATED',clip,count)
