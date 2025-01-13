'''
Created on 16 Nov 2021

@author: gianni
'''

from anchorscad import args, shape, tranX, tranY, translate, datatree, \
    surface_args, anchorscad_main, ModuleDefault

import anchorscad_models.cases.outline_tools as ot 

DELTA=ot.DELTA


@shape
@datatree(chain_post_init=True)
class RaspberryPi5Outline(ot.BaseOutline):

    board_size: tuple=(85, 56, 1.5)
    bevel_radius: float=3.0
    
    HOLE_POSITIONS=tuple(
        ot.OutlineHolePos(ot.OutlineHoleSpec(
                2.7/2, 
                5.5/2, 
                surface_args('face_corner', 4, 0)), 
            pos)
        for pos in
            ((3.5, 3.5), (3.5, 3.5 + 49), (3.5 + 58, 3.5), (3.5 + 58, 3.5 + 49)))
    
    SIDE_ACCESS=ot.OutlineLayout(surface_args('face_corner', 4, 0), (
        ('usbC', ot.USBC, tranX(11.2)),
        ('hdmi1', ot.MICRO_HDMI, tranX(25.8)),
        ('hdmi2', ot.MICRO_HDMI, tranX(39.2)),
        ('cpu', ot.CPU_PACKAGE_PI5, translate((24.0, 15, 0))),
        ))

    OSIDE_ACCESS=ot.OutlineLayout(surface_args('face_corner', 4, 2), (
        ('header100', ot.HEADER_100_CENTRE, tranX(85 - 3.5 - 29)),
        ))
    
    FRONT_ACCESS=ot.OutlineLayout(
        surface_args('face_corner', 4, 1, post=tranY(1)), (
        ('usbA2', ot.USBA, tranX(29.1)),
        ('usbA3', ot.USBA, tranX(47)),
        ('rj45', ot.ETHERNET, tranX(10.2)),
        ))
    
    BOTTOM_ACCESS=ot.OutlineLayout(surface_args('face_corner', 1, 3), (
        ('micro_sd', ot.MICRO_SD, tranX((34.0 + 22.0) / 2)),
        ))
    
    REAR_ACCESS=ot.OutlineLayout(surface_args('face_corner', 4, 3), (
        ('power_sw', ot.POWER_SW, tranX(56 - 18.4)),
        ))
    
    ALL_ACCESS_ITEMS=(SIDE_ACCESS, FRONT_ACCESS, BOTTOM_ACCESS, OSIDE_ACCESS, REAR_ACCESS)

    EXAMPLE_SHAPE_ARGS=args(fn=32)


MAIN_DEFAULT=ModuleDefault(True)

if __name__ == "__main__":
    anchorscad_main(False)

