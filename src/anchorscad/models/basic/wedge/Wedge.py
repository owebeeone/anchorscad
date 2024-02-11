'''
Created on 24 Sep 2021

@author: gianni
'''

import anchorscad as ad
from anchorscad.extrude import PathBuilder, LinearExtrude


@ad.shape
@ad.datatree
class Wedge(ad.CompositeShape):
    '''
    <description>
    '''
    size_base: tuple=(20, 10, 10)
    size_wedge: tuple=(15, 10, 5)
    size_door: tuple=(5,3, 10)
    chminey_size: tuple=(2, 10)
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.size_base).solid(
            'base').colour([1, 1, 0, 0.5]).at('centre')
        
        # Roof
        lower_x = self.size_wedge[0] / 2
        h = self.size_wedge[2]
        path = (PathBuilder()
            .move([0, 0])
            .line([-lower_x, 0], 'lower_left')
            .line([0, h], 'left_side')
            .line([lower_x, 0], 'right_side')
            .line([0, 0], 'lower_right')
            .build())
        
        shape = LinearExtrude(path=path, h=self.size_wedge[1])

        maker.add_at(shape.solid('roof').at('lower_left', 0, rh=0.5),
                     'face_centre', 4)
        # Door
        
        door = ad.Box(self.size_door).hole(
            'door').colour([1, 0, 0, 0.5]).at(
                'face_edge', 0, 0)
            
        maker.add_at(door, 
                     'face_edge', 0, 0)
        
        # Chimney
        
        chimney = ad.Cone(
            r_base=self.chminey_size[0],
            r_top=self.chminey_size[0],
            h=self.chminey_size[1],
            fn=20).solid(
            'chimney').colour([0, 0, 0, 0.5]).at(
                'base')
            
        maker.add_at(chimney, 
                     'face_edge', 4, 1,
                     post=ad.ROTX_180 * ad.translate([0, -5, 0]))
        
        return maker
        
if __name__ == '__main__':
    ad.anchorscad_main(False)
