"""CC0 animation-library motion, native two-hand pike layer and authored thrust."""
import bpy, os, math, json, hashlib, sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rig_constants import PIKE_START, PIKE_END, PIKE_ORIGIN
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retarget import prepare, apply_matrices
R = Path(os.environ['ANIM_ROOT']); M = R/'masters/barbarian-pikeman'
source = M/'barbarian-pikeman.blend'
CLIPS = {'idle': (8,10,True), 'move': (8,12,True), 'attack': (10,14,False),
         'hit': (4,12,False), 'death': (10,10,False)}

def aim(rig, name, direction):
    p = rig.pose.bones[name]; q = p.bone.matrix_local.to_quaternion()
    q = (q @ Vector((0,1,0))).rotation_difference(Vector(direction).normalized()) @ q
    matrix = q.to_matrix().to_4x4(); matrix.translation = p.head
    p.matrix = matrix; bpy.context.view_layer.update()

def limb(rig, up, lo, target, pole):
    a = rig.pose.bones[up].head.copy(); target = Vector(target)
    axis = target-a; l1 = rig.data.bones[up].length; l2 = rig.data.bones[lo].length
    distance = min(axis.length,l1+l2-.0001); axis.normalize()
    along = (l1*l1-l2*l2+distance*distance)/(2*distance)
    height = max(0,l1*l1-along*along)**.5
    side = Vector(pole)-a; side = (side-axis*side.dot(axis)).normalized()
    elbow = a+axis*along+side*height
    aim(rig,up,elbow-a); aim(rig,lo,target-elbow)

def floor_gap():
    deps = bpy.context.evaluated_depsgraph_get(); lowest = 100
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or obj.hide_render or obj.name == 'GEO-cream-stone-base' or obj.parent == pike:
            continue
        ev = obj.evaluated_get(deps); mesh = ev.to_mesh()
        for vertex in mesh.vertices:
            v = ev.matrix_world @ vertex.co
            floor = .103 if ((v.x+.14)/.59)**2+((v.y-.07)/(.59*.66))**2 < 1 else .015
            lowest = min(lowest,v.z-floor)
        ev.to_mesh_clear()
    return lowest

