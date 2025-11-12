import anchorscad as ad
from anchorscad_models.basic.box_side_bevels import BoxSideBevels
from anchorscad_models.basic.extruded_sequence import ExtrudedSequence, ExtrudedSequenceBuilder, SequenceItem
from anchorscad_models.screws.CountersunkScrew import CountersunkScrew


@ad.shape
@ad.datatree(frozen=True)
class ToggleSwitchMTS103(ad.CompositeShape):
    """
    MTS-103 toggle switch outline.
    """
    shaft_r: float = ad.dtfield(3.0, doc="Radius of the toggle switch shaft")
    shaft_h: float = ad.dtfield(8.7, doc="Height of the toggle switch shaft")
    bat_r: float = ad.dtfield(1.5, doc="Radius of the toggle switch body")
    bat_h: float = ad.dtfield(14, doc="Height of the toggle switch body")
    bat_angle: float | ad.Angle = ad.dtfield(10, doc="Angle of the bat")
    bat_offset: float = ad.dtfield(4, doc="Offset of the bat from the shaft")
    w: float = ad.dtfield(8.0, doc="Width of the switch body (e.g., X-dimension)")
    h: float = ad.dtfield(13.0, doc="Length of the switch body (e.g., Y-dimension)")
    d: float = ad.dtfield(10.0, doc="Depth of the main switch body (Z-dimension)")
    terminal_d: float = ad.dtfield(4.0, doc="How far terminals extend beyond the main body depth")
    terminal_cavity_d: float = ad.dtfield(8, doc="How far terminal cavity extends beyond the main body depth")
    terminal_cavity_h: float = ad.dtfield(12, doc="How wide terminal cavity extends beyond the main body width")
    
    case_size: tuple[float, float, float] = ad.dtfield(self_default=lambda s: (s.w, s.d, s.h))
    case_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='case_')
    bat_node: ad.Node[ad.Cylinder] = ad.ShapeNode(ad.Cylinder, prefix='bat_')
    shaft_node: ad.Node[ad.Cylinder] = ad.ShapeNode(ad.Cylinder, prefix='shaft_')
    
    terminal_cavity_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (s.w, s.terminal_cavity_d, s.terminal_cavity_h))
    terminal_cavity_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='terminal_cavity_')

    fn: int = 32
    
    def build(self) -> ad.Maker:

        case_shape = self.case_node()
        maker = case_shape.solid('case').at('face_centre', 'back')
        
        shaft_shape = self.shaft_node()
        maker.add_at(shaft_shape.solid('shaft').at('base'), 'face_centre', 'front', post=ad.ROTX_180)
        
        bat_shape = self.bat_node()
        maker.add_at(
            bat_shape.solid('bat')
            .at('base'), 
            'shaft', 'top', 
            post=ad.rotX(180) * ad.tranZ(self.bat_offset) * ad.rotX(self.bat_angle))
        
        terminal_cavity_shape = self.terminal_cavity_node()
        maker.add_at(
            terminal_cavity_shape.solid('terminal_cavity').colour("blue", 0.5)
            .at('face_centre', 'front'), 
            'case', 'face_centre', 'back', 
            post=ad.ROTX_180)
        return maker
    
    
@ad.shape
@ad.datatree(frozen=True)
class RockerSwitchKCD3(ad.CompositeShape):
    """
    KCD-3 rocker switch outline.
    """
    w: float = ad.dtfield(10.5, doc="Width of the rocker switch body")
    h: float = ad.dtfield(26.0, doc="Height of the rocker switch body")
    d: float = ad.dtfield(20.0, doc="Depth of the rocker switch body")
    
    case_size: tuple[float, float, float] = ad.dtfield(self_default=lambda s: (s.w, s.d, s.h))
    case_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='case_')
    
    lip_w: float = ad.dtfield(2.5, doc="Width of the lip")
    lip_h: float = ad.dtfield(2.4, doc="Height of the lip")
    lip_d: float = ad.dtfield(2.3, doc="Depth of the lip")
    
    lip_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (s.lip_w * 2 + s.w, s.lip_d, s.lip_h * 2 + s.h))
    lip_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='lip_')
    
    terminal_cavity_d: float = ad.dtfield(40, doc="How far terminal cavity extends beyond the main body depth")

    terminal_cavity_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (s.w, s.terminal_cavity_d, s.h))
    terminal_cavity_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='terminal_cavity_')
    
    wing_w: float = ad.dtfield(7.5, doc="Width of the wing")
    wing_h: float = ad.dtfield(4.5, doc="Height of the wing")
    
    wing_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (s.wing_w, s.d, s.wing_h))
    wing_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='wing_')
    
    def build(self) -> ad.Maker:
        case_shape = self.case_node()
        maker = case_shape.solid('case').at('face_centre', 'back', post=ad.ROTX_180)
    
        lip_shape = self.lip_node()
        maker.add_at(
            lip_shape.solid('lip').at('face_centre', 'back'), 
            'case', 'face_centre', 'front', 
            post=ad.ROTX_180)
        
        terminal_cavity_shape = self.terminal_cavity_node()
        maker.add_at(
            terminal_cavity_shape.solid('terminal_cavity').colour("blue", 0.5)
            .at('face_centre', 'front'), 
            'case', 'face_centre', 'back', 
            post=ad.ROTX_180)
        
        wing_shape = self.wing_node()
        for side in ('top', 'base'):
            maker.add_at(
                wing_shape.solid(('wing', side)).colour("green").at('face_centre', side), 
                'case', 'face_centre', side, 
                post=ad.ROTX_180)
        
        bound_box = ad.Box(self.bbox_size())
        maker.add_at(
            bound_box.cage('bound_box').transparent(True).colour("red", 0.5).at('face_centre', 'front'),
            'lip', 'face_centre', 'front')
        
        return maker
    
    def bbox_size(self) -> tuple[float, float, float]:
        """
        Bounding box size of the rocker switch and cavities.
        """
        return (
            self.lip_size[0],
            self.case_size[1] + self.lip_size[1] + self.terminal_cavity_size[1],
            self.case_size[2] + self.wing_size[2] * 2
        )

