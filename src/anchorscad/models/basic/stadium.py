'''
Created on 7-Jun-2023

@author: gianni
'''

import anchorscad as ad


@ad.datatree
class StadiumOutline:
    
    r: float=ad.dtfield(10, doc='Radius of the stadium')
    w: float=ad.dtfield(20, doc='Width of the stadium')
    t: float=ad.dtfield(0, doc='Top width of the stadium')
    offset: float=ad.dtfield(0, doc='Offset of the stadium path')
    square_left: bool=ad.dtfield(False, doc='Square the left side of the stadium')
    square_right: bool=ad.dtfield(False, doc='Square the right side of the stadium')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
            .move([self.r, self.r + self.t / 2])
            .line([self.r + self.w, self.r + self.t / 2], 'top'))
        if self.square_right:
            builder.stroke(self.r, name='right_top')
            builder.stroke(self.r, angle=-90, name='right_upper')
            builder.stroke(self.t, angle=0, name='right')
            builder.stroke(self.r, angle=-0, name='right_lower')
            builder.stroke(self.r, angle=-90, name='right_base')
        else:
            builder.arc_tangent_point([self.r * 2 + self.w, self.t / 2], name='right_upper')
            builder.stroke(self.t, angle=0, name='right')
            builder.arc_tangent_point([self.r + self.w, -self.r - self.t / 2], name='right_lower')
        builder.stroke(self.w, name='base')
        if self.square_left:
            builder.stroke(self.r, name='left_base')
            builder.stroke(self.r, angle=-90, name='left_lower')
            builder.stroke(self.t, angle=-0, name='left')
            builder.stroke(self.r, angle=-0, name='left_upper')
            builder.stroke(self.r, angle=-90, name='left_top')
        else:
            builder.arc_tangent_point([0, -self.t / 2], name='left_lower')
            builder.stroke(self.t, angle=0, name='left')
            builder.arc_tangent_point([self.r, self.r + self.t / 2], name='left_upper')
            
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
        (s.r * 2 + s.w, s.r * 2 + s.t, s.h))
   
    hide_cage: bool=False
    cage_box_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    
    cage_node: ad.Node=ad.CageOfNode()
    
    SIDE_HORIZ_NAMES={'left': 'left', 'right': 'right', 0: 'left', 1: 'right'}
    SIDE_VERT_NAMES={'upper': 'upper', 'lower': 'lower', 0: 'upper', 1: 'lower'}
    
    EXAMPLE_SHAPE_ARGS=ad.args(square_right=False)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base'),
        ad.surface_args('arc_centre', 'right', 'lower', rh=0),
        ad.surface_args('stadium', 'right_lower', 0.5),
    )

    def build(self) -> ad.Maker:
        
        cage_shape = self.cage_box_node()
        maker = self.cage_node(cage_shape).at('centre')
        
        shape = self.linear_extrude_node()
        
        maker.add_at(shape.solid('stadium').at('top', 0.5),
                     'face_edge', 'front', 2,
                     post=ad.ROTX_180 * ad.translate((0, -self.h, 0)))
        
        return maker
    
    @ad.anchor('The "top" of the stadium prism.')
    def top(self, h=0, rh=0) -> ad.GMatrix:
        h = h + self.h * rh
        return self.maker.at('face_centre', 'top') * ad.tranZ(-h)
    
    @ad.anchor('The "base" of the stadium prism.')
    def base(self, h=0, rh=0) -> ad.GMatrix:
        h = h + self.h * rh
        return self.maker.at('face_centre', 'base') * ad.tranZ(-h)
    
    @ad.anchor('Arc centres.')
    def arc_centre(self, side_horiz: str='left', side_vert: str='upper', rh=0) -> ad.GMatrix:
        '''Anchor for the arc centres of the stadium prism. If the anchors are flattened, there
        are no arc centres and it will raise an exception.
        Acceptable names are 'left'/'right' and 'upper'/'lower' or 0/1 for each respectively.
        '''
        horiz = self.SIDE_HORIZ_NAMES.get(side_horiz, None)
        if not horiz:
            raise ValueError(f'Unknown horizontal side name: {side_horiz}')
        
        vert = self.SIDE_VERT_NAMES.get(side_vert, None)
        if not vert:
            raise ValueError(f'Unknown vertical side name: {side_vert}')
        
        segment_name = f'{horiz}_{vert}'
        
        return self.maker.at('stadium', 'centre_of', segment_name, rh=rh)


@ad.shape
@ad.datatree
class StadiumRevolution(ad.CompositeShape):
    '''Prism of the "Stadium" sgame.
    '''
    
    inner_r: float=15
    outline_node: ad.Node=ad.Node(
        StadiumOutline, {'offset': 'inner_r'}, expose_all=True)
    outline: ad.Path=ad.dtfield(self_default=lambda s: s.outline_node())
    
    sweep_angle: float=90
    rotate_extrude_node: ad.Node=ad.ShapeNode(
        ad.RotateExtrude, 'path',
        {'angle': 'sweep_angle'}, prefix='rot_extrude_', expose_all=True)
    rot_extrude_path: ad.Path= ad.dtfield(self_default=lambda s: s.outline.build())
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(square_right=True, t=5)
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
        return self.maker.at('stadium', 'top', 0.5, angle=self.sweep_angle
            ) * ad.tranZ(self.r + self.t / 2) * ad.ROTX_90 * ad.ROTY_270 * ad.ROTX_180
    
    @ad.anchor('The "base" side of the stadium revolution.')    
    def base(self) -> ad.GMatrix:
        return self.maker.at('stadium', 'top', 0.5) * ad.tranZ(self.r + self.t / 2) * ad.ROTX_90 * ad.ROTY_270
    

# A shape consisting of a sequence of stadium prisms and revolutions.
@ad.shape
@ad.datatree
class StadiumSequence(ad.CompositeShape):
    '''Assembles a sequence of stadium prisms and revolutions base-to-top.'''
    
    prism_node: ad.Node=ad.ShapeNode(StadiumPrism, expose_all=True)
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
        
        shape_1, transform = self.make_shape(self.sequence[0])
        
        maker = shape_1.solid(('element-0')).at('base')
        
        for i, args in enumerate(self.sequence[1:]):
            shape, transform = self.make_shape(args)
            maker.add_at(shape.solid(f'element-{i + 1}').at('base'), 
                         f'element-{i}', 'top', post=transform)
        return maker
    
    def make_shape(self, adargs: tuple) -> ad.Shape:
        args, kwds = adargs[1]
        kwds = dict(kwds)  # This code mutates kwds so we need to copy it.
        user_transform = kwds.pop('transform', ad.IDENTITY)
        if adargs[0] == 'P':
            return self.prism_node(*args, **kwds), ad.ROTX_180 * user_transform
        elif adargs[0] == 'R':
            transform = ad.ROTX_180
            
            if 'sweep_angle' in kwds:
                angle = ad.angle(kwds['sweep_angle'])
                if angle.degrees() < 0:
                    transform = ad.ROTX_180 * ad.ROTZ_180
                    kwds['sweep_angle'] = -kwds['sweep_angle']
                
            shape = self.revolution_node(*args, **kwds)
            return shape, transform * user_transform
        else:
            raise ValueError(f'Unknown shape type: {args[0]}')
        
    @ad.anchor('The "top" side of the stadium sequence.')
    def top(self) -> ad.GMatrix:
        return self.maker.at(f'element-{len(self.sequence)-1}', 'top')


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