for clip,(count,fps,loop) in CLIPS.items():
    if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','): continue
    (M/'clips'/f'{clip}.json').unlink(missing_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source)); sc = bpy.context.scene
    rig = bpy.data.objects['RIG-pikeman']; pike = bpy.data.objects['CTRL-pike']
    rpos = rig.location.copy(); ppos = pike.location.copy()
    neutral = {p.name:p.matrix.copy() for p in rig.pose.bones}
    hand_local = {s:pike.matrix_world.inverted() @ (rig.matrix_world @ rig.pose.bones['hand_'+s].head) for s in ['r','l']}
    hand_rotation = {s:rig.pose.bones['hand_'+s].matrix.to_quaternion() for s in ['r','l']}
    phases = [i/count if loop else min(i/(count-2),1) if clip=='death' else i/(count-1) for i in range(count+int(loop))]
    if clip == 'hit': phases = [0,.65,.30,0]
    motion, provenance = prepare(rig,R,clip,phases) if clip!='attack' else (None,{'method':'original weapon-specific thrust'})
    rig.animation_data_clear(); pike.animation_data_clear()
    for p in rig.pose.bones: p.rotation_mode = 'QUATERNION'
    sc.render.fps = fps; sc.frame_start = 1; sc.frame_end = count
    samples = []; floor_corrections = []
    for i,phase in enumerate(phases):
        sc.frame_set(i+1); rig.location = rpos; rig.rotation_euler = (0,0,0)
        pike.location = ppos; pike.rotation_euler = (0,0,0)
        apply_matrices(rig,neutral)
        if motion:
            matrices = motion[i]['matrices']
            if clip == 'death':
                # Blend the native source's first pose out of the painted guard.
                blend = min(1,phase/.25); blend = blend*blend*(3-2*blend)
                matrices = {name:neutral[name].lerp(mat,blend) for name,mat in matrices.items()}
            apply_matrices(rig,matrices)
            rig.location = rpos+motion[i]['root']
            bpy.context.view_layer.update()
            if clip in ['move','death']:
                correction = -floor_gap(); rig.location.z += correction
                floor_corrections.append(correction)
            elif clip in ['idle','hit']:
                # Keep the painted wide stance planted while the open source
                # supplies the torso/reaction. No foot rotation is overwritten.
                for side in ['r','l']:
                    target = neutral['foot_'+side].translation-(rig.location-rpos)
                    limb(rig,'thigh_'+side,'calf_'+side,target,
                         ((-.40 if side=='r' else .23),-.30,.48))
            bpy.context.view_layer.update()
            if clip != 'death':
                # Carry control follows the torso translation; both wrists solve
                # to the same shaft and retain the calibrated grip orientation.
                delta = rig.pose.bones['spine_03'].head-neutral['spine_03'].translation
                pike.location = ppos+(rig.location-rpos)+delta*.65
            else:
                ease = phase*phase*(3-2*phase)
                pike.rotation_euler.x = math.pi/2*ease
                pike.location.y += .50*ease; pike.location.z -= .94*ease
                bpy.context.view_layer.update()
                inv = Matrix.Translation(ppos).inverted()
                low = min((pike.matrix_world @ (inv @ v)).z for v in [Vector(PIKE_START),Vector(PIKE_END)])
                pike.location.z += max(0,.12-low)
        else:
            amount = [0,-.12,-.2,.15,1,.9,.55,.2,.05,0][i]
            pike.location += Vector((.08,-.14,-.06))*amount
            direction = (Vector(PIKE_END)-Vector(PIKE_START)).normalized()
            thrust = direction.rotation_difference(Vector((.65,-.62,.44)).normalized())
            axis, angle = thrust.to_axis_angle()
            pike.rotation_euler = Quaternion(axis,angle*amount).to_euler()
            rig.location += Vector((.035,-.06,0))*amount
            p = rig.pose.bones['spine_03']
            p.rotation_quaternion = p.rotation_quaternion @ Quaternion((0,0,1),-.08*amount)
            bpy.context.view_layer.update()
            for side in ['r','l']:
                limb(rig,'thigh_'+side,'calf_'+side,
                     neutral['foot_'+side].translation-(rig.location-rpos),
                     ((-.40 if side=='r' else .23),-.30,.48))
        bpy.context.view_layer.update()
        if clip == 'move':
            # The straight-legged walk raises the torso from the braced rest.
            # Lower the carrying height to retain the entire long pike in the
            # fixed painting camera; hands solve after this equipment adjustment.
            inv = Matrix.Translation(ppos).inverted()
            top = max(world_to_camera_view(sc,sc.camera,pike.matrix_world @ (inv @ v)).y
                      for v in [Vector(PIKE_START),Vector(PIKE_END)])
            if top > .97:
                pike.location -= (sc.camera.matrix_world.to_quaternion() @ Vector((0,1,0)))*((top-.97)*sc.camera.data.ortho_scale)
                bpy.context.view_layer.update()
        if clip != 'death':
            for side in ['r','l']:
                target = rig.matrix_world.inverted() @ (pike.matrix_world @ hand_local[side])
                pole = (-.56,-.16,1.00) if side=='r' else (.14,-.18,.85)
                limb(rig,'upperarm_'+side,'lowerarm_'+side,target,pole)
                p = rig.pose.bones['hand_'+side]; mat = (pike.rotation_euler.to_quaternion() @ hand_rotation[side]).to_matrix().to_4x4()
                mat.translation = p.head; p.matrix = mat
                bpy.context.view_layer.update()
        for obj in [rig,pike]:
            obj.keyframe_insert('location',frame=i+1); obj.keyframe_insert('rotation_euler',frame=i+1)
        for p in rig.pose.bones:
            for prop in ['location','rotation_quaternion','scale']: p.keyframe_insert(prop,frame=i+1)
        samples.append({s:list(rig.matrix_world @ rig.pose.bones['hand_'+s].head) for s in ['r','l']})
    info = {'frames':count,'fps':fps,'loop':loop,'source_master_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'hand_positions':samples[:count], 'motion':provenance,'floor_corrections_m':floor_corrections}
    sc['clip_info'] = json.dumps(info)
    for obj in [rig,pike]:
        if obj.animation_data and obj.animation_data.action:
            obj.animation_data.action.name = 'barbarian-pikeman-'+clip+'-'+obj.name
            for layer in obj.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fc in bag.fcurves:
                            for kp in fc.keyframe_points:
                                kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
    sc.frame_set(1); (M/'clips').mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
    (M/'clips'/f'{clip}.json').write_text(json.dumps(info,indent=2))
    print('CLIP_OK',clip,count,flush=True)
