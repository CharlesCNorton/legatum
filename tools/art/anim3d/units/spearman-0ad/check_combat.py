"""Check exported attack planting/drive and hit timing; no aesthetic approval."""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB


def check(path):
    g = GLB(path)
    nodes = {n['name']: i for i, n in enumerate(g.doc['nodes']) if 'name' in n}
    clips = {a['name']: a for a in g.doc['animations']}
    def positions(clip, time):
        worlds = g.worlds(clips[clip], time)
        return {n: worlds[i][12:15] for n, i in nodes.items()}
    initial = positions('attack', 0)
    samples = [positions('attack', i/120) for i in range(141)]
    foot_slide = max(math.hypot(p[n][0]-initial[n][0], p[n][2]-initial[n][2])
                     for p in samples for n in ['foot_L','foot_R'])
    drive = max(p['hip'][2]-initial['hip'][2] for p in samples)
    stretch = max(abs(math.dist(p[a+s],p[b+s])-math.dist(initial[a+s],initial[b+s]))
                  for p in samples for s in ['_L','_R'] for a,b in [('thigh','leg'),('leg','foot')])
    def torso(p):
        v = [a-b for a,b in zip(p['chest'],p['spine'])]
        length = math.sqrt(sum(x*x for x in v))
        return [x/length for x in v]
    original = positions('hit', 0); vector = torso(original)
    angles = [math.degrees(math.acos(max(-1,min(1,sum(a*b for a,b in zip(vector,torso(positions('hit',f/30))))))))
              for f in range(25)]
    recovered = positions('hit', 24/30)
    idle = positions('idle', 0)
    recovery = max(math.dist(idle[n],recovered[n]) for n in idle)
    hit_samples = [positions('hit', f/30) for f in range(25)]
    back = max(original['hip'][2]-p['hip'][2] for p in hit_samples)
    drop = max(original['hip'][1]-p['hip'][1] for p in hit_samples)
    step = hit_samples[4]['foot_L'][2]-hit_samples[8]['foot_L'][2]
    root_motion = max(math.dist(original['Spearman'],p['Spearman']) for p in hit_samples)
    root_matrix_error = max(abs(a-b) for f in range(25)
                            for a,b in zip(g.worlds(clips['hit'],f/30)[nodes['Spearman']],
                                           g.worlds(clips['idle'],0)[nodes['Spearman']]))
    endpoint_error = max(abs(a-b) for n in nodes.values()
                         for a,b in zip(g.worlds(clips['hit'],.8)[n],g.worlds(clips['idle'],0)[n]))
    def local_angle(name, frame):
        c = next(c for c in clips['hit']['channels'] if c['target'] == {'node':nodes[name],'path':'rotation'})
        values = g.accessor(clips['hit']['samplers'][c['sampler']]['output'])
        q,r = values[0],values[frame]
        dot = abs(sum(a*b for a,b in zip(q,r)))/math.sqrt(sum(a*a for a in q)*sum(b*b for b in r))
        return math.degrees(2*math.acos(min(1,dot)))
    bend = local_angle('spine',4)+local_angle('chest',4)
    neck_angles = [local_angle('neck',f) for f in range(25)]
    idle_keys = {(c['target']['node'],c['target']['path']):
                 g.accessor(clips['idle']['samplers'][c['sampler']]['output'])[0]
                 for c in clips['idle']['channels']}
    exact_endpoints = 0
    for c in clips['hit']['channels']:
        values = g.accessor(clips['hit']['samplers'][c['sampler']]['output'])
        expected = idle_keys[(c['target']['node'],c['target']['path'])]
        exact_endpoints += values[0] == values[-1] == expected
    errors = []
    if not .10 <= drive <= .18: errors.append('Attack hip drive must be 10-18 cm toward +Z')
    if foot_slide > .003: errors.append('Attack planted ankles slide more than 3 mm')
    if stretch > .001: errors.append('Attack leg lengths change by more than 1 mm')
    if not 4 <= angles.index(max(angles)) <= 6: errors.append('Hit must peak on frame 4-6')
    if not 20 <= bend <= 25.1: errors.append('Hit spine/chest recoil must total 20-25 degrees')
    if not .12 <= back <= .151: errors.append('Hit pelvis must recoil 12-15 cm')
    if not .045 <= drop <= .07: errors.append('Hit pelvis must visibly drop about 5 cm')
    if not .12 <= step <= .18: errors.append('Rear foot must catch the weight during frames 4-8')
    if root_motion > 1e-7 or root_matrix_error > 1e-7: errors.append('Hit root must remain fixed')
    if recovery > 1e-7 or endpoint_error > 1e-7: errors.append('Hit frame 24 must exactly match idle frame zero')
    if neck_angles.index(max(neck_angles)) != 5: errors.append('Neck recoil must peak one frame after torso')
    if exact_endpoints != len(clips['hit']['channels']): errors.append('Every hit endpoint key must equal idle zero exactly')
    return {'valid':not errors, 'attack':{'hip_drive_m':drive,'ankle_horizontal_slide_m':foot_slide,
            'leg_length_variation_m':stretch,'samples_at_120fps':len(samples)},
            'hit':{'peak_torso_degrees':max(angles),'peak_frame':angles.index(max(angles)),
                   'spine_chest_bend_degrees':bend,'pelvis_back_m':back,'pelvis_drop_m':drop,
                   'rear_foot_step_m':step,'root_motion_m':root_motion,'root_matrix_error':root_matrix_error,
                   'neck_peak_frame':neck_angles.index(max(neck_angles)),
                   'exact_idle_endpoint_channels':exact_endpoints,
                   'frame_24_recovery_error_m':recovery,'frame_24_idle_matrix_error':endpoint_error}, 'errors':errors,
            'limits':'Ankle planting, joint lengths and torso timing; not collisions or browser playback.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('glb',type=Path)
    parser.add_argument('--output',type=Path); args = parser.parse_args()
    result = check(args.glb); raw = json.dumps(result,indent=2); print(raw)
    if args.output: args.output.write_text(raw+'\n')
    raise SystemExit(not result['valid'])
