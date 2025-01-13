'''
Created on 6 Aug 2022

@author: gianni
'''

from mimetypes import init
from sys import prefix

from pythonopenscad.base import Intersection
from anchorscad.models.basic.poly_conical import Segment, PolyConical
import anchorscad as ad
import numpy as np
import anchorscad.models.basic.pipe as pipe
from anchorscad.models.basic.box_side_bevels import BoxSideBevels
from anchorscad.models.basic.box_cylinder import BoxCylinder


@ad.shape
@ad.datatree
class HoleLocations(ad.CompositeShape):
    '''
    Mounting screw locator for 4 equally spaced screws and
    holes for ground wire and power cable.
    Intended to be used as a cage.
    
    Provides anchor locations for mount screws, ground screw
    and centre of mount screws which is the centre of the
    fan.
    '''
    
    w_centres: float=(37.82 + 44.40) / 2
    
    w_ground: float=(25.4 + 19.12) / 2
    
    w_cable: float=(64.92 + 56.20) / 2
    
    size: tuple=ad.dtfield(
        self_default=lambda s:
            (s.w_centres, 1, s.w_centres),
        doc='Screw location cage.')
    
    gnd_offset: float=ad.dtfield(
        self_default=lambda s:
            np.sqrt(
                s.w_ground * s.w_ground 
                - s.w_centres * s.w_centres / 4)
            + s.w_centres / 2
        )
    
    box_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Box),
        init=False)

    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        ad.surface_args('mount_screw', 0,),
        ad.surface_args('mount_screw', 1,),
        ad.surface_args('mount_screw', 2,),
        ad.surface_args('mount_screw', 3,),
        ad.surface_args('centre',),
        ad.surface_args('ground_screw',),
        ad.surface_args('cable_hole',),
        )

    def build(self) -> ad.Maker:
        maker = self.box_node().cage('mount_screw_locator').at()
        return maker

    @ad.anchor('Mount screw')
    def mount_screw(self, side):
        return self.maker.at('face_corner', 'front', side)
    
    @ad.anchor('Ground screw')
    def ground_screw(self):
        return self.centre() * ad.tranY(self.gnd_offset)
    
    @ad.anchor('Cable hole')
    def cable_hole(self):
        return self.ground_screw() * ad.tranY(-self.w_cable)
    
    @ad.anchor('Centre of screws')
    def centre(self):
        return self.maker.at('face_centre', 'front')
    

@ad.datatree(frozen=True)
class FanRotorPlatePath:
    
    outside_r: float=ad.dtfield(
        100.0, 'Outer radius')
    
    radii: tuple=ad.dtfield(
        ((21, 0), 
         (22.5, 1.35), 
         (32, 1.35), 
         (34.5, 1.35 * 2), 
         (45, 1.35 * 2), 
         (56, 15 + 1.35 * 2),),
        'Radii and depths measured from outside to inside.')
    
    thickness: float=ad.dtfield(0.6, 'Rotor plate thickness')
    
    def build(self) -> ad.Path:
        
        builder = ad.PathBuilder()
        
        builder.move((self.outside_r, 0))
        builder.line((self.outside_r, self.thickness))
        for i, t in enumerate(self.radii):
            r_delta, depth = t
            builder.line(
                (self.outside_r - r_delta, depth + self.thickness), 
                ('top_segment', i))
        
        for i, t in enumerate(reversed(self.radii)):
            r_delta, depth = t
            builder.line(
                (self.outside_r - r_delta, depth), 
                ('bottom_segment', len(self.radii) - i))
        
        return builder.build()
        

@ad.shape
@ad.datatree
class FanRotorPlate(ad.CompositeShape):
    '''Plate for fan rotor.'''
    
    plate_path: ad.Path=ad.dtfield(
        FanRotorPlatePath().build(),
        'Path for fan rotor plate.')
    
    plate_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.RotateExtrude, prefix='plate_'),
        init=False)

    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        maker = self.plate_node().solid('plate').at()
        return maker


