'''
Created on 29-Jul-2023

@author: gianni
'''

import anchorscad as ad
from anchorscad.models.basic.pipe import Pipe
from anchorscad.models.basic.stadium import StadiumPrism
import numpy as np

@ad.datatree
class DrainProfile:
    r_flange: float=ad.dtfield(245 / 2, doc='Outer radius of drain')
    r_flange_inner_flat: float=ad.dtfield(8, doc='Flat component of inner flange')
    r_flange_inner: float=ad.dtfield(165 / 2, doc='Inner radius of drain')
    h_flange_inner: float=ad.dtfield(20.87 - 3.57, doc='Height of flange')
    r_drain_inner: float=ad.dtfield(115.4 / 2, doc='Inner radius of drain')
    h_drain_inner: float=ad.dtfield(63.5, doc='Height of drain')
    r_drain_lip: float=ad.dtfield(5.04, doc='Radius of drain lip')
    h_small_drain: float=ad.dtfield(20.2, doc='Height of small drain')
    t_flange: float=ad.dtfield(7.5, doc='Thickness of flange')

    def build(self) -> ad.Path:
        flat = self.r_flange_inner_flat
        path = (ad.PathBuilder()
                .move((-self.r_flange, -self.t_flange))
                .line((-self.r_flange, 0), 'outer_edge')
                .line((-self.r_flange_inner, 0), 'top')
                .spline((
                        (-self.r_flange_inner - flat, -self.h_flange_inner), 
                        (-self.r_drain_inner - flat, -self.h_flange_inner)),
                        cv_len=(8, 6),
                        name='bevel')
                .stroke(flat, name='inner_flange_flat')
                .stroke(self.h_drain_inner,
                        degrees=-90, 
                        name='upper_inside')
                .stroke(self.r_drain_lip,
                        degrees=90,
                        name='lip')
                .stroke(self.h_small_drain,
                        degrees=-90,
                        name='lower_inside')
                .stroke(18,
                        degrees=-90,
                        name='cutline')
                .stroke(65, degrees=-90, name='outer_drain')
                .build())
        
        return path

@ad.shape
@ad.datatree
class DrainOutline(ad.CompositeShape):
    '''Model of the drain to be used as an outline for inserts.
    '''

    profile_node: ad.Node=ad.Node(DrainProfile)
    drain_outline_path: ad.Path=ad.dtfield(self_default=lambda s: s.profile_node().build())   
    rotate_extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, prefix='drain_outline_')

    fn: int=ad.dtfield(128, doc='Number of facets for the linear extrusion')

    EXAMPLE_ANCHORS=(
        ad.surface_args('flange_base', scale_anchor=2),)

    @ad.anchor('top of drain')
    def top(self) -> ad.GMatrix:
        return ad.IDENTITY
    
    @ad.anchor('base of flange')
    def flange_base(self) -> ad.GMatrix:
        return ad.tranZ(-self.h_flange_inner)


    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.rotate_extrude_node()
        maker = shape.solid('drain').at()
        return maker

@ad.shape
@ad.datatree
class DrainPipe(ad.CompositeShape):
    inside_r: float=ad.dtfield(110 / 2 - 3.4, doc='Radius of pipe')
    outside_r: float=ad.dtfield(110.8 / 2, doc='Radius of pipe')
    h: float=ad.dtfield(100, doc='Length of pipe')
    hole_h_delta: float=ad.dtfield(0.1, doc='Delta height of hole')

    pipe_node: ad.Node=ad.ShapeNode(Pipe, expose_all=True)

    fn: int=ad.dtfield(128, doc='Number of facets for the linear extrusion')

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.pipe_node()
        maker = shape.composite('pipe').at()
        return maker


@ad.shape
@ad.datatree
class DrainOutlineAssembly(ad.CompositeShape):

    outline_node: ad.Node=ad.Node(DrainOutline)
    outline: ad.Shape=ad.dtfield(self_default=lambda s: s.outline_node())
    pipe_node: ad.Node=ad.Node(DrainPipe, expose_all=True)
    pipe: ad.Shape=ad.dtfield(self_default=lambda s: s.pipe_node())

    pipe_offset: float=ad.dtfield(10, doc='Offset of pipe from base of flange')

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        maker = self.outline.composite('outline').at()
        maker.add_at(self.pipe.composite('pipe').at('base', rh=1),
                  'flange_base', post=ad.tranZ(self.pipe_offset))
        return maker
    
