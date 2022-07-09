'''
Created on 9-Jul-2022

@author: gianni
'''

import anchorscad as ad
from typing import Tuple

@ad.shape
@ad.datatree(frozen=True)
class SingleHoleGauge(ad.CompositeShape):
    '''A plate with a line of holes of different radii provided in hole_rs.'''
    hole_rs: Tuple[float]=ad.dtfield(doc='Tuple of hole radii')
    h: float=ad.dtfield(5, 'Depth of plate')
    sep: float=ad.dtfield(5, 'Margin of separation between holes and edges')
    x: float=ad.dtfield(doc='Width (x) of plate', 
                        self_default=lambda s: 
                            sum(s.hole_rs) * 2 + (len(s.hole_rs) + 1) * s.sep)
    y: float=ad.dtfield(doc='Depth (y) of plate', 
                        self_default=lambda s: max(s.hole_rs) * 2 + 2 * s.sep)
    plate_size: Tuple[float]=ad.dtfield(doc='The (x, y, z) size of the plate Box shape',
                                 self_default=lambda s: (s.x, s.y, s.h - 2 * s.epsilon))
    plate_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='plate_'), init=False)
    hole_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, 'h'), init=False)
    epsilon: float=ad.dtfield(0.005, 'Fudge factor to remove aliasing')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64, hole_rs=(3, 4, 5, 6, 10))
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        maker = self.plate_node().solid('plate').at('centre')
        
        offset = self.sep
        for i, r in enumerate(self.hole_rs):
            hole = self.hole_node(r=r)
            offset += r
            maker.add_at(
                hole.hole(('hole', i))
                    .at('base', post=ad.translate((0, -offset, -self.epsilon))),
                'face_edge', 'base', 1)
            offset += r + self.sep
        return maker
    

@ad.shape
@ad.datatree(frozen=True)
class HoleGauge(ad.CompositeShape):
    '''A plate with a matrix of holes of different radii provided in hole_rss.'''
    hole_rss: Tuple[Tuple[float]]=ad.dtfield(doc='Tuple of tuple of hole radii')
    
    single_hole_gauge: ad.Node=ad.dtfield(
        ad.ShapeNode(SingleHoleGauge,
                     exclude=('hole_rs', 'x', 'y', 'plate_size')),
                     init=False)
    shapes: Tuple[ad.Shape]=ad.dtfield(
            doc='Tuple of shapes placed in the hole gauge plate',
            self_default=lambda s: tuple(s.single_hole_gauge(hole_rs=rs) for rs in s.hole_rss),
            init=False)
    plate_size: Tuple[float]=ad.dtfield(
            doc='The (x, y, z) size of the plate Box shape',
            self_default=lambda s:(
                max(sh.x for sh in s.shapes),
                sum(sh.y for sh in s.shapes) - (len(s.shapes) - 1) * s.sep,
                s.h - 2 * s.epsilon),
            init=False)
    plate_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='plate_'),
                                   doc='The plate node factory',
                                   init=False)
        
    EXAMPLE_SHAPE_ARGS=ad.args(
        fn=64, 
        hole_rss=((3, 4, 5, 6, 8, 10), (16, 14, 12)))
    
    def build(self) -> ad.Maker:
        # Create a builder plate the size of the entire assembly.
        maker = self.plate_node().solid('plate').at('centre')
        
        # Adds all shapes into the assembly plate.
        offset = 0
        for i, shape in enumerate(self.shapes):
            maker.add_at(shape.composite(('inner_plate', i))
                         .at('face_edge', 'base', 0, post=ad.tranY(-offset)),
                         'face_edge', 'base', 0)
            offset += shape.y - self.sep
        return maker


MAIN_DEFAULT=ad.ModuleDefault(True)  # Default to --write

if __name__ == "__main__":
    ad.anchorscad_main()
