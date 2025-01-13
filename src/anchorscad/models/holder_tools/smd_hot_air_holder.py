'''
Created on 28-Dec-2023

@author: gianni

Model for a hot air wand holder. See HotAirHolder class below.

Designed for a Gordak 853 / YIHUA 853A Bottom Heating Preheating Station PCB Preheater Soldering Station 
BGA Rework Station. See https://www.aliexpress.com/item/1005004627110148.html
'''

import anchorscad as ad
from anchorscad.models.hinges.Hinge import HingeChain
from typing import Tuple

from anchorscad.models.basic.box_side_bevels import BoxSideBevels
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew
from anchorscad.models.basic.box_cylinder import BoxCylinder

import numpy as np



@ad.shape
@ad.datatree
class HotAirHolderScaffold(ad.CompositeShape):
    '''
    Use a HingeChain to create a scaffold for the hot air gun holder.
    This makes holes for the ventilation that would otherwise be blocked by the hinge plates.
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
        '''Make a vent hole for the given link index.'''
        
        link_size = self.hinge_chain.compute_plate_size(i)
        
        # Should probably be a property of the hinge chain.
        bar_r = self.hinge_chain.hinge_shape.hinge_bar_shape.bar_r
        
        smaller_size = (link_size[0] - self.vent_margin[0] * 2,
                        link_size[1] - (self.vent_margin[1] + bar_r) * 2,
                        link_size[2] + self.epsilon)

        return self.vent_node(size=smaller_size)
    

@ad.shape
@ad.datatree
class HotAirHolderScrewLocator(ad.CompositeShape):
    '''Provides screw holes for the hot air holder mounting against existing M3
    threaded mounting holes on the preheating station. These holes were likely
    originally for mounting an air gun holder rest but this is a good use for these
    holes so there is it. The device has holes on the left and right sides of the
    preheating station. Holes are provided for both sides but only one side is needed.'''

    plate_h: float=ad.dtfield(7, doc='Height of plate')    
    screw_sep: float=ad.dtfield((13.47 + 18.83) / 2, doc='Separation between screws')
    
    screw_x_offset: float=ad.dtfield(38.68 - 31.64, doc='X offset between screws')
    screw_y_offset: float=ad.dtfield(54.6 - 39.85, doc='Y offset between screws')
    
    side: int=ad.dtfield(0, doc='Side of preheating station 0=Left, 1=Right')
    
    cage_size: Tuple[float, float, float]=ad.dtfield(
            self_default=lambda s: (s.screw_x_offset, s.screw_y_offset, s.plate_h), 
            doc='Size screw placement cage')
    
    cage_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    
    screw_shaft_overall_length: float=ad.dtfield(
        15, doc='The overall length of the screw shaft.')
    screw_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.screw_shaft_overall_length,
        doc='The length of the screw shaft that freely passes the screw threads.')
    screw_size_name: str=ad.dtfield('M3', doc='The name of the screw size.')
    screw_hole_node: ad.Node=ad.ShapeNode(CountersunkScrew, prefix='screw_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(screw_as_solid=True, fn=64)

    def build(self) -> ad.Maker:
        
        maker = self.cage_node().cage('screw_cage').at('centre')
        
        screw_shape = self.screw_hole_node()
        
        for i in range(2):
            maker.add_at(
                screw_shape.composite(('screw_hole', i)).at('top'),
                'face_corner', 'top', i * 2 + self.side)
        
        return maker


@ad.shape
@ad.datatree
class HotAirHolderPoleMountHoles(ad.CompositeShape):
    '''Provides holes for mounting the pole to the plate. These are just the
    mounting hole for the pole, the screw hole and the access hole the size of the screw head
    for the screw that holds the pole in place.'''
    
    pole_r: float=ad.dtfield(16.2 / 2, doc='Radius of pole')
    pole_h: float=ad.dtfield(50, doc='Height of pole')
    
    pole_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='pole_')
    
    pole_screw_r: float=ad.dtfield(5.2 / 2, doc='Radius of pole screws')
    pole_screw_h: float=ad.dtfield(12, doc='Height of pole screws')
    pole_screw_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='pole_screw_')
    
    pole_screw_access_r: float=ad.dtfield(16.2 / 2, doc='Radius of head of pole screws')
    pole_screw_access_h: float=ad.dtfield(50, doc='Height of pole screw access hole')
    pole_screw_access_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='pole_screw_access_')
    pole_screw_access_offset: float=ad.dtfield(8, doc='Offset of pole screw access hole from edge of plate')

    def build(self) -> ad.Maker:
        
        pole_hole_shape = self.pole_hole_node()
        maker = pole_hole_shape.solid('pole_hole').at('centre')
        
        screw_hole_shape = self.pole_screw_node()
        maker.add_at(screw_hole_shape.solid('pole_screw').at('top'),
                'top', post=ad.ROTX_180)
        
        screw_access_hole_shape = self.pole_screw_access_node()
        maker.add_at(screw_access_hole_shape.solid('pole_screw_access').at('top'),
                'pole_screw', 'top', post=ad.tranZ(-self.pole_screw_access_offset))
        
        return maker
    
@ad.shape
@ad.datatree
class HotAirHolderPoleMount(ad.CompositeShape):
    '''Combines the mount pole mounting model, HotAirHolderPoleMountHoles and
    a half rounded block to make a pole mount block.'''
    
    mount_holes_node: ad.Node=ad.ShapeNode(HotAirHolderPoleMountHoles)
    mount_holes: HotAirHolderPoleMountHoles=ad.dtfield(
        self_default=lambda s: s.mount_holes_node(),
        doc='The holes shape for the pole mount')

    mount_margin: float=ad.dtfield(3, doc='Margin between mount and edge of plate')
    
    mount_z_size_offset: float=ad.dtfield(-5, doc='Offset of mount size in Z')
    
    mount_size: Tuple[float, float, float]=ad.dtfield(
            self_default=lambda s: (s.mount_holes.pole_r * 2 + s.mount_margin * 2,
                                    s.mount_holes.pole_r * 2 + s.mount_z_size_offset,
                                    s.pole_h), 
            doc='Size of pole mount')
    
    mount_node: ad.Node=ad.ShapeNode(BoxCylinder, prefix='mount_')
    hole_depth: float=ad.dtfield(20, doc='Depth of hole for pole mount')
    
    def build(self) -> ad.Maker:
        
        mount_shape = self.mount_node()
        
        maker = mount_shape.composite('mount').at('centre')
        
        maker.add_at(
            self.mount_holes.hole('mount_holes').at('top'),
            'cylinder', 'top', post=ad.tranZ(self.hole_depth - self.mount_holes.pole_h))
        
        return maker


@ad.shape
@ad.datatree
class HotAirHolder(ad.CompositeShape):
    '''The final assembly of the hot air holder.
    '''
    
    scaffold_node: ad.Node=ad.ShapeNode(HotAirHolderScaffold)
    scaffold: HotAirHolderScaffold=ad.dtfield(
        self_default=lambda s: s.scaffold_node(),
        doc='The scaffold to use for the hot air holder')
    
    sl_plate_h: float=ad.dtfield(
        self_default=lambda s: s.scaffold.hinge_chain.hinge_shape.hinge_bar_shape.bar_r, 
        doc='Height of plate')
    
    screw_locator_node: ad.Node=ad.ShapeNode(HotAirHolderScrewLocator, prefix='sl_')
    screw_offset: Tuple[float, float, float]=ad.dtfield(
        default=(3, 2, -16), 
        doc='Offset of screw locator from edge of plate')
    
    pole_h: float=ad.dtfield(
        self_default=lambda s: s.scaffold.hinge_chain.compute_plate_size(0)[0],
        doc='Height of pole mount')
    pole_mount_node: ad.Node=ad.ShapeNode(HotAirHolderPoleMount)
    
    # Apply new defaults to injected fields for this device.
    nib_r: float=ad.dtfield(4.3, 'Radius of inner hinge nib')
    seg_count: int=ad.dtfield(10, 'Number of segments in hinge bar')
    chain_width_seq: Tuple[float, ...]=ad.dtfield((32, 85, 75), doc='Sequence of widths of chain links')
    sep: float=ad.dtfield(0.17, 'Separation between hinge sides. Depends on how accurate the printer is.')
    fn: int=ad.dtfield(128, doc='Number of facets')
    
    
    def build(self) -> ad.Maker:
        
        maker = self.scaffold.solid('scaffold').at()
        
        screw_locator_left_shape = self.screw_locator_node()
        maker.add_at(
            screw_locator_left_shape.composite('screw_locator_left').at('face_edge', 'right', 2),
            'chain', ('plate', 0), 'face_edge', 'left', 2, post=ad.translate(self.screw_offset))
        
        
        screw_locator_right_shape = self.screw_locator_node(side=1)
        right_offset = np.array(self.screw_offset) + np.array((0, 0, -12))
        maker.add_at(
            screw_locator_right_shape.composite('screw_locator_right').at('face_edge', 'right', 2),
            'chain', ('plate', 0), 'face_edge', 'left', 2, post=ad.translate(right_offset))
        
        mount_shape = self.pole_mount_node()
        maker.add_at(
            mount_shape.composite('pole_mount').at('face_corner', 'back', 2),
            'scaffold', 'chain', ('plate', 2), 'face_corner', 'base', 3)
        
        return maker
    
    
    
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()