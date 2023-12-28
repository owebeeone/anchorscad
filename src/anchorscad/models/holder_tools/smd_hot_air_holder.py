'''
Created on 28-Dec-2023

@author: gianni
'''

import anchorscad as ad
from anchorscad.models.hinges.Hinge import HingeChain
from typing import Tuple

from anchorscad.models.basic.box_side_bevels import BoxSideBevels



@ad.shape
@ad.datatree
class HotAirHolderScaffold(ad.CompositeShape):
    '''
    Use a HingeChain to create a scaffold for the hot air gun holder.
    This makes holes for the ventilation that would otherwise be blocked by plate.
    '''
    
    bar_margin: float=ad.dtfield(3, doc='Margin between bar and edge of plate')
    bar_h: float=ad.dtfield(45, doc='Height of hinge bar')
    sep: float=ad.dtfield(0.2, doc='Separation between hinge sides')
    seg_count: int=ad.dtfield(11, 'Number of segments in hinge bar')
    
    chain_width_seq: Tuple[float, ...]=ad.dtfield((30, 63, 57), doc='Sequence of widths of chain links')
    hinge_chain_node: ad.Node=ad.ShapeNode(HingeChain)
    hinge_chain: HingeChain=ad.dtfield(
        self_default=lambda s: s.hinge_chain_node(),
        doc='The hinge chain to use for the scaffold')

    vent_margin: Tuple[float, float]=ad.dtfield((10, 8), doc='Margin between vent and edge of plate')
    
    vent_bevel_radius: float=ad.dtfield(8, doc='Bevel radius for vent holes')
    vent_node: ad.Node=ad.ShapeNode(BoxSideBevels, prefix='vent_')
    
    epsilon: float=ad.dtfield(0.01, doc='Epsilon to add to holes to prevent aliasing')
 
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=True,
                               fn=64)
    xEXAMPLE_ANCHORS=tuple((
        ad.surface_args('chain', ('plate', 0), 'face_centre', 'base'),
        ad.surface_args('chain', ('sep_cage', 0), 'face_centre', 'base'),
    ))

    
    def build(self) -> ad.Maker:

        maker = self.hinge_chain.solid('chain').at()
        
        for i in range(1, len(self.chain_width_seq)):
            vent_shape = self.make_vent(i)
            maker.add_at(
                vent_shape.hole(('vent', i)).colour('magenta').at('centre'),
                'chain', ('plate', i), 'centre')

        return maker
            
    def make_vent(self, i):
        '''Make a vent for the given link index.'''
        
        link_size = self.hinge_chain.compute_plate_size(i)
        
        bar_r = self.hinge_chain.hinge_shape.hinge_bar_shape.bar_r
        
        smaller_size = (link_size[0] - self.vent_margin[0] * 2,
                        link_size[1] - (self.vent_margin[1] + bar_r) * 2,
                        link_size[2] + self.epsilon)

        vent_shape = self.vent_node(size=smaller_size)

        
        return vent_shape
    
    
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()