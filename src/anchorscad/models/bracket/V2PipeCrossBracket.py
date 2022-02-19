'''
Created on 26 Aug 2021

@author: gianni
'''


from dataclasses import dataclass

import ParametricSolid.core as core
import ParametricSolid.extrude as extrude
import ParametricSolid.linear as l
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew, FlatSunkScrew
import numpy as np

# Note this function is buggy.
def cone_cyl_plane_intersection_slope(
        cone_radius_at_intersection_base,
        cone_base_radius,
        code_top_radius,
        cone_overall_height,
        cylinder_radius):
    '''Compute the slope of the intersection of a cylinder and cone
    where the cone axis is perpendicular and intersecting with the cylinder. 
    '''
    x0 = cone_radius_at_intersection_base
    rc = cylinder_radius
    m = cone_overall_height / (cone_base_radius - code_top_radius)
    h = x0 - rc / m
    cost = rc / h
    o = x0 - h * np.sqrt(1 - cost * cost)
    return ( o / rc )


ABS_SHRINK_FACTOR=1.0 / 1.015

@core.shape('anchorscad/models/bracket/PipeCrossBracket')
@dataclass
class V2PipeCrossBracket(core.CompositeShape):
    '''
    Pipe cross bracket V2.
    '''
    
    radius1: float=24.6 / 2
    radius2: float=19.31 / 2
    mid_padding: float=0
    base_hang_factor: float=0.5
    clip_hang_factor: float=0.15
    holder_radius_factor:float = 1.5
    cross_angle: float=90
    tie_width: float= 5.5
    tie_height: float=2.5
    tie_wing_size: float=1
    tie_delta: float= 2
    tie_angle: float= -10
    tie_slant_angle: float= 0
    screw1_size_name: str='M2.6'
    screw1_len: float=19.0
    screw_angle: float=23.0
    cutter_grade: float = 1
    flat_cutter_offset: float = 2
    shrink_factor: float = 1.0
    
    fn: int=72
    
    
    NOEXAMPLE_ANCHORS=(
        core.surface_args('bracket', 'top'),
        core.surface_args('bracket', 'base'),
        core.surface_args('side1', 'surface', 0, 0, tangent=False),
        core.surface_args('side2', 'surface', 0, 0, tangent=False),)
    
    EXAMPLE_ANCHORS=(
        core.surface_args(
            'pipe1', 'surface', 15, 
            rh=0.5, radius_delta=1.5, tangent=False),
        core.surface_args(
            'pipe2', 'surface', 15,
            rh=0.5, radius_delta=1.5, tangent=False),)
    
    EXAMPLES_EXTENDED={'small': core.ExampleParams(
                            core.args(
                                radius1=19.31 / 2,
                                tie_angle=0,
                                cutter_grade=1)),
                       'small_abs': core.ExampleParams(
                            core.args(
                                radius1=19.31 / 2,
                                tie_angle=0,
                                cutter_grade=1,
                                shrink_factor=ABS_SHRINK_FACTOR)),
                       'large': core.ExampleParams(
                            core.args(radius2=19.31 / 2,
                                      tie_angle=-10)), 
                       'large_abs': core.ExampleParams(
                            core.args(
                                radius2=24.6 / 2,
                                shrink_factor=ABS_SHRINK_FACTOR)), 
                       'slanted': core.ExampleParams(
                            core.args(radius1=19.31 / 2,
                            tie_angle=0,
                            holder_radius_factor=2,
                            tie_slant_angle=13,
                            tie_delta=6,
                            screw_angle=17,
                            cutter_grade=0.6,
                            cross_angle=60))}
    
    def __post_init__(self):
        
        holder_rad = (self.holder_radius_factor * self.radius1 * 
                      (1.0 + self.base_hang_factor))
        
        side1_cage = core.Cone(
            h=self.radius1 * (1 + self.clip_hang_factor), 
            r_base=self.radius1 * (1 + self.clip_hang_factor),
            r_top=holder_rad,
            fn=self.fn
            )
        
        side2_cage = core.Cone(
            h=self.radius2 * (1 + self.clip_hang_factor), 
            r_base=self.radius2 * (1 + self.clip_hang_factor),
            r_top=holder_rad,
            fn=self.fn
            )
        
        pad = core.Cone(
            h=self.mid_padding, 
            r_base=holder_rad,
            r_top=holder_rad,
            fn=self.fn
            )
        
        holder = core.Cone(
            h=side1_cage.h + side2_cage.h + self.mid_padding, 
            r_base=holder_rad,
            r_top=holder_rad,
            fn=self.fn
            )
        
        maker = holder.cage('bracket').at('base')

        maker.add_at(
            side1_cage.solid('side1').at('base'), 'bracket', 'base')

        maker.add_at(
            side2_cage.solid('side2').at('base', pre=l.rotZ(self.cross_angle)),
            'bracket', 'top')
        
        maker.add_at(pad.solid('pad').at('base'), 
                     'side1', 'top',
                      post=l.translate([0, 0, self.mid_padding]))
        
        pipe1_hole = core.Cone(
            h=10 * self.radius1,
            r_base=self.radius1,
            r_top=self.radius1,
            fn=self.fn
            )
        pipe2_hole = core.Cone(
            h=10 * self.radius2,
            r_base=self.radius2,
            r_top=self.radius2,
            fn=self.fn
            )
        
        xlation1 = [0, -self.radius1 * self.clip_hang_factor, 0]
        xlation2 = [0, -self.radius2 * self.clip_hang_factor, 0]
        
        maker.add_at(pipe1_hole.hole('pipe1').at('centre', pre=l.ROTZ_180), 
                     'side1', 'base',
                     post=l.ROTX_90 * l.translate(xlation1))
        maker.add_at(pipe2_hole.hole('pipe2').at('centre', pre=l.ROTZ_180), 
                     'side2', 'base',
                     post=l.ROTX_90 * l.translate(xlation2))

        # Tie grooves/slots
        
        tie_mid = self.tie_width / 2.0
        wing_point_x = self.tie_wing_size + tie_mid
        wing_point_y = self.tie_height / 2.0
        tie_height = self.tie_height
        
        tie_path = (extrude.PathBuilder()
            .move([0, wing_point_y])
            .line([0, 0], 'centre')
            .line([-tie_mid, 0], 'base_l')
            .line([-wing_point_x, wing_point_y], 'wing_l_lower')
            .line([-tie_mid, tie_height], 'wing_l_upper')
            .line([0, tie_height], 'top_l')
            .line([tie_mid, tie_height], 'top_r')
            .line([wing_point_x, wing_point_y], 'wing_r_upper')
            .line([tie_mid, 0], 'winr_r_lower')
            .line([0, 0], 'base_r')
            .build())
        
        tie_path = tie_path.transform(l.translate([0, -wing_point_y, 0]))
        
        twist_factor = 0.9
        extrude_height = (self.radius1 + self.radius2 + self.mid_padding) * twist_factor
        tie_shape1 = extrude.LinearExtrude(
            tie_path, 
            extrude_height,
            twist=-self.cross_angle, 
            fn=self.fn * 2)
        
        tie_shape2 = extrude.LinearExtrude(
            tie_path, 
            extrude_height,
            twist=180 - self.cross_angle, 
            fn=self.fn * 2)
        
        tie_args = (
            (tie_shape1, 1, 1, 0),
            (tie_shape2, -1, 1, 180),
            (tie_shape1, 1, 1, 180),
            (tie_shape2, -1, 1, 0),
                )
        
        q = 90 - self.cross_angle
        angle1 = self.cross_angle
        angle2 = -self.cross_angle
        
        # Based on the angle between the pipes being bracketed we have
        # some different params.
        # TODO - make these computationally derived.
        if self.cross_angle > 85:
            tie_params = (
                (1, 1, 0, 0, -self.cross_angle, 0),
                (1, -1, 180, 0, 180 - self.cross_angle, 0),
                (-1, 1, 0, 180, 180 - self.cross_angle, 0),
                (-1, -1, 180, 180, -self.cross_angle, 0),
                )
        elif self.cross_angle > 75:
            #~80degs
            tie_params = (
                (1, 1, 0, 0, -self.cross_angle - 10, 10),
                (1, -1, 180, 0, 180 - self.cross_angle + 15, 15),
                (-1, 1, 0, 180, 180 - self.cross_angle + 15, 15),
                (-1, -1, 180, 180, -self.cross_angle - 10, 10),
                )
        elif self.cross_angle > 65:
            # 65degs
            tie_params = (
                (1.3, 1.3, 0, 0, -self.cross_angle - 10, 10),
                (1.3, -1.3, 180, 0, 180 - self.cross_angle + 45, 45),
                (-1.3, 1.3, 0, 180, 180 - self.cross_angle + 15, 15),
                (-1.3, -1.3, 180, 180, -self.cross_angle - 10, 10),
                )
        else:
            # under 65degs
            tie_params = (
                (1.3, 1.3, 0, 0, -self.cross_angle - 10, 10),
                (1.3, -1.3, 180, 0, 180 - self.cross_angle + 65, 55),
                (-1.3, 1.3, 0, 180, 180 - self.cross_angle + 65, 55),
                (-1.3, -1.3, 180, 180, -self.cross_angle - 10, 10),
                )
        
        pipe_1_offs = self.radius1
        pipe_2_offs = self.radius1
        
        cols = ([1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1])
        tie_delta = self.tie_delta
        
        
        tie_shape2 = extrude.LinearExtrude(
            tie_path, 
            extrude_height,
            twist=180 - self.cross_angle, 
            fn=self.fn * 2)
        
        for i in range(4):
            
            ti = tie_params[i]
              
