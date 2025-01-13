'''
Created on 5 Dec 2021

@author: gianni
'''

from dataclasses import dataclass
import anchorscad.core as core
import anchorscad.extrude as e
import anchorscad_lib.linear as linear

@core.shape
@dataclass
class PolyhedraExtrusionTest(core.CompositeShape):
    '''
    <description>
    '''
    
    size: tuple=(10, 20, 10)
    size2: tuple=(5, 5, 10.1)
    
    EXAMPLE_SHAPE_ARGS=core.args()
    
    
    def __post_init__(self):
        shape1 = self.make_extrusion(self.size)
        shape2 = self.make_extrusion(self.size2)
        
        maker = shape1.solid('outer').at('centre')
        
        maker.add_at(shape2.hole('hole').at('centre'), 'centre')

        self.set_maker(maker)
        
    def make_extrusion(self, size):
        path = (e.PathBuilder()
                 .move((0, 0))
                 .line((0, size[1]), 'lhs')
                 .line((size[0], size[1]), 'top')
                 .line((size[0], 0), 'rhs')
               #  .line((0, 0), 'base')
                 .build())
        shape = e.LinearExtrude(path, size[2], use_polyhedrons=True)
        shape_cage = core.Box(size)
        maker = shape_cage.cage('cage').at('face_corner', 0, 0)
        maker.add_at(shape.solid('shape').at('rhs', post=linear.ROTY_270), 
                     'face_corner', 0, 0)
        return maker

@core.shape
@dataclass
class PolyhedraCircularTest(core.CompositeShape):
    '''
    <description>
    '''
    
    size: tuple=(10, 20, 90)
    size2: tuple=(5, 20.1, 90.1)
    offset: tuple=(3, 1)
    fn: int=120
    
    EXAMPLE_SHAPE_ARGS=core.args()
    
    
    def __post_init__(self):
        shape1 = self.make_extrusion(self.size, self.offset)
        shape2 = self.make_extrusion(self.size2, self.offset)
        
        maker = shape1.solid('outer').at('top', 0.5, self.size[2] / 2)
        
        maker.add_at(shape2.hole('hole').at('top', 0.5, self.size2[2] / 2), 
                     'top', 0.5, self.size[2] / 2)

        self.set_maker(maker)
        
    def make_extrusion(self, size, offset):
        path = (e.PathBuilder()
                 .move(offset)
                 .line((offset[0], size[1]), 'lhs')
                 .line((size[0], size[1]), 'top')
                 .line((size[0], offset[1]), 'rhs')
               #  .line(offset, 'base')
                 .build())
        shape = e.RotateExtrude(path, size[2], fn=self.fn, use_polyhedrons=True)
        maker = shape.solid('shape').at()
        return maker


if __name__ == "__main__":
    core.anchorscad_main(False)
