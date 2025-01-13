'''
Created on 2023-07-14

@author: gianni
'''

import anchorscad as ad
import anchorscad_models.basic.torus as torus
import numpy as np


@ad.shape
@ad.datatree
class CircularBelt(ad.CompositeShape):
    '''A basic torus, however paramerters are circumference diameter of the
    section. This is useful for making a belt with a specific length and diameter.
    '''
    l: float=ad.dtfield(doc='The length of the belt')
    d: float=ad.dtfield(doc='The diameter of the belt')

    torus_r_hole: float=ad.dtfield(self_default=lambda s: s.l / (2 * np.pi))
    torus_r_section: float=ad.dtfield(self_default=lambda s: s.d / 2)

    torus_node: ad.Node=ad.ShapeNode(
        torus.Torus, prefix='torus_', expose_all=True)
    fn: int=512
    torus_metadata_fn: int=ad.dtfield(32, doc='fn parameter for torus section')
    
    EXAMPLE_SHAPE_ARGS=ad.args(d=3, l=220)
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={
        'example2': ad.ExampleParams(shape_args=ad.args(d=4.7, l=290))
    }

    def build(self) -> ad.Maker:
        shape = self.torus_node()
        maker = shape.solid('belt').at('centre')
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