#             maker.add_between(
#                 core.at_spec('pipe1', 'surface', pipe_1_offs * ti[0], ti[2],
#                              rh=0.5, radius_delta=tie_delta),
#                 core.at_spec('pipe2', 'surface', pipe_2_offs * ti[1], ti[3],
#                              rh=0.5, radius_delta=tie_delta),
#                 core.lazy_shape(
#                     core.Cone, 'h', 
#                     other_args=core.args(
#                         r_base=3, fn=self.fn)
#                         ).solid(('tie_cone', i)).colour(cols[i]),
#                 core.at_spec('base', post=l.IDENTITY),
#                 core.at_spec('top'),
#                 align_axis=l.X_AXIS,
#                 align_plane=l.X_AXIS
#                 )
#             
               
            maker.add_between(
                core.at_spec('pipe1', 'surface', pipe_1_offs * ti[0], ti[2],
                             rh=0.5, radius_delta=tie_delta),
                core.at_spec('pipe2', 'surface', pipe_2_offs * ti[1], ti[3],
                             rh=0.5, radius_delta=tie_delta),
                core.lazy_shape(
                    extrude.LinearExtrude, 'h', 
                    other_args=core.args(
                        path=tie_path, twist=ti[4], fn=self.fn * 2)
                        ).hole(('tie_hole', i)).colour(cols[i] + [0.5]),
                core.at_spec('centre', rh=0, post=l.ROTX_90 * l.rotZ(ti[5])),
                core.at_spec('centre', rh=1, post=l.IDENTITY),
                align_axis=l.Y_AXIS,
                align_plane=l.Y_AXIS
                )
             
            
        # Flatten cutter
        cutter_scale = 1
        cutter_size = holder_rad * cutter_scale
        
        # With the intersection of code and pipe we should have a plane.
        # This determines the angle of the plane and creates a cutter prism for
        # slicing at the plane.
        cutter_grade = cone_cyl_plane_intersection_slope(
            side1_cage.r_top, side1_cage.r_top, side1_cage.r_base, 
            side1_cage.h, pipe1_hole.r_base) * self.cutter_grade
        cutter_h = cutter_scale * side1_cage.h * cutter_grade
        cutter_cage_shape = core.Box([cutter_size, cutter_size, cutter_h])
        
        # Creates a cube cage around a triangular prism as another cage
        # to add a hole (cutter_shape_bugger) that slices the top off
        # the end of the model.                       
        cutter_path = (extrude.PathBuilder()
                       .move([0, 0])
                       .line([0, cutter_h], 'side')
                       .line([cutter_size, 0], 'hypot')
                       .line([0, 0], 'base')
                       .build())
        cutter_shape = extrude.LinearExtrude(
            cutter_path, h=cutter_size)
        
        cutter_path_bigger = cutter_path.transform(l.scale(2))
        
        cutter_shape_bigger = extrude.LinearExtrude(
            cutter_path_bigger, h=cutter_size)
        
        cutter_cage = (cutter_cage_shape.cage('cutter_cage')
                .colour([1, 0.5, 1, 0.5]).at('face_edge', 1, 0))
        cutter_cage.add_at(cutter_shape.cage('cutter')
                           .colour([0.5, 1, 1, 0.5]).at('base', 0.5, cutter_shape.h),
                           post=l.ROTX_180)
        
        cutter_cage.add_at(cutter_shape_bigger.hole('cutter_bigger')
                           .colour([0, 0.5, 1, 0.5]).at('hypot', 0), 
                           'cutter', 'hypot', 0)
        
        maker.add_at(cutter_cage.composite('face_cutter')
                     .at('face_edge', 1, 3, post=l.ROTX_90), 
                     'side1', 'surface', 0, 90, rh=1, tangent=False,
                     post=l.ROTX_180 * l.translate(
                         [0, 0, self.flat_cutter_offset]))
        
        # Add lock screw holes
        
        lock_screw = FlatSunkScrew(
            shaft_overall_length=self.radius1 * 2,
            shaft_thru_length=self.radius1 * 0.1,
            size_name=self.screw1_size_name,
            include_thru_shaft=False,
            include_tap_shaft=False,
            head_depth_factor=0.5,
            as_solid=False,
            fn=self.fn)
        
        maker.add_at(lock_screw.composite('screw1').at('top'),
                     'side1', 'surface', side1_cage.h * 0.7, self.screw_angle, tangent=False)
        maker.add_at(lock_screw.composite('screw2').at('top'),
                     'side2', 'surface', side2_cage.h * 0.7, self.screw_angle, tangent=False)
              
        # Orient for slicing and apply printing shrink compensation in the
        # X/Y plane as the Z axis does not shrink as that is constantly
        # filled as each layer is deposited at the correct location.
        self.maker = maker.solid('scaled').at(
            'face_cutter', 'cutter', 'hypot', 0.5, cutter_size / 2,
            post=l.ROTX_180 * l.scale([
                self.shrink_factor, 
                self.shrink_factor, 
                1]))
        
#         for i in range(4):
#             
#             ti = tie_params[i]
#               
#             self.maker.add_between(
#                 core.at_spec('scaled', 'pipe1', 'surface', pipe_1_offs * ti[0], ti[2],
#                              rh=0.5, radius_delta=tie_delta),
#                 core.at_spec('scaled', 'pipe2', 'surface', pipe_2_offs * ti[1], ti[3],
#                              rh=0.5, radius_delta=tie_delta),
#                 core.lazy_shape(
#                     core.Cone, 'h', 
#                     other_args=core.args(
#                         r_base=3, fn=self.fn)
#                         ).solid(('tie_cone', i)).colour(cols[i]),
#                 core.at_spec('base', post=l.IDENTITY),
#                 core.at_spec('top'),
#                 align_axis=l.X_AXIS,
#                 align_plane=l.X_AXIS
#                 )
            
    
if __name__ == "__main__":
    core.anchorscad_main(False)
