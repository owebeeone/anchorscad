'''
An isosceles triangle quilt pattern.


'''

import anchorscad as ad
import anchorscad_models.quilting.patterns.pat_utils as pu
import numpy as np

_SIZE_SCALE = 1.0

@ad.datatree
class PointTurner:

    l: float = 159.0
    w: float = 25.0
    bl: float = 20.0
    sr: float = 0.5
    sr_angle: float = -160.0


    def build(self) -> ad.Path:
        builder = ad.PathBuilder(multi=True)

        builder.move((self.bl, 0))
        builder.line((0, 0), 'base')
        builder.arc_tangent_radius_sweep(radius=self.w / 2, sweep_angle=-180, name='arc')
        builder.stroke(self.l - self.bl - self.sr, name='top')
        builder.arc_tangent_radius_sweep(radius=self.sr, sweep_angle=self.sr_angle, name='sr')
        builder.spline(((self.bl + 1, 0), (self.bl, 0)), cv_len=(25, 50), name='curve')

        return builder.build()
    
@ad.datatree
class GradWedge:
    gh: float = 5.0
    gbase_w: float = 0.3
    gtop_w: float = 2.0
    
    def build(self) -> ad.Path:
        builder = ad.PathBuilder()
        builder.move((0, 0))
        builder.line((-self.gbase_w / 2, 0), 'lhs_base')
        builder.line((-self.gtop_w / 2, self.gh), 'lhs')
        builder.line((self.gtop_w / 2, self.gh), 'top')
        builder.line((-self.gbase_w / 2, 0), 'rhs')
        builder.line((0, 0), 'rhsbase')
        
        return builder.build()
    
@ad.shape
@ad.datatree
class GradWedgeShape(ad.CompositeShape):
    '''A grad wedge quilt pattern.'''
    grad_wedge: GradWedge = ad.dtfield(default_factory=GradWedge, doc='The grad wedge pattern')
    path: ad.Path = ad.dtfield(self_default=lambda s: s.grad_wedge.build())
    linear_extrude: ad.Node = ad.ShapeNode(ad.LinearExtrude, {'path': 'path', 'h': 'h'})
    h: float = ad.dtfield(15, 'The height of the shape')
    fn: int = ad.dtfield(64, 'The number of facets for the extrusion')

    def build(self) -> ad.Maker:
        maker = self.linear_extrude().solid('extrusion').at('lhs_base', 0)
        return maker
    

@ad.shape
@ad.datatree
class PointTurnerShape(ad.CompositeShape):
    '''A point turner quilt pattern.'''
    point_turner: PointTurner = ad.dtfield(default_factory=PointTurner, doc='The point turner pattern')
    path: ad.Path = ad.dtfield(self_default=lambda s: s.point_turner.build())
    bevel: float = 1.5
    path_shrunk: ad.Path = ad.dtfield(self_default=lambda s: s.path.transform(offset=-s.bevel))
    h: float = ad.dtfield(4, 'The height of the shape')
    h_shrunk: float = ad.dtfield(self_default= lambda s: s.h -  s.bevel, doc='The height of the shrunk shape')
    linear_extrude: ad.Node = ad.ShapeNode(ad.LinearExtrude, {'path': 'path', 'h': 'h_shrunk'})
    path_shrunk_extrude: ad.Node = ad.ShapeNode(ad.LinearExtrude, {'path': 'path_shrunk', 'h': 'h'})
    
    wedge_node: ad.Node[GradWedgeShape] = ad.dtfield(ad.ShapeNode(GradWedgeShape), doc='The grad wedge')
    
    fn: int = ad.dtfield(64, 'The number of facets for the extrusion')

    def build(self) -> ad.Maker:
        maker = self.linear_extrude().solid('extrusion').at('centre_of', 'arc')
        
        shrunk = self.path_shrunk_extrude().solid('shrunk').at('centre_of', 'arc')
        maker.add_at(shrunk, 'centre_of', 'arc', 0)
        
        maker = maker.hull('hull').at('centre_of', 'arc', 0)
    
        wedge = self.wedge_node().solid('wedge').at()
        maker.add_at(wedge, 'extrusion', 'top', 0, post=ad.rotX(45) * ad.ROTY_180 * ad.tranY(self.h - self.bevel -1))
 
        
        return maker

MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    pu.main(PointTurner().build(), ['--csq', '--pdf', '--pdf-stroke=0.05'])
    ad.anchorscad_main(False)

