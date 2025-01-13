

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


def xxx(result):
    print(f'XXX--- {repr(str(result.rendered_shape))}')

class RendererTest(unittest.TestCase):
    
    def testBasic(self):
        shape = ad.Box()
        result = render(shape)
        
        self.assertEqual(
            str(result.rendered_shape), 
            "// Start: lazy_union\ndefault_5_default_5();\n// End: lazy_union\n\n// Modules.\n\n// 'PartMaterial undef-default - undef-default'\nmodule default_5_default_5() {\n  // 'None : _combine_solids_and_holes'\n  union() {\n    cube(size=[1.0, 1.0, 1.0]);\n  }\n} // end module default_5_default_5\n")
        
    def testEmpty(self):
        shape = Empty()
        result = render(shape)
        
        self.assertEqual(
            str(result.rendered_shape), 
            "// Start: lazy_union\n// End: lazy_union\n")
        
    def testMaterialDefaultMap(self):
        
        self.assertEqual(
            MAP_DEFAULT.map_attributes(ad.ModelAttributes()), 
            ad.ModelAttributes().with_material(MATERIAL_BP))
        
        self.assertEqual(
            MAP_DEFAULT.map_attributes(
              ad.ModelAttributes().with_material(MATERIAL_WA)), 
            ad.ModelAttributes().with_material(MATERIAL_WA))
        
    def testMaterialMap(self):
        self.assertEqual(
            MAP_BG_RH_GG.map_attributes(
                ad.ModelAttributes().with_material(MATERIAL_BG)), 
            ad.ModelAttributes().with_material(MATERIAL_GG))
        
        self.assertEqual(
            MAP_BG_RH_GG.map_attributes(
                ad.ModelAttributes().with_material(MATERIAL_WA)), 
            ad.ModelAttributes().with_material(MATERIAL_WA))
        
        self.assertEqual(
            MAP_BG_RH_GG.map_attributes(
                ad.ModelAttributes().with_material(MATERIAL_RH)), 
            ad.ModelAttributes().with_material(MATERIAL_GG))
        
        self.assertEqual(
            MAP_BG_RH_GG.map_attributes(ad.ModelAttributes()), 
            ad.ModelAttributes())
        
        self.assertEqual(
            MAP_STACK_A.map_attributes(ad.ModelAttributes()),
            ad.ModelAttributes().with_material(MATERIAL_BG))
        
        self.assertEqual(
            MAP_STACK_A.map_attributes(
                ad.ModelAttributes().with_material(MATERIAL_BG,)), 
             ad.ModelAttributes().with_material(MATERIAL_GG))
        
        self.assertEqual(
            MAP_STACK_B.map_attributes(ad.ModelAttributes()),
            ad.ModelAttributes().with_material(MATERIAL_GG))
        
    def testRenderMaterial(self):
        result = render(BOX_MAKER)
        
        self.maxDiff = None
        self.assertEqual(
            str(result.rendered_shape),
            '''// Start: lazy_union
default_5_red_HIPS_5();
default_5_blue_PETG_5_cured();
// End: lazy_union

// Modules.

// 'PartMaterial undef-default - blue_PETG 5.0'
module default_5_blue_PETG_5() {
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
} // end module default_5_blue_PETG_5

// 'PartMaterial undef-default - blue_PETG 5.0'
module default_5_blue_PETG_5_cured() {
  difference() {
    default_5_blue_PETG_5();
    default_5_red_HIPS_5();
  }
} // end module default_5_blue_PETG_5_cured

// 'PartMaterial undef-default - red_HIPS 5.0'
module default_5_red_HIPS_5() {
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
} // end module default_5_red_HIPS_5
''')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'RendererTest.testBasic']
    unittest.main()
