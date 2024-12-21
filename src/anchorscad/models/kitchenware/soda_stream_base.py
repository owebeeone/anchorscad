'''
Created on 15-Dec-2024

@author: gianni
'''

import anchorscad as ad


@ad.datatree
class SodaStreamBasePath:
    '''Path bulder for the profile of a sodastream bottle base.'''
    
    w: float=ad.dtfield(1.5, doc='Width of the base wall')
    r: float=ad.dtfield(85 / 2, doc='Radius of bottle')
    h: float=ad.dtfield(5, doc='Height of the base')
    rb: int=ad.dtfield(75 / 2, doc='Radius of the base')
    support_arc_t: float=ad.dtfield(0.24, doc='Angle of the support arc in t')
    
    def build(self) -> ad.Path:
        
        builder = (ad.PathBuilder()
                .move((0, 0))
                .line((self.rb, 0), 'base')
                .spline(
                    (
                        (self.rb + 10, 30),
                        (self.r + self.w, 0),
                        (self.r + self.w, self.r + 10 - self.w)
                    ),
                    cv_len=(5, 40),
                    name='base-outer-wall',)
                .arc_points_radius((self.r, self.r + 10), self.w, direction=True, name='top')
                .spline(
                    (
                        (self.r, 30),
                        (self.rb, 10),
                        (self.rb - 10, self.w)
                    ),
                    cv_len=(45, 5),
                    name='base-inner-wall',))
        
        centre = (0, self.w + self.r)
        with builder.construction() as cbuilder:
            (cbuilder.move((0, self.w))
                .arc_centre_sweep(centre, 90, name='bottle-outline')
                .stroke(10, 'bottle-outline-wall')
            )

        sp = builder.at('bottle-outline', self.support_arc_t)
        
        builder.line(sp, 'support-start')
        builder.arc_centre_sweep(centre, -90 * self.support_arc_t, name='support-arc')
                    
        return builder.build()


@ad.shape
@ad.datatree
class SodaStreamBase(ad.CompositeShape):
    '''
    Base of a SodaStream bottle.
    '''
    path_builder: ad.Node = ad.ShapeNode(SodaStreamBasePath)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(5, doc='Height of the shape')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude)
    
    drain_hole_r: float=ad.dtfield(3, doc='Radius of the drain hole')
    drain_hole_h: float=ad.dtfield(10, doc='Height of the drain hole')
    hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='drain_hole_')
    
    drain_count: int=ad.dtfield(12, doc='Number of drain holes')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=128)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('extrusion').at('base', 0, post=ad.ROTX_180)

        hole_shape = self.hole_node()        
        for i in range(self.drain_count):
            maker = maker.add_at(
                hole_shape.hole(('hole', i)).at('centre'),
                'support-start', 0, degrees=i * 360 / self.drain_count)
        
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
