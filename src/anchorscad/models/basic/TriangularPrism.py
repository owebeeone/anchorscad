'''
Created on 12 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
from ParametricSolid import linear as l
from ParametricSolid.extrude import PathBuilder, LinearExtrude


@core.shape('anchorscad.models.basic.TriangularPrism')
@dataclass
class TriangularPrism(core.CompositeShape):
    '''
    Generates a triangular prism given the width depth and height.
    This is caged by a core.Box for box anchors and also named 2D path
    anchors.
    '''
    size: tuple
    
    EXAMPLE_SHAPE_ARGS=core.args([30, 10, 3])
    EXAMPLE_ANCHORS=(core.surface_args('base'),
                     core.surface_args('face_centre', 1),)
    
    def __post_init__(self):
        maker = core.Box(self.size).cage(
            'cage').at('centre')
        
        path = (PathBuilder()
            .move([0, 0])
            .line([0, self.size[0]], 'face1')
            .line([self.size[1], 0], 'face2')
            .line([0, 0], 'face3')
            .build())
            
        shape = LinearExtrude(path, h=self.size[2])
        
        maker.add_at(shape.solid('prism').at('face3', 0.5, rh=0.5), 
                     'face_centre', 2, post=l.ROTX_180)
        
        self.maker = maker

    @core.anchor('Base of the prism.')
    def base(self, *args, **kwds):
        return self.maker.at('prism', 'face3', 1, *args, **kwds)

if __name__ == '__main__':
    core.anchorscad_main(False)