@ad.shape
@ad.datatree
class FanModel(ad.CompositeShape):
    '''
    Mounting screw locator for 4 equally spaced screws and
    holes for ground wire and power cable.
    Intended to be used as a cage.
     
    Provides anchor locations for mount screws, ground screw
    and centre of mount screws which is the centre of the
    fan.
    '''    
    
    outside_r: float=ad.dtfield(
        100.0, 'Outer radius')
    fan_h: float=ad.dtfield(
        51.76, 'Fan height')
    inner_rim_r: float=ad.dtfield(
        170/2, 'Inner radius of top ring')
    blade_w: float=ad.dtfield(
        18, 'Width of blade ring')
    inside_r: float=ad.dtfield(
        self_default=lambda s: s.outside_r - s.blade_w,
        doc='Inner radius of fins')
    
    
    motor_base_offset: float=ad.dtfield(
        16.0 - 12.31, 'height of ')
    
    hole_locations_node: ad.Node=ad.dtfield(
        ad.ShapeNode(HoleLocations),
        init=False
        )
    
    fan_fins_node: ad.Node=ad.dtfield(
        ad.ShapeNode(pipe.Pipe, {'h': 'fan_h'}, expose_all=True),
        init=False
        )

    motor_case_segments: tuple=ad.dtfield(
        (Segment(80 / 2, 13.8), 
         Segment(88.8 / 2, 23.52), 
         Segment(92.3 / 2, 11.45),  
         Segment(86.56 / 2, 7.8),  
         Segment(86.56 / 2, 11),  
         Segment(66.36 / 2, 5.14), 
         Segment(45.62 / 2)),
        'Shape of motor case')
    
    motor_case_node: ad.Node=ad.dtfield(
        ad.ShapeNode(PolyConical, prefix='motor_case_', expose_all=True),
        init=False)
    
    rotor_plate_node: ad.Node=ad.dtfield(
        ad.ShapeNode(FanRotorPlate),
        init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        fn=64, 
        hole_h_delta=0.02,
        motor_case_angle=270,
        plate_angle=275
        )
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('mount_screw', 0,),
        ad.surface_args('mount_screw', 1,),
        ad.surface_args('mount_screw', 2,),
        ad.surface_args('mount_screw', 3,),
        ad.surface_args('centre',),
        ad.surface_args('ground_screw',),
        ad.surface_args('cable_hole',),
        )
    
    def build(self) -> ad.Maker:
        maker = self.hole_locations_node().cage('cage').at(
            'centre', post=ad.ROTX_180)
        
        fan = self.fan_fins_node()
        
        maker.add_at(fan.solid('fan').at('base'),
                     'centre', post=ad.tranZ(-self.motor_base_offset))
        
        motor_case = self.motor_case_node()
        
        maker.add_at(motor_case.solid('motor_case').at('base'),
                     'centre')
        rotor_plate = self.rotor_plate_node()
        
        maker.add_at(rotor_plate.solid('rotor_plate').at(), 
                     'centre', 
                     post=ad.ROTX_180 * ad.tranZ(self.motor_base_offset))
        
        return maker
    

