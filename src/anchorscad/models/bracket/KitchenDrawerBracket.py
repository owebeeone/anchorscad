'''
Models for an alternative bracket for Hettich drawers.

Created on 12 Oct 2021

@author: gianni
'''

import anchorscad as ad
from anchorscad.models.basic.cone_ended_prism import ConeEndedPrism
from anchorscad.models.basic.box_side_bevels import BoxSideBevels
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew, \
    FlatSunkScrew
from anchorscad.models.screws.tnut import Tnut


UPPER_LEAF_H=28.9
UPPER_CLAMP_NOTCH_H=13.5 + UPPER_LEAF_H
LIP_LEAF_H=50.7
LOWER_CLAMP_NOTCH_H=9.0 + LIP_LEAF_H
BRACKET_NOTCH=88.8
OVERALL_H=100
LEAF_D=30
RADIUS_TOP=2
LIP_DEPTH=4.4
TOP_WIDTH=11.6
WALL_T=1.4
RADIUS_UNDER=RADIUS_TOP - WALL_T
NOTCH_DEPTH=18.8
CUT_WIDTH=3.15
NOTCH_CENTRE_DEPTH=16.5 + WALL_T
SCREW_HOLE_SEPS=63.71
SCREW_TOP_OFFS=(14.17 + 7.45 / 2)
SCREW_WIDTH=7.4
SCREW_OUTER_OFFS=2.2
SCREW_HOLE_DIA=3.6
BRACKET_TOP_WIDTH=14.4
BRACKET_BASE_WIDTH=12.4
epsilon=0.001

DRAWER_SIDE_PATH=(ad.PathBuilder().move([0, 0])
      .line([0, LIP_DEPTH - RADIUS_TOP], 'lip')
      .arc_tangent_point([RADIUS_TOP, LIP_DEPTH], name='lip_top_arc_l')
      .line([TOP_WIDTH - RADIUS_TOP, LIP_DEPTH], 'upper_top')
      .arc_tangent_point([TOP_WIDTH, LIP_DEPTH - RADIUS_TOP], name='lip_top_arc_r')
      .line([TOP_WIDTH, -OVERALL_H + LIP_DEPTH], 'side_r')
      .line([TOP_WIDTH - WALL_T, -OVERALL_H + LIP_DEPTH], 'base')
      .line([TOP_WIDTH - WALL_T, LIP_DEPTH - RADIUS_TOP], 'side_ir')
      .arc_tangent_point([TOP_WIDTH - RADIUS_TOP, LIP_DEPTH - WALL_T], name='lip_top_arc_ir')
      .line([RADIUS_TOP, LIP_DEPTH - WALL_T], 'lower_top')
      .arc_tangent_point([WALL_T, LIP_DEPTH - RADIUS_TOP], name='lip_top_arc_il')
      .line([WALL_T, 0], 'ilip')
      .line([0, 0], 'ulip')
      .build())

BRACKET_YS=(
   - epsilon,
   BRACKET_NOTCH - LOWER_CLAMP_NOTCH_H,
   BRACKET_NOTCH - LIP_LEAF_H,
   BRACKET_NOTCH - UPPER_CLAMP_NOTCH_H,
   BRACKET_NOTCH - UPPER_LEAF_H,
   BRACKET_NOTCH,
   )

DRAWER_CUTOUT_PATH=(ad.PathBuilder().move([0, BRACKET_YS[0]])
      .line([0, BRACKET_YS[1]], 'lhs_1')
      .line([-NOTCH_DEPTH, BRACKET_YS[1]], ('notch', 'l', 'base'))
      .line([-NOTCH_DEPTH, BRACKET_YS[2]], ('notch', 'l', 'side'))
      .line([-NOTCH_DEPTH + NOTCH_CENTRE_DEPTH, 
             BRACKET_YS[2]], ('notch', 'l', 'top'))
      .line([-NOTCH_DEPTH + NOTCH_CENTRE_DEPTH, 
             BRACKET_YS[3]], 'lhs_2')
      .line([-NOTCH_DEPTH, BRACKET_YS[3]], ('notch', '2', 'base'))
      .line([-NOTCH_DEPTH, BRACKET_YS[4]], ('notch', '2', 'side'))
      .line([0, BRACKET_YS[4]], ('notch', '2', 'top'))
      .line([0, BRACKET_YS[5]], 'lhs_3')
      .line([CUT_WIDTH + epsilon, BRACKET_YS[5]], 'top')
      .line([CUT_WIDTH + epsilon, 0], 'rhs')
      .line([0, 0], 'base')
      .build())


