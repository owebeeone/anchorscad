import unittest


from anchorscad_lib.utils.colours import Colour 
from anchorscad_lib.test_tools import iterable_assert


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
        
    def test_hex_colour(self):
        c1 = Colour('#fff')
        self.assertEqual(c1.value, (1, 1, 1, 1))
        c1 = Colour('#fff7')
        self.assertEqual(c1.value, (1, 1, 1, 0x77/0xff))
        c1 = Colour('#f0f0f0')
        self.assertEqual(c1.value, (0xf0/0xff, 0xf0/0xff, 0xf0/0xff, 1))
        c1 = Colour('#f0f0f0f0')
        self.assertEqual(c1.value, (0xf0/0xff, 0xf0/0xff, 0xf0/0xff, 0xf0/0xff))
        
        self.assertEqual(c1.to_hex(), "#f0f0f0f0")
    
    def test_hex_colour_malformed(self):
        self.assertRaises(AssertionError, Colour, "#errerr")
        self.assertRaises(AssertionError, Colour, "#err")
        self.assertRaises(AssertionError, Colour, "#errerrff")
        self.assertRaises(AssertionError, Colour, "#errf")
        
        self.assertRaises(AssertionError, Colour, "#f")
        self.assertRaises(AssertionError, Colour, "#faaba")

    def test_hsv(self):
        c1 = Colour('red')
        self.assertEqual(c1.to_hsv(), (0, 1, 1, 1))
        c1 = Colour('blue')
        self.assertEqual(c1.to_hsv(), (0.6666666666666666, 1, 1, 1))
        c1 = Colour('yellow')
        self.assertEqual(c1.to_hsv(), (0.16666666666666666, 1, 1, 1))
        c1 = Colour('cyan')
        self.assertEqual(c1.to_hsv(), (0.5, 1, 1, 1))
        c1 = Colour('magenta')
        self.assertEqual(c1.to_hsv(), (0.8333333333333334, 1, 1, 1))
        c1 = Colour('black')
        self.assertEqual(c1.to_hsv(), (0, 0, 0, 1))
        c1 = Colour('white')
        self.assertEqual(c1.to_hsv(), (0, 0, 1, 1))
        
        self.assertEqual(Colour('red'), Colour(hsv=(0, 1, 1, 1)))
        
        self.assertEqual(Colour('white'), Colour(hsv=(0, 0, 1, 1)))
        self.assertEqual(Colour('white', 0.5), Colour(hsv=(0, 0, 1, 0.5)))
        self.assertEqual(Colour('white', 0.5), Colour(hsv=(0, 0, 1), a=0.5))
        
    def test_hsv_malformed(self):
        self.assertRaises(AssertionError, Colour, hsv=(0, 0, 1, 1), a=0.5)
        self.assertRaises(AssertionError, Colour, hsv=(0, 0, 1, 1, 1))
        self.assertRaises(AssertionError, Colour, "white", hsv=(0, 0, 1, 1))
        self.assertRaises(AssertionError, Colour, g=1, hsv=(0, 0, 1, 1))
        self.assertRaises(AssertionError, Colour, b=1, hsv=(0, 0, 1, 1))
        self.assertRaises(AssertionError, Colour, 1, 1, 1, 1, hsv=(0, 0, 1, 1))
        
    def test_copy(self):
        c1 = Colour('red')
        self.assertEqual(c1, Colour(c1))
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    