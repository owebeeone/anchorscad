'''
Created on 29 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
from anchorscad.models.screws.holes import CountersinkSelfTapHole
from anchorscad.models.basic.box_cylinder import BoxCylinder


@core.shape('anchorscad.models.screws.screw_tab')
@dataclass
class ScrewTab(core.CompositeShape):
    '''
    <description>
    '''
    dia: float=2.6 # Screw M size
    width: float=dia * 1.9 + 2
    depth: float=dia * 1.5 / 2 + 1
    h: float=8 
    screw: type=CountersinkSelfTapHole
    fn: int=36
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=(core.surface_args('face_corner', 0, 0),)
    
    def __post_init__(self):
        max_outer_dia = (
            self.width 
            if self.width < self.depth * 2 
            else self.depth * 2)
        tab = BoxCylinder((self.depth, self.width, self.h), fn=self.fn)
        screw =self.screw(
            dia = self.dia,
            thru_len=self.h, 
            tap_len=0, 
            outer_delta=None,
            outer_dia=max_outer_dia, 
            counter_sink_overlap=0.5,
            fn=self.fn)
        
        maker = tab.solid('tab').at('face_corner', 0, 0)
        maker.add_at(screw.composite('screw').at('top'), 
                     'cylinder', 'top')
        
        self.maker = maker

    @core.anchor('An example anchor specifier.')
    def side(self, *args, **kwds):
        return self.maker.at('face_edge', *args, **kwds)

if __name__ == '__main__':
    core.anchorscad_main(False)
