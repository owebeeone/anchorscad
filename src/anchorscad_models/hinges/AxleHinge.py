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
            .line((self.sep, 0), 'foot_left') # Anchor point for plate
            .line((self.sep, self.sep), 'foot_left_sep')
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

        maker.add_at(axle_hole, 'centre_of', 'axle_tube', rh=0.5)        
        
        return maker


@ad.shape
@ad.datatree
class HingeWithAxle(ad.CompositeShape):
    '''
    A assembly of hinge segments
    '''
    n: int=ad.dtfield(9, doc='The number of segments')
    
    segment_node: ad.Node=ad.ShapeNode(HingeWithAxleSegment)
    
    material_a: str = ad.Material('hinge_left')
    material_b: str = ad.Material('hinge_right')
    
    cage_a: bool = False
    cage_b: bool = False
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args(('segment', 0), 'centre_of', 'axle_tube', rh=1, normal_segment='foot_base'),
        )
    
    
    def apply_material(self, named_shape, even):
        mat = self.material_a if even else self.material_b
        if mat:
            return named_shape.material(mat)
        return named_shape
    
    def name_shape(self, shape, i, even):
        name = ('segment', i)
        
        is_cage = self.cage_a if even else self.cage_b
        
        shape_type = ad.ModeShapeFrame.CAGE if is_cage else ad.ModeShapeFrame.COMPOSITE
        
        return shape.named_shape(name, shape_type)
    
    def apply_shape(self, shape, i, even):
        
        return self.apply_material(
            self.name_shape(shape, i, even),
            even)
        
    
    def build(self) -> ad.Maker:
        shape = self.segment_node()
        
        normal_spec = {'normal_segment' : 'foot_base'}
        
        maker = (self.apply_shape(shape, 0, True)
                 .at('centre_of', 'axle_tube', rh=1, **normal_spec))
        
        for i in range(1, self.n):
            even = i % 2 == 0
            trans = self.sep if even else -self.sep

            applied_shape = self.apply_shape(shape, i, even)
            maker.add_at(
                applied_shape.at('centre_of', 'axle_tube', t=0.6, rh=even, **normal_spec),
                (('segment', i - 1)), 'centre_of', 'axle_tube', t=0.6, rh=even,
                **normal_spec,
                post=ad.ROTY_180 * ad.tranZ(trans))
        
        return maker
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
