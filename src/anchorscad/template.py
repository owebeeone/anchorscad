'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad
import numpy as np

@ad.shape('${file}/ShapeName')
@ad.datatree
class ShapeName(ad.CompositeShape):
    '''
    <description>
    '''
    
    size: tuple=(1, 2, 3)
    
    EXAMPLE_SHAPE_ARGS=ad.args()

    def __post_init__(self):
        shape = ad.Box(self.size)
        maker = shape.solid('box').at('face_corner', 0, 0)
        self.set_maker(maker)
        

    @ad.anchor('An example anchor')
    def origin(self):
        return self.maker.at()


if __name__ == "__main__":
    ad.anchorscad_main(False)
