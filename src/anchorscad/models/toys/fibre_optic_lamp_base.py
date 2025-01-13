'''
Created on 18 Jul 2021

@author: gianni
'''

from typing import Tuple
import anchorscad as ad
from anchorscad.models.components.board.arduino_nano import ArduinoNanoClassicMountPad
from anchorscad.models.components.led.cylindical_led import CylindricalLedBody
from anchorscad.models.components.sockets.dc_022_a import Dc022aHousing
import numpy as np
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew, \
    FlatHeadScrew
from anchorscad.models.components.switches.tactile_evq import TactileEvqHole

from anchorscad.models.components.board.buck_lm2596_hw411 import \
    ModuleBuckLm2586Hw411MountPad


@ad.datatree
class FibreOpticLampBasePathBuilder:
    '''A simple example of a path builder.'''

    r_base: float = ad.dtfield(50, doc='Width of block')
    h_corner: float = ad.dtfield(18, doc='Height of corner')
    sl_corner: float = ad.dtfield(12, doc='split length of corner')
    l_top: float = ad.dtfield(40, doc='Length of top')
    r_hole: float = ad.dtfield(17.4 / 2, doc='Radius of hole')
    path_metadata: ad.ModelAttributes = ad.EMPTY_ATTRS

    def build(self) -> ad.Path:
        path_modifer = ad.PathModifier(
            trim_negx=True, join_type=ad.PathModifier.OFFSET_MITRE, mitre_limit=3
        )
        builder = (
            ad.PathBuilder(path_modifier=path_modifer)
            .move((0, 0))
            .line((self.r_base, 0), 'base')
            .spline(
                (
                    (self.r_base + self.sl_corner, self.h_corner / 2),
                    (self.r_base + self.sl_corner, self.h_corner / 1.6),
                    (self.r_base, self.h_corner),
                ),
                cv_len=(self.sl_corner, self.sl_corner / 2),
                name='corner',
                metadata=self.path_metadata,
            )
            .stroke(self.l_top, name='top_slant')
            .line_wop(lambda last: (0, last.lastPosition()[1]), 'top_cap')
        )

        return builder.build()


@ad.shape
@ad.datatree(frozen=True)
class FibreOpticLampShell(ad.CompositeShape):
    '''
    A shell for a fibre optic lamp.
    '''

    path_builder: ad.Node = ad.ShapeNode(FibreOpticLampBasePathBuilder)
    inner_path: ad.Path = ad.dtfield(self_default=lambda s: s.path_builder().build())
    fn: int = ad.dtfield(64, doc='Number of facets for the extrude')
    outer_fn: int = ad.dtfield(self_default=lambda s: s.fn, 
                               doc='Number of facets for the outer extrude',
                               init=True)

    inner_extrude_node: ad.Node = ad.ShapeNode(
            ad.RotateExtrude, 
            {'path_fn' : 'path_fn', 'fn' : 'outer_fn'}, 
            prefix='inner_', 
            expose_all=True)
    inner_shape: ad.Node = ad.dtfield(self_default=lambda s: s.inner_extrude_node())

    shell_thickness: float = 2.5
    outer_path: ad.Path = ad.dtfield(
        self_default=lambda s: s.inner_path.transform(offset=s.shell_thickness, metadata=s.path_metadata)
    )
    outer_extrude_node: ad.Node = ad.ShapeNode(
            ad.RotateExtrude, 
            {'path_fn' : 'path_fn', 'fn' : 'outer_fn'}, 
            prefix='outer_', 
            expose_all=True)
    outer_shape: ad.Node = ad.dtfield(self_default=lambda s: s.outer_extrude_node())

    EXAMPLE_SHAPE_ARGS = ad.args(fn=256, outer_angle=270)
    EXAMPLE_ANCHORS = ()

    def build(self) -> ad.Maker:
        maker = self.outer_shape.solid('outer').at('base', 0, post=ad.ROTX_180 * ad.ROTZ_270)

        inner_maker = self.inner_shape.hole('inner').at('base', 0)

        maker.add_at(inner_maker, 'base', 0, apply_offset=False)

        return maker


