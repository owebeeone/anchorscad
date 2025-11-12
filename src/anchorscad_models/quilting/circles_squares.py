'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad
import numpy as np

INCH=25.4
ROOT2=np.sqrt(2)

@ad.shape
@ad.datatree
class Circle(ad.CompositeShape):
    '''
    A circle template for quilting.
    '''
    inner_radius: float=ad.dtfield(5 * INCH * ROOT2 / 2, 'Inner radius of the circle')
    outer_radius: float=ad.dtfield(6 * INCH * ROOT2 / 2, 'Outer radius of the circle')
    thickness: float=ad.dtfield(2., 'Thickness of the circle')
    inner_thickness: float=ad.dtfield(self_default=lambda s: s.thickness + s.epsilon, doc='Thickness of the inner circle')
    inner_circle_node: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'inner_radius', 'h': 'inner_thickness'}, expose_all=True)
    outer_circle_node: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'outer_radius', 'h': 'thickness'}, expose_all=True)
    epsilon: float=ad.dtfield(0.01, 'Epsilon for tearing suppression')
    
    fn: int=ad.dtfield(256, 'Number of facets for the circle')
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        maker = self.outer_circle_node().solid('outer_circle').at('centre')
        maker.add_at(self.inner_circle_node().hole('inner_circle').at('centre'), 'centre')
        return maker


@ad.shape
@ad.datatree
class Square(ad.CompositeShape):
    '''
    A square template for quilting.
    '''
    inner_size: float=ad.dtfield(5 * INCH, 'Side length of the square')
    outer_size: float=ad.dtfield(6 * INCH, 'Side length of the outer square')
    thickness: float=ad.dtfield(2., 'Thickness of the square')
    inner_thickness: float=ad.dtfield(self_default=lambda s: s.thickness + s.epsilon, doc='Thickness of the inner square')
    outer_thickness: float=ad.dtfield(self_default=lambda s: s.thickness, doc='Thickness of the outer square')
    
    inner_size_param: float=ad.dtfield(self_default=lambda s: (s.inner_size, s.inner_size, s.inner_thickness), doc='Side length of the inner square')
    outer_size_param: float=ad.dtfield(self_default=lambda s: (s.outer_size, s.outer_size, s.outer_thickness), doc='Side length of the outer square')
    
    inner_square_node: ad.Node=ad.ShapeNode(ad.Box, {'size': 'inner_size_param'}, expose_all=True)
    outer_square_node: ad.Node=ad.ShapeNode(ad.Box, {'size': 'outer_size_param'}, expose_all=True)
    epsilon: float=ad.dtfield(0.02, 'Epsilon for tearing suppression')
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    
    def build(self) -> ad.Maker:
        maker = self.outer_square_node().solid('outer_square').at('centre')
        maker.add_at(self.inner_square_node().hole('inner_square').at('centre'), 'centre')
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(write_files=True, write_stl_mesh_files=True)

if __name__ == "__main__":
    ad.anchorscad_main()