@ad.shape
@ad.datatree(frozen=True)
class FanHousing(ad.CompositeShape):
    '''Housing for a austwood centrigulal fan.'''
    
    fan_node: ad.Node=ad.dtfield(
        ad.ShapeNode(FanModel, prefix='fan_'),
        init=False)
    
    fan_cage_node: ad.Node=ad.dtfield(
        ad.CageOfNode(),
        init=False)
    
    gap_small: float=ad.dtfield(
        5.0, 'Small side gap between fan and housing')
    gap_large: float=ad.dtfield(
        20.0, 'Large side gap between fan and housing')
    gap_vertical: float=ad.dtfield(
        2.0, 'Vertical gap between fan and housing')

    wall_thickness: float=ad.dtfield(3.0, 'Thickness of wall')
    base_thickness: float=ad.dtfield(11.0, 'Thickness of base')
    
    base_size: tuple=ad.dtfield(
        self_default=lambda s: 
            (s.gap_large + s.gap_small + 2 * s.fan_outside_r,
             s.gap_large + 2 * s.fan_outside_r,
             s.base_thickness),
        init=False)
    base_bevel_radius: float=ad.dtfield(10.0, 'Bevel radius of base')
    
    base_node: ad.Node=ad.dtfield(
        ad.ShapeNode(BoxSideBevels, prefix='base_'),
        init=False)

    screw_r: float=ad.dtfield(4.06 / 2, 'Screw radius')
    screw_h: float=ad.dtfield(
        self_default=lambda s: 
            s.base_thickness 
                - s.fan_motor_base_offset
                + s.gap_vertical
                + s.epsilon,
        init=False)
    epsilon: float=ad.dtfield(0.02, 'A small value to avoid rounding errors')
    
    screw_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='screw_'),
        init=False)
    
    screw_head_r: float=ad.dtfield(7.5 / 2, 'Screw head radius')
    screw_head_h: float=ad.dtfield(2.5, 'Screw head height')
    
    screw_head_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='screw_head_'),
        init=False)
    
    cable_r: float=ad.dtfield(7.5 / 2, 'Cable hole radius')
    cable_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 
            {'h': 'screw_h'}, prefix='cable_', expose_all=True),
        init=False)
    
    cable_channel_size: tuple=ad.dtfield(
        self_default=lambda s: (s.cable_r, s.screw_h),
        init=False)
    cable_channel_node: ad.Node=ad.dtfield(
        ad.ShapeNode(BoxCylinder,
                     prefix='cable_channel_'),
        init=False)
    
    mount_screw_r: float=ad.dtfield(5.06 / 2, 'Mount screw radius')
    mount_screw_h: float=ad.dtfield(
        self_default=lambda s: s.base_thickness + 2 * s.epsilon,
        init=False)
    mount_screw_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='mount_screw_'),
        init=False)
    
    mount_screw_margin: float=ad.dtfield(10, 'Mount screw margin')
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=True, fn=128)
    SCREW_ANCHORS=(
        ad.surface_args('mount_screw', 0,),
        ad.surface_args('mount_screw', 1,),
        ad.surface_args('mount_screw', 2,),
        ad.surface_args('mount_screw', 3,),
        ad.surface_args('ground_screw',))
    
    CABLE_ANCHOR=ad.surface_args('cable_hole',)
    
    CABLE_HOLE_LINE_ANCHOR=ad.surface_args(
        'cable_hole_vertical', 'top', post=ad.ROTX_270)
    CABLE_HOLE_PLANE_ANCHOR=ad.surface_args(
        'housing', 'base_plate', 'face_centre', 'front')
    
    EXAMPLE_ANCHORS=(
        # CABLE_HOLE_LINE_ANCHOR,
        # ad.surface_args('cable_hole_point')
    )
    
    def build(self) -> ad.Maker:
        
        fan_shape = self.fan_node()
        maker = fan_shape.hole('fan').colour([1, 0, 0]).at('centre')
        
        
        base = self.base_node()
        
        maker.add_at(base.solid('base_plate')
                     .at('face_centre', 'base', post=ad.ROTX_180), 
                     'centre', 
                     post=ad.tranZ(
                         -self.fan_motor_base_offset 
                         + self.gap_vertical))
        
        result_maker = maker.solid('housing').at('centre')
               
        result_maker.add_at(
            self.fan_cage_node(fan_shape).at('centre'),
            'centre')
        
        # Screw holes.
        for i, anchor in enumerate(self.SCREW_ANCHORS):
            result_maker.add_at(
                self.screw_node().hole(('screw_hole', i))
                .at('base', rh=1, h=-self.epsilon / 2), 
                anchor=anchor)
            
            result_maker.add_at(
                self.screw_head_node().hole(('screw_head', i))
                .at('base'),
                ('screw_hole', i), 'base')
                
        
        # Cable hole.
        result_maker.add_at(
            self.cable_node().hole('cable_hole_vertical')
            .at('base', rh=1, h=-self.epsilon / 2), 
            anchor=self.CABLE_ANCHOR)
        
        line = result_maker.at(anchor=self.CABLE_HOLE_LINE_ANCHOR)
        plane = result_maker.at(anchor=self.CABLE_HOLE_PLANE_ANCHOR)
        
        intersection = ad.plane_line_intersect(plane, line)
        
        box_cyl_size = (self.cable_r * 2,
                        self.cable_r,
                        ad.distance_between(intersection, line) + self.epsilon)
        
        box_cyl_shape = (self.cable_channel_node(size=box_cyl_size)
                            .hole('cable_channel')
                            .at('face_edge', 'top', 2))
        result_maker.add_at(
            box_cyl_shape, 
            post=self.CABLE_HOLE_LINE_ANCHOR.apply(result_maker) * ad.ROTY_180)
        
        # Add mount screws.
        mount_screw_shape = self.mount_screw_node()
        for i in range(4):
            result_maker.add_at(
                mount_screw_shape.hole(('mount_screw', i)).at('base'),
                'base_plate', 'face_corner', 'top', i, 
                post=ad.translate(
                    (self.mount_screw_margin, 
                     self.mount_screw_margin, 
                     self.epsilon)))
        
        return result_maker

    @ad.anchor('Point alighted to cable hole and edge of housing')
    def cable_hole_point(self) -> ad.GMatrix:
        
        line = self.CABLE_HOLE_LINE_ANCHOR.apply(self)
        plane = self.CABLE_HOLE_PLANE_ANCHOR.apply(self)
        return ad.plane_line_intersect(plane, line)
 

MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()