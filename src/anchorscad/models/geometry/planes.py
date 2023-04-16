'''
Created on 26 Jan 2021

@author: gianni
'''

from dataclasses import dataclass
import anchorscad.core as core
import anchorscad.linear as l


@core.shape
@dataclass
class Planes(core.CompositeShape):
    '''
    A set of planes
    '''
    mat1: l.GMatrix=l.IDENTITY
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        maker = core.Box([100, 100, 1]).solid(
            'plane1').colour([1, 1, 0, 0.5]).at('centre')
        
        self.set_maker(maker)

    @core.anchor('An example anchor specifier.')
    def side(self, *args, **kwds):
        return self.maker.at('face_edge', *args, **kwds)

if __name__ == '__main__':
    core.anchorscad_main(False)
