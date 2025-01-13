'''
Created on 25 Jan 2021

@author: gianni
'''

from datatrees import datatree, Node

import anchorscad.core as core
from anchorscad_models.cases.rpi.rpi4_outline import RaspberryPi4Outline
from anchorscad_models.cases.rpi.rpi_case import RaspberryPiCase
from anchorscad_models.vent.fan.fan_vent import FanVentScrewHoleParams, FAN_30x7_TYPE3


@core.shape
@datatree(chain_post_init=True)
class RaspberryPi4Case(RaspberryPiCase):
    '''A Raspberry Pi 4 Case.'''
    do_versioned_example: bool=False
    outline_model_node: Node=Node(RaspberryPi4Outline)


@core.shape
@datatree(chain_post_init=True)
class RaspberryPi4CaseFanType3(RaspberryPiCase):
    '''A Raspberry Pi 4 Case.'''
    do_versioned_example: bool=False
    fan_vent_screw_params: FanVentScrewHoleParams=FAN_30x7_TYPE3
    outline_model_node: Node=Node(RaspberryPi4Outline)
    
MAIN_DEFAULT=core.ModuleDefault(all=True)

if __name__ == "__main__":
    core.anchorscad_main(False)
