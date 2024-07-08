'''
Created on 12-Dec-2023

@author: gianni

Auto door holder. Consists of a ring, a hook and a hook-mount. Ring is usually attached
to the door and the hook-mount against the wall. The hook is fasted to the hook-mount
by inserting a rod. The hook and ring are aligned so that when the door is opened, it 
raises the hook which then falls into the ring keeping the hook in place.

https://photos.app.goo.gl/qKShjvXtq7jKiSBWA - video of operation.
https://photos.app.goo.gl/MVbkSCrLY2QVoaD69 - photo of installed door holder.

These were printed with black PETG and 3 perimiters at 25% infill. PETG seems to have 
good UV resistance so should be a reasonable choice for outdoor use.
'''

import anchorscad as ad

from anchorscad.models.screws.CountersunkScrew import CountersunkScrew
from anchorscad.models.basic.stadium import StadiumPrism


@ad.datatree
class DoorHolderRingPath:
    '''
    Path builder for the door holder ring.
    '''
    
    ring_r_upper: float=ad.dtfield(18, doc='Inner upper ring radius.')
    ring_r_lower: float=ad.dtfield(21.5, doc='Inner lower ring radius.')
    ring_r_outer: float=ad.dtfield(25, doc='Outer ring radius.')
    ring_thickness: float=ad.dtfield(14, doc='Ring thickness.')
    
    def build(self):
        builder = (ad.PathBuilder()
            .move([self.ring_r_lower, 0])
            .line([self.ring_r_upper, self.ring_thickness], 'inner')
            .line([self.ring_r_outer, self.ring_thickness], 'top')
            .line([self.ring_r_outer, 0], 'outer')
            .line([self.ring_r_lower, 0], 'bottom')
            )
        return builder.build()


@ad.shape
@ad.datatree
class DoorHolderRingScaffold(ad.CompositeShape):
    '''
    Basic door holder ring. Simple ring with a base plate.
    '''
    
    ring_path_node: ad.Node=ad.Node(DoorHolderRingPath)
    ring_path: ad.Path=ad.dtfield(self_default=lambda s: s.ring_path_node().build())
    
    ring_cage_node: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'ring_r_outer', 'h': 'ring_thickness'})
    cage_of_node: ad.Node=ad.CageOfNode()
       
    ring_extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, prefix='ring_')
    
    base_plate_size: tuple=ad.dtfield(
        self_default=lambda s: (
            s.ring_r_outer * 2 * 0.75, 
            (s.ring_r_outer - s.ring_r_upper) * 1.7,
            s.ring_thickness), doc='The size of the base plate.')
    base_plate_node: ad.Node=ad.ShapeNode(ad.Box, prefix='base_plate_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False, fn=128)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        
        cage_shape = self.ring_cage_node()
        maker = self.cage_of_node(cage_shape).at('centre')
        
        ring_shape = self.ring_extrude_node()
        maker.add_at(ring_shape.solid('ring').at(), 'top', post=ad.ROTX_180)
        
        base_plate_shape = self.base_plate_node()
        
        maker.add_at(base_plate_shape.solid('base_plate').at('face_centre', 'front'),
                     'surface', rh=0.5)
        
        return maker


@ad.shape
@ad.datatree
class DoorHolderRing(ad.CompositeShape):
    '''
    Door holder ring with screw holes at an angle inside the ring.
    '''
    
    ring_scaffold_node: ad.Node=ad.ShapeNode(DoorHolderRingScaffold)
    ring_scaffold_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.ring_scaffold_node())
    
    screw_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: s.ring_scaffold_shape.base_plate_size[1] * 2, 
        doc='The overall length of the screw shaft.')
    screw_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.screw_shaft_overall_length,
        doc='The length of the screw shaft that freely passes the screw threads.')
    screw_size_name: str=ad.dtfield('DECK_10g-10', doc='The name of the screw size.')
    screw_hole_node: ad.Node=ad.ShapeNode(CountersunkScrew, prefix='screw_')
    screw_angle: float=ad.dtfield(20, doc='The angle of the screw hole.')
    screw_offset: float=ad.dtfield(8, doc='The X offsets of the screw holes.')

    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False, fn=128, screw_hide_cage=False)
    
    EXAMPLE_ANCHORS=(
        #ad.surface_args('scaffold', 'base_plate', 'centre'),
    )

    
    def build(self) -> ad.Maker:
        shape = self.ring_scaffold_shape
        maker = shape.composite('scaffold').at()
        
        screw_hole = self.screw_hole_node()
        
        width = shape.base_plate_size[1]
        
        maker.add_at(screw_hole.composite(('screw_hole', 0)).at('top'),
                     'scaffold', 'base_plate', 'centre', 
                     post=ad.ROTX_270 
                            * ad.rotX(self.screw_angle) 
                            * ad.translate((-self.screw_offset, 0, width / 2.5)))
        maker.add_at(screw_hole.composite(('screw_hole', 1)).at('top'),
                     'scaffold', 'base_plate', 'centre', 
                     post=ad.ROTX_270 
                            * ad.rotX(self.screw_angle) 
                            * ad.translate((self.screw_offset, 0, width / 2.5)))

        return maker
    
    def upper_width(self):
        return self.ring_scaffold_shape.ring_r_outer - self.ring_scaffold_shape.ring_r_upper
    
    @ad.anchor('top front of the ring.')
    def front_top(self, rw=0):
        
        return self.at('scaffold', 'surface', degrees=180) * ad.ROTX_90 \
                * ad.tranY(- rw * self.upper_width())
    
