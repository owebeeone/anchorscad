

import unittest
from unittest import TestCase
from test_tools import iterable_assert
import anchorscad as ad
import anchorscad.extrude as extrude
from dataclasses import dataclass


TEST_META_DATA = ad.EMPTY_ATTRS.with_fn(10)

class ExtrudeTest(TestCase):
    
    def testColinearRemoveal(self):
        path = (extrude.PathBuilder()
                .move([0, 0])
                .line([10, 0])
                .line([10, 10])
                .line([10, 10]) # duplicate should be removed
                .line([20, 10])
                .line([20, 0])
                .line([0, 0])
                .build())
        
        #path = path.transform(ad.rotZ(45) * ad.translate([1, 1, 0]))
        
        poly = path.polygons(TEST_META_DATA)[0]

        removed = ad.clean_polygons(poly, colinear_remove=True)
        
        iterable_assert(self.assertAlmostEqual, removed,
                        ([10.,  0.],
                          [10.,  10.],
                          [20.,  10.],
                          [20.,  0.]))
    
    def testColinearRemoveal_doubleOverlap(self):
        path = (extrude.PathBuilder()
                .move([10, 0])
                .line([20, 0])
                .line([-10, 0])
                .line([-10, 10])
                .line([10, 10])
                .line([10, 0])
                .line([20, 0])
                .line([10, 0])
                .build())
        
        #path = path.transform(ad.rotZ(45) * ad.translate([1, 1, 0]))
        
        poly = path.polygons(TEST_META_DATA)[0]

        removed = ad.clean_polygons(poly, colinear_remove=False)
        
        iterable_assert(self.assertAlmostEqual, removed,
                        ([10.,  0.],
                        [-10.,  0.],
                        [-10.,  10.],
                        [10.,  10.]))


    def testOverlappingRange(self):
        self.assertEqual(extrude._eval_overlapping_range([1, 5], [4, 8]), (4, 5))
        self.assertEqual(extrude._eval_overlapping_range([5, 1], [8, 4]), (4, 5))
        self.assertEqual(extrude._eval_overlapping_range([1, 5], [6, 8]), None)
        self.assertEqual(extrude._eval_overlapping_range([1, 5], [5, 8], tolerance=0.1), None)
    

if __name__ == "__main__":
    unittest.main()
