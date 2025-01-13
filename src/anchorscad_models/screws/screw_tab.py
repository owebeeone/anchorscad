'''
Tabs with screw hole support models.

Created on 29 Sep 2021

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.screws.holes import CountersinkSelfTapHole
from anchorscad_models.basic.box_cylinder import BoxCylinder


@ad.shape
@ad.datatree
class ScrewTab(ad.CompositeShape):
    '''
    Creates a tab with a screw hold. Can be placed on the side of a box
    to make a support hole.
    '''
    dia: float=2.6 # Screw M size
    width: float=dia * 1.9 + 2
    depth: float=dia * 1.5 / 2 + 1
    h: float=8 
    screw: type=CountersinkSelfTapHole
    box_cyl_node: ad.Node=ad.ShapeNode(BoxCylinder, {})
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=(
        ad.surface_args('side'),
        ad.surface_args('face_corner', 0, 0),
        ad.surface_args('round_top'),)
    
    def build(self) -> ad.Maker:
        tab = self.box_cyl_node((self.width, self.depth, self.h))
        max_outer_dia = (
            self.width 
            if self.width < self.depth * 2 
            else self.depth * 2)
        screw = self.screw(
            dia=self.dia,
            thru_len=self.h, 
            tap_len=0, 
            outer_delta=None,
            outer_dia=max_outer_dia, 
            counter_sink_overlap=0.5,
            fn=self.fn)
        
        maker = tab.solid('tab').at('face_corner', 0, 0)
        maker.add_at(screw.composite('screw').at('top'), 
                     'round_top')
        
        return maker

    @ad.anchor('Mounting point.')
    def side(self, face='back', edge=2):
        return self.maker.at('face_edge', face, edge)


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
