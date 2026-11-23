"""Unit-owned paths and atlas contract; Blender and Pillow entry points share this."""
import os
import math
from pathlib import Path

SLUG = 'autonomous-armour'
# Closed belt wraps the raised end sprockets and the grounded road tyres.
# All distances use the shoe centerline; its .0535m outer ridge meets stone.
GEAR_X, GEAR_Y = -.25, .08
ROAD_X = [-1.45 + i*.58 for i in range(6)]
SPROCKETS = [(-1.73, .98), (1.73, 1.16)]

def belt(radius, sprocket_radius):
    circles=[(x,.326+radius,radius+.0325) for x in ROAD_X]
    circles += [(x,z,sprocket_radius) for x,z in SPROCKETS]
    points=sorted(set((x+r*math.cos(i*math.tau/128),z+r*math.sin(i*math.tau/128))
                      for x,z,r in circles for i in range(128)))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def half(points):
        result=[]
        for p in points:
            while len(result)>1 and cross(result[-2],result[-1],p)<=0:result.pop()
            result.append(p)
        return result
    polygon=list(reversed(half(points)[:-1]+half(list(reversed(points)))[:-1]))
    segments=[(a,b,math.dist(a,b)) for a,b in zip(polygon,polygon[1:]+polygon[:1])]
    return segments,sum(s[2] for s in segments)

ROAD_RADIUS=.27
TRACK_R=.34
for _ in range(80):
    TRACK_SEGMENTS,TRACK_LENGTH=belt(ROAD_RADIUS,TRACK_R)
    MOVE_TRAVEL=5*TRACK_LENGTH/64
    ROAD_RADIUS=MOVE_TRAVEL/(5*math.pi/6)
    TRACK_R=MOVE_TRAVEL/(2*math.pi/3)
TRACK_SEGMENTS,TRACK_LENGTH=belt(ROAD_RADIUS,TRACK_R)
MOVE_TRAVEL=5*TRACK_LENGTH/64

def trackpoint(t):
    distance=(t%1)*TRACK_LENGTH
    for a,b,length in TRACK_SEGMENTS:
        if distance<=length:
            q=distance/length
            return (GEAR_X+a[0]+q*(b[0]-a[0]),a[1]+q*(b[1]-a[1]),
                    math.atan2(a[1]-b[1],b[0]-a[0]))
        distance-=length
    raise AssertionError('Belt parameter escaped closed path')
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
MASTER = ROOT / 'masters' / SLUG
ASSETS = ROOT / 'assets' / SLUG
REVIEW = ROOT / 'review/3d-v2'
HERE = Path(__file__).resolve().parent
CLIPS = {'idle': (8, 10, True), 'move': (8, 12, True),
         'attack': (10, 14, False), 'hit': (4, 12, False), 'death': (10, 10, False)}
for directory in (MASTER, ASSETS, REVIEW):
    directory.mkdir(parents=True, exist_ok=True)


def log(message):
    with (REVIEW / f'{SLUG}-log.md').open('a') as f:
        f.write(message + '\n')
