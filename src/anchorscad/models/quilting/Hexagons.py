'''
Created on 4 Oct 2021

@author: gianni
'''

import anchorscad as ad
import numpy as np

INCH=25.4

def radians(degs):
    return degs * np.pi / 180

@ad.shape
@ad.dataclass
class HalfHexagon(ad.CompositeShape):
    '''
    <description>
    '''
    small_r: float=None
    large_r: float=None
    t: float=3.0
    
    DEFAULT_SMALL_R = 3 * INCH
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        
        if self.large_r is None and self.small_r is None:
            self.small_r = self.DEFAULT_SMALL_R
            
        if not self.small_r is None:
            self.large_r = self.small_r / np.cos(radians(30))
        else:
            self.small_r = self.large_r * np.cos(radians(30))
            
        ypos2 = self.large_r * np.sin(radians(30))
        
        path = (ad.PathBuilder()
            .move([0, 0])
            .line([0, self.large_r], 'upper_side')
            .line([self.small_r, ypos2], 'edge1')
            .line([self.small_r, -ypos2], 'edge2')
            .line([0, -self.large_r], 'edge3')
            .line([0, 0], 'lower_side')
            .build())
        
        shape = ad.LinearExtrude(path, h=self.t)
        
        return shape.solid('half_hexagon').at(
            'upper_side', 0, post=ad.ROTX_270)
        

if __name__ == '__main__':
    ad.anchorscad_main(False)