@ad.shape
@ad.datatree(frozen=True)
class KitchenDrawerMountHole(ad.CompositeShape):
    '''
    Elongated screw hole.
    Args:
      h: The overall height of the screw hole.
      rw: Width of screw hole (the longest depth).
      r: Radius of screws.
      shell_w: Shell width of screw holes.
      h_cs: Height of the countersunk portion of the screw hole.
      r_top_cs: Top radius of screw hole
      t_base_cs: Base radius of screw hole (usually same as r).
      h_access: Extra hole to ensure access to hole.
    '''
    h: float=16
    rw: float=SCREW_WIDTH - 1
    r: float=SCREW_HOLE_DIA / 2
    shell_w: float=SCREW_OUTER_OFFS
    h_cs: float=SCREW_OUTER_OFFS
    r_top_cs: float= SCREW_HOLE_DIA / 2 + SCREW_OUTER_OFFS
    t_base_cs: float= SCREW_HOLE_DIA / 2
    h_access: float=15
    
    # Injects just the ShapeNode fields.
    cone_node: ad.Node=ad.ShapeNode(ConeEndedPrism, {})
    
    epsilon: float=epsilon
    fn: int=64
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('base'),
        ad.surface_args('top'),)
    
    def build(self) -> ad.Maker:
        
        w = self.rw - 2 * self.r
        sr = self.shell_w + self.r
        shell = self.cone_node(h=self.h, w=w, r_base=sr, r_top=sr)
        
        maker = shell.solid('shell').at('base')
        
        hole = self.cone_node(h=self.h + 2 * self.epsilon, 
                              w=w, 
                              r_base=self.r, 
                              r_top=self.r)
        
        cs_hole = self.cone_node(h=self.h_cs + 2 * self.epsilon, 
                              w=w, 
                              r_base=self.t_base_cs, 
                              r_top=self.r_top_cs)
    
        access_hole = self.cone_node(h=self.h_access + 2 * self.epsilon, 
                              w=w, 
                              r_base=self.r_top_cs, 
                              r_top=self.r_top_cs)

        
        maker.add_at(hole.hole('hole').at('base'),
                     'base', post=ad.tranZ(self.epsilon))
        maker.add_at(cs_hole.hole('cs_hole').at('top'),
                     'top', post=ad.tranZ(self.epsilon))
        maker.add_at(access_hole.hole('access_hole').at('base'),
                     'top', post=ad.ROTX_180 * ad.tranZ(self.epsilon))
        
        return maker
        
    def centre_offs(self):
        return self.rw / 2 + self.shell_w


