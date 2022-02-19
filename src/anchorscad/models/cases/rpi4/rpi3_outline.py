'''
Created on 16 Nov 2021

@author: gianni
'''

from dataclasses import dataclass

import ParametricSolid.core as core
from ParametricSolid.linear import tranX, tranY, tranZ, ROTX_180, \
                                   translate
import ParametricSolid.linear as l
import anchorscad.models.basic.box_side_bevels as bbox
from anchorscad.models.basic.TriangularPrism import TriangularPrism
from anchorscad.models.grille.case_vent.basic import RectangularGrilleHoles
from anchorscad.models.fastners.snaps import Snap
from anchorscad.models.vent.fan.fan_vent import FanVent
from anchorscad.models.screws.screw_tab import ScrewTab
import anchorscad.models.cases.outline_tools as ot 
from time import time

DELTA=ot.DELTA

@core.shape('anchorscad/models/cases/rpi3_outline')
@dataclass
class RaspberryPi3Outline(ot.BaseOutline):

    board_size: tuple=(85, 56, 1.5)
    bevel_radius: float=3.0
    
    HOLE_POSITIONS=tuple(
        ot.OutlineHolePos(ot.OutlineHoleSpec(
            2.7/2, 
            5.5/2, 
            core.surface_args('face_corner', 4, 0)), 
            pos)
        for pos in
            ((3.5, 3.5), (3.5, 3.5 + 49), (3.5 + 58, 3.5), (3.5 + 58, 3.5 + 49)))
    
    SIDE_ACCESS=ot.OutlineLayout(core.surface_args('face_corner', 4, 0), (
        ('usbM', ot.USBMICRO, tranX(10.6)),
        ('hdmi1', ot.HDMI_A, tranX(32)),
        ('audio', ot.AUDIO, tranX(53.5)),
        ('cpu', ot.CPU_PACKAGE, translate((20.0, 24.5, 0))),
        ))

    OSIDE_ACCESS=ot.OutlineLayout(core.surface_args('face_corner', 4, 2), (
        ('header100', ot.HEADER_100, tranX(27.0)),
        ))
    
    FRONT_ACCESS=ot.OutlineLayout(
        core.surface_args('face_corner', 4, 1, post=tranY(1)), (
        ('usbA2', ot.USBA, tranX(29)),
        ('usbA3', ot.USBA, tranX(47)),
        ('rj45', ot.ETHERNET, tranX(10.4)),
        ))
    
    BOTTOM_ACCESS=ot.OutlineLayout(core.surface_args('face_corner', 1, 3), (
        ('micro_sd', ot.MICRO_SD, tranX((34.0 + 22.0) / 2)),
        ))
    
    ALL_ACCESS_ITEMS=(SIDE_ACCESS, FRONT_ACCESS, BOTTOM_ACCESS, OSIDE_ACCESS)

    EXAMPLE_SHAPE_ARGS=core.args(fn=32)


if __name__ == "__main__":
    core.anchorscad_main(False)

