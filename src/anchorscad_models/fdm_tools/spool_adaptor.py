'''
Created on 2023-09-3

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.TriangularPrism import TriangularPrism


@ad.datatree
class SpoolAdaptorProfile:
    '''The cross section of the spool adaptor.'''
    t: float=ad.dtfield(2, doc='Thickness of the main outer portion of the adaptor.')
    h: float=ad.dtfield(4.1, doc='Height of the main outer portion of the adaptor.')
    ot: float=ad.dtfield(0.6, doc='Overhang of the top of the adaptor.')
    ob: float=ad.dtfield(0.75, doc='Overhang of the base of the adaptor.')
    oh: float=ad.dtfield(0.75, doc='Overhang thickness of the adaptor.')
    r: float=ad.dtfield(199 / 2, doc='Inner radius of the adaptor (spool radius).')

    def build(self) -> ad.Path:
        path = (ad.PathBuilder()
                .move((self.r, 0))
                .line((self.r, self.h), 'left')
                .line((self.r - self.ot, self.h + self.oh), 'left_top_overhang')
                .line((self.r + self.t, self.h + self.oh), 'top')
                .line((self.r + self.t, - self.oh), 'right')
                .line((self.r - self.ob, - self.oh), 'base')
                .line((self.r - self.ob, 0), 'left_base_overhang')
                .line((self.r, 0), 'left_overhang')
                ).build()
        return path


@ad.shape
@ad.datatree
class SpoolAdaptorRing(ad.CompositeShape):
    '''A spool adaptor ring for cardboard spools so they can be used in the Bambu AMS
    (automatic material system). Cardboard spools will wear and damage the AMS so this
    adaptor ring is used to protect the AMS from the cardboard spool.
    '''

    profile_node: ad.Node=ad.ShapeNode(SpoolAdaptorProfile)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.profile_node().build())

    extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, expose_all=True)

    fn: int=256

    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()


    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('adaptor').at()
        return maker
    

@ad.shape
@ad.datatree
class SpoolAdaptor(ad.CompositeShape):
    '''A spool adaptor ring for cardboard spools so they can be used in the Bambu AMS
    (automatic material system). Cardboard spools will wear and damage the AMS so this
    adaptor ring is used to protect the AMS from the cardboard spool.

    This model includes ribs to provide more interference with the spool. If you don't
    ribs just set rib_count to 0.
    '''

    ring_node: ad.Node=ad.ShapeNode(SpoolAdaptorRing)
    ring: ad.Maker=ad.dtfield(self_default=lambda s: s.ring_node())

    rib_w: float=ad.dtfield(0.5, doc='Width of the ribs.')
    rib_h: float=ad.dtfield(0.5, doc='Height of the ribs.')
    rib_count: int=ad.dtfield(3, doc='Number of ribs.')

    rib_size: tuple=ad.dtfield(
        self_default=lambda s: (s.rib_w, s.rib_h, s.h + s.ot))
    rib_skew: float=ad.dtfield(0.5, doc='rib shape skew.')

    rib_node: ad.Node=ad.ShapeNode(TriangularPrism, prefix='rib_')

    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    EXAMPLES_EXTENDED={
        # For creality cardboard spools - these are a bit too big in diameter for the AMS
        # so you need to leave the AMS door ajar to fit them in.
        'creality': ad.ExampleParams(
            shape_args=ad.args(h=4.2, r=199 / 2),
            anchors=()),
        'siddament' : ad.ExampleParams(
            shape_args=ad.args(h=3.1, r=198.2 / 2),  # Was 197.7 / 2
        ),
    }

    def build(self) -> ad.Maker:
        maker = self.ring.composite('spool_adaptor').at()

        for i in range(self.rib_count):
            maker.add_at(
                self.rib_node().composite(('rib', i)).at('base', 0.5),
                'spool_adaptor', 'adaptor', 'left', 0,
                angle=360 * i / self.rib_count
            )
        return maker



MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == "__main__":
    ad.anchorscad_main()
