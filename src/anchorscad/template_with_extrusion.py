'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad


@ad.datatree
class ExamplePathBuilder:
    '''A simple example of a path builder.'''
    
    w1: float=ad.dtfield(5, doc='Width of block')
    r: float=ad.dtfield(4, doc='Radius of bumps')
    m: float=ad.dtfield(5, doc='Margin')
    n: int=ad.dtfield(4, doc='Number of bumps')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((0, 0))
                .line((0, self.m + self.r), 'left-side')
                .stroke(self.w1, -90, name='left-top'))
        
        
        if self.n > 0:
            builder.arc_tangent_radius_sweep(self.r, -180, degrees=90, name=('rise', 0)) \
                .arc_tangent_radius_sweep(self.r, 180, side=True, name=('fall', 0))
            
            for i in range(1, self.n):
                builder.arc_tangent_radius_sweep(self.r, -180, name=('rise', i)) \
                    .arc_tangent_radius_sweep(self.r, 180, side=True, name=('fall', i))
        
        builder.arc_tangent_radius_sweep(self.r, -180, name=('rise', self.n))
        builder.stroke(self.w1, 90, name='right-top')
        builder.stroke(self.m + self.r, -90, name='right-side')
        builder.line((0, 0), 'base')
        
                    
        return builder.build()


@ad.shape
@ad.datatree
class ShapeName(ad.CompositeShape):
    '''
    <description>
    '''
    x: float=10
    y: float=20
    z: float=30
    
    path_builder: ad.Node = ad.ShapeNode(ExamplePathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(5, doc='Height of the shape')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.x, s.y, s.z))
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, 'size'), init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('extrusion').at('base', 0.5)
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
