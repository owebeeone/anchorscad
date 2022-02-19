'''
Created on 14 Feb 2022

@author: gianni
'''

from dataclasses import dataclass

from ParametricSolid.core import shape
import ParametricSolid.core as core
from ParametricSolid.datatree import datatree, Node
import ParametricSolid.extrude as e
import ParametricSolid.linear as l


@core.shape('anchorscad.models.quilting.machne.WingNutWings')
@datatree
class WingNutWings(core.CompositeShape):
    '''
    Provides a single wing shape for a wing-nut assembly.
    '''
    h: float=10.6
    
    outer_r: float=16 / 2
    sweep_angle_degrees: float=44
    linex_node: Node=core.ShapeNode(e.LinearExtrude, 'h')
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(core.surface_args('base'),)
    
    def __post_init__(self):
        path = (e.PathBuilder()
                .move([0, 0], direction=[-1, 0])
                .arc_tangent_radius_sweep(
                    radius=self.outer_r,
                    sweep_angle_degrees=self.sweep_angle_degrees,
                    side=True,
                    name='arc')
                .line([-3/2, 16], name='side')
                .line([0, 16], name='end')
                .line([0, 0], name='middle')
                .build())
        
        shape = self.linex_node(path=path)
        maker = shape.solid('lhs').at()
        
        maker.add_at(shape.solid('rhs').at(post=l.scale([-1, 1, 1])))
                
        self.maker = maker
        
    @core.anchor('The centre of the arc for attaching to cylinder')
    def arc_centre(self):
        return self.at('lhs', 'arc', 0)


@core.shape('anchorscad.models.quilting.machne.WingNutCap')
@datatree
class WingNutCap(core.CompositeShape):
    '''
    Provides a shape to be used to make a winged bolt.
    Defaults are for a 3inch x 1/4inch rounded head, square neck bolt.
    '''
    r: float=6.5 / 2
    
    sq_size: tuple=(6.5, 6.5, 3.7)
    
    wings_node: Node=core.ShapeNode(WingNutWings)
    
    outer_cyl_node: Node=core.ShapeNode(core.Cylinder, {'r': 'outer_r'}, 'h')
    inner_cyl_node: Node=core.ShapeNode(core.Cylinder, 'r', 'h')
    
    sq_node: Node=core.ShapeNode(core.Box, prefix='sq_')

    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(core.surface_args('base'),)
    
    def __post_init__(self):
        outer_cyl = self.outer_cyl_node()
        
        maker = outer_cyl.solid('outer').at('centre')
        
        maker.add_at(self.inner_cyl_node().hole('inner')
                     .at('centre'), 
                     'centre')
        
        maker.add_at(self.sq_node().hole('key')
                     .at('face_centre', 1), 'top')
        
        wing = self.wings_node()
        
        for i in range(2):
            maker.add_at(wing.solid(('wing', i))
                         .at('arc_centre'), 
                         'surface', 0, i * 180)
        
        self.maker = maker


if __name__ == '__main__':
    core.anchorscad_main(False)
