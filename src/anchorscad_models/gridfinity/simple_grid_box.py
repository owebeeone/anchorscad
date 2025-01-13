'''
Created on 28-Feb-2024

@author: gianni
'''

import anchorscad as ad
from typing import Tuple


@ad.shape
@ad.datatree
class SimpleGridBox(ad.CompositeShape):
    '''
    A box with a grid of rectangular holes.
    '''
    x: float=ad.dtfield(150, 'Width of the box')
    y: float=ad.dtfield(319 / 2, 'Length of the box')
    z: float=ad.dtfield(130 / 6, 'Height of the box')
    
    t: float=ad.dtfield(2.4, doc='Thickness of the wall')
    bt: float=ad.dtfield(1.6, doc='Thickness of the base')
    
    o: float=ad.dtfield(0.2, doc='Compensation for the printer overhang.')
    
    nx: int=ad.dtfield(1, doc='Number of rectangular holes in the x direction')
    ny: int=ad.dtfield(2, doc='Number of rectangular holes in the y direction')
    
    eps: float=ad.dtfield(0.01, doc='Epsilon for the holes')
    
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.x - s.o, s.y - s.o, s.z))
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box), init=False)
    
    hole_size: tuple=ad.dtfield(
        doc='The (x,y,z) size of the holes',
        self_default=lambda s: (
            (s.size[0] - s.t) / s.nx - s.t, 
            (s.size[1] - s.t) / s.ny - s.t, 
            s.size[2] - s.bt + s.eps))
    hole_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='hole_'), init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(nx=1, ny=2)
    
    EXAMPLES_EXTENDED={
        'small_holes' : ad.ExampleParams(
            shape_args=ad.args(
                x=763 - 4 * 150, 
                z=130 / 6,
                nx=4, 
                ny=4),
        ),
        'medium_holes' : ad.ExampleParams(
            shape_args=ad.args(
                x=763 - 4 * 150, 
                z=130 / 6,
                nx=4, 
                ny=2),
        ),
        'larger_holes' : ad.ExampleParams(
            shape_args=ad.args(
                x=763 - 4 * 150, 
                z=130 / 6,
                nx=2, 
                ny=2),
        ),
        'one_hole' : ad.ExampleParams(
            shape_args=ad.args(
                nx=1, 
                ny=1),
        ),
        'B5x6' : ad.ExampleParams(
            shape_args=ad.args(
                x=(322 - 1.5) / 2,
                y=(348- 1.5) / 2,
                nx=5,
                ny=6),
        ),
        'B4x5' : ad.ExampleParams(
            shape_args=ad.args(
                x=(322 - 1.5) / 2,
                y=(348- 1.5) / 2,
                nx=4,
                ny=5),
        ),
        'B6x1' : ad.ExampleParams(
            shape_args=ad.args(
                x=(322 - 1.5) / 2,
                y=(348- 1.5) / 2,
                nx=6,
                ny=1),
        ),
        'rings' : ad.ExampleParams(
            shape_args=ad.args(
                x=(322 - 1.5) / 2,
                y=(348- 1.5) / 2,
                nx=10,
                ny=1),
        )
    }

    def build(self) -> ad.Maker:
        shape = self.box_node()
        maker = shape.solid('box').at('face_centre', 'base', post=ad.ROTX_180)
        
        hole_shape = self.hole_node()
        
        for i in range(self.nx):
            for j in range(self.ny):
                box_hole = hole_shape.hole(('hole', i, j )).at('face_corner', 'base', 0)
                maker = maker.add_at(
                    box_hole,
                    'face_corner', 'base', 0, post=ad.translate((
                        self.t + i * (self.hole_size[0] + self.t),
                        self.t + j * (self.hole_size[1] + self.t),
                        -self.bt)))

        return maker
    

