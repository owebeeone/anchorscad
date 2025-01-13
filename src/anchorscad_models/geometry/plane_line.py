'''
Created on 8 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import anchorscad as ad

@ad.shape
@dataclass
class PlaneLine(ad.CompositeShape):
    '''
    Example of planes intersecting at a line.
    This is a demonstration of the plane-plane and line-plane intersection
    api.
    '''
    plane1: ad.GMatrix = ad.translate([0, 0, 0]) * ad.rotV([1, 0.5, 0], 95)
    plane2: ad.GMatrix = ad.translate([0, 0, 0]) * ad.rotV([10, -10.3, 0 ], 45)
    plane3: ad.GMatrix = ad.translate([10, -10, -20]) * ad.rotV([1, 1, 1], 170)
    size: tuple = (100, 100, 0.1)
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        maker = ad.AnnotatedCoordinates().cage('origin').at()
        maker.add_at(
            ad.Box(self.size).solid('plane1')
            .transparent(True).colour([1, 1, 0, 0.3]).at('centre'),
            pre = self.plane1)
        
        maker.add_at(
            ad.Box(self.size).solid('plane2')
            .transparent(True).colour([0, 1, 1, 0.3]).at('centre'),
            pre = self.plane2)
          
        maker.add_at(
            ad.AnnotatedCoordinates().solid('plane2_coords').at(),
            'plane2', 'centre')
         
        maker.add_at(
            ad.Box(self.size).solid('plane3')
            .transparent(True).colour([1, 0, 1, 0.3]).at('centre'),
            pre = self.plane3)
          
        maker.add_at(
            ad.AnnotatedCoordinates().solid('plane3_coords').at(),
            'plane3', 'centre')
         
        plane1_mat = maker.at('plane1', 'centre')
        plane2_mat = maker.at('plane2', 'centre')
        plane3_mat = maker.at('plane3', 'centre')
        plane2_mat_xlated = plane2_mat * ad.translate([40, 0, 0])
        
        maker.add_at(
            ad.AnnotatedCoordinates().solid('plane2_moved_coords').at(),
            pre=plane2_mat_xlated)
        
        intersection = ad.plane_intersect(plane2_mat_xlated, plane1_mat)
        
        maker.add_at(
            ad.AnnotatedCoordinates(label='plane-plane-X')
                .solid('ad.plane_intersect').at(),
            pre=intersection)
        
        intersection_point = ad.plane_line_intersect(plane3_mat, intersection)
        
        maker.add_at(
            ad.AnnotatedCoordinates(label="line-plane-X")
                .solid('ad.plane_line_intersect').at(),
            pre=intersection_point)
        
        return maker

if __name__ == '__main__':
    ad.anchorscad_main(False)