# A door holder hook outline.
@ad.datatree
class DoorHolderHookPath:
    '''
    Path builder for the door holder hook.
    '''
    
    hook_length: float=ad.dtfield(20, doc='The length of the hook.')
    hook_thickness: float=ad.dtfield(20, doc='The thickness of the hook.')

    ring_thickness: float=ad.dtfield(14, doc='Ring thickness.')
    
    hook_segment_size: float=ad.dtfield(30, doc='The size of the hook segments.')
    hook_mid_segment_size: float=ad.dtfield(5, doc='The size of the hook segments.')
    
    def build(self):
        
        ssize = self.hook_segment_size
        mssize = self.hook_mid_segment_size
        
        builder = (ad.PathBuilder()
            .move([0, 0], direction=(-1, 0))
            .arc_centre_sweep((0, self.ring_thickness), sweep_angle_degrees=-60, name='base_start')
            .spline(((-ssize + 1, self.ring_thickness), (-ssize, self.ring_thickness)), 
                   cv_len=(self.ring_thickness * 0.5, self.ring_thickness * 1.3),
                   name='base_mid')
            .stroke(self.ring_thickness, degrees=90, name='hook_catch_side')
            
            .rspline((-ssize * 1, 1.5 * self.ring_thickness),
                     cv_len=(self.ring_thickness * 1.1, self.ring_thickness),
                     degrees=(-90, -100, 0),
                     name='base_tail')
            
            .rspline((ssize, self.ring_thickness * 2),
                     cv_len=(self.ring_thickness * 2, self.ring_thickness * 3),
                     degrees=(0, 180, 180),
                     name='left')
            
            .spline(((-1, self.ring_thickness * 2), (0, self.ring_thickness * 2)),
                     cv_len=(self.ring_thickness, self.ring_thickness),
                     name='right')
            
            .arc_tangent_point((0, 0), name="hook_end")
            
            )

        return builder.build()
    
