'''
Created on 8 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l

@core.shape('anchorscad.models.geometry.plane_line')
@dataclass
class PlaneLine(core.CompositeShape):
    '''
    Example of planes intersecting at a line.
    This is a demonstration of the plane-plane and line-plane intersection
    api.
    '''
    plane1: l.GMatrix = l.translate([0, 0, 0]) * l.rotV([1, 0.5, 0], 95)
    plane2: l.GMatrix = l.translate([0, 0, 0]) * l.rotV([10, -10.3, 0 ], 45)
    plane3: l.GMatrix = l.translate([10, -10, -20]) * l.rotV([1, 1, 1], 170)
    size: tuple = (100, 100, 0.1)
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
    
    def __post_init__(self):
        maker = core.AnnotatedCoordinates().cage('origin').at()
        self.maker = maker
        maker.add_at(
            core.Box(self.size).solid('plane1')
            .transparent(True).colour([1, 1, 0, 0.3]).at('centre'),
            pre = self.plane1)
        
        maker.add_at(
            core.Box(self.size).solid('plane2')
            .transparent(True).colour([0, 1, 1, 0.3]).at('centre'),
            pre = self.plane2)
          
        maker.add_at(
            core.AnnotatedCoordinates().solid('plane2_coords').at(),
            'plane2', 'centre')
         
        maker.add_at(
            core.Box(self.size).solid('plane3')
            .transparent(True).colour([1, 0, 1, 0.3]).at('centre'),
            pre = self.plane3)
          
        maker.add_at(
            core.AnnotatedCoordinates().solid('plane3_coords').at(),
            'plane3', 'centre')
         
        plane1_mat = maker.at('plane1', 'centre')
        plane2_mat = maker.at('plane2', 'centre')
        plane3_mat = maker.at('plane3', 'centre')
        plane2_mat_xlated = plane2_mat * l.translate([40, 0, 0])
        
        maker.add_at(
            core.AnnotatedCoordinates().solid('plane2_moved_coords').at(),
            pre=plane2_mat_xlated)
        
        intersection = l.plane_intersect(plane2_mat_xlated, plane1_mat)
        
        maker.add_at(
            core.AnnotatedCoordinates(label='plane-plane-X')
                .solid('l.plane_intersect').at(),
            pre=intersection)
        
        intersection_point = l.plane_line_intersect(plane3_mat, intersection)
        
        maker.add_at(
            core.AnnotatedCoordinates(label="line-plane-X")
                .solid('l.plane_line_intersect').at(),
            pre=intersection_point)

if __name__ == '__main__':
    core.anchorscad_main(False)
