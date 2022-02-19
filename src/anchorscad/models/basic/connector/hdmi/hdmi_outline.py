'''
Created on 2 Oct 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
import ParametricSolid.extrude as e
import numpy as np


@core.shape('anchorscad.models.basic.connector.hdmi.hdmi_outline')
@dataclass
class HdmiOutline(core.CompositeShape):
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
    tolerance:float=0.4
    show_cage: bool=False
        
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(
        core.surface_args('face_edge', 0, 0),
        )
    
    def __post_init__(self):
        maker = self.cage_shape().at('centre')
        y1 = self.size[2] - self.h3
        y2 = self.size[2] - self.h2
        path = (e.PathBuilder()
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
        
        shape = e.LinearExtrude(path, self.size[1])
        
        maker.add_at(shape.solid('hdmi').at('base_lhs', 0),
                     'face_edge', 0, 0, post=l.ROTX_270)
        
        self.maker = maker

    def cage_shape(self):
        shape = core.Box(self.size)
        if self.show_cage:
            return shape.solid(
                'cage').transparent(1).colour([0, 1, 0, 0.5])
        else:
            return shape.cage('cage')
        
        return shape.cage('cage')


@core.shape('anchorscad.models.basic.connector.hdmi.hdmi_outline_test')
@dataclass
class HdmiOutlineTest(core.CompositeShape):
    outline: core.CompositeShape=HdmiOutline()
    w: float = 2.0
    
    EXAMPLE_SHAPE_ARGS=core.args()
    
    def __post_init__(self):
        size = (self.outline.size[0] + 2 * self.w, 
                self.outline.size[1] / 3,
                self.outline.size[2] + 2 * self.w)
        shape = core.Box(size)
        maker = shape.solid('test').at()
        
        maker.add_at(self.outline.hole('outline').at('centre'),
                     'centre')
        self.maker = maker


if __name__ == '__main__':
    core.anchorscad_main(False)
