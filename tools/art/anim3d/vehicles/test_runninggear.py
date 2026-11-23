"""Mechanical belt invariants independent of Blender/rendering."""
import math
import unittest
from runninggear import route


class BeltTests(unittest.TestCase):
    def test_stadium_length_and_closed_seam(self):
        length,point=route([(-1.39,.79,.4),(1.39,.79,.4)])
        self.assertAlmostEqual(length,5.56+math.tau*.4,places=3)
        self.assertEqual(point(0),point(1))
        self.assertLess(math.dist(point(-1e-7)[:2],point(1e-7)[:2]),length*3e-7)

    def test_raised_sprockets_keep_planted_run(self):
        length,point=route([(-1.7,1.05,.31),(-1.05,.64,.25),(1.1,.64,.25),(1.65,1.14,.34)])
        samples=[point(i/10000) for i in range(10000)]
        self.assertAlmostEqual(min(p[1] for p in samples),.39,places=5)
        # Constant path speed even through the circular ends (chord error <1%).
        distances=[math.dist(a[:2],b[:2]) for a,b in zip(samples,samples[1:])]
        self.assertGreater(min(distances),length/10000*.99)
        self.assertLessEqual(max(distances),length/10000*1.001)

    def test_shoe_axis_follows_tangent(self):
        _,point=route([(-1,.8,.4),(1,.9,.35)])
        for i in range(100):
            t=i/100;before=point(t-1e-6);after=point(t+1e-6);_,_,angle=point(t)
            dx,dz=after[0]-before[0],after[1]-before[1]
            tangent=(math.cos(angle),-math.sin(angle))
            self.assertGreater((dx*tangent[0]+dz*tangent[1])/math.hypot(dx,dz),.999)


if __name__=='__main__':unittest.main()