# A door holder hook. This joins to the [DoorHolderRing]
@ad.shape
@ad.datatree
class DoorHolderHook(ad.CompositeShape):
    '''
    The hook component of the door holder.
    '''
    
    hook_path_node: ad.Node=ad.Node(DoorHolderHookPath)
    hook_path: ad.Path=ad.dtfield(
        self_default=lambda s: s.hook_path_node().build())
    hook_width: float=ad.dtfield(20, doc='The width of the hook.')
    
    extrude_node: ad.Node=ad.ShapeNode(
        ad.LinearExtrude, {'h': 'hook_width'}, expose_all=True, prefix='hook_')
    
    ring_node: ad.Node=ad.ShapeNode(DoorHolderRing)
    
    axis_pin_location: ad.GMatrix=ad.dtfield(
        self_default=lambda s: ad.translate((0, 0, s.ring_thickness)),
        doc='The pin location.')

    axle_r: float=ad.dtfield(
        (10.2 + 0.1) / 2, 
        doc='The radius of the axle hole. Note the 0.1 increase for printer tolerance.')
    pin_hole_r: float=ad.dtfield(
        self_default=lambda s: s.axle_r + 0.25, doc='The radius of the pin.')
    pin_node: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'pin_hole_r', 'h': 'hook_width'})
    
    # Apart from the standard ShapeNode fields, none of the fields are injected.
    stadium_node: ad.Node=ad.ShapeNode(StadiumPrism, {})

    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=(
        # ad.surface_args('pin_axis'),
        # ad.surface_args('ring', 'front_top', 1),
        # ad.surface_args('hook', 'base_start', 1, rh=0.5),
    )

    def build(self) -> ad.Maker:
        hook_shape = self.extrude_node()
        maker = hook_shape.solid('hook').at()
        
        ring_shape = self.ring_node()
        maker.add_at(ring_shape.hole('ring')
                     .at('front_top', 0.5, post=ad.ROTZ_270),
                     'hook', 'base_mid', 1, rh=0.5)
        
        pin_hole_shape = self.pin_node()
        maker.add_at(pin_hole_shape.hole('pin_hole').at('base'),
                     'hook', 'base_start', post=self.axis_pin_location * ad.ROTX_90)
        
        return maker
    
    @ad.anchor('The pin location.')
    def pin_axis(self, centre=False):
        centre_transform = ad.IDENTITY
        if centre:
            centre_transform = ad.tranZ(-self.hook_width / 2)
        return self.at('hook', 'base_start', 0) \
            * self.axis_pin_location * ad.ROTX_90 * centre_transform
    
    def make_clearance_shape(self, clearance: float):
        '''Make a clearance shape for allowing the hook to be inserted into the mount.'''

        shape = self.stadium_node(
            r=self.ring_thickness + clearance,
            w=3 * self.ring_thickness,
            t=0,
            h=self.hook_width + 2 * clearance)

        
        return shape