HOLE_COMPENSATION = 0.1


@ad.shape
@ad.datatree
class FibreOpticLampSmallLens(ad.CompositeShape):
    '''
    A place for a lens for the fibre optic lamp.
    '''

    small_lens_hole_r: float = ad.dtfield(6.3 / 2 + HOLE_COMPENSATION, 'Radius of lens hole')
    cyl_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='small_lens_hole_')

    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)

    def build(self) -> ad.Maker:
        shape = self.cyl_node()

        maker = shape.solid('lens_hole').at()

        return maker


@ad.datatree
class WingProfileBuilder:
    '''A simple example of a path builder.'''

    w_tag: float = ad.dtfield(3, doc='Width of tag')
    h_tag: float = ad.dtfield(5, doc='Height of tag')
    w_shelf: float = ad.dtfield(1.5, doc='Width of shelf')
    h_stem: float = ad.dtfield(1.55, doc='Height of stem')

    def build(self) -> ad.Path:
        builder = (
            ad.PathBuilder()
            .move((0, 0))
            .line((self.w_tag, 0), 'base')
            .stroke(self.h_tag, angle=90, name='tag_rhs')
            .stroke(self.w_shelf, angle=90, name='shelf')
            .stroke(self.h_stem, angle=-90, name='stem_rhs')
            .stroke(self.w_tag - self.w_shelf, angle=90, name='tag_top')
            .line((0, 0), 'tag_lhs')
        )

        return builder.build()


@ad.shape
@ad.datatree
class FibreOpticLampLargeLens(ad.CompositeShape):
    '''
    A place for a lens for the fibre optic lamp.
    '''

    lge_inner_lens_hole_r: float = ad.dtfield(
        15.2 / 2 + HOLE_COMPENSATION, 'Radius of the innerlens hole'
    )
    inner_cyl_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='lge_inner_lens_hole_')

    lge_outer_lens_hole_r: float = ad.dtfield(
        16.5 / 2 + HOLE_COMPENSATION, 'Radius of the innerlens hole'
    )
    lge_outer_lens_hole_h: float = ad.dtfield(0.5, 'Height of the outer lens hole')
    outer_cyl_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='lge_outer_lens_hole_')

    wing_path_node: ad.Node = ad.ShapeNode(WingProfileBuilder, prefix='wing_')
    wing_path: ad.Node = ad.dtfield(self_default=lambda s: s.wing_path_node().build())

    wing_h: float = ad.dtfield(2.8 + HOLE_COMPENSATION, doc='Width of wing')
    wing_extrude_node: ad.Node = ad.ShapeNode(ad.LinearExtrude, prefix='wing_')

    epsilon: float = ad.dtfield(0.01, doc='Small offset to avoid z-fighting')

    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)

    EXAMPLE_ANCHORS = (
        ad.surface_args(('wing', 0), 'base', 0.5, rh=0.5),
        ad.surface_args(('wing', 1), 'base', 0.5, rh=0.5),
    )

    def build(self) -> ad.Maker:
        shape = self.inner_cyl_node()

        maker = shape.solid('inner_lens_hole').at()

        outer_shape = self.outer_cyl_node()

        maker.add_at(
            outer_shape.solid('outer_lens_hole').at('base'),
            'inner_lens_hole',
            'base',
            rh=1,
            post=ad.tranZ(self.epsilon),
        )

        wing_shape = self.wing_extrude_node()

        for i in range(2):
            maker.add_at(
                wing_shape.solid(('wing', i)).at('tag_top', 0, rh=0.5),
                'outer_lens_hole',
                'surface',
                angle=180 * i,
                rh=1,
                post=ad.ROTX_90 * ad.ROTZ_90 * ad.ROTX_180 * ad.ROTZ_180 * ad.rotY(2),
            )

        return maker


