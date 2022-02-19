'''
Created on 5 Feb 2021

@author: gianni
'''


from dataclasses import dataclass
import unittest

import ParametricSolid.core as core
import ParametricSolid.extrude as extrude
import ParametricSolid.linear as l
from ParametricSolid.renderer import render
from ParametricSolid.test_tools import iterable_assert
import numpy as np


@dataclass
class TestMetaData:
    fn: int=10


class ExtrudeTest2(unittest.TestCase):
    
        
    def makeArcPointsPath(self, start_angle, middle_angle, end_angle):
        r = 10
        offset = np.array([5, 5])
        angles = np.array([start_angle, middle_angle, end_angle]) / 180 * np.pi
        points_t = np.array([np.cos(angles), np.sin(angles)]) * r
        points = np.transpose(points_t)
        return (extrude.PathBuilder()
            .move(offset)
            .line(points[0] + offset, 'edge1')
            .arc_points(points[1] + offset, points[2] + offset, name='arc')
            .line(offset, 'edge2')
            .build())

    def testArcPoints_4(self):
        test_angles = ((190, 170, 270), (190, 185, 270))
        test_angles = ((190, 185, 270),)
        for angles in test_angles:
            path = self.makeArcPointsPath(*angles)
            
            iterable_assert(self.assertAlmostEqual, path.polygons(TestMetaData()),
                            ([[ 5.        ,  5.        ],
                               [-4.84807753,  3.26351822],
                               [-4.51056516,  8.09016994],
                               [-1.9465837 , 12.193398  ],
                               [ 2.24362644, 14.61261696],
                               [ 7.07911691, 14.78147601],
                               [11.4278761 , 12.66044443],
                               [14.27183855,  8.74606593],
                               [14.94521895,  3.95471537],
                               [13.29037573, -0.59192903],
                               [ 9.69471563, -3.82947593],
                               [ 5.        , -5.        ],
                               [ 5.        ,  5.        ]],))  

    def testArcTangentPoint_2(self):
        r_bevel = 5
        r_sphere = 15
        sin_t = r_bevel / (r_sphere + r_bevel)
        cos_t = np.sqrt(1 - sin_t ** 2)
        p1 = [cos_t * r_sphere, -sin_t * r_sphere]
        p2 = [cos_t * (r_sphere + r_bevel), 0]
        
        path = (extrude.PathBuilder()
            .move([0, 0])
            .line([0, -r_sphere], 'edge1')
            .arc_tangent_point(p1, degrees=90, name='sphere')
            .arc_tangent_point(p2, degrees=0, name='bevel')
            .line([0, 0], 'edge2')
            .build())
        
        iterable_assert(self.assertAlmostEqual, path.polygons(TestMetaData()),
                        ([[ 0.00000000e+00,  0.00000000e+00],
                           [ 0.00000000e+00, -1.50000000e+01],
                           [ 1.97145374e+00, -1.48698813e+01],
                           [ 3.90870442e+00, -1.44817827e+01],
                           [ 5.77814237e+00, -1.38424373e+01],
                           [ 7.54733440e+00, -1.29629373e+01],
                           [ 9.18558654e+00, -1.18585412e+01],
                           [ 1.06644765e+01, -1.05484094e+01],
                           [ 1.19583467e+01, -9.05527162e+00],
                           [ 1.30447497e+01, -7.40503245e+00],
                           [ 1.39048372e+01, -5.62632221e+00],
                           [ 1.45236875e+01, -3.75000000e+00],
                           [ 1.47299710e+01, -3.12455926e+00],
                           [ 1.50166668e+01, -2.53165585e+00],
                           [ 1.53788012e+01, -1.98157613e+00],
                           [ 1.58100912e+01, -1.48386352e+00],
                           [ 1.63030546e+01, -1.04715292e+00],
                           [ 1.68491386e+01, -6.79020900e-01],
                           [ 1.74388693e+01, -3.85854229e-01],
                           [ 1.80620153e+01, -1.72739105e-01],
                           [ 1.87077655e+01, -4.33728971e-02],
                           [ 1.93649167e+01,  2.66453526e-15],
                           [ 0.00000000e+00,  0.00000000e+00]],))
        
    def test_stroke(self):
        path = (extrude.PathBuilder()
            .move([0, 0], direction=[0, -1])
            .stroke(2, degrees=-120, name='stoke1')
            .stroke(2, degrees=-120, name='stoke2')
            .stroke(2, degrees=-120, name='stoke3')
            .build())

        iterable_assert(self.assertAlmostEqual, path.polygons(TestMetaData()),
                        ([[ 0.00000000e+00,  0.00000000e+00],
                          [-1.73205081e+00,  1.00000000e+00],
                          [-6.66133815e-16,  2.00000000e+00],
                          [ 7.77156117e-16,  6.66133815e-16]],))
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()