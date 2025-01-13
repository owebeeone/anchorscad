'''
Created on 25/09/2024

@author: gianni
'''

import anchorscad as ad

from anchorscad_models.components.resistor.square_trimpot import Bourns3296
from anchorscad_models.screws.CountersunkScrew import FlatHeadScrew


@ad.shape
@ad.datatree(frozen=True)
class ModuleBuckLm2586Hw411(ad.CompositeShape):
    '''
    Outline for a buck converter module with LM2596 and HW411 components.
    '''
    pcb_size: tuple=ad.dtfield(
        (43, 21.5, 1.5),
        doc='The (x,y,z) size of PCB for the buck converter module')
    pcb_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='pcb_'))
    
    cap_h: float=11.7 - 1.5
    cap_r: float=4
    cap_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='cap_'))
    
    mount_r: float=1.5
    mount_h: float=ad.dtfield(self_default=lambda s: s.pcb_size[2] + 2 * s.epsilon)
    mount_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='mount_'))
    
    trimpot_node: ad.Node = ad.ShapeNode(Bourns3296, {})
        
    epsilon: float=0.01
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.pcb_node()
        maker = shape.solid('pcb').at('centre')
        
        cap_shape = self.cap_node()
        
        cap_in = cap_shape.solid('cap_in').at('surface', 0)
        maker.add_at(cap_in, 'face_edge', 'left', 2, post=ad.ROTZ_180)
        
        cap_out = cap_shape.solid('cap_out').at('surface', 0)
        maker.add_at(cap_out, 'face_edge', 'right', 2, post=ad.ROTZ_180)
        
        mount_hole_shape = self.mount_node()
        
        
        for i, c, sign in ((0, 'left', -1), (1, 'right', 1)):
            mount_hole = mount_hole_shape.hole(('mount_hole', i)) \
                .at('base', 0)
            maker.add_at(mount_hole, 
                         'face_corner', c, 2, 1, 
                         pre=ad.translate(
                             (-(5.1 + mount_hole_shape.h) * sign, 
                              (1.15 + mount_hole_shape.h) * sign,
                              self.epsilon)),
                         post=ad.ROTX_90)
            
        trimpot = self.trimpot_node(variant='W')
        
        trimpot_maker = trimpot.solid('trimpot').at('mount_corner')
        
        maker.add_at(trimpot_maker, 
                     'face_corner', 'top', 0, 
                     post=ad.ROTX_180 * ad.ROTZ_180 * ad.translate((-20, 1.13, 0)))
        
        return maker

    
@ad.shape
@ad.datatree
class ModuleBuckLm2586Hw411MountPad(ad.CompositeShape):

    board_node: ad.Node = ad.ShapeNode(ModuleBuckLm2586Hw411, {})
    board: ModuleBuckLm2586Hw411 = ad.dtfield(self_default=lambda s: s.board_node())
    
    pad_margin: tuple=(0.2, 0.2, 6)
    pad_box_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (
            s.board.pcb_size[0] + s.pad_margin[0] * 2, 
            s.board.pcb_size[1] + s.pad_margin[1] * 2, 
            s.pad_margin[2]),
        doc='Size of the pad box')
    pad_box_node: ad.Node = ad.ShapeNode(
        ad.Box, prefix='pad_box_', expose_all=True)
    
    pcb_screw_hole_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: s.pad_box_size[2] - 0.01,
        doc='Overall screw length')
    pcb_screw_hole_shaft_thru_length: float=0
    pcb_screw_hole_tap_len: float=ad.dtfield(
        self_default=lambda s: s.pcb_screw_hole_shaft_overall_length 
                             - s.pcb_screw_hole_shaft_thru_length)
    pcb_screw_hole_size_name=ad.dtfield('M3')
    
    
    pcb_screw_hole_node: ad.Node=ad.dtfield(ad.ShapeNode(FlatHeadScrew, prefix='pcb_screw_hole_'))
    
    mock_board_material = ad.Material('mock_board', kind=ad.NON_PHYSICAL_MATERIAL_KIND)
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64,
                                 pcb_screw_hole_hide_cage=False,
                                 pcb_screw_hole_shaft_hide_cage=False)
    
    EXAMPLE_ANCHORS = (ad.surface_args('face_centre', 'base'),)
        
    def build(self) -> ad.Maker:
        
        pad_box = self.pad_box_node()
        maker = pad_box.solid('pad_box').at('face_centre', 'base', post=ad.ROTX_180)

        mock_board_maker = self.board.solid('mock_board') \
                .material(self.mock_board_material) \
                .at('face_centre', 'top', rh=1, post=ad.tranZ(-0.2))
        
        maker.add_at(mock_board_maker, 'face_centre', 'top')
        
        
        pcb_screw_hole_shape = self.pcb_screw_hole_node()
        for i in range(2):
            pcb_screw_hole = pcb_screw_hole_shape.composite(('pcb_screw_hole', i)).at('top')
            maker.add_at(pcb_screw_hole, 'mock_board', ('mount_hole', i), 'top', post=ad.ROTX_180)
        
        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