@ad.shape
@ad.datatree
class FibreOpticLampLightPipe(ad.CompositeShape):
    pipe_hole_h: float = ad.dtfield(15.0, 'Height of light pipe hole')
    pipe_hole_r_base: float = ad.dtfield(17.3 / 2, 'Base radius of light pipe hole')
    pipe_hole_r_top: float = ad.dtfield(17.8 / 2, 'Top radius of light pipe hole')

    pipe_hole_node: ad.Node = ad.ShapeNode(ad.Cone, prefix='pipe_hole_')

    pipe_wall_h: float = ad.dtfield(
        self_default=lambda s: s.pipe_hole_h - 2 * s.epsilon, doc='Height of light pipe wall'
    )
    pipe_wall_thickness: float = ad.dtfield(4, doc='Thickness of light pipe wall')
    pipe_wall_r: float = ad.dtfield(
        self_default=lambda s: s.pipe_hole_r_top + s.pipe_wall_thickness,
        doc='Base radius of light pipe wall',
    )
    pipe_wall_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='pipe_wall_')

    epsilon: float = ad.dtfield(0.01, doc='Small offset to avoid z-fighting')

    def build(self) -> ad.Maker:
        pipe_shape = self.pipe_wall_node()
        maker = pipe_shape.solid('pipe_wall').colour('grey').at('base', rh=1)

        hole_shape = self.pipe_hole_node()
        maker.add_at(
            hole_shape.hole('pipe_hole').at('base'),
            'pipe_wall',
            'base',
            post=ad.tranZ(self.epsilon),
        )

        return maker


@ad.shape
@ad.datatree
class FasteningColumns(ad.CompositeShape):
    '''
    A base for a fibre optic lamp.
    '''

    col_r: float = ad.dtfield(10 / 2, doc='Radius of column')
    col_h: float = ad.dtfield(50, doc='Height of column')
    col_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='col_')
    col_count: int = ad.dtfield(3, doc='Number of columns')

    shell_shape: FibreOpticLampShell = ad.dtfield(FibreOpticLampShell(), doc='Shell shape')

    col_base_offset: float = ad.dtfield(0.9, doc='The relative position of the column base')
    col_angle_offset: float = ad.dtfield(0.25, doc='The ralative rotation of the first column')
    
    cut_cyl_h: float = ad.dtfield(10, doc='Height of the cut plane')
    
    screw_hole_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: 24 - 0.01,
        doc='Overall screw length')
    screw_hole_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.cut_cyl_h - 0.01)
    screw_hole_tap_len: float=ad.dtfield(
        self_default=lambda s: s.screw_hole_shaft_overall_length - s.screw_hole_shaft_thru_length)
    screw_hole_size_name=ad.dtfield('M2.6')

    screw_hole: ad.Node=ad.dtfield(ad.ShapeNode(CountersunkScrew, prefix='screw_hole_'))
    
    base_part: ad.Part = ad.Part('base', 10)
    top_part: ad.Part = ad.Part('top', 5)
    locator_h: float = ad.dtfield(2, doc='Height of locator cone')
    locator_r_base: float = ad.dtfield(
        self_default= lambda s: s.col_r - 1, 
        doc='Base radius of locator cone')
    locator_r_top: float = ad.dtfield(
        self_default= lambda s: s.locator_r_base / 2, 
        doc='Top radius of locator cone')
    locator_part: ad.Part = ad.dtfield(
        self_default= lambda s: s.base_part.use_priority(s.top_part, 1),
        doc='Part for the locator. It is the top_part name with higher priority than the base.'
    )
    locator_node: ad.Node = ad.ShapeNode(ad.Cone, prefix='locator_')

    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)

    def build(self) -> ad.Maker:
        column_shape_upper = self.col_node().solid('upper').colour("firebrick").at('base')
        column_shape_lower = self.col_node(h=self.cut_cyl_h).solid('lower').colour("cyan").at('base', rh=1)
        column_shape = column_shape_upper.solid('column').at('base')
        column_shape.add_at(column_shape_lower)
        
        # Create a locator cone for allowing auto alignment of the columns. This becomes a part
        # of the top part but a higher priority than the base part so it will eat into the base.
        locator_shape = self.locator_node().solid('locator').colour("green")\
            .part(self.locator_part).at('top', rh=1)
        
        column_shape.add_at(locator_shape, 'base')
        
        screw_hole = self.screw_hole().composite('screw_hole').at('top')
        
        column_shape.add_at(screw_hole, 'base', pre=ad.tranZ(self.cut_cyl_h - 0.01))

        caged_maker = self.shell_shape.outer_shape.cage('shell').at('base')

        for i in range(self.col_count):
            column = column_shape.composite(('column', i)).at('lower', 'base')

            caged_maker.add_at(
                column,
                'base',
                self.col_base_offset,
                angle=(i + self.col_angle_offset) * 360 / self.col_count,
            )

        columns_maker = caged_maker.composite('all_columns').at()

        columns_maker.add_at(
            self.shell_shape.outer_shape.solid('mask')
                .colour("pink", 0.3)
                .transparent(True).at('base'), 
            'base')

        maker = columns_maker
        #maker = columns_maker.intersect('columns_masked').at()

        return maker


