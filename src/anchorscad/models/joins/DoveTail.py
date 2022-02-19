'''
Created on 21 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l
from ParametricSolid.extrude import PathBuilder, LinearExtrude

@core.shape('anchorscad.models.joins')
@dataclass
class DoveTail(core.CompositeShape):
    '''Creates a dovetail join.
    Args:
     overall_width: Width of the enclosing volume.
     overall_height: Height of the enclosing volume.
     t: Thickness of the enclosing volume.
     side: False selects the upper jaw and True the lower jaw.
     dt_edge_width: The width of the dove tail.
     dt_widtha: The larger width of the dove tail.
     dt_widthb: The smaller width of the dove tail.
     edge_shrink: Allowance to overhang (printer error compensation).
    '''
    overall_width: float=90
    overall_height: float=30
    t: float=3
    side: bool=False
    dt_edge_width: float=60
    dt_depth: float=8
    dt_widtha: float=12 # Approximate
    dt_widthb: float=8 # Approximate
    edge_shrink: float=0.01 
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={
        'upper': core.ExampleParams(
            shape_args=core.args(side=False),
            anchors=()),
        'lower': core.ExampleParams(
            shape_args=core.args(side=True),
            anchors=())
        }
    
    def __post_init__(self):
        
        box_size = [self.overall_width, self.overall_height, self.t]
        maker = core.Box(box_size).cage(
            'dovetail_cage').colour([1, 1, 0, 0.5]).at('centre')
            
        dt_width = (self.dt_widtha + self.dt_widthb) / 2
        dt_overhang = self.dt_widtha - self.dt_widthb
        trial_count = int((self.dt_edge_width - dt_overhang) / dt_width)
        assert trial_count > 0, f'Allocated dovetail width ({dt_width}) is too small.'
        
        # Make an even number of tails
        count = trial_count - 1 if trial_count & 1 else trial_count
        
        actual_dt_width = self.dt_edge_width / count
        adj_factor = actual_dt_width / dt_width
        actual_dt_widtha = self.dt_widtha * adj_factor
        
        offseta = actual_dt_widtha / 4 + self.edge_shrink
        depth = self.dt_depth + self.edge_shrink
        mid_offset = 0.5 * actual_dt_width
        
        # Makes a single tail path and reuse.
        dt_path = (PathBuilder().move([0, 0])
                   .line((-offseta, 0), ('front', 'right'))
                   .line((offseta - mid_offset, depth), ('side', 'right'))
                   .line((-mid_offset, depth), ('back', 'right'))
                   .line((-offseta - mid_offset, depth), ('back', 'left'))
                   .line((-actual_dt_width + offseta, 0), ('side', 'left'))
                   .line((-actual_dt_width, 0), ('front', 'left'))
                   .build()
                   )
                    
        pathbuilder = PathBuilder().move([0, 0])
        dw_trans = l.translate([-actual_dt_width, 0, 0])
        dw_current_trans = l.IDENTITY
        
        half_count = count // 2
        
        for i in range(half_count - 1, -1, -1):
            pathbuilder = dt_path.transform_to_builder(
                dw_current_trans, pathbuilder, (i,))
            dw_current_trans = dw_current_trans * dw_trans

        
        half_height = self.overall_height / 2
        if self.side:
            half_height = -half_height
        (pathbuilder
               .line([-self.overall_width / 2, 0],
                     ('outline', 'front', 'left'))
               .line([-self.overall_width / 2, half_height],
                     ('outline', 'side', 'left'))
               .line([0, half_height],
                     ('outline', 'back', 'left'))
               .line([self.overall_width / 2, half_height],
                     ('outline', 'back', 'right'))
               .line([self.overall_width / 2, 0],
                     ('outline', 'side', 'right'))
               .line([half_count * actual_dt_width, 0],
                     ('outline', 'front', 'right'))
               )
        
        dw_current_trans = dw_current_trans.I
        for i in range(count - 1, half_count - 1, -1):
            pathbuilder = dt_path.transform_to_builder(
                dw_current_trans, pathbuilder, (i,))
            dw_current_trans = dw_current_trans * dw_trans

        path = pathbuilder.build()
        
        shape = LinearExtrude(path, h=self.t)
        
        maker.add_at(shape.solid('front').at(
            ('front', 'right', half_count - 1), post=l.ROTX_90),
                     'face_centre', 1)
        
        self.maker = maker
        
if __name__ == '__main__':
    core.anchorscad_main(False)
