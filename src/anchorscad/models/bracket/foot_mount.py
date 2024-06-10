'''
Created on 27-Dec-2023

@author: gianni
'''

import anchorscad as ad
from anchorscad.models.basic.trapezoid_prism import TrapezoidPrism

from anchorscad.models.screws.CountersunkScrew import CountersunkScrew

from anchorscad.models.screws.tnut import TnutM8


@ad.shape
@ad.datatree
class FootMount(ad.CompositeShape):
    '''
    A foot mount for a specific piece of furniture.
    '''
    base_w: float=ad.dtfield(71, "length of base of the trapezoid")
    side_l: float=ad.dtfield(105, "length of the trapezoid sides")
    top_w: float=ad.dtfield(61, "length of the top of the trapezoid")
    h: float=ad.dtfield(37, "height of the foot mount")
    trapz_node: ad.Node=ad.dtfield(ad.ShapeNode(TrapezoidPrism))
    
    foot_hole_centre_offset: float=ad.dtfield(
        42, "offset of the foot hole centre from the base of the trapezoid")
    
    screw_shaft_overall_length: float=ad.dtfield(
        50, doc='The overall length of the screw shaft.')
    screw_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.screw_shaft_overall_length,
        doc='The length of the screw shaft that freely passes the screw threads.')
    screw_size_name: str=ad.dtfield('DECK_10g-10', doc='The name of the screw size.')
    screw_hole_node: ad.Node=ad.ShapeNode(CountersunkScrew, prefix='screw_')
    
    screw_angle: float=ad.dtfield(45, doc='The angle of the screw hole.')
    screw_offset: float=ad.dtfield(24, doc='The X offsets of the screw holes.')
    
    
    tnut_node: ad.Node=ad.ShapeNode(TnutM8, prefix='tnut_')
    
    screw_relative_offsets: float=ad.dtfield((0.2, 0.45, 0.8), doc='The relative offsets of the screws.')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    
    xEXAMPLE_ANCHORS=(
        ad.surface_args('mount', 'right'),
        ad.surface_args('mount', 'path_base'),
        ad.surface_args(('screw_left', 0), 'top'),
        )
    

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.trapz_node()
        maker = shape.solid('mount').at('base', post=ad.ROTX_180)
        
        tnut_shape = self.tnut_node()
        
        maker.add_at(
            tnut_shape.hole('tnut').at('base'),
            'mount', 'path_base', 0.5, rh=1, post=ad.ROTX_270 * ad.tranY(self.foot_hole_centre_offset))
        
        screw_shape = self.screw_hole_node()
        for i, offset in enumerate(self.screw_relative_offsets):
            
            maker.add_at(
                screw_shape.composite(('screw_left', i)).at('top'),
                'mount', 'left', offset, 
                pre=ad.tranX(self.screw_offset) * ad.tranZ(3),
                post=ad.rotX(180-self.screw_angle))
            
            maker.add_at(
                screw_shape.composite(('screw_right', i)).at('top'),
                'mount', 'right', 1 - offset, 
                pre=ad.tranX(-self.screw_offset) * ad.tranZ(3), 
                post=ad.rotX(180-self.screw_angle) )
            
        
        return maker




# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