@ad.shape
@ad.datatree
class PowerAdapterHousing(ad.CompositeShape):
    '''
    A housing for a power adapter.
    '''

    shell_shape: FibreOpticLampShell = ad.dtfield(FibreOpticLampShell(), doc='Shell shape')
    jack_housing_node: ad.Node = ad.ShapeNode(Dc022aHousing)

    def build(self) -> ad.Maker:
        housing_shape = self.jack_housing_node()

        housing = housing_shape.composite('jack').at('stadium', 'right', rh=0, post=ad.ROTZ_270)

        shell_shape = self.shell_shape

        # Use the shell inner shape to position the jack.
        housing.add_at(
            shell_shape.cage('shell_cage').at('inner', 'base', 1, angle=90),
            'stadium',
            'right',
            rh=0,
            post=ad.ROTZ_180 * ad.ROTY_180 * ad.translate((0, -22, -2)),
        )

        # Add the outer shape to cut the jack hole.
        cut_shape = shell_shape.outer_shape
        housing.add_at(cut_shape.solid('cutter').at('base'), 'shell_cage', 'base')

        maker = housing.intersect('jack_masked').at()

        maker.add_at(
            housing_shape.socket_shape.hole('jack_hole').at('base'), 'jack', 'housing', 'base'
        )

        return maker


