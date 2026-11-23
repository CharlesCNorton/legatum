"""CC0 source motion, rest/roll calibrated to MPFB, with a two-handed attack."""
import ast
import hashlib
import json
import math
import os
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Quaternion, Vector
sys.path.insert(0, str(Path(__file__).parent))
import retarget
R = Path(os.environ['ANIM_ROOT'])
M = R/'masters/phalangite'
master = M/'phalangite.blend'
clips = {'idle': (8, 10, True), 'move': (8, 12, True),
         'attack': (10, 14, False), 'hit': (4, 12, False), 'death': (10, 10, False)}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
    if isinstance(node, ast.FunctionDef) and node.name in {'aim_bone', 'limb'}:
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<shared rig solver>', 'exec'))
requested = os.environ.get('CLIP')
report = json.loads((M/'animation-audit.json').read_text()) if requested and (M/'animation-audit.json').exists() else {}
if requested:
    clips = {requested: clips[requested]}


def lowest(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    low = min((ev.matrix_world @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    return low


for clip, (count, fps, loop) in clips.items():
    bpy.ops.wm.open_mainfile(filepath=str(master))
    sc = bpy.context.scene
    rig = bpy.data.objects['Phalangite MPFB game_engine']
    body = bpy.data.objects['MPFB anatomical male • original topology']
    weapon = bpy.data.objects['CTRL-sarissa']
    neutral = {n: Matrix(v) for n, v in json.loads(rig['neutral_pose']).items()}
    initial = rig.location.copy()
    weapon0 = weapon.matrix_world.copy()
    gr, gl = Vector(weapon['grip_r']), Vector(weapon['grip_l'])
    palm = Vector((.015, -.025, .035))
    base = bpy.data.objects['GEO-stationary-cream-base']
    base_matrix = base.matrix_world.copy()
    rig.rotation_mode = weapon.rotation_mode = 'QUATERNION'
    for p in rig.pose.bones:
        p.rotation_mode = 'QUATERNION'
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, count
    footrest = {s: rig.pose.bones['calf_'+s].tail.copy() for s in ['l', 'r']}
    phases = [i/count for i in range(count+1)] if loop else [0, .32, .68, 1] if clip == 'hit' else [0, .09, .23, .39, .56, .73, .90, 1, 1, 1]
    motion = 'Original weapon-specific attack'
    captured = None
    if clip in retarget.ACTIONS:
        captured, motion = retarget.prepare(rig, R, clip, phases)
    support = [body] + [o for o in sc.objects if o.type == 'MESH' and any(k in o.name for k in ['sandal', 'sole', 'greave'])]
    grip_errors = []
    for i in range(count+1 if loop else count):
        for p in rig.pose.bones:
            p.matrix_basis = neutral[p.name]
        rig.location = initial
        rig.rotation_quaternion = Quaternion()
        weapon.matrix_world = weapon0
        offset, angle = Vector(), 0
        if captured:
            retarget.apply_matrices(rig, captured[i]['matrices'])
            rig.location = initial+captured[i]['root']
            bpy.context.view_layer.update()
            # Support comes from the actual body/soles; never change captured
            # foot rotations to conceal a rest-space retargeting error.
            rig.location.z += .094-min(lowest(ob) for ob in support)
            if clip == 'death':
                # Keep the fall centred over its own stone, retaining source
                # articulation. The source's root travel is not gameplay travel.
                rig.location.x = initial.x-.12*phases[i]
                rig.location.y = initial.y+.03*phases[i]
            else:
                # The rigid two-handed weapon follows the captured shoulders.
                offset = (rig.location-initial)*.55
                offset.z += .005*math.sin(2*math.pi*phases[i]) if loop else 0
                if clip == 'hit':
                    amount = [0, 1, .35, 0][i]
                    offset.x -= .045*amount
                    angle = .045*amount
        else:
            thrust = [0, -.035, -.055, .06, .15, .15, .10, .04, 0, 0][i]
            rig.location.x += max(0, thrust)*.32
            offset = Vector((thrust, -.02*thrust, -.035*math.sin(math.pi*i/9)))
            angle = -.075*math.sin(math.pi*i/9)
            p = rig.pose.bones['spine_02']
            p.rotation_quaternion = neutral[p.name].to_quaternion() @ Quaternion((0, 1, 0), .09*math.sin(math.pi*i/9))
            target = footrest['l']+Vector((.02, -.045*math.sin(math.pi*i/9), 0))
            limb('thigh_l', 'calf_l', target-(rig.location-initial), (.35, -.4, .5))
            limb('thigh_r', 'calf_r', footrest['r']-(rig.location-initial), (-.35, -.4, .5))
        if i == 0 and clip in {'hit', 'death'}:
            rig.location = initial
            for p in rig.pose.bones:
                p.matrix_basis = neutral[p.name]
        bpy.context.view_layer.update()
        transform = Matrix.Translation(gr+offset) @ Matrix.Rotation(angle, 4, 'Y') @ Matrix.Translation(-gr)
        weapon.matrix_world = transform @ weapon0
        if clip == 'death' and i >= 1:
            t = min(1, i/6)
            t = t*t*(3-2*t)
            start, end = Vector(weapon['start']), Vector(weapon['end'])
            direction = Vector((.40, .916, 0)).normalized()
            rot = Quaternion().slerp((end-start).normalized().rotation_difference(direction), t)
            center = ((start+end)*.5).lerp(Vector((.25, .02, .13)), t)
            weapon.matrix_world = Matrix.Translation(center) @ rot.to_matrix().to_4x4() @ Matrix.Translation(-(start+end)*.5) @ weapon0
        else:
            for side, grip in [('r', gr), ('l', gl)]:
                goal = rig.matrix_world.inverted() @ (transform @ grip-palm)
                limb('upperarm_'+side, 'lowerarm_'+side, goal, (-.49, -.26, 1.12) if side == 'r' else (.15, -.28, .85))
                aim_bone('hand_'+side, (.04, -.02, .10))
            bpy.context.view_layer.update()
            for side, grip in [('r', gr), ('l', gl)]:
                grip_errors.append((rig.matrix_world @ rig.pose.bones['hand_'+side].head+palm-transform @ grip).length)
        # Source lower-body and root motion remain inspectable in provenance.
        for p in rig.pose.bones:
            p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = p.matrix_basis.to_quaternion()
            for prop in ['location', 'rotation_quaternion', 'scale']:
                p.keyframe_insert(prop, frame=i+1)
        for ob in [rig, weapon]:
            for prop in ['location', 'rotation_quaternion']:
                ob.keyframe_insert(prop, frame=i+1)
        assert (base.matrix_world.translation-base_matrix.translation).length < 1e-8
    for ob in [rig, weapon]:
        action = ob.animation_data.action
        action.name = f'Phalangite {clip} '+ob.name
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:
                            k.interpolation = 'BEZIER'
                            k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
    sc['clip'] = json.dumps({'name': clip, 'frames': count, 'fps': fps, 'loop': loop})
    sc['source_sha256'] = hashlib.sha256(master.read_bytes()).hexdigest()
    sc.frame_set(1)
    assert max(grip_errors, default=0) < .08, (clip, max(grip_errors))
    (M/'clips').mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
    report[clip] = {'frames': count, 'max_grip_error_m': max(grip_errors, default=0), 'stationary_base': True, 'terminal_hold': clip == 'death', 'motion': motion}
(M/'animation-audit.json').write_text(json.dumps(report, indent=2))
(M/'animation-inputs.json').write_text(json.dumps({n: hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['animate.py', 'retarget.py']}, indent=2))
print('FIVE_CLIPS_READY', {n: v['frames'] for n,v in report.items()})
