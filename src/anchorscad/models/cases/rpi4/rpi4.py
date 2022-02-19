'''
Created on 25 Jan 2021

@author: gianni
'''

from ParametricSolid.datatree import datatree, Node

import ParametricSolid.core as core
from anchorscad.models.cases.rpi4.rpi4_outline import RaspberryPi4Outline
from anchorscad.models.cases.rpi4.rpi_case import RaspberryPiCase


@core.shape('anchorscad/models/cases/rpi4_case')
@datatree
class RaspberryPi4Case(RaspberryPiCase):
    '''A Raspberry Pi 4 Case.'''
    do_versioned_example: bool=False
    outline_model_class: Node=Node(RaspberryPi4Outline)
    
if __name__ == "__main__":
    core.anchorscad_main(False)

