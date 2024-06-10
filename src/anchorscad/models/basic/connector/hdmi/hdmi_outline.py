'''
HDMI Type A connector utilities.

Created on 2 Oct 2021

@author: gianni
'''

import anchorscad as ad
from anchorscad import args, datatree, dtfield, CompositeShape, \
    shape, surface_args, PathBuilder, LinearExtrude, Box, Shape, \
    anchorscad_main, ShapeNode, Maker, ROTX_270, Node, cageof
import numpy as np


@shape
@datatree(frozen=True)
class HdmiOutline(CompositeShape):
    '''
    Hole cut out for HDMI Type A.
    '''
    size: tuple=(15.4, 11, 5.9)
    w2: float=12.65 + 0.2
    w3: float=10.2 + 0.2
    h2: float=4.0
    h3: float=4.3
    r: float=0.7
    plug_cutout: tuple=(18.2, 10, 8.2)
    
    cage_shape: Shape=dtfield(ShapeNode(Box), init=False)
    cage_node: Node=ad.CageOfNode()

    EXAMPLE_SHAPE_ARGS=args(hide_cage=False)
    NOEXAMPLE_ANCHORS=(
        surface_args('face_edge', 0, 0),)
    
    def build(self) -> Maker:
        cage_shape = self.cage_node(self.cage_shape())
        maker = cage_shape.at('centre')
        y1 = self.size[2] - self.h3
        y2 = self.size[2] - self.h2
        path = (PathBuilder()
            .move([0, 0])
            .line([-self.w3 / 2, 0], 'base_lhs')
            .line([-self.w2 / 2, y1], 'side_l_lhs')
            .line([-self.size[0] / 2, y2], 'side_m_lhs')
            .line([-self.size[0] / 2, self.size[2]], 'side_u_lhs')
            .line([0, self.size[2]], 'top_lhs')
            .line([self.size[0] / 2, self.size[2]], 'top_rhs')
            .line([self.size[0] / 2, y2], 'side_u_rhs')
            .line([self.w2 / 2, y1], 'side_m_rhs')
            .line([self.w3 / 2, 0], 'side_l_rhs')
            .line([0, 0], 'base_rhs')
            .build())
        
        extruded_shape = LinearExtrude(path, self.size[1])
        
        maker.add_at(extruded_shape.solid('hdmi').at('base_lhs', 0),
                     'face_edge', 0, 0, post=ROTX_270)
        return maker


@shape
@datatree
class HdmiOutlineTest(CompositeShape):
    '''Test shape for HdmiOutline. Print this shape to check the
    tolerances of the HdmiOutline shape work with your printer.'''
    outline: Shape=HdmiOutline()
    w: float=dtfield(2.0, 'Width of the test walls.')
    size: tuple=dtfield(
            self_default=lambda s: (
                s.outline.size[0] + 2 * s.w, 
                s.outline.size[1] / 3,
                s.outline.size[2] + 2 * s.w), 
            doc='The (x,y,z) size of HdmiOutlineTest')
    box_node: Node=dtfield(ShapeNode(Box), init=False)
    
    EXAMPLE_SHAPE_ARGS=args()
    
    def build(self) -> Maker:
        shape = self.box_node()
        maker = shape.solid('test').at()
        
        maker.add_at(self.outline.hole('outline').at('centre'),
                     'centre')
        return maker


MAIN_DEFAULT=ad.ModuleDefault(True)
if __name__ == '__main__':
    anchorscad_main(False)
