'''
Created on 16 Nov 2021

@author: gianni
'''

from anchorscad import args, shape, tranX, translate, datatree, \
    surface_args, anchorscad_main

import anchorscad_models.cases.outline_tools as ot 

DELTA=ot.DELTA

@shape
@datatree(chain_post_init=True)
class RaspberryPi4Outline(ot.BaseOutline):

    board_size: tuple=(85, 56, 1.5)
    bevel_radius: float=3.0
    
    HOLE_POSITIONS=tuple(
        ot.OutlineHolePos(ot.OutlineHoleSpec(
            2.7/2, 
            5.5/2, 
            surface_args('face_corner', 'top', 0)), 
            pos)
        for pos in
            ((3.5, 3.5), (3.5, 3.5 + 49), (3.5 + 58, 3.5), (3.5 + 58, 3.5 + 49)))
    
    SIDE_ACCESS=ot.OutlineLayout(surface_args('face_corner', 4, 0), (
        ('usbC', ot.USBC, tranX(3.5 + 7.7)),
        ('hdmi1', ot.MICRO_HDMI, tranX(3.5 + 7.7 + 14.8)),
        ('hdmi2', ot.MICRO_HDMI, tranX(3.5 + 7.7 + 14.8 + 13.5)),
        ('audio', ot.AUDIO, tranX(3.5 + 7.7 + 14.8 + 13.5 + 7 + 7.5)),
        ('cpu', ot.CPU_PACKAGE, translate((22.0, 25, 0))),
        ))

    OSIDE_ACCESS=ot.OutlineLayout(surface_args('face_corner', 4, 2), (
        ('header100', ot.HEADER_100, tranX(27.0)),
        ))
    
    FRONT_ACCESS=ot.OutlineLayout(surface_args('face_corner', 4, 1), (
        ('usbA2', ot.USBA, tranX(9)),
        ('usbA3', ot.USBA, tranX(27)),
        ('rj45', ot.ETHERNET, tranX(45.75)),
        ))
    
    BOTTOM_ACCESS=ot.OutlineLayout(surface_args('face_corner', 1, 3), (
        ('micro_sd', ot.MICRO_SD, tranX((34.15 + 22.15) / 2)),
        ))
    
    ALL_ACCESS_ITEMS=(SIDE_ACCESS, FRONT_ACCESS, BOTTOM_ACCESS, OSIDE_ACCESS)

    EXAMPLE_SHAPE_ARGS=args(fn=32)


if __name__ == "__main__":
    anchorscad_main(False)

