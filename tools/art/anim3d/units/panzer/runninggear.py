"""Closed belt around the registered end sprockets and road-wheel contact run.

The hull is a convex envelope of circles in the physical X/Z plane. Sampling by
arc length keeps every separate shoe moving at constant mechanical speed.
"""
import bisect
import math


def route(circles):
    points = sorted((x + r*math.cos(i*math.tau/192), z + r*math.sin(i*math.tau/192))
                    for x,z,r in circles for i in range(192))
    def cross(o,a,b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[];upper=[]
    for seq,half in ((points,lower),(reversed(points),upper)):
        for p in seq:
            while len(half)>1 and cross(half[-2],half[-1],p)<=0:half.pop()
            half.append(p)
    # Clockwise: top run travels toward the panzer's nose.
    ring=list(reversed(lower[:-1]+upper[:-1]))
    start=max(range(len(ring)),key=lambda i:ring[i][1])
    ring=ring[start:]+ring[:start];ring.append(ring[0])
    lengths=[0.]
    for a,b in zip(ring,ring[1:]):lengths.append(lengths[-1]+math.dist(a,b))
    def point(t):
        distance=(t%1)*lengths[-1]
        i=min(len(ring)-2,bisect.bisect_right(lengths,distance)-1)
        a,b=ring[i:i+2];f=(distance-lengths[i])/(lengths[i+1]-lengths[i])
        return (a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1]),-math.atan2(b[1]-a[1],b[0]-a[0]))
    return lengths[-1],point
