"""Measure inter-drone triangle intersections in all sampled mechanical poses."""
import bpy
import hashlib
import json
import os
from pathlib import Path
from mathutils.bvhtree import BVHTree

M = Path(os.environ['ANIM_ROOT']) / 'masters/drone-swarm'


def tree(root):
    vertices, faces, owners = [], [], []
    for ob in root.children_recursive:
        if ob.type != 'MESH':
            continue
        offset = len(vertices)
        vertices.extend(ob.matrix_world @ v.co for v in ob.data.vertices)
        faces.extend(tuple(i + offset for i in p.vertices) for p in ob.data.polygons)
        owners.extend([ob.name] * len(ob.data.polygons))
    return BVHTree.FromPolygons(vertices, faces), owners


reports = []
master_sha = hashlib.sha256((M / 'drone-swarm.blend').read_bytes()).hexdigest()
for clip, n in [('idle', 8), ('move', 8), ('attack', 10), ('hit', 4), ('death', 10)]:
    bpy.ops.wm.open_mainfile(filepath=str(M / (clip + '.blend')))
    assert bpy.context.scene.get('source_master_sha256') == master_sha, 'Stale clip: ' + clip
    roots = [bpy.data.objects['RIG-drone' + str(i)] for i in (1, 2, 3)]
    for frame in range(1, n + 1):
        bpy.context.scene.frame_set(frame)
        trees = [tree(root) for root in roots]
        for a, b in ((0, 1), (0, 2), (1, 2)):
            pairs = trees[a][0].overlap(trees[b][0])
            intersections = len(pairs)
            if intersections:
                reports.append({'clip': clip, 'frame': frame, 'pair': [a + 1, b + 1],
                                'triangle_intersections': intersections,
                                'objects': sorted({(trees[a][1][i], trees[b][1][j]) for i, j in pairs})})
(M / 'collisions.json').write_text(json.dumps({
    'status': 'fail' if reports else 'pass', 'frames': 40,
    'master_sha256': master_sha, 'intersections': reports}, indent=2) + '\n')
print(json.dumps(reports, indent=2))
assert not reports, 'Inter-drone surfaces intersect; see collisions.json'