@ad.datatree(frozen=True)
class WireHoleProfilePath(ad.CompositeShape):
    """
    Wire hole.
    """
    r: float = ad.dtfield(6.6 / 2, doc="Radius of the wire hole")
    d: float = ad.dtfield(0.0, doc="Depth of hole")
    
    def build(self) -> ad.Path:
        path = (ad.PathBuilder()
            .move((0, 0))
            .line((-self.r, 0), 'centerline')
            .arc_tangent_radius_sweep(
                radius=self.r, 
                side=True,
                sweep_angle=-180, 
                angle=90, 
                name='arc')
            .stroke(length=self.d + self.r, name='rhs')
            .stroke(length=self.r * 2, angle=-90, name='base')
            .stroke(length=self.d + self.r, angle=-90, name='lhs')
            .build())
        return path

@ad.shape
@ad.datatree(frozen=True)
class WireHole(ad.CompositeShape):
    """
    Wire hole.
    """
    profile_path_node: ad.ShapeNode[WireHoleProfilePath]
    
    path: ad.Path = ad.dtfield(self_default=lambda s: s.profile_path_node().build())
    
    vd: float = ad.dtfield(5.0, doc="Vertical depth of the wire hole")
    ld: float = ad.dtfield(30.0, doc="Lateral depth of the wire hole")
    radius: float = ad.dtfield(6.0, doc="Radius of the wire hole")
    wh_angle: ad.Angle = ad.dtfield(ad.angle(99), doc="Angle of the wire hole")
    
    anchors: tuple[str, str] = ('lhs', 'rhs')
    
    seq_builder_node: ad.ShapeNode[ExtrudedSequenceBuilder]
    seq_builder: ExtrudedSequenceBuilder = ad.dtfield(self_default=lambda s: s.seq_builder_node())
    sequence: tuple[SequenceItem, ...] = ad.dtfield(self_default=lambda s: 
        s.seq_builder
        .reset()
        .linear(s.vd)
        .rotate(s.radius, s.wh_angle, anchor=ad.PathAnchor.anchor(s.anchors[0], t=0))
        .linear(s.ld)
        .rotate(s.radius, s.wh_angle, anchor=ad.PathAnchor.anchor(s.anchors[1], t=0))
        .linear(s.vd)
        .build())
    ex_seq_node: ad.ShapeNode[ExtrudedSequence]
    
    EXAMPLE_ANCHORS=(
        ad.surface_args(('item', 0), 'base', 0, h=2, ex_end=True),
        )
    
    def build(self) -> ad.Maker:
        profile_path_shape = self.ex_seq_node()
        maker = profile_path_shape.solid('wire_hole').at()
        return maker
    

@ad.shape
@ad.datatree(frozen=True)
class ScrewHole(ad.CompositeShape):
    
    outline_shape: RockerSwitchKCD3 | None = None
    outline_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: s.outline_shape.bbox_size())
        
    top_screw_shaft_overall_length: float = ad.dtfield(self_default=lambda s: s.outline_size[2])
    top_screw_shaft_thru_length: float = ad.dtfield(self_default=lambda s: s.outline_size[2])
    top_screw_tap_shaft_dia_delta: float = 0
    top_screw_size_name: str = "9g"
    top_screw_head_depth_factor: float = 1.1
    top_screw_include_thru_shaft: bool = False
    top_screw_as_solid: bool = False
    top_screw_hole_node: ad.Node = ad.ShapeNode(CountersunkScrew, prefix='top_screw_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        outline_shape=RockerSwitchKCD3(),
        top_screw_as_solid=True)
    
    def build(self) -> ad.Maker:
        top_screw_shape = self.top_screw_hole_node()
        maker = top_screw_shape.composite('top_screw').at()
        return maker
    
