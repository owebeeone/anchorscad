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
    r: float=an.dtfield(
        self_default=lambda s: s.size[0] / 2,
        init=False)
    h: float=an.dtfield(
        self_default=lambda s: s.size[2],
        init=False)
    extrude_node: an.Node=an.dtfield(
        an.ShapeNode(an.LinearExtrude, 'h'),
        init=False)
    cylinder_node: an.Node=an.dtfield(
        an.ShapeNode(an.Cylinder, 'r', 'h'),
        init=False)
    box_cage_of_node: an.Node=an.dtfield(
        an.Node(an.cageof, prefix='box_cage_'),
        init=False)
    cylinder_cage_of_node: an.Node=an.dtfield(
        an.Node(an.cageof, prefix='cylinder_cage_'),
        init=False)
    
    EXAMPLE_SHAPE_ARGS=an.args(fn=32,
                               box_cage_as_cage=False,
                               cylinder_cage_as_cage=False)
    EXAMPLE_ANCHORS=(
        an.surface_args('face_centre', 'base'),
        an.surface_args('face_centre', 'back'),
        an.surface_args('cylinder', 'base'),
        an.surface_args('round_centre', rh=1),)
    
    def build(self) -> an.Maker:
        cage_size = (self.size[0], self.size[1] + self.r, self.size[2])
        maker = self.box_cage_of_node(an.Box(cage_size)).at(
                'face_corner', 0, 0)
            
        path = (an.PathBuilder()
            .move([0, 0])
            .line([-self.r, 0], 'edge1')
            .line([-self.r, self.size[1]], 'edge2')
            .arc_tangent_point([self.r, self.size[1]], name='arc')
            .line([self.r, 0], 'edge3')
            .line([0, 0], 'edge4')
            .build())
        
        shape = self.extrude_node(path)
        
        maker.add_at(shape.solid('box_cylinder')
                     # .colour([0, 0, 1, 0.4])
                     # .transparent(True)
                     .at('edge2', 0.5),
                     'face_edge', 'base', 1,
                     post=an.ROTX_270 * an.tranX(-self.r / 2))
        
        cylinder_cage = self.cylinder_cage_of_node(
            self.cylinder_node(fn=2 * self.fn if self.fn else None),
            properties=an.CageOfProperties(name='cylinder', colour=(1, 0, 0, 0.4)))
        maker.add_at(cylinder_cage.at('surface'),
                     'box_cylinder', 'arc', 0.5, post=an.ROTY_180)
        
        return maker

    @an.anchor('Round centre.')
    def round_centre(self, h=0, rh=None):
        return self.maker.at('cylinder', 'base', h=h, rh=rh)
    
    @an.anchor('Round top.')
    def round_top(self, h=0, rh=None):
        return self.maker.at('cylinder', 'top', h=h, rh=rh)


if __name__ == '__main__':
    an.anchorscad_main()
