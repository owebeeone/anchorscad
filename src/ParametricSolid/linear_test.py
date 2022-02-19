'''

'''
import unittest

from ParametricSolid import linear
from ParametricSolid.test_tools import iterable_assert
import numpy as np


class TestLinear(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass
    
    def testVectorEquality(self):
        v1 = linear.GVector([1., 0, 0, 1])
        v2 = linear.GVector([1., 0, 0])
        self.assertTrue(v1 == v2, "Vector eq failed")
        self.assertTrue(v2 == v2, "Vector eq failed")
        self.assertFalse(v1 != v2, "Vector ne failed")
        self.assertFalse(v2 != v2, "Vector ne failed")
        
        w = linear.GVector([2., 0, 0])
        self.assertFalse(w == v1, "Vector eq failed")
        self.assertTrue(w != v1, "Vector ne failed")
        
        
    def testMatrixEquality(self):
        m1 = linear.GMatrix([[0.5, 0.0, 0, 0], [0, 0.6, 0, 0], [0, 0, 0.7, 0], [0, 0, 0, 1]])
        m2 = linear.GMatrix([[0.5, 0.0, 0, 0], [0, 0.6, 0, 0], [0, 0, 0.7, 0], [0, 0, 0, 1]])
        self.assertTrue(m1 == m2, "GMatrix eq failed")
        self.assertTrue(m2 == m2, "GMatrix eq failed")
        self.assertFalse(m1 != m2, "GMatrix ne failed")
        self.assertFalse(m2 != m2, "GMatrix ne failed")
        
        
        n = linear.GMatrix([[1, 0.0, 0, 0], [0, 0.6, 0, 0], [0, 0, 0.7, 0], [0, 0, 0, 1]])
        self.assertFalse(n == m1, "GMatrix eq failed")
        self.assertTrue(n != m1, "GMatrix ne failed")
        
    def testMatrixConstruct(self):
        m1 = linear.GMatrix([[0.5, 0.0, 0, 0], [0, 0.6, 0, 0], [0, 0, 0.7, 0], [0, 0, 0, 1]])
        m2 = linear.GMatrix(m1)
        self.assertTrue(m1 == m2, "GMatrix eq failed")
        self.assertFalse(m1 != m2, "GMatrix ne failed")
        

    def testVectorConstruction(self):
        l3 = [1., 2, 3]
        l4 = [1., 2, 3, 1]
        v1 = linear.GVector(l3)
        v2 = linear.GVector(l4)
        self.assertEqual(v1, linear.GVector(v2), "3x vector copy construction failed")
        self.assertEqual(linear.GVector(np.array(l3)), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.array(l4)), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.array([l3])), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.array([l4])), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.array([l3]).T), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.array([l4]).T), v1, "vector construction failed")
        
        self.assertEqual(linear.GVector(np.matrix([l3])), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.matrix([l4])), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.matrix([l3]).T), v1, "vector construction failed")
        self.assertEqual(linear.GVector(np.matrix([l4]).T), v1, "vector construction failed")
        
        self.assertRaises(linear.MatrixShapeError, linear.GVector, np.array([1]))
        self.assertRaises(linear.MatrixShapeError, linear.GVector, np.array([l3, l3]))
        self.assertRaises(linear.MatrixShapeError, linear.GVector, np.matrix([[1]]))
        self.assertRaises(linear.MatrixShapeError, linear.GVector, np.matrix([l3, l3]))
        self.assertRaises(TypeError, linear.GVector, [object()])


    def testMatrixConstruction(self):
        v = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        v3 = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]
        
        m = linear.GMatrix(np.matrix(v))
        m3 = linear.GMatrix(np.matrix(v3))
        self.assertEqual(m, m3, 'A 3x4 and and 4x4 should me equal')
        self.assertEqual(m, m.I, 'Identity inverse should be equal')
        
        m2 = linear.GMatrix(m)
        self.assertEqual(m2, m, 'copy constructor failed')
        self.assertEqual(linear.GMatrix(m2.m), m, 'np.matrix constructor failed')
        
        vm = np.matrix(v)
        v3m = np.matrix(v3)
        va = np.array(v)
        v3a = np.array(v3)
        
        self.assertEqual(linear.GMatrix(vm), m, 'np.matrix constructor failed')
        self.assertEqual(linear.GMatrix(v3m), m, 'np.matrix constructor failed')
        self.assertEqual(linear.GMatrix(va), m, 'np.array constructor failed')
        self.assertEqual(linear.GMatrix(v3a), m, 'np.array constructor failed')
        
        self.assertRaises(TypeError, linear.GMatrix, 5)
        self.assertRaises(TypeError, linear.GMatrix, [5])
        self.assertRaises(linear.ConversionException, linear.GMatrix, [[4],[4]])
        self.assertRaises(linear.MatrixShapeError, linear.GMatrix, np.array([5]))
        self.assertRaises(linear.MatrixShapeError, linear.GMatrix, np.array([[4],[4]]))
        self.assertRaises(linear.MatrixShapeError, linear.GMatrix, np.matrix([5]))
        self.assertRaises(linear.MatrixShapeError, linear.GMatrix, np.matrix([[4],[4]]))
        
        v2 = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 2]]
        self.assertRaises(linear.MatrixInvalidError, linear.GMatrix, v2)
        
        v3A = [linear.GVector([1., 0, 0]).A[:3], 
               linear.GVector([0., 1, 0]).A[:3],
               linear.GVector([0., 0, 1]).A[:3]]
        
        m3I = linear.GMatrix(v3A)
        self.assertEqual(m3I, linear.IDENTITY, 'Identity inverse should be equal')
        
    def testVectorAdd(self):
        v1 = linear.GVector([1, 2, 3, 1])
        v2 = linear.GVector([1, -2, 3, 1])
        vs = linear.GVector([2, 0, 6, 1])
        self.assertEqual(v1 + v2, vs, 'add failed')
        self.assertEqual(v1 + [1, -2, 3, 1], vs, 'add failed')
        self.assertEqual([1, -2, 3, 1] + v1, vs, 'add failed')
        self.assertEqual(+vs, vs, 'negate fails')
                
    def testVectorSub(self):
        v1 = linear.GVector([1, 2, 3, 1])
        v2 = linear.GVector([1, -2, 3, 1])
        vs = linear.GVector([0, 4, 0, 1])
        self.assertEqual(v1 - v2, vs, 'subtract failed')
        self.assertEqual(v2 - v1, -vs, 'negate fails')
        self.assertEqual(v1 - [1, -2, 3, 1], vs, 'subtract failed')
        self.assertEqual([1, -2, 3, 1] - v1, -vs, 'negate fails')
        
    def testVectorScalarMul(self):
        v1 = linear.GVector([3, 6, 9, 1])
        vs = linear.GVector([6, 12, 18, 1])
        self.assertEqual(v1 * 2, vs, 'vector multiply failed')
        self.assertEqual(2 * v1, vs, 'vector multiply failed')
        
    def testVectorScalarDiv(self):
        v1 = linear.GVector([3, 6, 9, 1])
        vs = linear.GVector([1, 2, 3, 1])
        self.assertEqual(v1 / 3, vs, 'vector divide failed')
        vs = linear.GVector([4, 2, 12 / 9.0, 1])
        self.assertEqual(12 / v1, vs, 'vector divide failed')
        
    def testScale(self):
        v = linear.GVector([1, 2, 3, 1])
        s = 3.5
        vr = linear.scale(s) * v
        self.assertEqual(vr.length(), s * v.length(), 'scale should result in scaling.')

    def testInvert(self):
        m = linear.GMatrix([[1, 1, 0, 0], [0, 2, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        self.assertEqual(m * m.I, linear.IDENTITY)
        
    def testMul(self):
        m = linear.GMatrix([[1, 1, 0, 0], [0, 2, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        mul = linear.GMatrix(m * m)
        self.assertNotEqual(mul, linear.IDENTITY)
        
    def doRotations(self, axis, rot_func, name):
        self.assertTrue(rot_func(0).is_approx_equal(linear.IDENTITY),
                        'Rotation by 0 should be identity')
        other = linear.GVector([1, 1, 2])
        self.assertTrue((rot_func(90) * axis).is_approx_equal(axis), name + 'should be unchanged')
        self.assertFalse((rot_func(90) * other).is_approx_equal(other), 
                         name + 'rotation should change 1,1,2')
        self.assertTrue(rot_func(90).I.is_approx_equal(rot_func(-90)),
                        'Inversion should rotate back')
        self.assertTrue(rot_func(45).I.is_approx_equal(rot_func(-45)), 
                        'Inversion should rotate back')
        self.assertTrue(rot_func(50).I.is_approx_equal(rot_func(-50)), 
                        'Inversion should rotate back')
        self.assertTrue((rot_func(40) * rot_func(50)).is_approx_equal(rot_func(90)), 
                        'rotation should be additive')
        self.assertTrue((rot_func(40)).is_approx_equal(linear.rotV(axis, 40)), 
                        'rotV should have same matrix')

    def doRotRadians(self, axis, rot_func, name):
        self.assertEqual(rot_func(90), 
                         rot_func(radians=np.pi / 2), 
                         name + ' pi/2 radians should be same as 90 degrees')
        self.doRotations(axis, rot_func, name)
        
    def testRotationXYZ(self):
        self.doRotRadians(linear.X_AXIS, linear.rotX, 'x axis')
        self.doRotRadians(linear.Y_AXIS, linear.rotY, 'y axis')
        self.doRotRadians(linear.Z_AXIS, linear.rotZ, 'z axis')
        self.doRotations(linear.X_AXIS, lambda d : linear.rotV(linear.X_AXIS, d), 'x axis rotV')
        self.doRotations(linear.Y_AXIS, lambda d : linear.rotV(linear.Y_AXIS, d), 'y axis rotV')
        self.doRotations(linear.Z_AXIS, lambda d : linear.rotV(linear.Z_AXIS, d), 'z axis rotV')
        aaxis = linear.GVector([1, 1, 1]).N
        self.doRotations(aaxis, lambda d : linear.rotV(aaxis, d), '[1, 1, 1].N axis')
        aaxis = linear.GVector([1, 1, 1])
        self.doRotations(aaxis, lambda d : linear.rotV(aaxis, d), '[1, 1, 1] axis')
        aaxis = linear.GVector([-1, 2, 1])
        self.doRotations(aaxis, lambda d : linear.rotV(aaxis, d), '[-1, 2, 1] axis')

    def testRotatFromTo(self):
        self.assertTrue(linear.rot_to_V(linear.X_AXIS, linear.Y_AXIS)
                        .is_approx_equal(linear.rotZ(90)))
        self.assertTrue(linear.rot_to_V(linear.X_AXIS, linear.Z_AXIS)
                        .is_approx_equal(linear.rotY(-90)))
        self.assertTrue(linear.rot_to_V(linear.Y_AXIS, linear.Z_AXIS)
                        .is_approx_equal(linear.rotX(90)))
        self.assertTrue(linear.rot_to_V(linear.X_AXIS, linear.X_AXIS + linear.Y_AXIS)
                        .is_approx_equal(linear.rotZ(45)))
        
    def testTranslate(self):
        v = linear.GVector([1, 2, 3])
        t = linear.translate([1, 2, 3])
        self.assertEqual(linear.translate(v), t, 
                         'Equivalence for initialization by list or GVector')
        self.assertEqual(t.I, linear.translate(-v),
                         'Inversion of translate is translate back.')
    
    def testRotAlign(self):
        preserve_axis = linear.GVector([1, 1, 1])
        preserve_frame = linear.rotV(preserve_axis, 22) * linear.rot_to_V(linear.Y_AXIS, preserve_axis)
        align_preserve_axis = preserve_frame * linear.X_AXIS
        plane_axis = linear.Z_AXIS
        xform = linear.rotAlign(preserve_axis, align_preserve_axis, plane_axis)
        
        iterable_assert(self.assertAlmostEqual, (xform * preserve_axis).A, preserve_axis)
        self.assertAlmostEqual((xform * align_preserve_axis).z, 0)


    def testMirror(self):
        pass
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    