@ad.shape
@ad.datatree(frozen=True)
class RockerSwitchKCD3CaseLowProfile(ad.CompositeShape):
    """
    KCD-3 rocker switch low profile case.
    """
    outline_node: ad.ShapeNode[RockerSwitchKCD3] = \
        ad.ShapeNode(RockerSwitchKCD3, prefix='outline_')
    outline_shape: RockerSwitchKCD3 = ad.dtfield(self_default=lambda s: s.outline_node())
    
    outline_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: s.outline_shape.bbox_size())
    
    delta_h: float = ad.dtfield(15.0, doc="Extra height to add to the case")
    delta_w: float = ad.dtfield(0.0, doc="Extra width to add to the case")
    delta_d: float = ad.dtfield(2.0, doc="Extra depth to add to the case")
    
    case_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (
            s.outline_size[1] + s.delta_d,
            s.outline_size[2] + s.delta_h * 2,
            s.outline_size[0] + s.delta_w * 2,
        )
    )
    case_bevel_radius: float=4.0
    case_node: ad.Node[BoxSideBevels] = ad.ShapeNode(BoxSideBevels, prefix='case_')
    
    case_base_h: float = ad.dtfield(10.0, doc="Height of the base of the case")
    case_base_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (
            s.case_size[0],
            s.case_size[1],
            s.case_base_h
        )
    )
    case_base_node: ad.Node[BoxSideBevels] = ad.ShapeNode(
        BoxSideBevels, {'bevel_radius': 'case_bevel_radius'}, prefix='case_base_', expose_all=True)
    
    case_lid_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (
            s.case_size[0],
            s.case_size[1],
            s.case_size[2] - s.case_base_h
        )
    )
    case_lid_node: ad.Node[BoxSideBevels] = ad.ShapeNode(
        BoxSideBevels, {'bevel_radius': 'case_bevel_radius'}, prefix='case_lid_', expose_all=True)
    
    lid_part: ad.Part = ad.Part("lid", priority=1.0)
    base_part: ad.Part = ad.Part("base", priority=1.1)
    
    wire_hole_node: ad.ShapeNode[WireHole] = ad.ShapeNode(WireHole, prefix='wh_')

    screw_positions: ad.AnchorArgs = (
        ad.surface_args('case_lid', 'face_corner', 'base', 0, post=ad.translate((5, 17, 0))),
        ad.surface_args('case_lid', 'face_corner', 'base', 1, post=ad.translate((17, 5, 0))),
        ad.surface_args('case_lid', 'face_corner', 'base', 2, post=ad.translate((14, 17, 0))),
        ad.surface_args('case_lid', 'face_corner', 'base', 3, post=ad.translate((17, 14, 0))),
    )
    screw_hole_node: ad.ShapeNode[ScrewHole]
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        fn=64,
        top_screw_as_solid=False)
    EXAMPLE_ANCHORS=(
        ad.surface_args('rocker_switch', 'terminal_cavity', 'face_corner', 'base', 2),
        )

    def build(self) -> ad.Maker:
        case_shape = self.case_node()
        maker = case_shape.cage('case').colour("cyan", 0.5).at(
            'face_centre', 'back', post=ad.ROTX_180)
        
        maker.add_at(
            self.outline_shape.hole('rocker_switch').at('bound_box', 'face_centre', 'front'),
            'case', 'face_centre', 'back', 
            post=ad.ROTZ_90)
        
        case_base_shape = self.case_base_node()
        maker.add_at(
            case_base_shape.solid('case_base')
            .part(self.base_part)
            .colour("green")
            .at('face_centre', 'top'),
            'case', 'face_centre', 'top')
        
        case_lid_shape = self.case_lid_node()
        maker.add_at(
            case_lid_shape.solid('case_lid')
            .part(self.lid_part)
            .colour("red", 0.1)
            .at('face_centre', 'base'),
            'case', 'face_centre', 'base')
        
        wire_hole_maker_upper = self.wire_hole_node() \
            .hole('wire_hole_upper') \
            .at(('item', 0), 'base', 0, h=2, ex_end=True)
            
        maker.add_at(wire_hole_maker_upper, 
                     'rocker_switch', 'terminal_cavity', 'face_corner', 'base', 1,
                     post=ad.ROTX_270 * ad.tranZ(3 - 0.01))

        wire_hole_maker_lower = self.wire_hole_node(anchors=self.wh_anchors[::-1]) \
            .hole('wire_hole_lower') \
            .at(('item', 0), 'base', 1, h=2, ex_end=True)
        
        maker.add_at(wire_hole_maker_lower, 
                     'rocker_switch', 'terminal_cavity', 'face_corner', 'top', 2,
                     post=ad.ROTX_270 * ad.ROTY_90 * ad.tranZ(3 - 0.01))
        
        screw_shape = self.screw_hole_node()
        for i, anchor in enumerate(self.screw_positions):
            screw_maker = screw_shape.composite(('screw', i)).at('top')
            maker.add_at(screw_maker, anchor=anchor)

        return maker


# Standard boilerplate for running and generating models
MAIN_DEFAULT = ad.ModuleDefault(all=2, write_stl_mesh_files=True) # Generate all default outputs

if __name__ == "__main__":
    ad.anchorscad_main()
