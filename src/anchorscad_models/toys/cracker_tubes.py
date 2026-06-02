'''
Created on 20 Nov 2025

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.pipe import Pipe
import numpy as np

OVERSIZE=0.01


@ad.datatree
class WedgedCircle:
    '''
    A circle with a wedge cut out of it.
    '''
    r: float = ad.dtfield(69.5 / 2 - OVERSIZE, 'Radius of the circle')
    w: float = ad.dtfield(4, 'Width of the wedge')
    d: float = ad.dtfield(2, 'Depth of the wedge')

    def build(self) -> ad.Path:
        
        builder = ad.PathBuilder()
        
        start_point = (self.r - self.d, 0)
        on_circle = (self.r, 0)
        wedge_angle = ad.angle(radians=(self.w / self.r) * np.pi / 4)
        lower = (wedge_angle.rotZ * ad.GVector((self.r, 0, 0))).A2
        upper = (lower[0], -lower[1])
        with builder.construction() as c:
            c.move((0, 0))
            c.line(start_point, 'centre-line')
            c.line(lower, 'lower_wedge_edge')
            c.move(start_point)
            c.line(upper, 'upper_wedge_edge')

        builder.move(lower)
        builder.arc_centre_sweep(
            centre=(0, 0), 
            sweep_angle=wedge_angle / 2 + ad.angle(radians=np.pi * 2))
        
        builder.spline(
            (on_circle, start_point), cv_len=(self.w / 2, self.d / 2),
            name='upper_wedge_curve')
        
        return builder.build()
    
@ad.shape
@ad.datatree
class WedgedPipe(ad.CompositeShape):
    '''
    A pipe with a wedged cut out of it.
    '''
    path_builder_node: ad.Node[WedgedCircle]=ad.ShapeNode(WedgedCircle, expose_all=True)
    path: ad.Path=ad.dtfield(self_default=lambda self: self.path_builder_node().build())
    
    h: float=ad.dtfield(80, 'Height of the pipe')
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    fn: int=ad.dtfield(64, 'Number of facets')
    
    EXAMPLE_SHAPE_ARGS=ad.args(h=80, fn=64)
    

    def build(self) -> ad.Maker:
        maker = self.extrude_node().solid('wedged cylinder').at('centre-line')
        return maker


@ad.shape
@ad.datatree
class Cracker(ad.CompositeShape):
    '''
    A cracker model with two pipes.
    '''
    h: float=80
    
    # Outer pipe dimensions
    outer_od: float=69.5 / 2 - OVERSIZE
    outer_id: float=61 / 2 + OVERSIZE
    
    # Inner pipe dimensions
    inner_od: float=59.3 / 2 - OVERSIZE
    inner_id: float=51 / 2 + OVERSIZE
    
    epsilon: float=0.01
    
    outer_pipe_node: ad.Node[Pipe]=ad.ShapeNode(Pipe, {'outside_r': 'outer_od', 'inside_r': 'outer_id'}, expose_all=True)
    inner_pipe_node: ad.Node[Pipe]=ad.ShapeNode(Pipe, {'outside_r': 'inner_od', 'inside_r': 'inner_id'}, expose_all=True)
    
    EXAMPLE_SHAPE_ARGS=ad.args(h=80, fn=64)
    
    def build(self) -> ad.Maker:

        # Outer Pipe
        
        maker = self.outer_pipe_node().solid('outer_pipe')\
            .part(ad.Part("outer", 1)).at('base')
        
        maker.add_at(
            self.inner_pipe_node().solid('inner_pipe')\
                .part(ad.Part("inner", 2)).at('base'),
            'base'
        )
        
        return maker


MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()

