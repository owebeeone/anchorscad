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
    
    EXAMPLES_EXTENDED={
        'lilyq': ad.ExampleParams(
            shape_args=ad.args(radius=52/2, 
                               t=0.5,
                               fn=64),
            anchors=()
            )
        }
    
    def build(self) -> ad.Maker:
        shape = ad.Cylinder(r=self.radius, h=self.t, fn=self.fn)
        
        maker = shape.solid("circle").at('base')
        
        return maker
    
MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
