

import unittest
from anchorscad.renderer import Renderer, render
import anchorscad as ad


posc = Renderer.model

@ad.shape
@ad.dataclass(frozen=True)
class Empty(ad.Shape):
    
    def render(self, renderer):
        pass


class RendererTest(unittest.TestCase):
    
    def testBasic(self):
        shape = ad.Box()
        result = render(shape)
        
        self.assertEqual(
            str(result.rendered_shape), 
            "// 'None : _combine_solids_and_holes'\nunion() {\n  cube(size=[1.0, 1.0, 1.0]);\n}\n")
        
    def testEmpty(self):
        shape = Empty()
        result = render(shape)
        
        self.assertEqual(
            str(result.rendered_shape), 
            "// 'pop:solid'\nunion();\n")
        
        
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'RendererTest.testBasic']
    unittest.main()
