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
    recovered = positions('hit', 20/30)
    recovery = max(math.dist(original[n],recovered[n]) for n in original)
    errors = []
    if not .10 <= drive <= .18: errors.append('Attack hip drive must be 10-18 cm toward +Z')
    if foot_slide > .003: errors.append('Attack planted ankles slide more than 3 mm')
    if stretch > .001: errors.append('Attack leg lengths change by more than 1 mm')
    if not 4 <= angles.index(max(angles)) <= 6: errors.append('Hit must peak on frame 4-6')
    if not 10 <= max(angles) <= 16: errors.append('Hit torso recoil must be 10-16 degrees')
    if recovery > .001: errors.append('Hit must recover by frame 20')
    return {'valid':not errors, 'attack':{'hip_drive_m':drive,'ankle_horizontal_slide_m':foot_slide,
            'leg_length_variation_m':stretch,'samples_at_120fps':len(samples)},
            'hit':{'peak_torso_degrees':max(angles),'peak_frame':angles.index(max(angles)),
                   'frame_20_recovery_error_m':recovery}, 'errors':errors,
            'limits':'Ankle planting, joint lengths and torso timing; not collisions or browser playback.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('glb',type=Path)
    parser.add_argument('--output',type=Path); args = parser.parse_args()
    result = check(args.glb); raw = json.dumps(result,indent=2); print(raw)
    if args.output: args.output.write_text(raw+'\n')
    raise SystemExit(not result['valid'])