@ad.shape
@ad.datatree
class MixGridBox(ad.CompositeShape):
    '''
    A box with a grid of rectangular holes.
    '''
    x: float=ad.dtfield(150, 'Width of the box')
    y: float=ad.dtfield(319 / 2, 'Length of the box')
    z: float=ad.dtfield(130 / 6, 'Height of the box')
    
    t: float=ad.dtfield(2.4, doc='Thickness of the wall')
    bt: float=ad.dtfield(1.6, doc='Thickness of the base')
    
    o: float=ad.dtfield(0.2, doc='Compensation for the printer overhang.')
    
    wx: Tuple[float, ...]=ad.dtfield((1,) * 3, doc='Number of rectangular holes in the x direction')
    wy: Tuple[float, ...]=ad.dtfield((2., 1.), doc='Number of rectangular holes in the y direction')
    
    count_x: int=ad.dtfield(self_default=lambda s: len(s.wx), doc='Number of holes in the x direction')
    count_y: int=ad.dtfield(self_default=lambda s: len(s.wy), doc='Number of holes in the y direction')
    sum_wx: float=ad.dtfield(self_default=lambda s: sum(s.wx), doc='Sum of wx')
    sum_wy: float=ad.dtfield(self_default=lambda s: sum(s.wy), doc='Sum of wy')
    asum_wx: Tuple[float, ...]=ad.dtfield(
        self_default=lambda s: (sum(s.wx[:i]) for i in range(s.count_x + 1)), 
        doc='Cumulative sum of wx')
    asum_wy: Tuple[float, ...]=ad.dtfield(
        self_default=lambda s: (sum(s.wy[:i]) for i in range(s.count_y + 1)), 
        doc='Cumulative sum of wy')
    
    eps: float=ad.dtfield(0.01, doc='Epsilon for the holes')
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.x - s.o, s.y - s.o, s.z))
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box), init=False)
    
    hole_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, {}), init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    
    EXAMPLES_EXTENDED={
        'rings' : ad.ExampleParams(
            shape_args=ad.args(
                x=(322 - 1.5) / 2,
                y=(348- 1.5) / 2),
        ),
        'insert' : ad.ExampleParams(
            shape_args=ad.args(
                x=397,
                y=240,
                z=22,
                wx=(1,) * 8,
                wy=(1,) * 6,
                bt=-0.01,
                ),
            anchors=(
                ad.surface_args('box', 'centre', scale_anchor=2),
                ad.surface_args(('hole', 3, 2), 'centre', scale_anchor=2),
            )
        )
    }

    def build(self) -> ad.Maker:
        shape = self.box_node()
        maker = shape.solid('box').at('face_centre', 'base', post=ad.ROTX_180)
        
        offx = self.t
        for i in range(self.count_x):
            xsize = self.x_size(i)
            offy = self.t
            for j in range(self.count_y):
                ysize = self.y_size(j)
                hole_size = self.hole_size(i, j)
                hole_shape = self.hole_node(size=hole_size)
                box_hole = hole_shape.hole(('hole', i, j )).at('face_corner', 'base', 0)
                maker = maker.add_at(
                    box_hole,
                    'face_corner', 'base', 0,
                    post=ad.translate((offx, offy, -self.bt)))
                offy += ysize + self.t
            offx += xsize + self.t

        return maker
    
    def x_open_size(self) -> float:
        '''The open size in the x direction.'''
        return self.size[0] - self.t * (self.count_x + 1)
    
    def y_open_size(self) -> float:
        '''The open size in the y direction.'''
        return self.size[1] - self.t * (self.count_y + 1)
    
    def x_size(self, col: int) -> float:
        '''The width of the holes in the "col" column.'''
        open_size = self.x_open_size()
        return open_size * self.wx[col] / self.sum_wx
    
    def y_size(self, row: int) -> float:
        '''The height of the holes in the "row" row.'''
        open_size = self.y_open_size()
        return open_size * self.wy[row] / self.sum_wy 
    
    def x_pos(self, col: int) -> float:
        '''The x position of the "col" column.'''
        if col == 0:
            return self.t
        
        return self.t * (col + 1) + self.asum_wx[col - 1] * self.x_open_size() / self.sum_wx
    
    def y_pos(self, row: int) -> float:
        '''The y position of the "row" row.'''
        if row == 0:
            return self.t
        
        return self.t * (row + 1) + self.asum_wy[row - 1] * self.y_open_size() / self.sum_wy
    
    def hole_size(self, col: int, row: int) -> Tuple[float, float, float]:
        '''The size of the hole at (col, row).'''
        return (self.x_size(col), self.y_size(row), self.size[2] - self.bt + self.eps)
    
    def hole_pos(self, col: int, row: int) -> Tuple[float, float, float]:
        '''The position of the hole at (col, row).'''
        return (self.x_pos(col), self.y_pos(row), -self.bt)


@ad.shape
@ad.datatree
class MixGridBoxSeparators(ad.CompositeShape):

    mix_grid_box: ad.Node=ad.ShapeNode(MixGridBox)
    
    epsilon: float=ad.dtfield(0.2, doc='Epsilon for the cut')
    
    cut_size: tuple=ad.dtfield(
        self_default=lambda s: (s.x / 2 - (s.t + s.epsilon), s.y - (s.t + s.epsilon) * 2, s.z),
        doc='The (x,y,z) size of the cut')
    cut_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='cut_'))
    
    EXAMPLES_EXTENDED={

        'insert' : ad.ExampleParams(
            shape_args=ad.args(
                x=396.5 + 2 * 2.4,
                y=239.75 + 2 * 2.4,
                z=20.4,
                wx=(1,) * 8,
                wy=(1,) * 6,
                bt=-0.01,
                t=2.4
                ),
            anchors=(
                ad.surface_args('box', 'centre', scale_anchor=2),
                ad.surface_args('cut', 'face_centre', 'left', scale_anchor=2),
            )
        )
    }
    
    def build(self) -> ad.Maker:
        
        shape = self.mix_grid_box()
        grid_maker = shape.solid('mix_grid_box').at('face_centre', 'base', post=ad.ROTX_180 * ad.ROTZ_90)
  
        cut_shape = self.cut_node().solid('cut').at('face_centre', 'left')
        
        grid_maker.add_at(cut_shape, 'centre', post=ad.ROTX_270 * ad.ROTY_90)

        maker = grid_maker.intersect('cut').at()    
   
        return maker 

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