@ad.shape
@ad.datatree(frozen=True)
class FibreOpticLampMockLedAssembly(ad.CompositeShape):
    '''
    A mock LED assembly for the circuit board.
    '''
    
    led_node: ad.Node = ad.ShapeNode(CylindricalLedBody, prefix='led_')
    
    board_size: Tuple[float, float, float] = ad.dtfield((22.2, 17, 1.45), doc='Size of the PCB board')
    board_node: ad.Node = ad.ShapeNode(ad.Box, prefix='board_')
    
    pcb_hole_r: float = ad.dtfield(1.1, doc='Radius of the PCB hole')
    pcb_hole_h: float = ad.dtfield(self_default=lambda s: s.board_size[2] + 2 * s.epsilon, 
                                   doc='Height of the PCB hole')
    pcb_hole_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='pcb_hole_')
    
    
    epsilon: float = ad.dtfield(0.01, doc='Small offset to avoid z-fighting')
    
    fn: int = 32
    
    EXAMPLE_ANCHORS=(ad.surface_args('face_centre', 'base'),
                     ad.surface_args(('led', 0), 'led_body', 'top', 1.0),)
    
    def build(self) -> ad.Maker:
        board_shape = self.board_node()
        maker = board_shape.solid('board').at('face_centre', 'base', post=ad.ROTX_180)
        
        led_shape = self.led_node()
        offs = self.led_r_base / np.cos(np.pi / 6)
        for i in range(3):
            maker.add_at(led_shape.solid(('led', i)).at('base', 0, post=ad.rotX(180)),
                'face_centre', 'top', post=ad.rotZ(120 * i + 90) * ad.tranY(offs) * ad.rotZ(-120 * i + 90))
            
        pcb_hole = self.pcb_hole_node()
        for i, c in ((0, 0), (1, 2)):
            maker.add_at(
                pcb_hole.hole(('pcb_hole', i))
                    .at('base', post=ad.translate((-1 - 1.1, -3 - 1.1, -self.epsilon))),
                'face_corner', 'base', c)
        
        return maker
    
    def height(self) -> float:
        '''Return the height of the mock LED assembly from the tip of the LED to 
        the base of the .'''
        return ad.distance_between_point_plane(
            point=self.maker.at('face_centre', 'base'),
            plane=self.maker.at(('led', 0), 'led_body', 'top', 1.0))
        

@ad.shape
@ad.datatree
class FibreOpticLampMockLedPcbSupportBox(ad.CompositeShape):
    
    height: float = ad.dtfield(10, doc='Height of the support box')
    mock_board: FibreOpticLampMockLedAssembly = FibreOpticLampMockLedAssembly()
    
    support_box_margin: Tuple[float, float, float] = (1, 1, 4)
    
    support_box_size: Tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (
            s.mock_board.board_size[0] + s.support_box_margin[0] * 2, 
            s.mock_board.board_size[1] + s.support_box_margin[1] * 2, 
            s.height - s.support_box_margin[2]),
        doc='Size of the support box')
    support_box_node: ad.Node = ad.ShapeNode(
        ad.Box, prefix='support_box_', expose_all=True)
    
    pcb_screw_hole_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: s.support_box_size[2] - 0.01,
        doc='Overall screw length')
    pcb_screw_hole_shaft_thru_length: float=0
    pcb_screw_hole_tap_len: float=ad.dtfield(
        self_default=lambda s: s.pcb_screw_hole_shaft_overall_length - s.pcb_screw_hole_shaft_thru_length)
    pcb_screw_hole_size_name=ad.dtfield('M2.6')
    
    pcb_screw_hole_node: ad.Node=ad.dtfield(ad.ShapeNode(FlatHeadScrew, prefix='pcb_screw_hole_'))
    
    mock_board_material = ad.Material('mock_board', kind=ad.NON_PHYSICAL_MATERIAL_KIND)
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=32, pcb_screw_hole_hide_cage=False)
    EXAMPLE_ANCHORS = (ad.surface_args('face_centre', 'base'),
                       ad.surface_args(('pcb_screw_hole', 0), 'top'),)
    
    def build(self) -> ad.Maker:
        
        support_box = self.support_box_node()
        maker = support_box.solid('support_box').at('face_centre', 'base', post=ad.ROTX_180)

        mock_board_maker = self.mock_board.solid('mock_board') \
                .material(self.mock_board_material) \
                .at('face_centre', 'top', rh=1)
        
        maker.add_at(mock_board_maker, 'face_centre', 'top')
        
        
        pcb_screw_hole_shape = self.pcb_screw_hole_node()
        for i in range(2):
            pcb_screw_hole = pcb_screw_hole_shape.composite(('pcb_screw_hole', i)).at('top')
            maker.add_at(pcb_screw_hole, 'mock_board', ('pcb_hole', i), 'top')
        
        return maker