@ad.shape
@ad.datatree
class DrainAssemblyWithCutout(ad.CompositeShape):
    '''Visual model of the outline with pipe with a cutout.'''
    assembly_node: ad.Node=ad.Node(DrainOutlineAssembly, expose_all=True)
    assembly: ad.Shape=ad.dtfield(self_default=lambda s: s.assembly_node())
    cutout_size: tuple=ad.dtfield((130, 130, 200), doc='Size of cutout')
    cutout_node: ad.Node=ad.Node(ad.Box, prefix='cutout_')

    def build(self) -> ad.Maker:
        maker = self.assembly.solid('assembly').at()
        maker.add_at(
            self.cutout_node().hole('cutout').at('face_corner', 1, 1)
        )

        return maker
    

@ad.datatree
class DrainHolderProfile(DrainProfile):
    '''Provides a Path for the drain holder for linear extrusion.'''

    r_holder_thickness: float=ad.dtfield(8, doc='Thickness of holder')
    pipe_side_upper_interference: float=ad.dtfield(0.3, doc='Interference of upper pipe side')
    pipe_side_lower_interference: float=ad.dtfield(0.0, doc='Interference of lower pipe side')
    pipe_side_h: float=ad.dtfield(80, doc='Height of pipe side')
    
    drain_side_upper_interference: float=ad.dtfield(0.0, doc='Interference of upper pipe side')
    drain_side_lower_interference: float=ad.dtfield(1.1, doc='Interference of lower pipe side')
    
    inside_r: float=ad.dtfield(110 / 2 - 3.4, doc='Inside radius of pipe')
    pipe_offset: float=ad.dtfield(10, doc='Offset of pipe from base of flange')

    def build(self) -> ad.Path:

        drain_y_start = - self.pipe_side_h - self.pipe_offset
        r_diff = self.r_drain_inner - self.inside_r

        angle_radians = ad.to_degrees(np.arctan(
            (self.drain_side_upper_interference - self.drain_side_lower_interference) 
            / self.h_drain_inner))
        


        path = (ad.PathBuilder()
                .move((self.inside_r - self.r_holder_thickness, 0))
                .line((self.inside_r - self.pipe_side_upper_interference, 0), 'top_edge')
                .line((self.inside_r - self.pipe_side_lower_interference, -self.pipe_side_h), 'pipe_side')
                .line((self.r_drain_inner - self.drain_side_upper_interference, drain_y_start), 'wedge')
                .line((self.r_drain_inner - self.drain_side_lower_interference, drain_y_start - self.h_drain_inner), 'drain_side')
                .stroke(self.r_holder_thickness + r_diff, degrees=-90 - angle_radians, name='drain_lip')
                .build())

        return path


def extents_to_height(extents: tuple) -> float:
    '''Convert extents to height.'''
    size = extents[1] - extents[0]
    return size[1]

def extents_to_width(extents: tuple) -> float:
    '''Convert extents to height.'''
    size = extents[1] - extents[0]
    return size[0]

def path_height(path: ad.Path) -> float:
    '''Get the height of a path.'''
    return extents_to_height(path.extents())

def path_width(path: ad.Path) -> float:
    '''Get the height of a path.'''
    return extents_to_width(path.extents())

