import unittest


from anchorscad.colours import Colour 
from tests.test_tools import iterable_assert


class ColourTest(unittest.TestCase):
    
    def test_colour_name(self):
        iterable_assert(
            self.assertAlmostEqual, 
            Colour('yellowgreen').value, 
            (154/255, 205/255, 50/255, 1))

    def test_colour_name_with_alpha(self):
        '''Test that we can create a colour by name with an alpha value'''
        c = Colour('red', 0.5)
        self.assertEqual(c.value, (1, 0, 0, 0.5))
        c = Colour('red', a=0.5)
        self.assertEqual(c.value, (1, 0, 0, 0.5))
        
    def test_malformed_name(self):
        
        self.assertRaises(AssertionError, Colour, 'red', 1, 1)
        self.assertRaises(AssertionError, Colour, 'red', 1, a=0.5)
        self.assertRaises(AssertionError, Colour, 'not a colour')
    
    def test_colour_rgb(self):
        '''Test that we can create a colour by name'''
        c = Colour((1, 0, 0))
        self.assertEqual(c.value, (1, 0, 0, 1))
        
    def test_colour_rgba(self):
        '''Test that we can create a colour by name'''
        c = Colour((1, 0, 0))
        self.assertEqual(c.value, (1, 0, 0, 1))
        
        c = Colour((1, 0, 0, 0.5))
        self.assertEqual(c.value, (1, 0, 0, 0.5))
        
        c = Colour((1, 0, 0), 0.5)
        self.assertEqual(c.value, (1, 0, 0, 0.5))
        
        c = Colour((1, 0, 0), a=0.5)
        self.assertEqual(c.value, (1, 0, 0, 0.5))
        
    def test_colour_rgb_malformed(self):
        '''Test that we can create a colour by name'''
        self.assertRaises(AssertionError, Colour, (1, 0, 0, 0.5), a=1)
        self.assertRaises(AssertionError, Colour, (1, 0, 0), 0.5, 0.5)
        self.assertRaises(AssertionError, Colour, (1, 0, 0), b=0.5)
        self.assertRaises(AssertionError, Colour, ('1', 0, 0))
        self.assertRaises(AssertionError, Colour, (1.1, 0, 0, 0.5))
        
    def test_colour_with_colour(self):
        '''Test that we can create a colour by name'''
        c = Colour(Colour('red'))
        self.assertEqual(c.value, (1, 0, 0, 1))
        
    def test_colour_with_colour_malformed(self):
        '''Test that we can create a colour by name'''
        c = Colour('red')
        self.assertRaises(AssertionError, Colour, c, 0.5)
        self.assertRaises(AssertionError, Colour, c, a=0.5)
        
    def test_colour_method(self):
        c = Colour('red')
        self.assertEqual(c.alpha(0.1).value, (1, 0, 0, 0.1))
        self.assertEqual(c.red(0.1).value, (0.1, 0, 0, 1))
        self.assertEqual(c.green(0.1).value, (1, 0.1, 0, 1))
        self.assertEqual(c.blue(0.1).value, (1, 0, 0.1, 1))
        
        self.assertEqual(c.red(0.1).green(0.2).blue(0.3).alpha(0.4).value,
                         (0.1, 0.2, 0.3, 0.4))
        self.assertEqual(c.blend(Colour('blue'), 0.75).value, (0.25, 0, 0.75, 1))
        
    def test_equality(self):
        c1 = Colour('red')
        c2 = Colour('red')
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, Colour('blue'))
        self.assertNotEqual(c1, Colour('red', 0.5))

        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    