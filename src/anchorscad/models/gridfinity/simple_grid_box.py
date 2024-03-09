'''
Created on 28-Feb-2024

@author: gianni
'''

import anchorscad as ad


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
    
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
