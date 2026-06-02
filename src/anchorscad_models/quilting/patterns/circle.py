'''
A circle quilt pattern.


'''

import anchorscad as ad
import anchorscad_models.quilting.patterns.pat_utils as pu

_SIZE_SCALE = 1.0

@ad.datatree
class Circle:

    r: float = 17.5 * _SIZE_SCALE
    side_margin: float = 0.25 * 25.4 * _SIZE_SCALE # 1/4 inch margin

    def circle(self, c: ad.PathBuilderPrimitives):
        c.move((self.r, 0))
        c.arc_centre_sweep((0, 0), 360, name='circle')
        
    def margin(self, c: ad.PathBuilderPrimitives):
        outer_r = self.r + self.side_margin
        c.move((outer_r, 0))
        c.arc_centre_sweep((0, 0), 360, name='margin')

    def build(self) -> ad.Path:
        builder = ad.PathBuilder(multi=True)

        # with builder.construction() as c:
        #     self.circle(c)
        
        self.circle(builder)

        return builder.build()

@ad.shape
@ad.datatree
class CircleShape(ad.CompositeShape):
    '''A circle quilt pattern.'''
    circle: Circle = ad.dtfield(default_factory=Circle, doc='The circle pattern')
    path: ad.Path = ad.dtfield(self_default=lambda s: s.circle.build())
    h: float = ad.dtfield(1.5, 'The height of the shape')
    linear_extrude: ad.Node = ad.ShapeNode(ad.LinearExtrude)
    fn: int = ad.dtfield(64, 'The number of facets for the extrusion')

    def build(self) -> ad.Maker:
        maker = self.linear_extrude().solid('extrusion').at()
        return maker

MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    pu.main(Circle().build(), ['--csq', '--pdf', '--pdf-stroke=0.05'])
    ad.anchorscad_main(False)
