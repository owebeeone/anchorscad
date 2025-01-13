'''
Created on 18 Sept 2022

@author: gianni
'''

import unittest
import math
import anchorscad.zero_finder as zf


class Test(unittest.TestCase):


    def testSolveXSinXmCosX(self):
        
        def func(x):
            sinx = math.sin(x)
            cosx = math.cos(x)
            
            y = 2*x*sinx - cosx
            
            return y
        
        guess0 = 2
        guess1 = 4
        print(f"func({guess0})={func(guess0)}")
        print(f"func({guess1})={func(guess1)}")

        root, stats = zf.zero_of(
            func, guess0, guess1, 
            max_error=1.e-14, 
            max_iteration=70, 
            provide_details=True)
        
        print("2*x*sinx - cosx root=", root, stats)

    def testSolveXmTanX(self):
        
        def func(x):
            
            y = 2*x - math.tan(x)
            
            return y
        
        guess0 = 2
        guess1 = -2
        # print(f"func({guess0})={func(guess0)}")
        # print(f"func({guess1})={func(guess1)}")

        root, stats = zf.zero_of(
            func, guess0, guess1, 
            max_error=1.e-14, 
            max_iteration=70, 
            provide_details=True)
        
        # print("2*x - math.tan(x) root=", root, stats)
        self.assertAlmostEqual(root, 0)
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSolver']
    unittest.main()