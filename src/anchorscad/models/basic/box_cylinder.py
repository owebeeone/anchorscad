'''
Created on 29 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import anchorscad as an


@an.shape('anchorscad.models.basic.box_cylinder')
@dataclass
class BoxCylinder(an.CompositeShape):
    '''
    <description>
    '''
    size: tuple=(10, 20, 30)
    fn: int=36
    
    EXAMPLE_SHAPE_ARGS=an.args()
    EXAMPLE_ANCHORS=(
        an.surface_args('face_corner', 0, 0),
        an.surface_args('cylinder', 'top'),
        an.surface_args('cylinder', 'base'),)
    
    def __post_init__(self):
        r = self.size[1] / 2
        self.r = r
        cage_size = (self.size[0] + r, self.size[1], self.size[2])
        maker = an.Box(cage_size).cage(
            'cage').colour([1, 1, 0, 0.5]).at(
                'face_corner', 0, 0)
            
        path = (an.PathBuilder()
            .move([0, 0])
            .line([-r, 0], 'edge1')
            .line([-r, self.size[0]], 'edge2')
            .arc_tangent_point([r, self.size[0]], name='arc')
            .line([r, 0], 'edge3')
            .line([0, 0], 'edge4')
            .build())
        
        shape = an.LinearExtrude(path, self.size[2], fn=self.fn)
        
        maker.add_at(shape.solid('box_cylinder').at('edge4', 1.0),
                     'face_edge', 0, 0, post=an.ROTY_180)
        
        maker.add_at(an.Cylinder(r=r, h=self.size[2])
                     .cage('cylinder').at('surface'),
                     'box_cylinder', 'arc', 0, pre=an.tranX(2 * r))
        
        self.maker = maker

    @an.anchor('Round centre.')
    def round_centre(self, h=0, rh=None):
        if not rh is None:
            h = h + rh * self.size[2]
        return (self.maker.at('face_centre', 4) 
                * an.translate((0, self.size[1] / 2 - self.r , -h)))


if __name__ == '__main__':
    an.anchorscad_main(False)
