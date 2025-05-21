'''
Created on 2025-05-16

@author: gianni
'''

import anchorscad as ad
import anchorscad_models.cases.outline_tools as ot 

DELTA=ot.DELTA

WROOM_PACKAGE=ot.ShapeFactory(
    ad.Box, 
    ad.args([15,  17, 3]),
    [0, 0, 0], 
    ad.args('face_edge', 4, 0, 0.5), 
    ot.IBOX_ANCHOR, 
    ot.no_op)

@ad.shape
@ad.datatree(chain_post_init=True)
class Esp32Outline(ot.BaseOutline):

    board_size: tuple=(28.5, 51.8, 1.6)
    bevel_radius: float=1.1
    
    CENTRES_X = (20 + 26.36) / 2
    CENTRES_Y = (43.8 + 50) / 2
    HOLE_POSITIONS=tuple(
        ot.OutlineHolePos(ot.OutlineHoleSpec(
            3.1 / 2, 
            3.1 / 2, 
            ad.surface_args('face_corner', 'top', 0)), 
            pos)
        for pos in
            ((2.6, 2.6), 
             (2.6, 2.6 + CENTRES_Y), 
             (2.6 + CENTRES_X, 2.6), 
             (2.6 + CENTRES_X, 2.6 + CENTRES_Y)))
    
    SIDE_ACCESS=ot.OutlineLayout(ad.surface_args('face_corner', 4, 0), (
        ('usbC', ot.USBC, ad.tranX(28.5 / 2)),
        ('cpu', WROOM_PACKAGE, ad.translate((28.5 / 2, 30, 0))),
        ))
    
    ALL_ACCESS_ITEMS=(SIDE_ACCESS,)

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
