'''
Created on 29 Sep 2023

@author: gianni



WARNING: THIS HAS NOT BEEN TESTED. THIS IS NOT GUARANTEED TO WORK.

The link to the Raspberry Pi 5 product brief is here:
https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-product-brief.pdf
(where the dimensions were used to configure the outline model)

'''

from anchorscad import datatree, Node, surface_args, anchorscad_main, shape, \
        ShapeNode, ModuleDefault, ROTX_270

from anchorscad_models.cases.rpi.rpi5_outline import RaspberryPi5Outline
from anchorscad_models.cases.rpi.rpi_case import RaspberryPiCase


@shape
@datatree(chain_post_init=True)
class RaspberryPi5Case(RaspberryPiCase):
    '''A Raspberry Pi 5 Case.'''
    
    CUT_PLANE = surface_args('outline', 'power_sw', 'base', post=ROTX_270)
    
    do_versioned_example: bool=False
    outline_model_node: Node=ShapeNode(RaspberryPi5Outline)
    fn: int=None
    
    # Some anchor locations for locating flange position and sizes.
    USBA2_A2 = surface_args(
        'outline', ('usbA2', 'outer'), 'face_edge', 1, 0, 0)
    USBA3_A1 = surface_args(
        'outline', ('usbA3', 'outer'), 'face_edge', 1, 0, 1)
    USBA2_A3 = surface_args(
        'outline', ('usbA2', 'outer'), 'face_edge', 1, 0, 1)
    ETH_A1 = surface_args(
        'outline', ('rj45', 'outer'), 'face_edge', 1, 0, 0)
    BOUND_LINES = (USBA2_A2, USBA3_A1, ETH_A1, USBA2_A3)
    
MAIN_DEFAULT=ModuleDefault(all=True)

if __name__ == "__main__":
    anchorscad_main(False)

