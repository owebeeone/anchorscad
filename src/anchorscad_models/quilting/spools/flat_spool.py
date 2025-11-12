'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad


@ad.datatree
class SpoolPathBuilder:
    '''Build a path for a flat spool.'''
    
    w: float=ad.dtfield(28.0, doc='Width of the spool')
    w2: float=ad.dtfield(self_default=lambda s: s.w / 2, doc='Half the width of the spool')
    r: float=ad.dtfield(8.3 / 2, doc='Radius of bumps')
    l: float=ad.dtfield(15, doc='Length of the flat part of the spool')  # noqa: E741
    n: int=ad.dtfield(3, doc='Number of sections')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((0, 0))
                .line((0, self.w2), 'left-side')
                .arc_tangent_radius_sweep(self.r, -180, name=('bump', 0)))
        
        angle = 90
        for i in range(self.n):
            builder.stroke(self.l, angle, name=('flat', i))
            builder.arc_tangent_radius_sweep(self.r, -180, angle=90, name=('bump', i + 1))
            angle = 90
        
        builder.stroke(self.w2, 0, name=('flat', self.n))
        builder.line((0, 0), 'center')
        
                    
        return builder.build()


@ad.shape
@ad.datatree
class FlatSpoolBasicShape(ad.CompositeShape):
    '''
    A flat spool with a flat part and a rounded part.
    '''
    path_builder: ad.Node = ad.ShapeNode(SpoolPathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(1.5, doc='Height of the shape')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('extrusion').at('center', 0.5)
        return maker


@ad.datatree
class SlitPathBuilder:
    '''Build a path for a slit.'''
    
    slit_w: float=ad.dtfield(0.2, doc='Width of the slit')
    slit_l: float=ad.dtfield(5.5, doc='Length of the slit')
    slit_taper_l: float=ad.dtfield(3, doc='Length of the taper of the slit')
    overshoot: float=ad.dtfield(0.005, doc='Printer fudge factor (x-y plane overshoot)')
    
    def width(self) -> float:
        return self.slit_w + self.overshoot

    def build(self) -> ad.Path:
        w = self.width()
        builder = (ad.PathBuilder()
                .move((-w, 0))
                .line((-w, self.slit_l - self.slit_taper_l), 'left-side')
                .line((-self.overshoot, self.slit_l), 'left-side-taper')
                .line((self.overshoot, self.slit_l), 'taper-point')
                .line((w, self.slit_l - self.slit_taper_l), 'right-side-taper')
                .line((w, 0), 'right-side')
                .line((-w, 0), 'base'))
        return builder.build()

@ad.shape
@ad.datatree
class FlatSpool(ad.CompositeShape):
    '''
    A flat spool with a flat part and a rounded part.
    '''
    basic_shape: ad.ShapeNode[FlatSpoolBasicShape]
    slit_path_builder_node: ad.ShapeNode[SlitPathBuilder]
    slit_path_builder: SlitPathBuilder=ad.dtfield(self_default=lambda s: s.slit_path_builder_node())
    slit_path: ad.Path=ad.dtfield(self_default=lambda s: s.slit_path_builder.build())
    slit_h: float=ad.dtfield(self_default=lambda s: s.h + 2 * s.epsilon)
    slit_extrude_node: ad.ShapeNode[ad.LinearExtrude] = ad.ShapeNode(ad.LinearExtrude, prefix='slit_')
    
    make_hook_holes: bool=ad.dtfield(False, doc='Whether to make hook holes')
    hook_hole_r: float=ad.dtfield(2.1, doc='Radius of the hook hole')
    hook_hole_node: ad.ShapeNode[ad.Cylinder] = ad.ShapeNode(ad.Cylinder, {'h': 'slit_h', 'r': 'hook_hole_r'})

    hook_hole_extrude_node: ad.ShapeNode[ad.LinearExtrude] = ad.ShapeNode(ad.LinearExtrude, {'h': 'hook_hole_h'})
    hook_hole_pos: float=ad.dtfield(4, doc='Position of the hook hole')
    
    slit_pos: float=ad.dtfield(0.65, doc='Position of the slit')
    
    epsilon: float=ad.dtfield(0.01, doc='Printer fudge factor - prevent tearing when rendering')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64, n=2)
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={
        'slot3': ad.ExampleParams(
            shape_args=ad.args(n=3),
        ),
        'slot4': ad.ExampleParams(
            shape_args=ad.args(n=4),
        ),
        'slot5': ad.ExampleParams(
            shape_args=ad.args(n=5),
        ),
        'slot6': ad.ExampleParams(
            shape_args=ad.args(n=6),
        ),
    }
    
    def build(self) -> ad.Maker:
        shape = self.basic_shape()
        maker = shape.solid('left').at('center', 0.5)
        maker_right = shape.solid('right').at('center', 0.5)
        maker.add_at(maker_right, 'center', 0.5, post=ad.ROTY_180)
        
        slit_shape = self.slit_extrude_node()
        for i in range(self.n):
            slit_maker_left = slit_shape.hole(('slit_left', i)).colour('red').at('base', 0.5)
            maker.add_at(slit_maker_left, 'left', ('bump', i), self.slit_pos, post=ad.tranY(-self.epsilon))
            slit_maker_right = slit_shape.hole(('slit_right', i)).colour('blue').at('base', 0.5)
            maker.add_at(slit_maker_right, 'right', ('bump', i), self.slit_pos, post=ad.tranY(-self.epsilon))
            
        if self.make_hook_holes:
            hook_hole_shape = self.hook_hole_node()
            hook_hole_maker = hook_hole_shape.hole(('hook_hole', 0)).at('base', 0, post=ad.ROTX_270)
            postpostpos = ad.translate((self.hook_hole_pos, -self.epsilon, 0))
            maker.add_at(hook_hole_maker, 'left', 'center', 0, post=postpostpos)
            hook_hole_maker = hook_hole_shape.hole(('hook_hole', 1)).at('base', 0, post=ad.ROTX_270)
            maker.add_at(hook_hole_maker, 'right', 'center', 0, post=postpostpos)
        
        return maker
    
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