@ad.shape
@ad.datatree
class DrainHolder(ad.CompositeShape):
    '''Model of the lower part of the drain.
    '''
    
    assembly_node: ad.Node=ad.Node(DrainOutlineAssembly, expose_all=True)
    assembly: ad.Shape=ad.dtfield(self_default=lambda s: s.assembly_node())

    
    profile_node: ad.Node=ad.Node(DrainHolderProfile)
    holder_path: ad.Path=ad.dtfield(self_default=lambda s: s.profile_node().build())
    rotate_extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, prefix='holder_')

    reinforcer_hole_inside_r: float=ad.dtfield(3.2, doc='Inner radius of hole for reinforcer rod')
    reinforcer_hole_outside_r: float=ad.dtfield(5, doc='Outer radius of hole for reinforcer rodd')
    reinforcer_hole_h: float=ad.dtfield(
        self_default=lambda s: path_height(s.holder_path), doc='Height of hole for reinforcer rod')
    reinforcer_pipe_node: ad.Node=ad.ShapeNode(Pipe, prefix='reinforcer_hole_', expose_all=True)
    reinforcer_count: int=ad.dtfield(3, doc='Number of reinforcer rods')

    snap_hole_r: float=ad.dtfield(3.2, doc='Radius of snap hole')
    snap_hole_h: float=ad.dtfield(self_default=lambda s: 2 + path_width(s.holder_path), doc='Height of snap hole')
    snap_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='snap_hole_')
    snap_hole_count: int=ad.dtfield(2, doc='Number of snap holes')
    snap_hole_angle_offset: float=ad.dtfield(20, doc='Angle offset of snap holes')
    snap_hole_z_pos: float=ad.dtfield(15, doc='Z position of snap holes')

    bottom_hole_r: float=ad.dtfield(5.3, doc='Radius of bottom hole')
    bottom_hole_w: float=ad.dtfield(5.3, doc='Stadium width of bottom hole')
    bottom_hole_h: float=ad.dtfield(25, doc='Height of bottom hole')
    bottom_hole_node: ad.Node=ad.ShapeNode(StadiumPrism, prefix='bottom_hole_')
    bottom_hole_count: int=ad.dtfield(15, doc='Number of bottom holes')
    bottom_hole_angle_offset: float=ad.dtfield(12, doc='Angle offset of bottom holes')
    bottom_hole_z_pos: float=ad.dtfield(22, doc='Z position of bottom holes')
    bottom_hole_offset: float=ad.dtfield(5, doc='lateral offset of bottom holes')
    bottom_hole_as_cage: bool=ad.dtfield(True, doc='Bottom hole as cage')
    bottom_hole_square_left: bool=ad.dtfield(True, doc='Bottom hole flattened on one end')

    grate_thickness: float=ad.dtfield(2, doc='Thickness of grate')
    grate_size: tuple=ad.dtfield(
        self_default=lambda s: 
            (s.grate_thickness, 2 * s.inside_r - 1, path_height(s.holder_path)))

    grate_node: ad.Node=ad.ShapeNode(ad.Box, prefix='grate_')

    grate_enable: bool=ad.dtfield(False, doc='Enable grate')

    cage_node: ad.Node=ad.CageOfNode()

    fn: int=ad.dtfield(128, doc='Number of facets for the linear extrusion')

    EXAMPLE_SHAPE_ARGS=ad.args(as_cage=False, drain_outline_degrees=90)

    def build(self) -> ad.Maker:

        maker = self.cage_node(self.assembly).at()

        holder_shape = self.rotate_extrude_node()

        holder_maker = holder_shape.solid('holder').at()
        
        if self.grate_enable:
            grate_shape = self.grate_node()
            holder_maker.add_at(
                grate_shape.solid('grate1').at('face_centre', 'top'))
            holder_maker.add_at(
                grate_shape.solid('grate2').at('face_centre', 'top'), post=ad.rotZ(90))

        maker.add_at(holder_maker.solid('holder').at(post=ad.tranZ(-self.pipe_offset - self.pipe_side_h)),
                     'flange_base')
        
        reinforcer_shape = self.reinforcer_pipe_node()

        for i in range(self.reinforcer_count):
            maker.add_at(
                reinforcer_shape
                    .composite(('reinforcer', i))
                    .at('surface'),
                'holder', 'top_edge', -0.5, degrees=i * 360 / self.reinforcer_count, post=ad.ROTX_90)
            
        snap_hole_shape = self.snap_hole_node()
        for i in range(self.snap_hole_count):
            maker.add_at(
                snap_hole_shape
                    .hole(('snap_hole', i))
                    .at('surface'),
                'holder', 'top_edge', -0.5,
                degrees=i * 360 / self.snap_hole_count + self.snap_hole_angle_offset,
                post=ad.tranZ(self.pipe_side_h - self.snap_hole_z_pos))
            
        bottom_hole_shape = self.bottom_hole_node()
        for i in range(self.bottom_hole_count):
            maker.add_at(
                bottom_hole_shape
                    .hole(('bottom_hole', i))
                    .at('base'),
                'holder', 'wedge', 0.5,
                degrees=i * 360 / self.bottom_hole_count + self.bottom_hole_angle_offset,
                post=ad.tranZ(self.bottom_hole_z_pos) * ad.tranY(self.bottom_hole_offset) * ad.ROTZ_90)

        return maker

@ad.datatree
class DrainGuageProfile(DrainHolderProfile):
    '''A profile of just the lower part of the holder.'''

    h_base_plate: float=ad.dtfield(2, doc='Height of base plate')

    def build(self) -> ad.Path:
        
        drain_y_start = - self.pipe_side_h - self.pipe_offset

        path = (ad.PathBuilder()
            .move((self.r_drain_inner - self.r_holder_thickness, drain_y_start))
            .line((self.r_drain_inner - self.drain_side_upper_interference, drain_y_start), 'top')
            .line((self.r_drain_inner - self.drain_side_lower_interference, drain_y_start - self.h_drain_inner), 'drain_side')
            #.stroke(self.r_holder_thickness, degrees=-90, name='drain_lip')
            .line((0, drain_y_start - self.h_drain_inner), 'base_plate_bottom')
            .stroke(self.h_base_plate, degrees=-90, name='base_plate_centre')
            .stroke(self.r_drain_inner - self.r_holder_thickness, degrees=-90, name='base_plate_top')
            .build())

        return path
    
