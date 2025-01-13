'''
Created on 8 Jan 2021

@author: gianni
'''

import os
from anchorscad.extrude_flex import make_offset_polygon2d, PathOffsetMaker
from anchorscad.runner import compare_generated
import anchorscad.svg_renderer as sr
import numpy as np
from anchorscad_lib.test_tools import iterable_assert
from anchorscad.renderer import render
import anchorscad_lib.linear as l
import anchorscad.extrude as extrude
import unittest
from unittest import TestCase
from dataclasses import dataclass
import anchorscad.renderer as renderer
import anchorscad.graph_model as gm
import anchorscad.core as core


@dataclass
class MockMetaData:
    fn: int = 10
    segment_lines: bool = False

UPDATE_GOLDEN_FILES = os.getenv('UPDATE_GOLDEN_FILES')

class ExtrudeTest(TestCase):
    
    def setUp(self):
        self.points = []
        # Golden files are stored in 'test-data' directory next to the test file
        self.golden_dir = os.path.join(os.path.dirname(__file__), 'test-data')
        self.update_golden_files = UPDATE_GOLDEN_FILES
        self.verbose = False
        
    def log_verbose(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def write(self, maker, test):
        result = render(maker)
        filename = f'test_{test}.scad'
        self.log_verbose(f'testing scad file: {filename}')
        
        scad_output = str(result.rendered_shape)
        
        self.compare_scad_with_golden(filename, scad_output)
        
    def compare_scad_with_golden(self, filename, scad_output: str):
        
        if self.update_golden_files:
            with open(os.path.join(self.golden_dir, filename), 'w') as f:
                f.write(scad_output)
            return
        
        # Load them into a list of lines
        with open(os.path.join(self.golden_dir, filename), 'r') as f:
            golden_lines = f.readlines()[:-1]
        
        # Convert the scad output to a list of lines, explicitly keeping newlines
        actual_lines = scad_output.splitlines(keepends=True) # remove the last empty line
            
        difference : compare_generated.FileDifference = compare_generated.compare_scad_lines(
            golden_lines, actual_lines)   
        if difference:
            self.fail(f'Difference found in {filename}: {difference}')    
            
    def compare_with_golden(self, filename, actual_output):
        golden_path = os.path.join(self.golden_dir, filename)
        if self.update_golden_files:
            # Update golden files if environment variable is set
            os.makedirs(os.path.dirname(golden_path), exist_ok=True)
            with open(golden_path, 'w') as f:
                f.write(actual_output)
        else:
            # Compare with existing golden file
            try:
                with open(golden_path, 'r') as f:
                    expected_output = f.read()
                self.assertEqual(expected_output, actual_output)
            except FileNotFoundError:
                self.fail(f"Golden file {golden_path} not found. Run with UPDATE_GOLDEN=1 to create it.")
        

    def testBezierExtents2D(self):
        b = extrude.CubicSpline([[0, 0], [1, -1], [1, 1], [0, 1]])
        iterable_assert(self.assertAlmostEqual, b.extents(),
                        [[0., -0.28], [0.75, 1]])
        minima = b.curve_maxima_minima_t()
        normal = b.normal2d(minima[0][0])
        self.assertAlmostEqual(normal[0], -1, 5)

    def testPathGenerator(self):
        builder = extrude.PathBuilder()
        builder.move([0, 0], 'start').spline(
            [[1, -1], [1, 1], [0, 1]], 'curve')

        path = builder.build()
        points = path.points(MockMetaData())

        expected = np.array([
            [0.,  0.],
            [0.27, -0.215],
            [0.48, -0.28],
            [0.63, -0.225],
            [0.72, -0.08],
            [0.75,  0.125],
            [0.72,  0.36],
            [0.63,  0.595],
            [0.48,  0.8],
            [0.27,  0.945],
            [0.,  1.]])

        iterable_assert(self.assertAlmostEqual, expected, points)

        node = path.get_node('curve')
        assert node is not None

        iterable_assert(self.assertAlmostEqual, node.extents(),
                        [[0., -0.28], [0.75, 1]])

    def testDirection(self):
        builder = extrude.PathBuilder()
        builder.move([0, 0], 'start'
                     ).line([1, 0], 'line'
                            ).spline([[2, 0], [2.5, 4], [3, 3]], 'curve')

        path = builder.build()
        points = path.points(MockMetaData())

        expected = np.array([
            [0., 0.],
            [1., 0.],
            [1.2855, 0.111],
            [1.544, 0.408],
            [1.7785, 0.837],
            [1.992, 1.344],
            [2.1875, 1.875],
            [2.368, 2.376],
            [2.5365, 2.793],
            [2.696, 3.072],
            [2.8495, 3.159],
            [3., 3.]])

        iterable_assert(self.assertAlmostEqual, expected, points)

        curve = path.get_node('curve')
        line = path.get_node('line')

        iterable_assert(self.assertAlmostEqual,
                        line.direction_normalized(1),
                        curve.direction_normalized(0))

        iterable_assert(self.assertAlmostEqual,
                        [[0, 0], [3, 3.16049383]],
                        path.extents())

    def testPreviousDirection(self):
        builder = extrude.PathBuilder()
        builder.move([0, 0], 'start'
                     ).line([1, 0], 'line'
                            ).spline([[2.5, 4], [3, 3]], 'curve', cv_len=(0.5,))

        path = builder.build()
        points = path.points(MockMetaData())

        iterable_assert(self.assertAlmostEqual,
                        path.get_node('curve').points,
                        np.array([[1.5, 0.],
                                  [2.5, 4.],
                                  [3., 3.]]))
        expected = np.array([
            [0., 0.],
            [1., 0.],
            [1.164, 0.111],
            [1.352, 0.408],
            [1.558, 0.837],
            [1.776, 1.344],
            [2., 1.875],
            [2.224, 2.376],
            [2.442, 2.793],
            [2.648, 3.072],
            [2.836, 3.159],
            [3., 3.]])

        iterable_assert(self.assertAlmostEqual, expected, points)

    def testPreviousDirectionFirstAngle(self):
        builder = extrude.PathBuilder()

        builder.move([0, 0], 'start'
                     ).line([1, 0], 'line'
                            ).spline([[2.5, 4], [3, 3]], 'curve', cv_len=(0.5,), angle=(90,))

        path = builder.build()
        points = path.points(MockMetaData())

        iterable_assert(self.assertAlmostEqual,
                        path.get_node('curve').points,
                        np.array([[1, 0.5],
                                  [2.5, 4.],
                                  [3., 3.]]))
        expected = np.array([
            [0., 0.],
            [1., 0.],
            [1.0425, 0.2325],
            [1.16, 0.6],
            [1.3375, 1.0575],
            [1.56, 1.56],
            [1.8125, 2.0625],
            [2.08, 2.52],
            [2.3475, 2.8875],
            [2.6, 3.12],
            [2.8225, 3.1725],
            [3., 3.]])

        iterable_assert(self.assertAlmostEqual, expected, points)

    def testPreviousDirectionSecondAngle(self):
        builder = extrude.PathBuilder()
        builder.move([0, 0], 'start'
                     ).line([1, 0], 'line'
                            ).spline([[2.5, 4], [3, 3]], 'curve', cv_len=(0.5,), angle=(None, -90))

        path = builder.build()

        iterable_assert(self.assertAlmostEqual,
                        path.get_node('curve').points,
                        np.array([[1.5, 0.],
                                  [4., 3.5],
                                  [3., 3.]]))

    def testPreviousDirectionSecondRelative(self):
        builder = extrude.PathBuilder()
        builder.move([0, 0], 'start'
                     ).line([1, 0], 'line'
                            ).spline([[2.5, 4], [3, 3]], 'curve', cv_len=(0.5,), rel_len=0.5)

        path = builder.build()

        iterable_assert(self.assertAlmostEqual,
                        path.get_node('curve').points,
                        np.array([[1.90138782, 0.],
                                  [2.19377423, 4.61245155],
                                  [3., 3.]]))

    def testPolygonMultiplePoltygons(self):
        builder = extrude.PathBuilder(multi=True)
        builder.move([0, 0], 'start'
                     ).line([1, 0], 'line'
                            ).spline([[2.5, 4], [3, 3]], 'curve', cv_len=(0.5,), rel_len=0.5
                                     ).move([1, 0]
                                            ).line([2, 0]
                                                   ).line([2, 1]
                                                          ).line([1, 2])

        path = builder.build()

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        (([[0., 0.],
                           [1., 0.],
                           [1.25326914, 0.12753619],
                           [1.47673525, 0.46679535],
                           [1.67713536, 0.95275334],
                           [1.86120651, 1.52038605],
                           [2.03568577, 2.10466933],
                           [2.20731016, 2.64057907],
                           [2.38281673, 3.06309113],
                           [2.56894253, 3.3071814],
                           [2.77242461, 3.30782573],
                           [3., 3.],
                           [1., 0.],
                           [2., 0.],
                           [2., 1.],
                           [1., 2.]]),
                         ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0),
                            (12, 13, 14, 15, 12))))

        # Try rotating the path.
        new_path = path.transform(l.rotZ(90))

        iterable_assert(self.assertAlmostEqual, new_path.polygons(MockMetaData()),
                        (([[0.,  0.],
                           [0.,  1.],
                           [-0.12753619,  1.25326914],
                           [-0.46679535,  1.47673525],
                           [-0.95275334,  1.67713536],
                           [-1.52038605,  1.86120651],
                           [-2.10466933,  2.03568577],
                           [-2.64057907,  2.20731016],
                           [-3.06309113,  2.38281673],
                           [-3.3071814,  2.56894253],
                           [-3.30782573,  2.77242461],
                           [-3.,  3.],
                           [0.,  1.],
                           [0.,  2.],
                           [-1.,  2.],
                           [-2.,  1.]]),
                         ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0),
                            (12, 13, 14, 15, 12))))

    def makeTestObject_s1(self, scale=1):
        return extrude.LinearExtrude(
            extrude.PathBuilder()
            .move([0, 0])
            .line([100 * scale, 0], 'linear')
            .spline([[150 * scale, 100 * scale], [20 * scale, 100 * scale]],
                    name='curve', cv_len=(0.5, 0.4), angle=(90,), rel_len=0.8)
            .line([0, 100 * scale], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
            h=40,
            fn=30,
            twist=90,
            scale=(1, 0.3)
        )

    def makeTestObject(self, scale=1):
        return extrude.LinearExtrude(
            extrude.PathBuilder()
            .move([0, 0])
            .line([100 * scale, 0], 'linear')
            .spline([[0,  100 * scale], [0, 100 * scale]],
                    name='curve', cv_len=(0.5, 0.4), angle=(100,), rel_len=0.8)
            .line([0, 1 * scale], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
            h=40,
            fn=30,
            twist=90,
            scale=(1, 0.3)
        )

    def testLinearExtrude(self):
        le = self.makeTestObject()
        iterable_assert(self.assertAlmostEqual, le.at('linear', 0.5).A,
                        [[1.,  0.,  0., 50.],
                         [0.,  0., -1.,  0.],
                         [0.,  1.,  0.,  0.],
                         [0.,  0.,  0.,  1.]])

    def test_find_a_b_c_from_point_tangent(self):
        d, p, t = extrude.find_a_b_c_from_point_tangent([10, 0], [-20, 20])
        expect_0 = d[0] * p[0] + d[1] * p[1] - d[2]
        self.assertAlmostEqual(expect_0, 0)
        k = 1
        expect_0 = d[0] * (p[0] + k * t[0]) + d[1] * (p[1] + k * t[1]) - d[2]
        self.assertAlmostEqual(expect_0, 0)
        k = -1
        expect_0 = d[0] * (p[0] + k * t[0]) + d[1] * (p[1] + k * t[1]) - d[2]
        self.assertAlmostEqual(expect_0, 0)

    def test_solve_circle_tangent_point(self):
        c, r = extrude.solve_circle_tangent_point([10, 0], [20, 20], [10, 10])
        iterable_assert(self.assertAlmostEqual, c, [5, 5])
        self.assertAlmostEqual(r, 7.0710678118654755)

        c, r = extrude.solve_circle_tangent_point([10, 0], [20, 20], [0, 10])
        iterable_assert(self.assertAlmostEqual, c, [5, 5])
        self.assertAlmostEqual(r, 7.0710678118654755)

        c, r = extrude.solve_circle_tangent_point([10, 0], [10, 10], [0, 0])
        iterable_assert(self.assertAlmostEqual, c, [5, 5])
        self.assertAlmostEqual(r, 7.0710678118654755)

    def makeArcLinearTestObject(self, scale=1):
        return extrude.LinearExtrude(
            extrude.PathBuilder()
            .move([0, 0])
            .line([100 * scale, 0], 'linear')
            .arc_tangent_point([20 * scale, 100 * scale],
                               name='arc', angle=90)
            .line([0, 100 * scale], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
            h=40,
            fn=30,
            twist=0,
            scale=(1, 1)
        )

    def testArcLinearTestObject(self):
        le = self.makeArcLinearTestObject()
        self.write(le, 'ArcLinear')
        iterable_assert(self.assertAlmostEqual, le.at('linear', 0.5).A,
                        [[1.,  0.,  0., 50.],
                         [0.,  0., -1.,  0.],
                         [0.,  1.,  0.,  0.],
                         [0.,  0.,  0.,  1.]])

    def makeArcArcExtrudeTestObject(self, scale=1):
        return extrude.RotateExtrude(
            extrude.PathBuilder()
            .move([0, 0])
            .line([100 * scale, 0], 'linear')
            .arc_tangent_point([20 * scale, 100 * scale],
                               name='arc', angle=90)
            .line([0, 100 * scale], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
            angle=90
        )

    def testArcArcExtrudeTestObject(self):
        le = self.makeArcArcExtrudeTestObject()
        self.write(le, 'ArcRotate')
        iterable_assert(self.assertAlmostEqual, le.at('linear', 0.5).A,
                        [[0.,  1.,  0., 50.],
                         [1.,  0.,  0.,  0.],
                         [0.,  0., -1.,  0.],
                         [0.,  0.,  0.,  1.]])

    def testArcTangentPoint(self):
        SCALE = 0.8

        path = (extrude.PathBuilder()
                .move([0, 0])
                .line([100 * SCALE, 0], 'linear')
                .arc_tangent_point([0 * SCALE, 100 * SCALE], name='curve', angle=90)
                .line([0, 100 * SCALE], 'linear2')
                .line([0, 0], 'linear3')
                .build())

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.,  0.],
                          [80.,  0.],
                          [79.01506725, 12.5147572],
                          [76.0845213, 24.72135955],
                          [71.28052194, 36.31923998],
                          [64.72135955, 47.02282018],
                          [56.56854249, 56.56854249],
                          [47.02282018, 64.72135955],
                          [36.31923998, 71.28052194],
                          [24.72135955, 76.0845213],
                          [12.5147572, 79.01506725],
                          [0., 80.],
                          [0., 80.],
                          [0.,  0.]],))

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
                .arc_tangent_point(p1, angle=90, name='sphere')
                .arc_tangent_point(p2, angle=0, name='bevel')
                .line([0, 0], 'edge2')
                .build())

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.00000000e+00,  0.00000000e+00],
                          [0.00000000e+00, -1.50000000e+01],
                          [1.97145374e+00, -1.48698813e+01],
                          [3.90870442e+00, -1.44817827e+01],
                          [5.77814237e+00, -1.38424373e+01],
                          [7.54733440e+00, -1.29629373e+01],
                          [9.18558654e+00, -1.18585412e+01],
                          [1.06644765e+01, -1.05484094e+01],
                          [1.19583467e+01, -9.05527162e+00],
                          [1.30447497e+01, -7.40503245e+00],
                          [1.39048372e+01, -5.62632221e+00],
                          [1.45236875e+01, -3.75000000e+00],
                          [1.47299710e+01, -3.12455926e+00],
                          [1.50166668e+01, -2.53165585e+00],
                          [1.53788012e+01, -1.98157613e+00],
                          [1.58100912e+01, -1.48386352e+00],
                          [1.63030546e+01, -1.04715292e+00],
                          [1.68491386e+01, -6.79020900e-01],
                          [1.74388693e+01, -3.85854229e-01],
                          [1.80620153e+01, -1.72739105e-01],
                          [1.87077655e+01, -4.33728971e-02],
                          [1.93649167e+01,  2.66453526e-15],
                          [0.00000000e+00,  0.00000000e+00]],))

    def testArcTangentPoint_3(self):
        r_bevel = 10

        path = (extrude.PathBuilder()
                .move([0, 0])
                .line([0, -r_bevel], 'edge1')
                .arc_tangent_point([r_bevel, 0], angle=180, name='bevel')
                .line([0, 0], 'edge2')
                .build())

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.,   0.],
                          [0., -10.],
                          [0.12311659,  -8.43565535],
                          [0.48943484,  -6.90983006],
                          [1.08993476,  -5.460095],
                          [1.90983006,  -4.12214748],
                          [2.92893219,  -2.92893219],
                          [4.12214748,  -1.90983006],
                          [5.460095,  -1.08993476],
                          [6.90983006,  -0.48943484],
                          [8.43565535,  -0.12311659],
                          [10.,   0.],
                          [0.,   0.]],))

    def testArcTangentPoint_4(self):
        r = 10

        path = (extrude.PathBuilder()
                .move([0, 0])
                .line([0, r], 'edge1')
                .arc_tangent_point([0, -r], angle=-90, name='arc')
                .line([0, 0], 'edge2')
                .build())

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.00000000e+00,  0.00000000e+00],
                          [0.00000000e+00,  1.00000000e+01],
                          [3.09016994e+00,  9.51056516e+00],
                          [5.87785252e+00,  8.09016994e+00],
                          [8.09016994e+00,  5.87785252e+00],
                          [9.51056516e+00,  3.09016994e+00],
                          [1.00000000e+01,  0.00000000e+00],
                          [9.51056516e+00, -3.09016994e+00],
                          [8.09016994e+00, -5.87785252e+00],
                          [5.87785252e+00, -8.09016994e+00],
                          [3.09016994e+00, -9.51056516e+00],
                          [6.12323400e-16, -1.00000000e+01],
                          [0.00000000e+00,  0.00000000e+00]],))

    def testArcTangentPoint_5(self):
        r = 10

        path = (extrude.PathBuilder()
                .move([0, 0])
                .line([0, r], 'edge1')
                .arc_tangent_point([0, -r], angle=90, name='arc')
                .line([0, 0], 'edge2')
                .build())

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.00000000e+00,  0.00000000e+00],
                          [0.00000000e+00,  1.00000000e+01],
                          [-3.09016994e+00,  9.51056516e+00],
                          [-5.87785252e+00,  8.09016994e+00],
                          [-8.09016994e+00,  5.87785252e+00],
                          [-9.51056516e+00,  3.09016994e+00],
                          [-1.00000000e+01,  1.22464680e-15],
                          [-9.51056516e+00, -3.09016994e+00],
                          [-8.09016994e+00, -5.87785252e+00],
                          [-5.87785252e+00, -8.09016994e+00],
                          [-3.09016994e+00, -9.51056516e+00],
                          [-1.83697020e-15, -1.00000000e+01],
                          [0.00000000e+00,  0.00000000e+00]],))

    def testArcTangentPoint_6(self):
        r_bevel = 3

        path = (extrude.PathBuilder()
                .move([0, 0])
                .line([r_bevel, 0], 'edge1')
                .arc_tangent_point([0, r_bevel], angle=180, name='bevel')
                .line([0, 0], 'edge2')
                .build())

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0., 0.],
                          [3., 0.],
                          [2.5306966, 0.03693498],
                          [2.07294902, 0.14683045],
                          [1.6380285, 0.32698043],
                          [1.23664424, 0.57294902],
                          [0.87867966, 0.87867966],
                          [0.57294902, 1.23664424],
                          [0.32698043, 1.6380285],
                          [0.14683045, 2.07294902],
                          [0.03693498, 2.5306966],
                          [0., 3.],
                          [0., 0.]],))

    def makePathQ1Q3(self, angle):
        p = 10
        return (extrude.PathBuilder()
                .move([0, 0])
                .line([-p, p], 'edge1')
                .arc_tangent_point([-p, -p], angle=angle, name='arc')
                .line([0, 0], 'edge2')
                .build())

    def testArcTangentPoint_7(self):
        path = self.makePathQ1Q3(-90)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.,   0.],
                          [-10.,  10.],
                          [-4.37016024,  13.44997024],
                          [2.21231742,  13.96802247],
                          [8.31253876,  11.44122806],
                          [12.60073511,   6.42039522],
                          [14.14213562,   0.],
                          [12.60073511,  -6.42039522],
                          [8.31253876, -11.44122806],
                          [2.21231742, -13.96802247],
                          [-4.37016024, -13.44997024],
                          [-10., -10.],
                          [0.,   0.]],))

    def testArcTangentPoint_8(self):
        path = self.makePathQ1Q3(90)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.00000000e+00,  0.00000000e+00],
                          [-1.00000000e+01,  1.00000000e+01],
                          [-1.14412281e+01,  8.31253876e+00],
                          [-1.26007351e+01,  6.42039522e+00],
                          [-1.34499702e+01,  4.37016024e+00],
                          [-1.39680225e+01,  2.21231742e+00],
                          [-1.41421356e+01,  1.73191211e-15],
                          [-1.39680225e+01, -2.21231742e+00],
                          [-1.34499702e+01, -4.37016024e+00],
                          [-1.26007351e+01, -6.42039522e+00],
                          [-1.14412281e+01, -8.31253876e+00],
                          [-1.00000000e+01, -1.00000000e+01],
                          [0.00000000e+00,  0.00000000e+00]],))

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

    def testArcPoints_1(self):
        path = self.makeArcPointsPath(10, 20, 30)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[5.,  5.],
                          [14.84807753,  6.73648178],
                          [14.78147601,  7.07911691],
                          [14.70295726,  7.41921896],
                          [14.61261696,  7.75637356],
                          [14.51056516,  8.09016994],
                          [14.39692621,  8.42020143],
                          [14.27183855,  8.74606593],
                          [14.13545458,  9.06736643],
                          [13.98794046,  9.38371147],
                          [13.82947593,  9.69471563],
                          [13.66025404, 10.],
                          [5.,  5.]],))

    def testArcPoints_2(self):
        path = self.makeArcPointsPath(10, 35, 30)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[5.,  5.],
                          [14.84807753,  6.73648178],
                          [14.13545458,  0.93263357],
                          [10.29919264, -3.48048096],
                          [4.65100503, -4.99390827],
                          [-0.87785252, -3.09016994],
                          [-4.39692621,  1.57979857],
                          [-4.70295726,  7.41921896],
                          [-1.69130606, 12.43144825],
                          [3.60826899, 14.90268069],
                          [9.38371147, 13.98794046],
                          [13.66025404, 10.],
                          [5.,  5.]],))

    def testArcPoints_3(self):
        test_angles = ((190, 170, 90), (190, 185, 90))
        for angles in test_angles:
            path = self.makeArcPointsPath(*angles)

            iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                            ([[5.00000000e+00,  5.00000000e+00],
                              [-4.84807753e+00,  3.26351822e+00],
                              [-5.00000000e+00,  5.00000000e+00],
                              [-4.84807753e+00,  6.73648178e+00],
                              [-4.39692621e+00,  8.42020143e+00],
                              [-3.66025404e+00,  1.00000000e+01],
                              [-2.66044443e+00,  1.14278761e+01],
                              [-1.42787610e+00,  1.26604444e+01],
                              [-8.88178420e-16,  1.36602540e+01],
                              [1.57979857e+00,  1.43969262e+01],
                              [3.26351822e+00,  1.48480775e+01],
                              [5.00000000e+00,  1.50000000e+01],
                              [5.00000000e+00,  5.00000000e+00]],))

    def testArcPoints_4(self):
        test_angles = ((190, 170, 270), (190, 185, 270))
        for angles in test_angles:
            path = self.makeArcPointsPath(*angles)

            iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                            ([[5.,  5.],
                              [-4.84807753,  3.26351822],
                              [-4.51056516,  8.09016994],
                              [-1.9465837, 12.193398],
                              [2.24362644, 14.61261696],
                              [7.07911691, 14.78147601],
                              [11.4278761, 12.66044443],
                              [14.27183855,  8.74606593],
                              [14.94521895,  3.95471537],
                              [13.29037573, -0.59192903],
                              [9.69471563, -3.82947593],
                              [5., -5.],
                              [5.,  5.]],))

    def makeArcPointsRadius(self, start_angle, end_angle, r, is_left=False):
        offset = np.array([5, 5])
        angles = np.array([start_angle, end_angle]) / 180 * np.pi
        points_t = np.array([np.cos(angles), np.sin(angles)]) * (r / 2)
        points = np.transpose(points_t)
        return (extrude.PathBuilder()
                .move(offset)
                .line(points[0] + offset, 'edge1')
                .arc_points_radius(points[1] + offset, r, name='arc', is_left=is_left)
                .line(offset, 'edge2')
                .build())

    def testArcPointsRadius_1(self):
        path = self.makeArcPointsRadius(0, 90, 10, False)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[5.,  5.],
                          [10.,  5.],
                          [15.43068778,  4.20139037],
                          [20.46476957,  6.38957857],
                          [23.58546912, 10.90526029],
                          [23.85251507, 16.38785397],
                          [21.18544609, 21.18544609],
                          [16.38785397, 23.85251507],
                          [10.90526029, 23.58546912],
                          [6.38957857, 20.46476957],
                          [4.20139037, 15.43068778],
                          [5., 10.],
                          [5.,  5.]],))

    def testArcPointsRadius_2(self):
        path = self.makeArcPointsRadius(0, 90, 10, True)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[5.,  5.],
                          [10.,  5.],
                          [10.79860963, -0.43068778],
                          [8.61042143, -5.46476957],
                          [4.09473971, -8.58546912],
                          [-1.38785397, -8.85251507],
                          [-6.18544609, -6.18544609],
                          [-8.85251507, -1.38785397],
                          [-8.58546912,  4.09473971],
                          [-5.46476957,  8.61042143],
                          [-0.43068778, 10.79860963],
                          [5., 10.],
                          [5.,  5.]],))

    def makePathWithSweep(self, sweep_angle, angle):
        p = 10
        r = p * np.sqrt(2)
        return (extrude.PathBuilder()
                .move([0, 0])
                .line([-p, p], 'edge1')
                .arc_tangent_radius_sweep(
                r,
                sweep_angle=sweep_angle,
                angle=angle,
                name='arc')
                .line([0, 0], 'edge2')
                .build())

    def testArcTangentSweep_1(self):
        path = self.makePathWithSweep(-270, -90)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.,   0.],
                          [-10.,  10.],
                          [-4.37016024,  13.44997024],
                          [2.21231742,  13.96802247],
                          [8.31253876,  11.44122806],
                          [12.60073511,   6.42039522],
                          [14.14213562,   0.],
                          [12.60073511,  -6.42039522],
                          [8.31253876, -11.44122806],
                          [2.21231742, -13.96802247],
                          [-4.37016024, -13.44997024],
                          [-10., -10.],
                          [0.,   0.]],))

    def testArcTangentSweep_2(self):
        path = self.makePathWithSweep(270, -90)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.00000000e+00,  0.00000000e+00],
                          [-1.00000000e+01,  1.00000000e+01],
                          [-1.34499702e+01,  4.37016024e+00],
                          [-1.39680225e+01, -2.21231742e+00],
                          [-1.14412281e+01, -8.31253876e+00],
                          [-6.42039522e+00, -1.26007351e+01],
                          [-8.21511329e-16, -1.41421356e+01],
                          [6.42039522e+00, -1.26007351e+01],
                          [1.14412281e+01, -8.31253876e+00],
                          [1.39680225e+01, -2.21231742e+00],
                          [1.34499702e+01,  4.37016024e+00],
                          [1.00000000e+01,  1.00000000e+01],
                          [0.00000000e+00,  0.00000000e+00]],))

    def makePathWithCentreSweep(self, sweep_angle):
        p = 10
        r = p * np.sqrt(2)
        return (extrude.PathBuilder()
                .move([0, 0])
                .line([-p, p], 'edge1')
                .arc_centre_sweep(
                [0, 0],
                sweep_angle=sweep_angle,
                name='arc')
                .line([0, 0], 'edge2')
                .build())

    def testArcCentreSweep_1(self):
        path = self.makePathWithCentreSweep(-270)

        iterable_assert(self.assertAlmostEqual, path.polygons(MockMetaData()),
                        ([[0.,   0.],
                          [-10.,  10.],
                          [-4.37016024,  13.44997024],
                          [2.21231742,  13.96802247],
                          [8.31253876,  11.44122806],
                          [12.60073511,   6.42039522],
                          [14.14213562,   0.],
                          [12.60073511,  -6.42039522],
                          [8.31253876, -11.44122806],
                          [2.21231742, -13.96802247],
                          [-4.37016024, -13.44997024],
                          [-10., -10.],
                          [0.,   0.]],))

    def testOffset(self):
        path = self.makePathWithCentreSweep(90)

        result = make_offset_polygon2d(
            path, 1, PathOffsetMaker.OFFSET_ROUND, MockMetaData())

        iterable_assert(self.assertAlmostEqual, result,
                np.array(
                    [[ -9.617316  , -10.92388   ],
                    [ -9.292893  , -10.707107  ],
                    [  0.70710677,  -0.70710677],
                    [  0.98768836,  -0.15643448],
                    [  0.8910065 ,   0.4539905 ],
                    [  0.70710677,   0.70710677],
                    [ -9.292893  ,  10.707107  ],
                    [ -9.843566  ,  10.987688  ],
                    [-10.453991  ,  10.891006  ],
                    [-10.760406  ,  10.649448  ],
                    [-12.201633  ,   8.9619875 ],
                    [-12.293868  ,   8.835037  ],
                    [-13.453375  ,   6.942894  ],
                    [-13.524614  ,   6.803079  ],
                    [-14.37385   ,   4.752844  ],
                    [-14.42234   ,   4.6036053 ],
                    [-14.9403925 ,   2.4457629 ],
                    [-14.96494   ,   2.2907765 ],
                    [-15.139053  ,   0.07845914],
                    [-15.139053  ,  -0.07845914],
                    [-14.96494   ,  -2.2907765 ],
                    [-14.9403925 ,  -2.4457629 ],
                    [-14.42234   ,  -4.6036053 ],
                    [-14.37385   ,  -4.752844  ],
                    [-13.524614  ,  -6.803079  ],
                    [-13.453375  ,  -6.942894  ],
                    [-12.293868  ,  -8.835037  ],
                    [-12.201633  ,  -8.9619875 ],
                    [-10.760406  , -10.649448  ],
                    [-10.233445  , -10.97237   ]]),
                places=5)

    def svg_compare(self, filename: str, svgRenderer: sr.SvgRenderer):
        svg_str = svgRenderer.to_svg_string()
        self.compare_with_golden(filename, svg_str)

    def testSvgRender(self):
        path = self.makePathWithCentreSweep(150)
        model = sr.SvgRenderer(path, img_margin_size=150,
                               target_image_size=(700, 700))
        self.svg_compare('testSvgRender.svg', model)
        self.log_verbose(model.path_render._segs.to_json(indent=2))

    def testSvgRender2(self):
        path = self.makeTestObject(scale=11).path
        model = sr.SvgRenderer(path)
        
        self.svg_compare('testSvgRender2.svg', model)


    def html_compare(self, filename: str, htmlRenderer: sr.HtmlRenderer):
        svg_str = htmlRenderer.create_html()
        self.compare_with_golden(filename, svg_str)
        
    def testSvgRender3(self):
        import anchorscad_models.tools.funnel.FilterFunnel as funnel
        clz = funnel.FilterFunnel
        maker, shape = clz.example('default')
        result = renderer.render(
                        maker, 
                        initial_frame=None, 
                        initial_attrs=core.ModelAttributes())
        html_renderer = sr.HtmlRenderer(result.paths.paths)
        # self.update_golden_files = True
        self.html_compare('testSvgRender3.html', html_renderer)
        
        
    def testConstructionRender(self):
        
        pathBuilder = extrude.PathBuilder()
        pathBuilder.move([0, 0])
        pathBuilder.line([100, 0], 'l1')
        pathBuilder.arc_tangent_point([100, 100], name='a1')

        with pathBuilder.construction() as contructionBuilder:
            contructionBuilder.move([100, 50])
            contructionBuilder.line([100, 0], 'cl1')
            contructionBuilder.move([100, 50])
            contructionBuilder.line([100, 100], 'cl2')
            
        path = pathBuilder.build()
        
        assert path.constructions
        
        html_renderer = sr.HtmlRenderer(
            {path: renderer.ShapePathCollection(
                    [renderer.ShapePath((gm.Node('test1'), gm.Node('test2')))])})

        # self.update_golden_files = True
        self.html_compare('testConstructionRender.html', html_renderer)
        

if __name__ == "__main__":
    unittest.main()
