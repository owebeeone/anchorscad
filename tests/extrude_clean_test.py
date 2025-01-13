

import unittest
from unittest import TestCase
from anchorscad_lib.test_tools import iterable_assert
import anchorscad as ad
import anchorscad.extrude as extrude


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
    

    def test_remove_negx(self):
        transitions = 3
        q = 1
        pathBuilder = (extrude.PathBuilder(path_modifier=extrude.PathModifier(trim_negx=True))
                .move([-10, 0])
                .line([20, 0 + q])
                .line([20, 10 * (transitions + 1) + q])
                .line([-10, 10 * (transitions + 1)]))
        
        for i in range(transitions, 0, -1):
            pathBuilder.line([-10, 10 * i])
            pathBuilder.line([10, 10 * i + q])
            pathBuilder.line([10, 10 * i - 5 + q])
            pathBuilder.line([-10, 10 * i - 5])
            
        pathBuilder.line([-10, 0])

        path = pathBuilder.build()
        
        poly = path.cleaned_polygons(TEST_META_DATA)[0]
        
        iterable_assert(self.assertAlmostEqual5, poly,
                        ([20.       ,  1.       ],
                         [20.       , 41.       ],
                         [ 0.       , 40.333332 ],
                         [ 0.       , 30.5      ],
                         [10.       , 31.       ],
                         [10.       , 26.       ],
                         [ 0.       , 25.5      ],
                         [ 0.       , 20.5      ],
                         [10.       , 21.       ],
                         [10.       , 16.       ],
                         [ 0.       , 15.5      ],
                         [ 0.       , 10.5      ],
                         [10.       , 11.       ],
                         [10.       ,  6.       ],
                         [ 0.       ,  5.5      ],
                         [ 0.       ,  0.3333333]))
        
    def test_remove_negx2(self):
        transitions = 3
        q = 1
        pathBuilder = (extrude.PathBuilder(path_modifier=extrude.PathModifier(trim_negx=True))
                .move([10, 0])
                .line([-20, 0 + q])
                .line([-20, 10 * (transitions + 1) + q])
                .line([10, 10 * (transitions + 1)]))
        
        for i in range(transitions, 0, -1):
            pathBuilder.line([10, 10 * i])
            pathBuilder.line([-10, 10 * i + q])
            pathBuilder.line([-10, 10 * i - 5 + q])
            pathBuilder.line([10, 10 * i - 5])
            
        pathBuilder.line([10, 0])

        path = pathBuilder.build()
        
        poly = path.cleaned_polygons(TEST_META_DATA)
        
        iterable_assert(self.assertAlmostEqual5, poly,
                        [[[10.      , 40.      ],
                          [ 0.      , 40.333332],
                          [ 0.      , 30.5     ],
                          [10.      , 30.      ]], 
                         [[10. , 25. ],
                          [ 0. , 25.5],
                          [ 0. , 20.5],
                          [10. , 20. ]], 
                         [[10. , 15. ],
                          [ 0. , 15.5],
                          [ 0. , 10.5],
                          [10. , 10. ]], 
                         [[10.       ,  5.       ],
                          [ 0.       ,  5.5      ],
                          [ 0.       ,  0.3333333],
                          [10.       ,  0.       ]]])
        
    def assertAlmostEqual6(self, a, b):
        self.assertAlmostEqual(a, b, places=6)
        
    def assertAlmostEqual5(self, a, b):
        self.assertAlmostEqual(a, b, places=5)
        
if __name__ == "__main__":
    unittest.main()
