'''
Created on 29 May 2022

@author: gianni
'''

import anchorscad as ad
from anchorscad.models.basic.regular_prism import RegularPrism


@ad.shape
@ad.datatree
class BoltHeadRecess(ad.CompositeShape):
    '''
    Creates a recess for an N sided bolt head.
    '''
    bolt_head_d: float=14.8
    bolt_sides: int=6
    bolt_h: float=8
    bolt_r: float=ad.dtfield(
        self_default=lambda s: s.bolt_head_d / 2, init=False) 
    head_node: ad.Node=ad.dtfield(
        ad.ShapeNode(RegularPrism, 
                     {'nsides': 'bolt_sides', 'r': 'bolt_r', 'h': 'bolt_h'}))
    head_turns: int=3

    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        turn_angle = 360 / (self.bolt_sides * self.head_turns)
        bolt_head = self.head_node()
        maker = bolt_head.solid(('bolt_head', 0)).at('base')
        for i in range(1, self.head_turns):
            maker.add_at(
                bolt_head.solid(('bolt_head', i)).at('base', pre=ad.rotZ(i * turn_angle))
                )
        return maker

@ad.shape
@ad.datatree
class BoltCoverHat(ad.CompositeShape):
    '''
    A "hat" for the bolt cover with zip tie holes.
    '''
    r: float=20
    h: float=6
    head_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder))
    
    tie_r: float=3
    tie_h: float=20
    
    tie_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='tie_'))
    
    tie_count: int=9
    tie_offs: float=ad.dtfield(
        self_default=lambda s: s.r - s.tie_r - 2)
    
    epsilon: float=0.001

    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        maker = self.head_node().solid('hat').at('base')
        
        tie = self.tie_node()
        for i in range(self.tie_count):
            maker.add_at(tie.hole(('tie', i)).at('base'),
                         'base', rh=1, 
                         pre=ad.rotZ(i * 360 / self.tie_count) * ad.tranX(self.tie_offs), 
                         post=ad.ROTX_180 * ad.tranZ(self.epsilon))
        
        return maker


@ad.shape
@ad.datatree
class BoltCover(ad.CompositeShape):
    '''
    Battery terminal cover where the terminal is a hex bolt. Has space for
    cables terminating at the battery terminal.
    '''
    cover_r_top: float=14
    cover_r_base: float=10
    cover_h: float=10
    
    cover_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, prefix='cover_'), init=False)
    
    base_cover_hole_r: float=14.7/2
    base_cover_hole_h: float=1.3
    base_cover_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='base_cover_hole_'), init=False)
    
    upper_bolt_head_d: float=14.8
    upper_bolt_h: float=5.9
    upper_recess_node: ad.Node=ad.dtfield(
        ad.ShapeNode(BoltHeadRecess, prefix='upper_'), init=False)
    
    lower_bolt_head_d: float=14.6
    lower_bolt_h: float=2.1
    lower_recess_node: ad.Node=ad.dtfield(
        ad.ShapeNode(BoltHeadRecess, prefix='lower_'), init=False)
    
    hat_node: ad.Node=ad.dtfield(ad.ShapeNode(BoltCoverHat), init=False)
    
    epsilon: float=0.01
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)

    def build(self) -> ad.Maker:

        shape = self.cover_node()
        maker = shape.solid('cover').at('base', post=ad.ROTX_180)
        
        base_cover_hole = self.base_cover_hole_node()
        
        maker.add_at(base_cover_hole.hole('base_cover_hole').at('base'),
                     'base', post=ad.tranZ(self.epsilon))
        
        lower_recess = self.lower_recess_node()
        
        maker.add_at(lower_recess
                        .hole('lower_recess')
                        .colour((0.0, 1.0, 0.35, 0.4))
                        .at('base'),
                     'base_cover_hole', 'base', rh=1, post=ad.tranZ(self.epsilon))
        
        upper_recess = self.upper_recess_node()
        
        maker.add_at(upper_recess.hole('upper_recess').at('base'),
                     'lower_recess', 'base', rh=1, post=ad.tranZ(self.epsilon))
        
        hat = self.hat_node()
        
        maker.add_at(hat.composite('hat').at('base'),
                     'base', rh=1)

        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
