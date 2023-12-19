

import unittest
from anchorscad.renderer import Renderer, render
import anchorscad as ad


posc = Renderer.model

@ad.shape
@ad.dataclass(frozen=True)
class Empty(ad.Shape):
    
    def render(self, renderer):
        pass
    
MATERIAL_BP = ad.Material('black_PLA')
MATERIAL_WA = ad.Material('white_ABS')
MATERIAL_RH = ad.Material('red_HIPS')
MATERIAL_GG = ad.Material('green_PETG')
MATERIAL_BG = ad.Material('blue_PETG')

MAP_DEFAULT = ad.MaterialMapDefault(MATERIAL_BP)

MAP_BG_RH_GG = ad.create_material_map(MATERIAL_BG, MATERIAL_GG, MATERIAL_RH, MATERIAL_GG)

MAP_DEFAULT_BG = ad.MaterialMapDefault(MATERIAL_BG)

MODEL_ATTRS = ad.ModelAttributes()

# Applies map before default hence the default value is not mapped.
MAP_STACK_A = ad.MaterialMapStack((MAP_BG_RH_GG, MAP_DEFAULT_BG))

# Applies default before map hence the default value is mapped.
MAP_STACK_B = ad.MaterialMapStack((MAP_DEFAULT_BG, MAP_BG_RH_GG))


BOX_SHAPE = ad.Box((10, 20, 30))
BOX_MAKER = (BOX_SHAPE.solid('box').material(MATERIAL_BG).at('centre')
             .add_at(BOX_SHAPE.solid('box2').material(MATERIAL_RH).at('centre'), 'face_centre', 'front'))



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
        
    def testMaterialDefaultMap(self):
        
        self.assertEqual(
            MAP_DEFAULT.map(None, MODEL_ATTRS), 
            MAP_DEFAULT.material)
        
        self.assertEqual(
            MAP_DEFAULT.map(MATERIAL_WA, MODEL_ATTRS), 
            MATERIAL_WA)
        
    def testMaterialMap(self):
        self.assertEqual(
            MAP_BG_RH_GG.map(MATERIAL_BG, MODEL_ATTRS), 
            MATERIAL_GG)
        
        self.assertEqual(
            MAP_BG_RH_GG.map(MATERIAL_WA, MODEL_ATTRS), 
            MATERIAL_WA)
        
        self.assertEqual(
            MAP_BG_RH_GG.map(MATERIAL_RH, MODEL_ATTRS), 
            MATERIAL_GG)
        
        self.assertEqual(
            MAP_BG_RH_GG.map(None, MODEL_ATTRS), 
            None)
        
        self.assertEqual(
            MAP_STACK_A.map(None, MODEL_ATTRS), 
            MATERIAL_BG)
        
        self.assertEqual(
            MAP_STACK_A.map(MATERIAL_BG, MODEL_ATTRS), 
            MATERIAL_GG)
        
        self.assertEqual(
            MAP_STACK_B.map(None, MODEL_ATTRS), 
            MATERIAL_GG)
        
    def testRenderMaterial(self):
        result = render(BOX_MAKER)
        
        
        self.maxDiff = None
        self.assertEqual(
            str(result.rendered_shape),
            '''// Start: lazy_union
// "pop - Material(name='red_HIPS'):solid"
union() {
  // 'None : _combine_solids_and_holes'
  union() {
    // 'box2'
    multmatrix(m=[[1.0, 0.0, 0.0, -5.0], [0.0, 0.0, -1.0, 5.0], [0.0, 1.0, 0.0, -10.0], [0.0, 0.0, 0.0, 1.0]]) {
      // 'box2 : _combine_solids_and_holes'
      union() {
        // 'box2'
        cube(size=[10.0, 20.0, 30.0]);
      }
    }
  }
}
// "pop - Material(name='blue_PETG'):solid"
union() {
  // 'None : _combine_solids_and_holes'
  union() {
    // 'box'
    multmatrix(m=[[1.0, 0.0, 0.0, -5.0], [0.0, 1.0, 0.0, -10.0], [0.0, 0.0, 1.0, -15.0], [0.0, 0.0, 0.0, 1.0]]) {
      // 'box : _combine_solids_and_holes'
      union() {
        // 'box'
        cube(size=[10.0, 20.0, 30.0]);
      }
    }
  }
}
// End: lazy_union
''')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'RendererTest.testBasic']
    unittest.main()
