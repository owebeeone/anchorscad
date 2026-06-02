'''
An isosceles triangle quilt pattern.


'''

import anchorscad as ad
import anchorscad_models.quilting.patterns.pat_utils as pu
import numpy as np

_SIZE_SCALE = 1.0

@ad.datatree
class Triangle:

    base_w: float = 150 * _SIZE_SCALE
    h: float = 213.6 * _SIZE_SCALE
    side_margin: float = 0.25 * 25.4 * _SIZE_SCALE # 1/4 inch margin

    def triangle(self, c: ad.PathBuilderPrimitives):
        c.move((0, 0))
        c.line((-self.base_w / 2, 0), 'base-lhs')
        c.line((0, self.h), 'lhs')
        c.line((self.base_w / 2, 0), 'rhs')
        c.line((0, 0), 'base-rhs')
        
    def margin(self, c: ad.PathBuilderPrimitives):
        side_l = np.sqrt(self.h**2 + (self.base_w / 2)**2)
        sinr = self.h / side_l
        cosr = (self.base_w / 2) / side_l
        x_margin = self.side_margin / sinr
        y_margin = self.side_margin / cosr
        c.move((0, 0))
        c.line((-self.base_w / 2 - x_margin, 0), 'm-base-lhs')
        c.line((0, self.h + y_margin), 'm-lhs')
        c.line((self.base_w / 2 + x_margin, 0), 'm-rhs')
        c.line((0, 0), 'm-base-rhs')
        

    def build(self) -> ad.Path:
        builder = ad.PathBuilder(multi=True)

        with builder.construction() as c:
            self.triangle(c)
        
        self.margin(builder)

        return builder.build()

@ad.shape
@ad.datatree
class TriangleShape(ad.CompositeShape):
    '''A six-petal quilt pattern: inner circle plus six outward arcs.'''
    triangle: Triangle = ad.dtfield(default_factory=Triangle, doc='The triangle pattern')
    path: ad.Path = ad.dtfield(self_default=lambda s: s.triangle.build())
    h: float = ad.dtfield(1.5, 'The height of the shape')
    linear_extrude: ad.Node = ad.ShapeNode(ad.LinearExtrude)
    fn: int = ad.dtfield(64, 'The number of facets for the extrusion')

    def build(self) -> ad.Maker:
        maker = self.linear_extrude().solid('extrusion').at()
        return maker

MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    pu.main(Triangle().build(), ['--csq', '--pdf', '--pdf-stroke=0.05'])
    ad.anchorscad_main(False)

