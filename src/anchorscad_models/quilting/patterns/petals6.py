'''
A six-petal quilt pattern: inner circle plus six outward arcs.


'''

import anchorscad as ad
import anchorscad_models.quilting.patterns.pat_utils as pu

_SIZE_SCALE = 37 / 39.75


@ad.datatree
class Petals6:

    pnts: int = 6
    inner_r: float = 33.5 / 2 * _SIZE_SCALE
    petal_start_offset: float = 13.4 * _SIZE_SCALE
    petal_outer_offset: float = 23 * _SIZE_SCALE

    @property
    def petal_start_r(self) -> float:
        return self.petal_start_offset + self.inner_r

    @property
    def petal_outer_r(self) -> float:
        return self.petal_outer_offset + self.inner_r

    def petals(self, c: ad.PathBuilderPrimitives):
        step_ang = 360 / self.pnts
        half_step_ang = step_ang / 2
        v_start = ad.GVector((self.petal_start_r, 0, 0))
        v_outer = ad.GVector((self.petal_outer_r, 0, 0))

        for i in range(self.pnts):
            centre_ang = ad.angle(i * step_ang)
            start_ang = centre_ang - ad.angle(half_step_ang)
            end_ang = centre_ang + ad.angle(half_step_ang)

            p_start = (start_ang.rotZ * v_start).A2
            p_outer = (centre_ang.rotZ * v_outer).A2
            p_end = (end_ang.rotZ * v_start).A2

            if i == 0:
                c.move(p_start)
            c.arc_points(p_outer, p_end, direction=True, name=('petal', i))
            
    def inner_circle(self, c: ad.PathBuilderPrimitives):
        
        c.move((self.inner_r, 0))
        c.arc_centre_sweep((0, 0), 360, name='inner_circle')


    def build(self) -> ad.Path:
        print(f'size={(self.petal_start_r, self.petal_outer_r)}')

        builder = ad.PathBuilder(multi=True)

        with builder.construction() as c:
            self.inner_circle(c)
        
        self.petals(builder)

        return builder.build()

@ad.shape
@ad.datatree
class Petals6Shape(ad.CompositeShape):
    '''A six-petal quilt pattern: inner circle plus six outward arcs.'''
    petals6: Petals6 = ad.dtfield(default_factory=Petals6, doc='The petals6 pattern')
    path: ad.Path = ad.dtfield(self_default=lambda s: s.petals6.build())
    h: float = ad.dtfield(1.5, 'The height of the shape')
    linear_extrude: ad.Node = ad.ShapeNode(ad.LinearExtrude)
    fn: int = ad.dtfield(64, 'The number of facets for the extrusion')

    def build(self) -> ad.Maker:
        maker = self.linear_extrude().solid('extrusion').at()
        return maker

MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    pu.main(Petals6().build(), ['--csq', '--pdf', '--pdf-stroke=0.05'])
    ad.anchorscad_main(False)
