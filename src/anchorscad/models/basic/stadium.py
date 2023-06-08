'''
Created on 7-Jun-2023

@author: gianni
'''

import anchorscad as ad


@ad.datatree
class StadiumOutline:
    
    r: float=10
    w: float=20
    offset: float=0
    square_left: bool=False
    square_right: bool=False
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
            .move([self.r, self.r])
            .line([self.r + self.w, self.r], 'top'))
        if self.square_right:
            builder.stroke(self.r, name='right_top')
            builder.stroke(self.r * 2, degrees=-90, name='right')
            builder.stroke(self.r, degrees=-90, name='right_base')
        else:
            builder.arc_tangent_point([self.r + self.w, -self.r], name='right')
        builder.stroke(self.w, name='base')
        if self.square_left:
            builder.stroke(self.r, name='left_base')
            builder.stroke(self.r * 2, degrees=-90, name='left')
            builder.stroke(self.r, degrees=-90, name='left_top')
        else:
            builder.arc_tangent_point([self.r, self.r], name='left')
            
        path = builder.build()
        
        if self.offset != 0:
            path = path.transform(ad.tranX(self.offset))
        
        return path


@ad.shape
@ad.datatree
class StadiumPrism(ad.CompositeShape):
    '''Prism of the "Stadium" sgame.
    '''
    
    outline_node: ad.Node=ad.Node(StadiumOutline)
    outline: ad.Path=ad.dtfield(self_default=lambda s: s.outline_node())
    
    h: float=10
    linear_extrude_node: ad.Node=ad.ShapeNode(
        ad.LinearExtrude, {'h': 'h'}, prefix='lin_extrude_', expose_all=True)
    lin_extrude_path: ad.Path= ad.dtfield(self_default=lambda s: s.outline.build())
    
    cage_size: tuple=ad.dtfield(self_default=lambda s: 
        (s.r * 2 + s.w, s.r * 2, s.h))
   
    as_cage: bool=False
    cage_box_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    
    cage_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(square_right=True)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base'),
    )

    def build(self) -> ad.Maker:
        
        cage_shape = self.cage_box_node()
        maker = self.cage_node(cage_shape).at('centre')
        
        shape = self.linear_extrude_node()
        
        maker.add_at(shape.solid('stadium').at('top', 0.5),
                     'face_edge', 'front', 2, post=ad.ROTX_180 * ad.tranY(-self.h))
        
        return maker
    
    @ad.anchor('The "top" of the stadium prism.')
    def top(self) -> ad.GMatrix:
        return self.maker.at('face_centre', 'top')
    
    @ad.anchor('The "base" of the stadium prism.')
    def base(self) -> ad.GMatrix:
        return self.maker.at('face_centre', 'base')
    

@ad.shape
@ad.datatree
class StadiumRevolution(ad.CompositeShape):
    '''Prism of the "Stadium" sgame.
    '''
    
    inner_r: float=15
    outline_node: ad.Node=ad.Node(
        StadiumOutline, {'offset': 'inner_r'}, expose_all=True)
    outline: ad.Path=ad.dtfield(self_default=lambda s: s.outline_node())
    
    sweep_degrees: float=90
    rotate_extrude_node: ad.Node=ad.ShapeNode(
        ad.RotateExtrude, 'path',
        {'degrees': 'sweep_degrees'}, prefix='rot_extrude_', expose_all=True)
    rot_extrude_path: ad.Path= ad.dtfield(self_default=lambda s: s.outline.build())
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(square_right=True)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base'),
    )

    def build(self) -> ad.Maker:
        
        shape = self.rotate_extrude_node()
        maker = shape.solid('stadium').at()
        
        return maker
    
    @ad.anchor('The "top" side of the stadium revolution.')
    def top(self) -> ad.GMatrix:
        return self.maker.at('stadium', 'top', 0.5, degrees=self.sweep_degrees
            ) * ad.tranZ(self.r) * ad.ROTX_90 * ad.ROTY_270 * ad.ROTX_180
    
    @ad.anchor('The "base" side of the stadium revolution.')    
    def base(self) -> ad.GMatrix:
        return self.maker.at('stadium', 'top', 0.5) * ad.tranZ(self.r) * ad.ROTX_90 * ad.ROTY_270
    

# A shape consisting of a sequence of stadium prisms and revolutions.
@ad.shape
@ad.datatree
class StadiumSequence(ad.CompositeShape):
    '''Assembles a sequence of stadium prisms and revolutions base-to-top.'''
    
    prism_node: ad.Node=ad.ShapeNode(StadiumPrism, 'h', expose_all=True)
    revolution_node: ad.Node=ad.ShapeNode(StadiumRevolution, expose_all=True)
    
    sequence: tuple=(
        ('P', ad.args(h=10)), 
        ('R', ad.args(inner_r=10)), 
        ('P', ad.args(h=10)))
    
    EXAMPLE_SHAPE_ARGS=ad.args(sequence=(
        ('P', ad.args(h=10)), 
        ('R', ad.args(inner_r=10)), 
        ('P', ad.args(h=10)), 
        ('R', ad.args(inner_r=20))), fn=64, square_right=True)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base'),
    )
    
    def build(self) -> ad.Maker:
        
        shape_1 = self.make_shape(self.sequence[0])
        
        maker = shape_1.solid(('element-0')).at('base')
        
        for i, args in enumerate(self.sequence[1:]):
            shape = self.make_shape(args)
            maker.add_at(shape.solid(f'element-{i + 1}').at('base'), 
                         f'element-{i}', 'top', post=ad.ROTX_180)
        return maker
    
    def make_shape(self, adargs: tuple) -> ad.Shape:
        args, kwds = adargs[1]
        if adargs[0] == 'P':
            return self.prism_node(*args, **kwds)
        elif adargs[0] == 'R':
            return self.revolution_node(*args, **kwds)
        else:
            raise ValueError(f'Unknown shape type: {args[0]}')
        
    @ad.anchor('The "top" side of the stadium sequence.')
    def top(self) -> ad.GMatrix:
        return self.maker.at(f'element-{len(self.sequence)-1}', 'top')


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