@ad.shape
@ad.datatree(frozen=True)
class KitchenDrawerOutline(ad.CompositeShape):
    '''Outline of side edge of drawer.
    
    This shape is to be used to locate the bracket components.
    '''
    t: float=1.1
    drawer_path: ad.Path=DRAWER_SIDE_PATH
    drawer_depth: float=100
    drawer_cut_path: ad.Path=DRAWER_CUTOUT_PATH
    drawer_cut_depth: float=WALL_T
    front_cut_depth: float=CUT_WIDTH
    hook_shape: ad.Shape=ad.Box(
        [WALL_T, LIP_DEPTH, 2 * (BRACKET_YS[3] - BRACKET_YS[2])])
    show_outline: bool=False
    
    extents: tuple=ad.dtfield(
        self_default=lambda s: s.drawer_path.extents(),
        init=False)
    
    cut_extents: tuple=ad.dtfield(
        self_default=lambda s: s.drawer_cut_path.extents(),
        init=False)
    
    front_size: tuple=ad.dtfield(
        self_default=lambda s: (
            s.extents[1][0] - s.extents[0][0],
            s.cut_extents[1][1] - s.cut_extents[0][1],
            s.front_cut_depth),
        init=False)
    
    fn: int=16
    

    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        ad.surface_args('upper_notch'),
        ad.surface_args('lower_notch'),)
    
    def build(self) -> ad.Maker:
        render_mode = (ad.ModeShapeFrame.SOLID 
                       if self.show_outline else 
                       ad.ModeShapeFrame.HOLE)
        drawer_shape = ad.LinearExtrude(
            path=self.drawer_path, h=self.drawer_depth, fn=self.fn)
        maker = drawer_shape.solid('drawer_side').at('base', 0)
        
        box_cage_shape = ad.Box(
            list(self.extents[1][i] - self.extents[0][i] for i in (0, 1))
            + [self.drawer_depth]
            )
        
        maker.add_at(box_cage_shape.cage('drawer_side_cage')
                     .colour([0, 1, 0, 0.5])
                     .at('face_edge', 0, 0),
                     'upper_top', 0.5, rh=1, post=ad.ROTX_180
                     )

        front_cut_shape = ad.Box(
            [self.front_size[0] + 2 * epsilon, 
             self.front_size[1] + 2 * epsilon, 
             self.front_size[2] + epsilon]
            )
        
        maker.add_at(front_cut_shape
                     .named_shape('front_cut_shape', render_mode)
                     .colour([0, 0, 1, 0.5])
                     .at('face_edge', 0, 0),
                     'drawer_side_cage', 'face_edge', 0, 0,
                     post=ad.translate([epsilon / 2, -epsilon, epsilon]))
                     
        cut_shape = ad.LinearExtrude(
            path=self.drawer_cut_path,
            h=self.drawer_cut_depth + 2 * epsilon, 
            fn=self.fn)
        
        maker.add_at(cut_shape
                     .named_shape('cut_shape', render_mode)
                     .colour([1, 0, 0, 0.5])
                     .at('base', 0),
                     'front_cut_shape', 'face_edge', 3, 2, 0,
                     post=ad.ROTZ_90 * ad.ROTX_180)

        maker.add_at(self.hook_shape.solid('hook')
                     .at('face_edge', 2, 1, 0.5),
                     'cut_shape', 'lhs_2', 0.5,
                     post=ad.IDENTITY)

        return maker

    @ad.anchor('Upper notch on side of drawer.')
    def lower_notch(self, t=0.0, **kwds):
        return self.at('cut_shape', ('notch', 'l', 'side'), t, **kwds)


    @ad.anchor('Upper notch on side of drawer.')
    def upper_notch(self, t=1.0, **kwds):
        return self.at('cut_shape', ('notch', '2', 'side'), t, **kwds)


@ad.shape
@ad.datatree
class KitchenDrawerSideAdjuster(ad.CompositeShape):
    '''The drawer level adjuster.'''
    r_outer: float=(BRACKET_YS[2] - BRACKET_YS[1]) / 2
    h_outer: float=WALL_T + 3
    r_offs: float=1.5
    r_inner1: float=(BRACKET_YS[2] - BRACKET_YS[1]) / 2 + 1.5
    r_inner2: float=(BRACKET_YS[2] - BRACKET_YS[1]) / 2 + 1
    h_inner: float=None
    screw_blade_hole: tuple=(
        (BRACKET_YS[2] - BRACKET_YS[1]) - 2,
        1.2,
        5)
    do_cut_model: bool=False
    
    inner_cone_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, {
            'h': 'h_inner',
            'r_base': 'r_inner2',
            'r_top': 'r_inner1'}),
        init=False
        )
    
    cut_h: float=ad.dtfield(
        self_default=lambda s: s.h_outer + epsilon,
        init=False)
    
    cut_outer_cone_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, {
            'h': 'cut_h',
            'r_base': 'r_inner1',
            'r_top': 'r_inner1'}),
        init=False
        )
    
    outer_cone_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, {
            'h': 'cut_h',
            'r_base': 'r_outer',
            'r_top': 'r_outer'}),
        init=False
        )
    
    fn: int=128
    
    EXAMPLE_SHAPE_ARGS=ad.args(h_inner=8)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        inner = self.inner_cone_node()
        maker = inner.solid('inner').at('base')
        
        if self.do_cut_model:
            # Cut model will cut the entire area.
            outer = self.cut_outer_cone_node()            
            maker.add_at(outer.solid('outer').at('base'),
                         'base', rh=1, h=-epsilon)
        else:
            outer = self.outer_cone_node()
            maker.add_at(outer.solid('outer').at('base'),
                         'base', rh=1, h=-epsilon,
                         post=ad.tranX(self.r_offs))

        if self.screw_blade_hole:
            blade = ad.Box(self.screw_blade_hole)
            
            maker.add_at(blade.hole('blade_hole')
                         .at('face_centre', 1),
                         'base', post=ad.tranZ(epsilon))

        return maker
        

