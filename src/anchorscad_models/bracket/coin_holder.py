'''
Created on 22-Dec-2023

@author: gianni

The "BOSS" asked me to make a coin holder for a 5 Swiss Franc coin so it can be
used as a Christmas tree decoration. This is the result.

I should use TPU to print this. PLA was a bit too difficult to insert the coin, I could
have printed half way and inseted the coin and then continued printing. PETG might work
since it is a bit more flexible than PLA. Excuse to buy a roll of white and red TPU.

The StadiumSequence shape seems to have become a little more useful than I originally
thought. I have used it in a few places now. It's a bit cumbersome as an API so I might
rethink it in the future.
'''
import anchorscad as ad

import anchorscad_models.basic.stadium as stadium


@ad.shape
@ad.datatree
class SwissEyeletBase(ad.CompositeShape):
    '''An eyelet hole in the shape of a rounded Red Cross.
    
    See https://photos.app.goo.gl/Kd9AKE8Em6kNZKMy9 for an example.
    '''
    d: float=10
    base_w: float=45
    depth: float=2
    depth_outer: float=4
    riser_l: float=5
    
    swiss_eyelet_r: float=1.5
    swiss_eyelet_inner_r: float=0.5
    swiss_eyelet_r: float=1.5
    swiss_eyelet_w: float=1
    swiss_eyelet_t: float=0.9
    swiss_eyelet_bend_degrees: float=90
    swiss_eyelet_sequence: tuple=ad.dtfield(self_default=lambda s:
        (
         ('P', ad.args(h=s.depth)),
         ('R', ad.args(sweep_angle=-s.swiss_eyelet_bend_degrees)),
         ('P', ad.args(h=s.depth)),
         ('R', ad.args(sweep_angle=s.swiss_eyelet_bend_degrees)),
         ('P', ad.args(h=s.depth)),
         ('R', ad.args(sweep_angle=-s.swiss_eyelet_bend_degrees)),
        ) * 4)
    
    swiss_eyelet_node: ad.Node=ad.ShapeNode(stadium.StadiumSequence, prefix='swiss_eyelet_')
    
    fn: int=ad.dtfield(128)
    
    xEXAMPLE_ANCHORS=(
        ad.surface_args('eyelet', 'element-2', 'stadium', 'base', 0.5),
    )
    
    def build(self) -> ad.Maker:
        
        # Creates a stadium shape sequence.
        swiss_eyelet_shape = self.swiss_eyelet_node()
        
        maker = swiss_eyelet_shape.solid('eyelet').at('base')

        return maker

@ad.datatree
class CoinHolderProfile:
    '''The cross section of the coin ring.
    The default parameters are for a 5 Swiss Franc coin.
    '''
    t: float=ad.dtfield(2, doc='Thickness of the main outer portion of the adaptor.')
    h: float=ad.dtfield(2.4, doc='Height of the main outer portion of the adaptor.')
    ot: float=ad.dtfield(0.6, doc='Overhang of the top of the adaptor.')
    ob: float=ad.dtfield(0.75, doc='Overhang of the base of the adaptor.')
    oh: float=ad.dtfield(0.75, doc='Overhang thickness of the adaptor.')
    r: float=ad.dtfield(31.6 / 2, doc='Inner radius of the coin.')
    br: float=ad.dtfield(1.5, doc='Bend radius of the adaptor.')

    def build(self) -> ad.Path:
        path = (ad.PathBuilder()
                .move((self.r, 0))
                .line((self.r, self.h), 'left')
                .line((self.r - self.ot, self.h + self.oh), 'left_top_overhang')
                .line((self.r + self.t - self.br, self.h + self.oh), 'top')
                .arc_tangent_radius_sweep(self.br, -90, name='top_right_bevel')
                .line((self.r + self.t, - self.oh - - self.br), 'right')
                .arc_tangent_radius_sweep(self.br, -90, name='base_right_bevel')
                .line((self.r - self.ob, - self.oh), 'base')
                .line((self.r - self.ob, 0), 'left_base_overhang')
                .line((self.r, 0), 'left_overhang')
                ).build()
        return path


@ad.shape
@ad.datatree
class CoinHolderRing(ad.CompositeShape):
    '''A coin holder ring and eyelet. This can be used to make a coin to it can
    be a decoration for a Christmas tree.
    
    Best printed in TPU. It will be too difficult to insert the coin if printed
    in PLA. PETG might work.
    '''

    profile_node: ad.Node=ad.ShapeNode(CoinHolderProfile)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.profile_node().build())

    extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, expose_all=True)
    
    swiss_eyelet_node: ad.Node=ad.ShapeNode(SwissEyeletBase, expose_all=True)

    fn: int=128

    EXAMPLE_SHAPE_ARGS=ad.args()
    xEXAMPLE_ANCHORS=(
        ad.surface_args('eyelet', 'element-2', 'stadium', 'base', 0.5, rh=0.5),
    )

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('ring').at()
        
        swiss_eyelet_shape = self.swiss_eyelet_node()
        maker.add_at(
            swiss_eyelet_shape.solid('eyelet').at('element-2', 'stadium', 'left', 0.5, rh=0.5), 
                'ring', 'right', 0.5, post=ad.ROTZ_90 * ad.tranZ(-1.9))
        return maker
    

MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == "__main__":
    ad.anchorscad_main()
