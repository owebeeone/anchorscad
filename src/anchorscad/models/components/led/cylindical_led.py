'''
Created on 19-Sep-2-24

@author: gianni
'''

import anchorscad as ad
import numpy as np


@ad.datatree(frozen=True)
class CylindricalLedPathBuilder:
    '''Profile path for a cylindical LED for RotateExtrude.
    Default values are for a 5mm LED.
    '''
    
    r: float=ad.dtfield(5 / 2, doc='Radius of the LED')
    r_base: float=ad.dtfield(6 / 2, doc='Radius of the base lip')
    h: float=ad.dtfield(8.6, doc='overall height of the LED')
    h_base: float=ad.dtfield(1, doc='base lip height')
    
    def build(self) -> ad.Path:
        
        h_body = self.h - self.h_base - self.r
        builder = (ad.PathBuilder()
                .move((0, 0))
                .line((self.r_base, 0), 'base')
                .line((self.r_base, self.h_base), 'base-side')
                .line((self.r, self.h_base), 'base-top')
                .line((self.r, h_body), 'side')
                .arc_tangent_radius_sweep(self.r, 90, side=True, name='top')
                .line((0, 0), 'centre-line'))
        
        return builder.build()

# The size parameters for a 5mm and 3mm LED.
LED_ARGS_5MM=ad.args(r=5 / 2, r_base=6 / 2, h=8.6, h_base=1)
LED_ARGS_3MM=ad.args(r=3 / 2, r_base=3.85 / 2, h=5.3, h_base=1)

@ad.shape
@ad.datatree(frozen=True)
class CylindricalLedBody(ad.CompositeShape):
    '''
    The main body of a cylindrical LED.
    '''
    path_builder: ad.Node = ad.ShapeNode(CylindricalLedPathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude)
    
    epsilon: float=ad.dtfield(0.001, doc='A delta to avoid Z-fighting')
    
    # The width of the cutout for the flat on the LED. This is 2 * the side
    # of a right-angled triangle with hypotenuse r_base and one side r.
    # Using Pythagoras' theorem, the width is 2 * sqrt(r_base^2 - r^2).
    cut_width: float=ad.dtfield(
        self_default=lambda s: s.epsilon + 2 * np.sqrt(s.r_base ** 2 - s.r ** 2),
        doc='Width of the cutout for the flat on the LED.')
    
    # Assemble the size parameters for ad.Box. This is automatically bound to
    # the cut_box_node by ad.Node.
    cut_size: float=ad.dtfield(
        self_default=lambda s: (s.cut_width, s.epsilon + s.r_base - s.r, s.h_base + s.epsilon),
        doc='Size (w, d, h) of the cutout for the flat on the LED')
    
    cut_box_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cut_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()
    
    EXAMPLES_EXTENDED={
        '5mm': ad.ExampleParams(shape_args=ad.args_add(LED_ARGS_5MM, fn=32)),
        '3mm': ad.ExampleParams(shape_args=ad.args_add(LED_ARGS_3MM, fn=32)),
    }

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('led_body').at('base', 0, post=ad.rotX(180))
        cut_box = self.cut_box_node()
        maker.add_at(
            cut_box.hole('cutout').at('face_edge', 'front', 0), 
            'base', 1, post=ad.ROTX_270 * ad.tranY(-self.epsilon / 2))
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
