'''
Created on 25 Jan 2021

@author: gianni
'''

from anchorscad.datatree import datatree, Node

import anchorscad.core as core
from anchorscad.models.cases.rpi.rpi3_outline import RaspberryPi3Outline
from anchorscad.models.cases.rpi.rpi_case import RaspberryPiCase
from anchorscad.linear import translate


@core.shape('anchorscad/models/cases/rpi3_case')
@datatree(chain_post_init=True)
class RaspberryPi3Case(RaspberryPiCase):
    '''A Raspberry Pi 3 Case.'''
    inner_size_delta: tuple=(1, 2, 22)
    inner_offset: tuple=(-0.5, 1, 3)
    rhs_grille_y_offs: float=5
    do_versioned_example: bool=False
    outline_model_class: Node=Node(RaspberryPi3Outline)
    fn: int=None
    
    HEADER_CORNER = core.surface_args(
        'outline', 'header100', 'face_edge', 3, 0, 0.5,
        post=translate([0, -rhs_grille_y_offs, 0]))
    
    # Some anchor locations for locating flange position and sizes.
    USBA2_A2 = core.surface_args(
        'outline', ('usbA2', 'outer'), 'face_edge', 1, 0, 0)
    USBA3_A1 = core.surface_args(
        'outline', ('usbA3', 'outer'), 'face_edge', 1, 0, 1)
    USBA2_A3 = core.surface_args(
        'outline', ('usbA2', 'outer'), 'face_edge', 1, 0, 1)
    ETH_A1 = core.surface_args(
        'outline', ('rj45', 'outer'), 'face_edge', 1, 0, 0)
    BOUND_LINES = (USBA2_A2, USBA3_A1, ETH_A1, USBA2_A3)
    

if __name__ == "__main__":
    core.anchorscad_main(False)