@ad.shape
@ad.datatree
class FibreOpticLampBase(ad.CompositeShape):
    '''
    A base for a fibre optic lamp.
    '''

    shell_node: ad.Node = ad.ShapeNode(FibreOpticLampShell)
    shell_shape: FibreOpticLampShell = ad.dtfield(self_default=lambda s: s.shell_node())

    inner_extents: np.array = ad.dtfield(
        self_default=lambda s: s.shell_shape.inner_path.extents(), doc='Outer extents of the shell'
    )

    cut_cyl_h: float = ad.dtfield(10, doc='Height of the cut cylinder')
    cut_cyl_r: float = ad.dtfield(
        self_default=lambda s: s.inner_extents[1][0] + s.shell_thickness / 2,
        doc='Radius of the cut cylinder',
    )

    cut_cyl_node: ad.Node = ad.ShapeNode(
        ad.Cylinder, {'fn' : 'outer_fn'}, prefix='cut_cyl_', expose_all=True)

    small_lens_hole_h: float = ad.dtfield(
        self_default=lambda s: s.shell_thickness * 1.5, doc='Height of the small lens hole'
    )
    small_lens_node: ad.Node = ad.ShapeNode(FibreOpticLampSmallLens)

    count_small_lens: int = ad.dtfield(6, doc='Number of small lenses')

    lge_inner_lens_hole_h: float = ad.dtfield(
        self_default=lambda s: s.shell_thickness * 1.3, doc='Height of the inner lens hole'
    )
    large_lens_node: ad.Node = ad.ShapeNode(FibreOpticLampLargeLens)

    count_large_lens: int = ad.dtfield(5, doc='Number of large lenses')
    lenses_as_holes: bool = ad.dtfield(True, doc='If True lenses are made as holes')

    pipe_hole_node: ad.Node = ad.ShapeNode(FibreOpticLampLightPipe)

    base_part: ad.Part = ad.Part('base', 10)
    top_part: ad.Part = ad.Part('top', 5)
    columns_node: ad.Node = ad.ShapeNode(FasteningColumns)

    jack_housing_node: ad.Node = ad.ShapeNode(PowerAdapterHousing)
    
    evq_hole_node: ad.Node = ad.ShapeNode(TactileEvqHole)
    
    board_node: ad.Node = ad.ShapeNode(FibreOpticLampMockLedAssembly)
    mock_board: FibreOpticLampMockLedAssembly = ad.dtfield(self_default=lambda s: s.board_node())

    # We need to compute height so we won't inject it here.    
    board_box_node: ad.Node = ad.ShapeNode(
        FibreOpticLampMockLedPcbSupportBox, {'height': None}, expose_all=True)
    
    switch_pos_anchor: ad.AnchorArgs = ad.surface_args(
        'outer', 'azimuth', 'corner', az_angle=14, angle=173 + 80)
    
    jack_pos_anchor: ad.AnchorArgs = ad.surface_args(
        'shell', 'outer', 'base', angle=135)
    
    buck_pad: ad.Node = ad.ShapeNode(
        ModuleBuckLm2586Hw411MountPad, 'pad_margin', prefix='buck_pad_')
    
    arduino_pad: ad.Node = ad.ShapeNode(
        ArduinoNanoClassicMountPad, prefix='arduino_pad_')

    EXAMPLE_SHAPE_ARGS = ad.args(
        fn=32, 
        path_fn=16, 
        outer_fn=128,
        outer_angle=270, 
        path_metadata=None) #ad.EMPTY_ATTRS.with_fn(8))
    EXAMPLE_ANCHORS = (ad.surface_args('corner', 1),
                       ad.surface_args('pipe', 'base'),
                       ad.surface_args('shell', 'inner', 'base'),)
    
    EXAMPLES_EXTENDED = {
        'fine': ad.ExampleParams(
            shape_args=ad.args(fn=64, path_fn=32, outer_fn=512),
        ),
        'draft': ad.ExampleParams(
            shape_args=ad.args(fn=16, path_fn=8, outer_fn=64),
        )
    }

    COLOURS = ('white', 'green', 'blue', 'pink', 'purple', 'red')

    def build(self) -> ad.Maker:
        outline_maker: ad.Maker = self.shell_shape.solid('shell').at()
        
        evq_switch_hole: TactileEvqHole = self.evq_hole_node()
        evq_switch_hole_maker = evq_switch_hole.hole('evq_switch') \
            .at('top', post=evq_switch_hole.scale * ad.ROTZ_90)
        
        outline_maker.add_at(evq_switch_hole_maker, anchor=self.switch_pos_anchor)
        small_lens_shape = self.small_lens_node()
        for i in range(self.count_small_lens):
            outline_maker.add_at(
                small_lens_shape.solid_hole(('small_lens', i), self.lenses_as_holes)
                .colour(self.COLOURS[i % len(self.COLOURS)])
                .at('base', rh=0.1),
                'corner',
                1,
                angle=i * 360 / self.count_small_lens,
            )

        large_lens_shape = self.large_lens_node()
        for i in range(self.count_large_lens):
            outline_maker.add_at(
                large_lens_shape.solid_hole(('large_lens', i), self.lenses_as_holes)
                .colour(self.COLOURS[i % len(self.COLOURS)])
                .at('outer_lens_hole', 'surface', 0, rh=0.8),
                'top_slant',
                0.3,
                angle=i * 360 / self.count_large_lens,
                post=ad.ROTX_90,
            )

        pipe_shape = self.pipe_hole_node()

        outline_maker.add_at(
            pipe_shape.composite('pipe').at('top'), 'top_cap', 1, 
                post=ad.tranZ(self.epsilon)
        )

        columns_shape = self.columns_node()
        outline_maker.add_at(columns_shape.composite('columns').at('base'), \
                             'shell', 'outer', 'base')
        
        trimmed_shape_maker = outline_maker.solid('outline').at('base')
        trimmed_shape_maker.add_at(self.shell_shape.outer_shape.solid('mask') \
            .at('base'), 'base')
        
        trimmed_shape = trimmed_shape_maker.intersect('trimmed').at('base')

        cut_cyl_shape = self.cut_cyl_node()
        lower_cutter = trimmed_shape.solid('outline').at('base')
        lower_cutter.add_at(cut_cyl_shape.solid('cut_cyl').at('base'), 'base')


        maker = lower_cutter.intersect('lower_base').part(self.base_part) \
            .at('base', post=ad.ROTX_180)

        jack_maker = (
            self.jack_housing_node().composite('jack').part(self.base_part)
                .at('shell_cage', 'base'))
        maker.add_at(jack_maker, anchor=self.jack_pos_anchor)

        top_maker = trimmed_shape.solid('top').part(self.top_part).at('base')

        maker.add_at(top_maker, 'base')
        
        board_height = np.abs(self.mock_board.height())
        avail_space = np.abs(ad.distance_between_point_plane(
            point=maker.at('pipe', 'base'),
            plane=maker.at('shell', 'inner', 'base')))
        
        board_box_shape = self.board_box_node(height=avail_space - board_height)
        board_box_maker = board_box_shape.composite('board_box') \
            .part(self.base_part).at('face_centre', 'base')
        
        maker.add_at(board_box_maker, 'shell', 'inner', 'base', post=ad.ROTZ_90)
        
        buck_pad = self.buck_pad().solid('buck_pad') \
            .part(self.base_part).at('face_edge', 'back', 2)

        maker.add_at(buck_pad, 'board_box', 'face_edge', 'back', 2, post=ad.ROTY_180)    
        
        arduino_pad = self.arduino_pad().solid('arduino_pad') \
            .part(self.base_part).at('face_edge', 'front', 0)
            
        maker.add_at(arduino_pad, 'board_box', 'face_edge', 'front', 0,
                     post=ad.ROTY_180)    
        

        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT = ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
