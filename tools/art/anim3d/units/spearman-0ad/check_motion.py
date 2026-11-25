"""Check actual skin positions between 30 fps keys; write a review receipt.

This checks ground clearance, not mesh/mesh collisions or aesthetic approval.
"""
import argparse, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB


def check(path):
    g = GLB(path); result = {}; errors = []
    for clip in g.doc['animations']:
        duration = max(g.accessor(s['input'])[-1][0] for s in clip['samplers'])
        count = round(duration*120)
        floor = math.inf; final = None
        for f in range(count+1):
            final = [p for _, p in g.vertices(clip, duration*f/count)]
            floor = min(floor, min(p[1] for p in final))
        result[clip['name']] = {'samples_at_120fps': count+1, 'min_ground_m': floor}
        if floor < -.002: errors.append(f'{clip["name"]}: ground penetration exceeds 2 mm')
        if clip['name'] == 'death':
            regions = g.doc['meshes'][0]['extras']['vertex_regions']
            body = [p for r in regions if r['part'] == 'body' for p in final[r['start']:r['start']+r['count']]]
            result['death']['final_body_ground_m'] = min(p[1] for p in body)
            if abs(result['death']['final_body_ground_m']) > .002:
                errors.append('Death body must rest on ground, not hang from the crest')
            previous = [p for _, p in g.vertices(clip, duration-1/30)]
            result['death']['last_frame_max_motion_m'] = max(math.dist(p,q) for p,q in zip(previous,final))
    return {'valid': not errors, 'clips': result, 'errors': errors,
            'limits': 'Ground clearance only; no mesh/mesh collision or browser pixel claim.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('glb', type=Path); p.add_argument('--output', type=Path)
    args = p.parse_args(); result = check(args.glb); raw = json.dumps(result, indent=2)
    print(raw)
    if args.output: args.output.write_text(raw+'\n')
    raise SystemExit(0 if result['valid'] else 1)
