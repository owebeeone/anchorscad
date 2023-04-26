'''
Created on 18 Sep 2021

@author: gianni
'''

import anchorscad as ad

INCH=25.4


@ad.shape
@ad.dataclass
class Circle(ad.CompositeShape):
    '''
    A Circle
    '''
    radius: float=1 * INCH
    t: float=1.5
    fn: int=60
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        shape = ad.Cylinder(r=self.radius, h=self.t, fn=self.fn)
        
        self.maker = shape.solid("circle").at('base')

if __name__ == '__main__':
    ad.anchorscad_main(False)
