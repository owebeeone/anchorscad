'''
Created on 21 Aug 2021

@author: gianni
'''

from dataclasses import dataclass

import ParametricSolid.core as core
import ParametricSolid.extrude as extrude
import ParametricSolid.linear as l
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew, FlatSunkScrew
import numpy as np


@core.shape('anchorscad/models/bracket/PipeCrossBracket')
@dataclass
class PipeCrossBracket(core.CompositeShape):
    '''
    Pipe cross bracket.
    '''
    
    radius1: float=24.6 / 2
    #radius2: float=24.6 / 2
    radius2: float=19.31 / 2
    padding: float=0.15
    clearance: float=12.0
    thickness: float=6.5
    screw_depth: float=7.0
    screw_depth_hole_delta: float=0.1
    clip_height: float= 10
    clip_height_hole_room: float= 0.5
    clip_wedge_run: float=4
    clip_pre_wedge_run: float=1
    clip_wedge_height: float=1
    clip_thickness:float=7.0
    nipple_offset: float=5
    nipple_width: float=4.0
    nipple_height: float=0.5
    nipple_dia: float=4
    edge_radius: float=1.0
    screw1_size_name: str='M2.6'
    screw1_len: float=19.0
    lock_screw_offsets: tuple=(0.27, 0.5, 0.73)
    lock_screw_edge_offset_factor: float=0.2
    tie_width: float= 5.5
    tie_height: float=2.5
    tie_wing_size: float=1
    tie_edge_offset: float=6
    gen_alternate_shape: bool=False
    alternate_depth: float=20.0
    alternate_hole_expansion_r=0.4  # Allow clearance for free motion.
    fn: int=37
    
    EXAMPLES_EXTENDED={'small': core.ExampleParams(
                            core.args(radius2=19.31 / 2,
                                      padding=0.5)), 
                       'large': core.ExampleParams(
                            core.args(radius2=24.6 / 2,
                                      padding=0.25)),  
                       'alternate': core.ExampleParams(
                             core.args(radius2=19.31 / 2,
                                       padding=0.5,
                                       tie_edge_offset=6,
                                       gen_alternate_shape=True))}
    
    NOEXAMPLE_ANCHORS=(
                core.surface_args('bbox', 'face_corner', 0, 0),
                core.surface_args('base', 'face_corner', 3, 1),)
    
    def __post_init__(self):
        size_x = self.clearance * 2 + self.thickness * 2 + self.radius1 * 2.0
        size_y = self.thickness + self.radius2 * 2.0
        size_z = size_x
        
        dimens = [size_x, size_y, size_z]
        
        maker = core.Box(dimens).cage('bbox').at(
            'face_corner', 0, 0)
        
        base_bbox = core.Box([size_x, self.screw_depth, size_z])
        
        base_type = (core.ModeShapeFrame.SOLID 
                      if self.gen_alternate_shape 
                      else core.ModeShapeFrame.CAGE)
        maker.add_at(base_bbox.named_shape('base', base_type).at('face_corner', 0, 0))
        maker.add_at(base_bbox.cage('base_insert').at('face_centre', 0),
                     'base', 'face_centre', 0, post=l.rotZ(-90) * l.rotY(180))
        
        hole_x = size_x / 2.0 - self.radius2
        outer_radius = self.radius2 + self.thickness
        outer_hole_x = hole_x - self.thickness
        rhs_outer_hole_x = outer_radius * 2.0 + outer_hole_x
        centre_height = self.padding + self.radius2
    
        path = (extrude.PathBuilder()
            .move([hole_x, 0])
            .line([0, 0], 'edge0')
            .line([0, self.screw_depth], 'edge1')
            .line([outer_hole_x, self.screw_depth], 'edge2')
            .line([outer_hole_x, centre_height], 'edge3')
            .arc_points_radius(
                [rhs_outer_hole_x, centre_height], 
                self.radius2 + self.thickness, name='edge4', metadata=self)
            .line([rhs_outer_hole_x, self.screw_depth], 'edge5')
            .line([size_x, self.screw_depth], 'edge6')
            .line([size_x, 0], 'edge7')
            .line([size_x - hole_x, 0], 'edge8')
            .line([size_x / 2 + self.radius2, 0], 'edge9')
            .line([size_x / 2 + self.radius2, centre_height], 'edge10')
            .arc_points_radius(
                [hole_x, centre_height], 
                self.radius2, direction=True, name='edge11', metadata=self)
            .line([hole_x, 0], 'edge12')
            .build())
        
        shape = extrude.LinearExtrude(path, dimens[2])
        shape_type = (core.ModeShapeFrame.CAGE 
                      if self.gen_alternate_shape 
                      else core.ModeShapeFrame.SOLID)
        
        maker.add_at(shape.named_shape('bracket', shape_type).at('edge0', 1.0),
            'face_corner', 0, 0, post=l.rotY(180))
        
        # Add alternate shape component
        
        if self.gen_alternate_shape:
            tie_clearance = self.tie_width / 2 + self.tie_wing_size + self.tie_edge_offset
            alt_size = [outer_radius * 2 + tie_clearance, 
                        outer_radius * 2,
                        self.alternate_depth]
            alt_shape = core.Box(alt_size)
            maker.add_at(alt_shape.solid('alt_box').at('face_edge', 1, 1),
                         'base', 'face_edge', 3, 2, post=l.ROTY_180)
            
            alt_hole_cage = core.Box(
                [alt_shape.size[1], 
                 alt_shape.size[1], 
                 alt_shape.size[2] + self.screw_depth])
            
            maker.add_at(alt_hole_cage.cage('alt_hole_cage').at('face_edge', 4, 3),
                         'alt_box', 'face_edge', 4, 3)
            
            alt_hole = core.Cone(h=alt_hole_cage.size[2] + 0.01, 
                                 r_base=self.radius2 + self.alternate_hole_expansion_r,
                                 r_top=self.radius2 + self.alternate_hole_expansion_r,
                                 fn=self.fn)
            maker.add_at(alt_hole.hole('alt_hole').at('centre'),
                         'alt_hole_cage', 'centre')
            
            
            # Generate alt lock screw holes
            alt_lock_screw = FlatSunkScrew(
                shaft_overall_length=self.thickness + 1,
                shaft_thru_length=self.thickness / 5,
                size_name=self.screw1_size_name,
                include_thru_shaft=False,
                include_tap_shaft=False,
                as_solid=False,
                fn=self.fn)
            
            for f in [0, 2, 3]:
                maker.add_at(
                    alt_lock_screw.composite(('alt_lock_screw', f))
                        .at('screw_cage', 'top'),
                    'alt_hole_cage', 'face_centre', f)
        
        # Generate tag fastener.
        
        wedge_hole_y = self.screw_depth_hole_delta + self.screw_depth
        nipple_top_y = wedge_hole_y - self.nipple_height
        nipple_top_x = self.nipple_offset + self.nipple_width / 1.2
        nipple_end_x = self.nipple_offset + self.nipple_width
        clip_wedge_start = nipple_end_x + self.clip_pre_wedge_run
        clip_wedge_end = clip_wedge_start + self.clip_wedge_run
        wedge_bottom_y = wedge_hole_y + self.clip_thickness
        
        tag_path = (extrude.PathBuilder()
            .move([0, 0])
            .line([0, -wedge_hole_y], 'edge0')
            .line([self.nipple_offset, -wedge_hole_y], 'edge1')
            .line([nipple_end_x, -wedge_hole_y], name='nipple_plate')
            .line([clip_wedge_start, -wedge_hole_y], 'edge3')
            .line([clip_wedge_end, -wedge_hole_y - self.clip_wedge_height], 'edge4')
            .line([clip_wedge_end, -wedge_bottom_y], 'edge5')
            .line([0, -wedge_bottom_y], 'edge6')
            .line([-self.clip_thickness, -wedge_bottom_y], 'edge6b')
            .line([-self.clip_thickness, self.screw_depth], 'edge7')
            .line([0, self.screw_depth], 'edge8')
            .line([0, 0], 'edge9')
            .build())
        
        tag_extrude_height = self.clip_height + self.clip_height_hole_room
        tag_shape = extrude.LinearExtrude(tag_path, tag_extrude_height)
        
        # Wedge for reinforcement of tag
        wedge_path = (extrude.PathBuilder()
            .move([0, 0])
            .line([0, self.screw_depth + wedge_bottom_y], 'edge0')
            .line([self.thickness, 0], 'edge1')
            .line([0, 0], 'edge2')
            .build())
        
        wedge_shape = extrude.LinearExtrude(wedge_path, self.clip_thickness)
        
        tag_solid_maker = tag_shape.solid('tag').at('edge0', 0)
        
        tag_solid_maker.add_at(wedge_shape.solid('wedge').at('edge0', 0.0),
                 'edge9', 0, 
                 post=(l.rotY(180) * l.rotZ(180) * l.rotX(90) 
                       * l.translate([0, -self.clip_thickness, tag_shape.h])))  
              
        # Screw hole
        
        screw1_cap_thickness = 0.3
        screw1_overall_len = wedge_bottom_y + self.screw_depth - screw1_cap_thickness
        screw1_tap_len = self.clip_thickness + wedge_hole_y
        screw1_shape = CountersunkScrew(
            shaft_overall_length=screw1_overall_len,
            shaft_thru_length=screw1_tap_len,
            size_name=self.screw1_size_name,
            include_thru_shaft=False,
            include_tap_shaft=False,
            as_solid=False,
            fn=self.fn)
        
        nipple = core.Sphere(
            r=self.nipple_dia / 2.0,
            fn=self.fn)
        
        at_args1 = core.args('nipple_plate', 0.5, post=l.translate([0, 2, 1]))
        at_args2 = core.args('nipple_plate', 0.5, post=l.translate([0, 8, 1]))
        
        tag_solid_maker.add_at(nipple.solid('nipple1').at('centre'), 
                               *at_args1[0], **at_args1[1])
        tag_solid_maker.add_at(nipple.solid('nipple2').at('centre'), 
                               *at_args2[0], **at_args2[1])
        
        tag_hole_maker = tag_shape.hole('tag').at('edge0', 0)
        tag_hole_maker.add_at(nipple.hole('nipple1').at('centre'), 
                               *at_args1[0], **at_args1[1])
        tag_hole_maker.add_at(nipple.hole('nipple2').at('centre'), 
                               *at_args2[0], **at_args2[1])
        
        screw_transform = l.rotY(180) * l.translate([0, self.clip_height / 2, 0])
        
        tag_solid_maker.add_at(
            screw1_shape.composite('screw1').at('screw_cage', 'top'),
            'tag', 'edge8', 2.0, post=screw_transform)
        
        tag_hole_maker.add_at(
            screw1_shape.composite('screw1').at('screw_cage', 'top'),
            'tag', 'edge8', 2.0, post=screw_transform)
        
        maker.add_at(tag_solid_maker.composite('tag').at('edge0', 0),
            'face_corner', 0, 0, post=l.rotY(-90))
        
        
        maker.add_at(tag_hole_maker.composite('tag_hole').at('edge1', 0),
            'base', 'face_corner', 3, 1, post=l.rotY(0) )
        
        screw2_shape = FlatSunkScrew(
            shaft_overall_length=screw1_overall_len,
            shaft_thru_length=1.9,
            size_name=self.screw1_size_name,
            head_sink_factor=0.5,
            include_thru_shaft=False,
            include_tap_shaft=False,
            as_solid=False,
            fn=self.fn)

        screw_2_locator = core.Box(
            [self.clip_height, self.clip_height, 1])
        
        screw_2_locator_shape = screw_2_locator.cage(
            'screw_2_locator').at('face_edge', 0, 0)
 
        screw_2_locator_shape.add_at(
            screw2_shape.composite('screw2').at('screw_cage', 'top'),
            'face_centre', 1)

        
        maker.add_at(screw_2_locator_shape.composite('screw2_1').at('face_corner', 0, 0),
                     'base', 'face_corner', 5, 1, post=l.translate(
                         [0, 0, 0]))
        maker.add_at(screw_2_locator_shape.composite('screw2_2').at('face_corner', 0, 0),
                     'base', 'face_corner', 2, 3, post=l.translate(
                         [0, 0, 0]))
        
        if not self.gen_alternate_shape:
            # Generate lock screw holes
            lock_screw = FlatSunkScrew(
                shaft_overall_length=self.thickness + 1,
                shaft_thru_length=self.thickness / 5,
                size_name=self.screw1_size_name,
                include_thru_shaft=False,
                include_tap_shaft=False,
                as_solid=False,
                fn=self.fn)
            
            edge3_factor = 1.0 - self.lock_screw_edge_offset_factor
            edge5_factor = self.lock_screw_edge_offset_factor
            
            for i, f in enumerate(self.lock_screw_offsets):
            
                y_offs = f * dimens[2]
            
                maker.add_at(lock_screw.composite(
                    f'lock_screw_{i + 1}').at('screw_cage', 'top'),
                             'bracket', 'edge3', edge3_factor, 
                             post=l.translate([0, y_offs, 0]) * l.rotX(180))
                
                
                maker.add_at(lock_screw.composite(
                    f'lock_screw_opp_{i + 1}').at('screw_cage', 'top'),
                             'bracket', 'edge5', edge5_factor, 
                             post=l.translate([0, y_offs, 0]) * l.rotX(180))
        
        # Tie grooves/slots
        
        tie_mid = self.tie_width / 2.0
        wing_point_x = self.tie_wing_size + tie_mid
        wing_point_y = self.tie_height / 2.0
        tie_height = self.tie_height
        
        tie_path = (extrude.PathBuilder()
            .move([0, 0])
            .line([-tie_mid, 0], 'base_l')
            .line([-wing_point_x, wing_point_y], 'wing_l_lower')
            .line([-tie_mid, tie_height], 'wing_l_upper')
            .line([0, tie_height], 'top_l')
            .line([tie_mid, tie_height], 'top_r')
            .line([wing_point_x, wing_point_y], 'wing_r_upper')
            .line([tie_mid, 0], 'winr_r_lower')
            .line([0, 0], 'base_r')
            .build())
        
        tie_shape = extrude.LinearExtrude(tie_path, self.radius1 * 2)
        
        tie_arc_radius = self.radius1 * 2.
        tie_arc_angle = 100
        tie_arc_path = tie_path.transform(
            l.translate([-tie_arc_radius, 0, 0]) * l.ROTZ_90)
        tie_round_shape = extrude.RotateExtrude(
            tie_arc_path, degrees=tie_arc_angle, fn=self.fn)
        
        tie_edge_offset = self.tie_edge_offset
        
        maker.add_at(tie_round_shape.hole('arc_tie_l').at('base_l', 0, tie_arc_angle / 2), 
                     'bracket', 'edge11', 0.5, tie_edge_offset,
                     post=l.translate([0, 0, 1]))
        maker.add_at(tie_round_shape.hole('arc_tie_r').at('base_l', 0, tie_arc_angle / 2), 
                     'bracket', 'edge11', 0.5, shape.h - tie_edge_offset,
                     post=l.translate([0, 0, 1]))
        
        tie_shape_type = tie_shape.hole
        tie_maker_l = tie_shape_type('tie_hole').at(
            'base_l', 0, self.radius1, 
            post=l.translate([-tie_edge_offset, 0, wing_point_y]) * l.rotX(-45))
        
        tie_maker_r = tie_shape_type('tie_hole').at(
            'base_l', 0, self.radius1, 
            post=l.translate([tie_edge_offset, 0, wing_point_y]) * l.rotX(-45))
            
        locations = (
            (tie_maker_l, ('face_edge', 3, 0, 0)),
            (tie_maker_r, ('face_edge', 3, 3, 1)),
            (tie_maker_r, ('face_edge', 3, 1, 1)),
            (tie_maker_r, ('face_edge', 3, 2, 1)),
            (tie_maker_l, ('face_edge', 3, 2, 0)),
            )
        
        for m, loc in locations:
            maker.add_at(m.composite(loc).at(), 'base', *loc)
            
        maker.add_at(tie_maker_r.composite(('tag', 'edge6', 1)).at(), 
                     'tag', 'edge6', 1, tag_shape.h) 
        maker.add_at(tie_maker_r.composite(('tag', 'edge6', 0)).at(), 
                     'tag', 'edge6', 1, 0, post=l.ROTX_90) 
        
        maker.add_at(tie_maker_r.composite(('tag', 'edge7', 1)).at(), 
                     'tag', 'edge7', 1, post=l.ROTX_90 * l.ROTV111_240) 
        maker.add_at(tie_maker_l.composite(('tag', 'edge7', 0)).at(), 
                     'tag', 'edge7', 0, post=l.ROTX_270 * l.ROTV111_240) 
#         maker.add_at(tie_maker_r.solid(('face_edge', 3, 0, 1)).at(), 'base', 'face_edge', 3, 0, 1)
        
        self.maker = maker
        

    
if __name__ == "__main__":
    core.anchorscad_main(False)
