'''
Created on 29 Sep 2021

@author: gianni
'''

from dataclasses import field
import anchorscad as an


@an.shape('anchorscad.models.basic.box_cylinder')
@an.datatree
class BoxCylinder(an.CompositeShape):
    '''
    A Box with half a cylinder protruding from one side.
    
    Build as an LinearExtrude but has both Cylinder and Box cages for anchors. 
    The Box cage is the primary shape.
    '''
    size: tuple=(10, 20, 30)
    r: float=field(init=False)  # reflects size[0] / 2
    h: float=field(init=False)  # reflects size[2]
    extrude_node: an.Node=an.ShapeNode(an.LinearExtrude, {})
    cylinder_node: an.Node=an.ShapeNode(an.Cylinder, 'r', 'h')
    box_cage_of_node: an.Node=an.Node(an.cageof, prefix='box_cage_')
    cyliner_cage_of_node: an.Node=an.Node(an.cageof, prefix='cylinder_cage_')
    
    EXAMPLE_SHAPE_ARGS=an.args(fn=32,
                               box_cage_as_cage=False,
                               cylinder_cage_as_cage=True)
    EXAMPLE_ANCHORS=(
        an.surface_args('face_corner', 0, 0),
        an.surface_args('cylinder', 'base'),
        an.surface_args('round_centre'),)
    
    def build(self) -> an.Maker:
        r = self.size[1] / 2
        self.r = r
        self.h = self.size[2]
        cage_size = (self.size[0] + r, self.size[1], self.size[2])
        maker = self.box_cage_of_node(an.Box(cage_size)).at(
                'face_corner', 0, 0)
            
        path = (an.PathBuilder()
            .move([0, 0])
            .line([-r, 0], 'edge1')
            .line([-r, self.size[0]], 'edge2')
            .arc_tangent_point([r, self.size[0]], name='arc')
            .line([r, 0], 'edge3')
            .line([0, 0], 'edge4')
            .build())
        
        shape = self.extrude_node(path, self.size[2])
        
        maker.add_at(shape.solid('box_cylinder').at('edge4', 1.0),
                     'face_edge', 0, 0, post=an.ROTY_180)
        
        cylinder_cage = self.cyliner_cage_of_node(
            self.cylinder_node(fn=2 * self.fn),
            properties=an.CageOfProperties(name='cylinder', colour=(1, 0, 0, 0.4)))
        maker.add_at(cylinder_cage.at('surface'),
                     'box_cylinder', 'arc', 0, pre=an.tranX(2 * r))
        
        return maker

    @an.anchor('Round centre.')
    def round_centre(self, h=0, rh=None):
        if not rh is None:
            h = h + rh * self.size[2]
        return (self.maker.at('face_centre', 4) 
                * an.translate((0, self.size[1] / 2 - self.r , -h)))


if __name__ == '__main__':
    an.anchorscad_main()
