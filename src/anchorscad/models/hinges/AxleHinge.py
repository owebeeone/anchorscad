'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad
import numpy as np

@ad.datatree
class AxleSegmentPathBuilder:
    '''
    <description>
    '''
    r: float=ad.dtfield(6, doc='The outer radius of the axle')
    fl: float=ad.dtfield(12, doc='The length of the foot')
    foot_curvature: float=ad.dtfield((0.5, 0.5), doc='The curvature of the foot')
    ft: float=ad.dtfield(3, doc='The thickness of the axle foot')
    bevel_angle: float=ad.dtfield(60, doc='The angle where the base of the sxle is a line')
    sep: float=ad.dtfield(0.2, doc='The separation between axle components')

    def build(self) -> ad.Path:
        
        sinr = np.sin(np.radians(self.bevel_angle))
        cosr = np.cos(np.radians(self.bevel_angle))
        
        start_point = (-self.r * sinr, self.r * (1 - cosr))
        
        pathbuilder = (ad.PathBuilder()
            .move(start_point)
            .arc_centre_sweep((0, self.r), -270 + self.bevel_angle, name='axle_tube')
            .spline(
                [(self.fl - 1, 0), (self.fl, 0)], 
                cv_len=self.foot_curvature,
                rel_len=0.7,
                name='flange')
            .line((self.fl, -self.ft), 'foot_right')
            .line((self.sep, -self.ft), 'foot_base')
            .line((self.sep, self.sep), 'foot_left')
            .line(start_point, 'axle_bevel')
        )
        
        return pathbuilder.build()


@ad.shape
@ad.datatree
class HingeWithAxleSegment(ad.CompositeShape):
    '''
    A hinge segment
    '''
    ar: float=ad.dtfield(3.2 / 2, doc='The radius of the axle hole')
    
    path_node: ad.Node=ad.ShapeNode(AxleSegmentPathBuilder)
    path : ad.Path=ad.dtfield(self_default=lambda s: s.path_node().build())
    
    h: float=ad.dtfield(10, doc='The width of the hinge axle segments.')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    epsilon: float=ad.dtfield(
        0.01, doc='Fudge factor to avoid OpenSCAD rendering artifancts')

    ah: float=ad.dtfield(
        self_default=lambda s: s.h + 2 * s.epsilon, 
        doc='The height of the axle hole')
    axle_node: ad.Node=ad.ShapeNode(ad.Cylinder, 
                                    {'r': 'ar', 'h': 'ah'}, 
                                    expose_all=True)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        
        maker = shape.solid('segment').at()
        
        axle_hole = self.axle_node().hole('axle_hole').at('centre')

        maker.add_at(axle_hole, 'centre_of', 'axle_tube', 0.5)        
        
        return maker


@ad.shape
@ad.datatree
class HingeWithAxle(ad.CompositeShape):
    '''
    A assembly of hinge segments
    '''
    n: int=ad.dtfield(9, doc='The number of segments')
    
    segment_node: ad.Node=ad.ShapeNode(HingeWithAxleSegment)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    
    def build(self) -> ad.Maker:
        shape = self.segment_node()
        
        maker = shape.composite(('segment', 0)).at('centre_of', 'axle_tube', 0.5)
        
        for i in range(1, self.n):
            even = i % 2 == 0
            trans = self.sep if even else -self.sep
            maker.add_at(
                shape.composite(('segment', i))
                    .at('centre_of', 'axle_tube', even),
                (('segment', i - 1)), 'centre_of', 'axle_tube', even,
                post=ad.ROTY_180 * ad.tranZ(trans))
        
        return maker
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
