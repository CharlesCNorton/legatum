"""Numerical mechanical invariants, independent of Blender."""
import math
import unittest
from runninggear import route

class PanzerTrackTests(unittest.TestCase):
    def setUp(self):
        self.length,self.point=route([(-1.5,.67,.33),(1.5,.67,.33),(-1.15,.51,.24),(1.132,.51,.24)])

    def test_closed_constant_speed_and_forward_tangent(self):
        self.assertEqual(self.point(0),self.point(1))
        for i in range(1000):
            a=self.point(i/1000);b=self.point((i+1)/1000)
            self.assertAlmostEqual(math.dist(a[:2],b[:2]),self.length/1000,delta=self.length/1000*.01)
            p=self.point(i/1000+1e-6);dx,dz=p[0]-a[0],p[1]-a[1]
            self.assertGreater((dx*math.cos(a[2])-dz*math.sin(a[2]))/math.hypot(dx,dz),.99)

    def test_lower_run_moves_backward_for_forward_travel(self):
        samples=[self.point(i/10000) for i in range(10000)]
        bottom=min(p[1] for p in samples)
        self.assertAlmostEqual(bottom,.27,places=6)
        indices=[i for i,p in enumerate(samples) if p[1]<bottom+1e-6]
        self.assertGreater(len(indices),100)
        for i in indices[1:-1]:
            self.assertLess(self.point((i+.1)/10000)[0],samples[i][0])

if __name__=='__main__':unittest.main()