@ad.shape
@ad.datatree
class KitchenDrawerBracket(ad.CompositeShape):
    '''
    An alternative bracket for Hettich drawers. These brackets are made with
    a cast alloy that seems to always fatigue fail. Also I have not been able
    to find replacement part.
    
    Features:
    This bracket is comprised of 3 parts.
    a) Main (outer) bracket.
    b) The inner plate.
    c) Adjustment knob.
    
    
    This bracket well need the following fasteners.
    a) 6mm T-nut
    b) M6 14mm counter sunk machine screw (mates with T-nut)
    c) M4 14mm self tapping flat head screw.
    d) M2.6 20mm counter sunk self tapping screw (for locking adjuster knob.)
    e) 1x25mm 6G self tapping screw to replace one of the original 
       12.5mm 6G screws.
    
    Unlike the original bracket, the main holding component is on the outside
    of the drawer. The drawer has a locking lip that is slots into the 
    main bracket. The inner plate holds the lip in the slot preventing the
    drawer from slipping away. This arrangement provides for substantially
    more material allowing for a 3D printed part to handle the load.
    
    Note that the upper screw mounting hole on the drawer front cannot be raised 
    without interfering with the drawer roller, hence the original screw is for
    the upper mounting hole but a new longer screw is used for the lower mounting
    hole.
    
    The M6 screw provides most of stabilization forces for the bracket and
    with the associated T-nut can be tightened substantially. Unlike the 
    original Hettich bracket, the bracket maintains a stiffer grip on the
    drawer front panel and it feels much nicer.
    
    Assembly:
    a) Insert T-nut into main (outer) bracket.
    b) Without inserting the adjustment knob, align the inner bracket
       over the t-nut hole and screw the M6 screw to fully press the
       t-nut in place then remove the M6 screw.
    c) Remove the old Hettich bracket.
    d) Insert the adjuster knob and attach the outer bracket and do not tighten
       the fasting screws completely (allow for movement).
    e) Attach the outer bracket and align the drawer lip with the corresponding
       hole.
    f) Insert and loosely tighten the M6 and M4 screws to hold the inner bracket
       in place.
    g) Close the drawer and turn the adjuster with a blade screw driver to 
       achieve the desired alignment.
    h) Tighten all the screws and insert the M2.6 locking screw to lock the
       adjuster knob.
    i) Enjoy a hassle free drawer.
    
    
    Note this is replacement for the Hettich 08855, 08856, 08857 08858 parts.
    
    This anchorcad model generates 6 OpenScad files for each of the different 
    component for left and right versions of the drawer bracket.
    
    Args:
      outline: The "outline" model used to locate the mounting holes and 
              to cut any interference with the side panel of the drawer.
      front_bevel_radius: The radius of the front bevel.
      mount_hole_lower: The Shape model for the lower front drawer mounting hole.
      mount_hole_lower: The Shape model for the upper front drawer mounting hole.
      expand_base_lower: The lower size of the base of the outer plate.
      expand_base_upper: The upper size of the base of the outer plate.
      screw_top_offs: Upper mount hole offset.
      screw_hole_seps: Lower mount hole offset from top hole.
      show_outline: Debugging setting for showing the drawer outline.
      adjuster: The shape type for theadjuster knob.
    '''
    outline: ad.Shape=KitchenDrawerOutline()
    front_bevel_radius: float=RADIUS_TOP

    mount_hole_lower_h=17
    mount_hole_lower_node: ad.Node=ad.ShapeNode(
        KitchenDrawerMountHole, 
        {'h': 'mount_hole_lower_h'}, 
        prefix='mount_hole_')
    
    mount_hole_upper_h=5
    mount_hole_upper_node: ad.Node=ad.ShapeNode(
        KitchenDrawerMountHole, 
        {'h': 'mount_hole_upper_h'}, 
        prefix='mount_hole_')
    
    expand_base_lower: float=30
    expand_base_upper: float=20
    expand_x_top: float=2
    expand_y_top: float=5
    screw_top_offs: float=SCREW_TOP_OFFS
    screw_hole_seps: float=SCREW_HOLE_SEPS
    show_outline: bool=False
    
    # Adjuster
    adjuster: type=KitchenDrawerSideAdjuster
    adjuster_offs: float=0
    
    # Inner bracket
    inner_h: float=5
    r_inner_bevel: float=5
    screw_size: float=2.6
    
    # Variants of this.
    show_adjuster: bool=False
    show_inner: bool=False
    make_mirror: bool=False
    
    # Fasteners
    countersunk_scew_hole_type : ad.Shape=CountersunkScrew
    flatsunk_scew_hole_type : ad.Shape=FlatSunkScrew
    
    front_size: tuple=ad.dtfield(
        self_default=lambda s: s.outline.front_size, init=False)
    
    box_side_bevels_node: ad.Node=ad.ShapeNode(BoxSideBevels, prefix='front_')
    
    linear_extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, {})
    
    tnut_node: ad.Node=ad.ShapeNode(Tnut, {})
    
    fn: int=64
    fa: float=None
    fs: float=None
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    EXAMPLES_EXTENDED={'outer': ad.ExampleParams(ad.args()),
                       'adjuster': ad.ExampleParams(
                            ad.args(
                                show_adjuster=True)),
                       'inner': ad.ExampleParams(
                            shape_args=ad.args(
                                show_inner=True),
                            anchors=(
                                # ad.surface_args(
                                #     'inner_plate', 'face_centre', 4),
                                # ad.surface_args(
                                #     'outline', 'drawer_side_cage', 'face_centre', 2),
                                ),
                            ),
                       'mirror_outer': ad.ExampleParams(
                            ad.args(make_mirror=True)),
                       'mirror_adjuster': ad.ExampleParams(
                            ad.args(
                                make_mirror=True,
                                show_adjuster=True)),
                       'mirror_inner': ad.ExampleParams(
                            ad.args(
                                make_mirror=True,
                                show_inner=True),
                            anchors=(
                                # ad.surface_args(
                                #     'inner_plate', 'face_centre', 4),
                                # ad.surface_args(
                                #     'outline', 'drawer_side_cage', 'face_centre', 2),
                                ),
                            ),
                        }
    
    def build(self) -> ad.Maker:
        render_mode = (ad.ModeShapeFrame.SOLID 
                       if self.show_outline else 
                       ad.ModeShapeFrame.HOLE)
        
        maker = self.outline.named_shape('outline', render_mode).at()
        
        front_shape = self.box_side_bevels_node()
        
        maker.add_at(front_shape.solid('front')
                     .at('centre'),
                     'front_cut_shape', 'centre'
                     )
        
        cut_extents = self.outline.drawer_cut_path.extents()
        width = cut_extents[1][0] - cut_extents[0][0]
        
        height_v = (maker.at('upper_notch') * ad.GVector((0, 0, 0))
                  - maker.at('lower_notch') * ad.GVector((0, 0, 0)))
        
        height = height_v.z
        base_upper_x = height/2 + self.expand_base_upper - 7
        base_lower_x = height/2 + self.expand_base_lower - 8
        top_x = height/2 + self.expand_x_top
        top_y = width + self.expand_y_top
        
        holder_path = (ad.PathBuilder()
                  .move([0, 0])
                  .line([-base_lower_x, 0], 'base_l')
                  .line([-base_lower_x, 14], 'base_l2')
                  .line([-top_x, top_y], 'side_l')
                  .line([0, top_y], 'top_l')
                  .line([top_x, top_y], 'top_r')
                  .line([base_upper_x, 0], 'side_r')
                  .line([0, 0], 'base_r')
                  .build())

        holder_shape = self.linear_extrude_node(
            path=holder_path, 
            h=self.outline.front_size[0] - self.outline.drawer_cut_depth)

        maker.add_at(holder_shape.solid('holder')
                     .colour([0.7, 0, 0.5])
                     .at('top_l', 0),
                     'lower_notch', rh=1, 
                     post=ad.translate(
                         [-self.expand_x_top, 
                          0, 
                          -self.expand_y_top]))
        
        mount_hole_upper = self.mount_hole_upper_node()
        
        screw_post = ad.ROTZ_90 * ad.translate(
                         [self.screw_top_offs, 
                          mount_hole_upper.centre_offs(),
                          0])
        maker.add_at(mount_hole_upper.composite('upper_hole').at('base'),
                     'front', 'face_edge', 1, 2, 1,
                     post=screw_post)
        
        maker.add_at(self.mount_hole_lower_node().composite('lower_hole').at('base'),
                     'front', 'face_edge', 1, 2, 1,
                     post=screw_post * ad.tranX(self.screw_hole_seps))
        
        maker.add_at(
            self.outline.hook_shape.hole('hook_hole')
            .at('face_centre', 0),
            'outline', 'hook',
            'face_centre', 0)
        
        adjuster_shape = self.adjuster(
            h_inner=holder_shape.h + 2 * epsilon,
            screw_blade_hole=None,
            do_cut_model=not self.show_adjuster,
            fn=self.fn)
        
        self.adjuster_solid = self.adjuster(
            h_inner=holder_shape.h)
        
        ib = self.r_inner_bevel
        holder_plate_size = (width + ib - 3.5, 
                             height + ib, 
                             self.inner_h)
        holder_plate = BoxSideBevels(holder_plate_size, ib)
        
        screw1_axis = ad.surface_args('upper_notch', rh=0, t=0.5,
                     post=ad.ROTX_90 * ad.tranY(12))
        
        screw2_axis = ad.surface_args('lower_notch', rh=0, t=0.5,
                     post=ad.ROTX_90 * ad.tranY(15))
        
        # Tnut side.
        outer_plane = ad.surface_args(
            'outline', 'drawer_side_cage', 'face_centre', 2)

        maker.add_at(self.tnut_node(left_handed=not self.make_mirror)
                     .hole('tnut1').at('base'),
                     post=ad.find_intersection(
                                maker, outer_plane, screw1_axis) 
                            * ad.ROTX_180
                            * ad.tranZ(epsilon))
        
        if self.show_inner:
            maker = maker.cage('main_bracket_cage').at()
            
        # Make adjuster hole.
        adjuster_yoffs = self.adjuster_offs + adjuster_shape.r_inner1
        maker.add_at(adjuster_shape.hole('adjuster')
                     .at('top', post=ad.ROTZ_90),
                     'lower_notch', rh=1, t=0.5,
                     post=ad.ROTX_90 * ad.translate(
                         (0, adjuster_yoffs, epsilon)))
        
        # Inner plate
        inner_msf = (ad.ModeShapeFrame.SOLID 
                     if self.show_inner 
                     else ad.ModeShapeFrame.CAGE)
        maker.add_at(holder_plate.named_shape('inner_plate', inner_msf)
                     # .colour((0, 1, 0, 0.3))
                     # .transparent(True)
                     .at('face_corner', 2, 0),
                     'lower_notch', rh=0, t=0,
                     post=ad.ROTZ_180 * ad.ROTY_180 
                            * ad.translate((-ib / 2, 0, ib))
                     )
        
        self_tap_screw_hole = self.flatsunk_scew_hole_type(
                shaft_overall_length=self.outline.front_size[1] + self.inner_h,
                shaft_thru_length=self.inner_h,
                tap_shaft_dia_delta=0,
                size_name="M4",
                head_depth_factor=0.1,
                include_tap_shaft=False,
                include_thru_shaft=False,
                as_solid=False,
                fn=self.fn)
        
        inner_plate_plane = ad.surface_args('inner_plate', 'face_centre', 4)
        screw2_intersection = ad.find_intersection(
            maker, inner_plate_plane, screw2_axis)
        
        
        maker.add_at(self_tap_screw_hole.composite('screw2')
                     # .colour((1, 0.2, 0.5, 0.4))
                     # .transparent(True)
                     .at('top'),
                     post=screw2_intersection * ad.tranZ(-epsilon))
        
        
        tnut_screw_hole = self.countersunk_scew_hole_type(
                shaft_overall_length=self.outline.front_size[1] + self.inner_h,
                shaft_thru_length=self.inner_h,
                tap_shaft_dia_delta=0,
                size_name="M6",
                head_depth_factor=1.1,
                include_tap_shaft=False,
                include_thru_shaft=False,
                as_solid=False,
                fn=self.fn)
        
        # Adjuster fixer screw.
        adjuster_fixer = self.countersunk_scew_hole_type(
                shaft_overall_length=25,
                shaft_thru_length=14,
                tap_shaft_dia_delta=0,
                size_name="M2.6",
                head_depth_factor=0.8,
                include_tap_shaft=False,
                include_thru_shaft=False,
                as_solid=False,
                fn=self.fn)
        
        maker.add_at(adjuster_fixer.composite('adjuster_fixer').at('top'), 
                     'holder', 'top_l', 0.72, rh=0.71,
                     post=ad.ROTX_180)
        
        # Inner plate transforms
        screw1_intersection = ad.find_intersection(
            maker, inner_plate_plane, screw1_axis)
        
        maker.add_at(tnut_screw_hole.composite('screw1').at('top'),
                     post=screw1_intersection)
        
        if self.show_adjuster:
            return self.adjuster_solid.solid('adjuster').at('base')
        else:
            if self.make_mirror:
                return maker.solid('mirror').at(post=ad.mirror(ad.X_AXIS))
            else:
                return maker

    @ad.anchor('An example anchor specifier.')
    def side(self, *args, **kwds):
        return self.maker.at('face_edge', *args, **kwds)


MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