@ad.shape
@ad.datatree
class DoorHolderHookMount(ad.CompositeShape):
    '''
    Mount plate for the door holder hook. Includes screw and axle holes.
    '''
    
    # Define your nodes here. For example:
    mount_node: ad.Node = ad.ShapeNode(ad.Box, prefix='mount_')
    hook_node: ad.Node = ad.ShapeNode(DoorHolderHook)
    hook_shape: ad.Shape = ad.dtfield(self_default=lambda s: s.hook_node())
    
    wing_w: tuple=ad.dtfield(12, doc='The width of the mount wings.')
    slack: float=ad.dtfield(0.5, doc='The slack of the hook.')
    margin: float=ad.dtfield(5, doc='The margin of the hook.')
    stopper: float=ad.dtfield(30, doc='The stopper part above axis.')
    
    mount_size: tuple=ad.dtfield(
        self_default=lambda s: (2 * s.wing_w + s.hook_shape.hook_width + 2 * s.slack, 
                                2 * (s.hook_shape.ring_thickness + 2 * s.slack) + s.margin,
                                2 * (s.hook_shape.ring_thickness + s.margin) + s.stopper), 
        doc='The size of the mount.')
    
    mount_node: ad.Node=ad.ShapeNode(ad.Box, prefix='mount_')
    
    # axle_r - injected by hook_node
    axle_h: float=ad.dtfield(
        self_default=lambda s: s.mount_size[0] - s.margin / 4, 
        doc='The height of the axle.')
    
    axle_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='axle_')
    
    mount_screw_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: s.mount_size[1] * 2, 
        doc='The overall length of the mount screw shaft.')
    mount_screw_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.mount_screw_shaft_overall_length,
        doc='The length of the mount screw shaft that freely passes the screw threads.')
    mount_screw_size_name: str=ad.dtfield('DECK_10g-10', doc='The name of the screw size.')
    mount_screw_hole_node: ad.Node=ad.ShapeNode(CountersunkScrew, prefix='mount_screw_')
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)
    EXAMPLE_ANCHORS = (
        #ad.surface_args('mount', 'face_centre', 'right'),
        #ad.surface_args('mount', 'face_corner', 'back', 0),
    )
    
    def build(self) -> ad.Maker:
        # Make the mount basic shape.
        mount_shape = self.mount_node()
        maker = mount_shape.solid('mount').transparent(False).colour('cyan', 0.5).at()
        
        # Here we remove the hook shape at the extreme angles and place it in the axle position.
        post_transform = ad.translate((1, -10, -mount_shape.size[0] / 2))
        # The hook cut shape is a slightly larger hook shape, this is determined by the slack parameter.
        hook_cut_shape = self.hook_node(
            hook_width=self.hook_shape.hook_width + 2 * self.slack,
            ring_thickness=self.hook_shape.ring_thickness + 2 * self.slack)
        # Add the hook cut shape as a hole at the closed location.
        maker.add_at(hook_cut_shape.hole('hook_low').transparent(0).colour('green', 0.1)
                     .at('pin_axis', centre=True),
                     'mount', 'face_centre', 'right',
                     post=post_transform)
        # Add the hook cut shape as a hole at the open location.
        maker.add_at(hook_cut_shape.hole('hook_high').colour('red')
                     .at('pin_axis', centre=True, post=ad.rotZ(-31)),
                'mount', 'face_centre', 'right',
                post=post_transform)

        # To make sure we actually place the hook into the hole, we need to make a clearance shape.
        # that should allow the hool to be inserted into the mount with no interference.        
        stadium_shape = hook_cut_shape.make_clearance_shape(0)
        
        maker.add_at(stadium_shape.hole('clearance').at('arc_centre', post=ad.rotZ(0)),
                     'hook_low', 'pin_axis')
        
        # The axle hole needs to be interference fit so it should be a bit smaller than the axle hole
        # in the hook.
        axle_shape = self.axle_node()
        maker.add_at(axle_shape.hole('axle').at('centre'),
                     'mount', 'face_centre', 'right',
                     post=post_transform * ad.tranZ(2))

        # Add the screw holes. The corners of the mount are reference points for the screw holes
        # but we want to place in the centre beteen the hook cutowt and the edge of the mount.
        # Hence we take the mount size over the X axis and remove the hook cutout width. The
        # divide by 4 is becuase we have 2 sides and we want to palce the centre of the holes 
        # half way between the hook cutout and the edge of the mount (divde by another 2) hence
        # divide by 4.
        face_size = (self.mount_size[0] - hook_cut_shape.hook_width) / 4
        
        screw_offset_xform = ad.translate((-face_size, -face_size, 0))
        
        screw_hole_shape = self.mount_screw_hole_node()
        for i in range(4):
            maker.add_at(screw_hole_shape.composite(('mount_screw_hole', i))
                         .at('top', post=screw_offset_xform),
                         'mount', 'face_corner', 'back', i)
            
        # Add a drain hole, otherwise the mount will fill with water for external settings.
        drain_hole_size = (hook_cut_shape.hook_width,
                           hook_cut_shape.ring_thickness,
                           self.mount_size[2] / 2)
       
        drain_hole_shape = ad.Box(size=drain_hole_size)
        
        maker.add_at(drain_hole_shape.hole('drain_hole').at('face_centre', 'top'),
                     'mount', 'face_centre', 'right',
                     post=post_transform * ad.ROTZ_90 * ad.ROTY_90)
        
        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
