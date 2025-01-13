'''
Created on 25/09/2024

@author: gianni
'''

import anchorscad as ad

from anchorscad_models.components.header.header import Header
from anchorscad_models.components.resistor.square_trimpot import Bourns3296
from anchorscad_models.screws.CountersunkScrew import FlatHeadScrew

PIN_PITCH = 2.54

@ad.shape
@ad.datatree(frozen=True)
class ArduinoNanoClassic(ad.CompositeShape):
    '''
    Outline for the classic Arduino Nano board.
    Pins are numbered from 1 to 30. Mount holes are numbered from 1 to 4
    in the same order as pins.
    '''
    pcb_size: tuple=ad.dtfield(
        (43.3, 18.5, 1.5),
        doc='The (x,y,z) size of PCB for the Arduino Nano Classic board')
    pcb_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='pcb_'))
    

    mount_r: float=1.7 / 2
    mount_h: float=ad.dtfield(self_default=lambda s: s.pcb_size[2] + 2 * s.epsilon)
    mount_node: ad.Node=ad.dtfield(ad.ShapeNode(
        ad.Cylinder, prefix='mount_', expose_all=True))
    
    small_fn: int=16
    pin_hole_r: float=1 / 2
    pin_hole_h: float=ad.dtfield(self_default=lambda s: s.pcb_size[2] + 2 * s.epsilon)
    pin_hole_node: ad.Node=ad.dtfield(ad.ShapeNode(
        ad.Cylinder, {'fn': 'small_fn'}, prefix='pin_hole_', expose_all=True))
    
    pitch: float=PIN_PITCH
    
    icsp_header_pins_x: int=2
    icsp_header_pins_y: int=3
    icsp_header_node: ad.Node=ad.ShapeNode(
        Header, {'pitch': 'pitch'}, prefix='icsp_header_', expose_all=True)
    
    usb_size: tuple=ad.dtfield((7.7, 5.7, 2.6))
    usb_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='usb_'))
    usb_anchor: tuple=ad.args('face_edge', 'right', 2, rh=0, post=ad.ROTZ_180 * ad.tranZ(1))
    
    epsilon: float=0.01
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=(
        ad.surface_args(('pin', 1), 'top', scale_anchor=0.5),
        ad.surface_args('icsp_header', ('pin', 1, 1), 'top', scale_anchor=0.5),
        )

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.pcb_node()
        maker = shape.solid('pcb').at('centre')
        

        pin_hole_shape = self.pin_hole_node()
        for i, pin_no, inc in ((-3, 0, 1), (3, 31, -1)):
            y = i * self.pitch
            for j in range(-7, 8):
                pin_no += inc
                x = j * self.pitch
                
                pin_hole = pin_hole_shape.hole(('pin', pin_no)) \
                    .colour('red').at('centre', post=ad.ROTX_180)
                maker.add_at(pin_hole, 
                            'centre', 
                            post=ad.translate((x, y, 0)))
                
        mount_hole_shape = self.mount_node()
        
        for i, mount_no, inc in ((-3, 0, 1), (3, 5, -1)):
            y = i * self.pitch
            for j in (-8, 8):
                mount_no += inc
                x = j * self.pitch
                mount_hole = mount_hole_shape.hole(('mount_hole', mount_no)) \
                    .colour('blue').at('centre')
                maker.add_at(mount_hole, 
                    'centre', 
                    post=ad.translate((x, y, 0)))
                
        icsp_header_shape = self.icsp_header_node()
        icsp_header = icsp_header_shape.solid('icsp_header').at('face_centre', 'base')
        maker.add_at(
            icsp_header, 'face_centre', 'top', 
            post=ad.ROTX_180 * ad.tranX(-7.5 * self.pitch))
        
        usb_shape = self.usb_node()
        usb_maker = usb_shape.solid('usb').at('face_edge', 'front', 0)
        maker.add_at(usb_maker, *self.usb_anchor[0], **self.usb_anchor[1])
        
        for pin_x in range(1, self.icsp_header_pins_x + 1):
            for pin_y in range(1, self.icsp_header_pins_y + 1):
                maker.add_at(
                    pin_hole_shape.hole(('pin_hole', pin_x, pin_y)).at('top'),
                    'icsp_header', ('pin', pin_x, pin_y), 'base',
                    post=ad.ROTX_180 * ad.tranZ(self.epsilon))
        
        return maker

    
@ad.shape
@ad.datatree
class ArduinoNanoClassicMountPad(ad.CompositeShape):

    board_node: ad.Node = ad.ShapeNode(ArduinoNanoClassic, {})
    board: ArduinoNanoClassic = ad.dtfield(self_default=lambda s: s.board_node())
    
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
    pcb_screw_hole_size_name=ad.dtfield('M1.6')
    
    
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
                .at('face_centre', 'top', rh=1, post=ad.tranZ(-1.5))
        
        maker.add_at(mock_board_maker, 'face_centre', 'top')
        
        pcb_screw_hole_shape = self.pcb_screw_hole_node()
        for i in range(1, 5):
            pcb_screw_hole = pcb_screw_hole_shape.composite(('pcb_screw_hole', i)).at('top')
            maker.add_at(pcb_screw_hole, 'mock_board', ('mount_hole', i), 'top', post=ad.ROTX_180)
        
        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