@ad.shape
@ad.datatree
class DrainGuage(ad.CompositeShape):
    '''A guage for the drain lower part.
    '''
    r_holder_thickness: float=ad.dtfield(4, doc='Thickness of holder')
    profile_node: ad.Node=ad.Node(DrainGuageProfile)
    profile: ad.Shape=ad.dtfield(self_default=lambda s: s.profile_node())

    guage_path: ad.Path=ad.dtfield(self_default=lambda s: s.profile.build())

    rotate_extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, prefix='guage_')

    text_depth: float=ad.dtfield(4, doc='Depth of text')
    text_halign: str='centre'
    text_text: str=ad.dtfield(self_default=lambda s: 
        f'{s.r_drain_inner:.1f} {s.drain_side_upper_interference:.1f} {s.drain_side_lower_interference:.1f}')
    
    text_shape_node: ad.Node=ad.ShapeNode(ad.Text, prefix='text_')

    fn: int=ad.dtfield(128, doc='Number of facets')

    
    EXAMPLES_EXTENDED={
        's11' : ad.ExampleParams(
            shape_args=ad.args(r_drain_inner=114.5 / 2, 
                drain_side_upper_interference=0.1,
                drain_side_lower_interference=1.1),
            anchors=()
            ),
    }

    def build(self) -> ad.Maker:
        maker = self.rotate_extrude_node().solid('guage').at(post=ad.rotZ(45))

        text_shape = self.text_shape_node()
        maker.add_at(
            text_shape.solid('text').at('default'),
            'base_plate_centre', 1, post=ad.ROTX_270)

        return maker


@ad.datatree
class DrainWedgeOutline(DrainHolderProfile):
    '''Outline for a wedge to fit pvc pipe into to wedge into drain.'''

    h_base_plate: float=ad.dtfield(2, doc='Height of base plate')
    drain_outline_inner_r: float=ad.dtfield(105 / 2, doc='Inner radius of drain')
    base_bevel_r: float=ad.dtfield(1.65, doc='Radius of base bevel')

    def build(self) -> ad.Path:
        
        drain_y_start = -1.1

        path = (ad.PathBuilder()
            .move((self.drain_outline_inner_r, drain_y_start))
            .line((self.r_drain_inner - self.drain_side_upper_interference, drain_y_start), 'top')
            .line(
                (self.r_drain_inner - self.drain_side_lower_interference, 
                 drain_y_start - self.h_drain_inner + self.base_bevel_r),
                'drain_side')
            .arc_tangent_radius_sweep(
                radius=self.base_bevel_r,
                sweep_angle_degrees=-90,
                name='base_bevel')
            .stroke(self.r_holder_thickness - self.base_bevel_r, degrees=0, name='drain_lip')
            .line((self.drain_outline_inner_r, drain_y_start - self.h_drain_inner), 'base_plate_bottom')
            .build())

        return path
    
@ad.shape
@ad.datatree
class DrainPipeShell(ad.CompositeShape):
    drainpipe_node: ad.Node=ad.Node(DrainPipe)

    base_outside_r: float=ad.dtfield(
        self_default=lambda s: s.outside_r - s.hole_h_delta, 
        doc='Radius of top of pipe shell')

    pipe_shell_node: ad.Node=ad.ShapeNode(
        ad.Cone, 
        'h',
        {'r_top': 'outside_r', 'r_base': 'base_outside_r'})
    
    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.pipe_shell_node()
        maker = shape.composite('pipe_shell').at()
        return maker


@ad.shape
@ad.datatree
class DrainWedge(ad.CompositeShape):
    '''Alernative to the DrainHolder, this allows the 100mm PVC pipe to 
    fit and wedge into the drain hole. It has a lip at the base to prevent
    the pipe from falling through. This should take far less time and material
    to print.
    '''
    h: float=ad.dtfield(63, doc='Height of wedge')
    r_holder_thickness: float=ad.dtfield(4, doc='Thickness of holder')
    
    profile_node: ad.Node=ad.Node(DrainWedgeOutline)
    profile: ad.Shape=ad.dtfield(self_default=lambda s: s.profile_node())

    wedge_path: ad.Path=ad.dtfield(self_default=lambda s: s.profile.build())

    rotate_extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, prefix='wedge_')

    drain_pipe_shell_node: ad.Node=ad.ShapeNode(DrainPipeShell)

    fn: int=ad.dtfield(256, doc='Number of facets')

    EXAMPLE_SHAPE_ARGS=ad.args(hole_h_delta=0.2)

    def build(self) -> ad.Maker:
        maker = self.rotate_extrude_node().solid('wedge').at(post=ad.rotZ(45))

        drain_pipe_shell_shape = self.drain_pipe_shell_node()

        maker.add_at(
            drain_pipe_shell_shape.hole('drain_pipe_shell').at('top')
            )

        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
