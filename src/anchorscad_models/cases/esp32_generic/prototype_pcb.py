'''
Created on 2025-05-16

@author: gianni
'''

import anchorscad as ad
import anchorscad_models.cases.outline_tools as ot 

DELTA=ot.DELTA

@ad.shape
@ad.datatree(chain_post_init=True)
class PrototypePcbOutline(ot.BaseOutline):

    board_size: tuple=(50, 70, 1.5)
    bevel_radius: float=0.1
    
    CENTRES_X = (48.3 + 44.1) / 2
    CENTRES_Y = (68 + 63.7) / 2
    HOLE_R = (48.3 - 44.1) / 4
    HOLE_POSITIONS=tuple(
        ot.OutlineHolePos(ot.OutlineHoleSpec(
            3.1 / 2, 
            3.1 / 2, 
            ad.surface_args('face_corner', 'top', 0)), 
            pos)
        for pos in
            ((2, 2), 
             (2, 2 + CENTRES_Y), 
             (2 + CENTRES_X, 2), 
             (2 + CENTRES_X, 2 + CENTRES_Y)))

    
    ALL_ACCESS_ITEMS=()
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
