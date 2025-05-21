'''
Created on 16-May-2025

@author: gianni
'''

from abc import ABC

from pyparsing import abstractmethod
import anchorscad as ad
import numpy as np

from anchorscad_models.screws.CountersunkScrew import CountersunkScrew
from anchorscad_models.screws.holes import CountersinkAccessHole, CountersinkSelfTapHole


@ad.datatree
class StripProfilePathBuilder:
    '''Led strip profile.'''
    strip_w: float = 12.1
    strip_d: float = 2.2
    strip_lip_d: float = 0.6
    strip_lip_w: float = 1.5
    
    def build(self) -> ad.Path:
        delta_d = self.strip_d - self.strip_lip_d
        delta_w = self.strip_w - self.strip_lip_w * 2
        builder = ad.PathBuilder()
        with builder.construction() as cbuilder:
            (cbuilder
                .move((0, 0))
                .line((-self.strip_w / 2, 0), 'l-base'))
        path = (builder
                .move((0, 0))
                .line((-self.strip_w / 2, 0), 'l-base-actual')
                .stroke(self.strip_lip_d, -90, name='l-side')
                .stroke(self.strip_lip_w, -90, name='l-top')
                .stroke(delta_d, 90, name='l-led-side')
                .stroke(delta_w, -90, name='top')
                .stroke(delta_d, -90, name='r-led-side')
                .stroke(self.strip_lip_w, 90, name='r-top')
                .stroke(self.strip_lip_d, -90, name='r-side')
                .line((0, 0), 'r-base')
                .build())
        
        return path


@ad.shape
@ad.datatree
class StripOutline(ad.CompositeShape):
    '''
    Outline of LED strip
    '''
    path_builder: ad.Node = ad.ShapeNode(StripProfilePathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(50, doc='Height of the shape')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('strip_outline').at()
        return maker
    

@ad.datatree
class LensProfilePathBuilder:
    '''The lens profile (not including space for LED strip).'''
    strip_w: float = 12.1
    strip_d: float = 2.2
    
    lens_delta_w: float = 2
    lens_delta_d: float = 0.4
    
    lens_w: float = ad.dtfield(self_default=lambda s : s.lens_delta_w + s.strip_w)
    lens_d: float = ad.dtfield(self_default=lambda s : s.lens_delta_d + s.strip_d)
    
    side_angles: tuple[float, float] = ad.dtfield(self_default=lambda s : (-80, 80))
    side_cv_len: tuple[float, float] = ad.dtfield(self_default=lambda s : (2, 1))
    
    with_wire_cavity: bool = False
    
    cavity_w: float = 10
    cavity_d: float = 5
    
    def build(self) -> ad.Path:
        builder = ad.PathBuilder()
        
        with builder.construction() as cbuilder:
            (cbuilder
                .move((0, 0))
                .line((-self.lens_w / 2, 0), 'l-base'))
            (cbuilder
                .move((self.lens_w / 2, 0))
                .line((0, 0), 'r-base'))
            
            
        if self.with_wire_cavity:
            (builder
                    .move((0, 0))
                    .line((0, -self.cavity_d), 'cl-cavity')
                    .line((-self.cavity_w / 2, -self.cavity_d), 'l-cavity-base')
                    .line((-self.cavity_w / 2, 0), 'l-cavity-side')
                    .line((-self.lens_w / 2, 0), 'l-base-actual'))
        else:
            (builder
                    .move((0, 0))
                    .line((-self.lens_w / 2, 0), 'l-base-actual'))
        (builder
                .spline(
                    ((-1 - self.lens_w / 2, self.lens_d), (-self.lens_w / 2, self.lens_d)), 
                    angle=self.side_angles, 
                    cv_len=self.side_cv_len,
                    name='l-side')
                .line((self.lens_w / 2, self.lens_d), 'top')
                .spline(
                    ((1 + self.lens_w / 2, 0), (self.lens_w / 2, 0)), 
                    angle=-np.array(self.side_angles[::-1]), 
                    cv_len=self.side_cv_len[::-1],
                    name='r-side'))
        if self.with_wire_cavity:
            (builder
                    .line((self.cavity_w / 2, 0), 'r-base-actual')
                    .line((self.cavity_w / 2, -self.cavity_d), 'r-cavity-side')
                    .line((0, -self.cavity_d), 'r-cavity-base'))
        else:
            (builder
                .line((0, 0), 'r-base-actual')
                )
        
        return builder.build()


@ad.shape
@ad.datatree
class LensOutline(ad.CompositeShape):
    '''
    Outline of LED strip
    '''
    path_builder_node: ad.Node = ad.ShapeNode(LensProfilePathBuilder)
    path_builder: LensProfilePathBuilder = ad.dtfield(self_default=lambda s: s.path_builder_node())
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder.build())
    
    h: float=ad.dtfield(50, doc='Height of the shape')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('strip_outline').at()
        return maker
    
    @property
    def lens_w(self) -> float:
        return self.path_builder.lens_w
    
    @property
    def lens_d(self) -> float:
        return self.path_builder.lens_d

@ad.shape
@ad.datatree(frozen=True)
class Lens(ad.CompositeShape):
    '''
    Outline of LED strip
    '''
    outline_node: ad.Node[LensOutline] = ad.ShapeNode(
        LensOutline, 
        {'h': 'h', 'with_wire_cavity': 'with_wire_cavity'}, 
        prefix='outline_', 
        expose_all=True)
    outline: LensOutline = ad.dtfield(self_default=lambda s: s.outline_node())
    strip_node: ad.Node[StripOutline] = ad.ShapeNode(StripOutline, {'h': 'h'}, prefix='strip_', expose_all=True)
    strip: StripOutline = ad.dtfield(self_default=lambda s: s.strip_node())
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32, h=233)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.outline
        maker = shape.solid('lens').at('top', 0.5)
        
        strip = self.strip
        shape_maker = strip.hole('strip_outline').at('l-base', 0)
        maker.add_at(shape_maker, 'l-base', 0)
        
        return maker
    
    @property
    def lens_w(self) -> float:
        return self.outline.lens_w
    
    @property
    def lens_d(self) -> float:
        return self.outline.lens_d
    
    
@ad.datatree
class HolderProfilePathBuilder:
    '''The lens profile (not including space for LED strip).'''
    lens_shape: Lens = Lens() # For w, d
    
    wall_w: float = 3.5
    foot_w: float = 1.5
    base_d: float = 2.5
    
    lens_top_ext: float = 1
    wall_d_factor_cp1: float = 0.9
    wall_d_factor: float = 0.6
    
    wire_wall_w: float = 2
    wire_hole_h: float = 5
    wire_hole_w: float = 2.5
    
    angle: float | ad.Angle = 30
    
    with_lower_wire_cavity: bool = False
    
    def build(self) -> ad.Path:
        angle = ad.angle(self.angle)
        rot = angle.rotZ.A[:2, :2]
        
        lens_d = self.lens_shape.lens_d
        lens_w = self.lens_shape.lens_w
    
        lens_start = rot @ np.array((0, lens_d))
        lens_end = rot @ np.array((lens_w, lens_d))
        lens_end_w_ext = rot @ np.array((lens_w + self.lens_top_ext, lens_d))
        lens_start_cp = rot @ np.array((-1, lens_d))
        
        holder_start = np.array((self.foot_w, self.base_d))
        actual_lens_start = holder_start + lens_start
        actual_lens_start_cp = holder_start + lens_start_cp
        
        actual_lens_end = holder_start + lens_end
        actual_lens_end_w_ext = holder_start + lens_end_w_ext
        
        rhs_wall_end_cp1 = (actual_lens_end_w_ext[0] + self.wall_w, 
                        actual_lens_end_w_ext[1] * self.wall_d_factor_cp1)
        
        
        rhs_wall_end = (actual_lens_end_w_ext[0] + self.wall_w, 
                        actual_lens_end_w_ext[1] * self.wall_d_factor)
        
        rhs_wall_end_cp2 = (actual_lens_end_w_ext[0] + self.wall_w, 
                        actual_lens_end_w_ext[1] * self.wall_d_factor + 1)

        builder = ad.PathBuilder()
        (builder
                .move((0, 0))
                .line((-self.foot_w, 0), 'l-base')
                .spline((actual_lens_start_cp, actual_lens_start), 
                        cv_len=(2, 1),
                        angle=(-90, 0),
                        name='l-side')
                .line(actual_lens_end, 'lens-top')
                .line(actual_lens_end_w_ext, 'lens-top-ext')
                .spline((rhs_wall_end_cp1, rhs_wall_end_cp2, rhs_wall_end), 
                        cv_len=(3, 3), 
                        name='wall-top')
                .line((rhs_wall_end[0], 0), 'r-side')
                .stroke(self.wire_wall_w, -90, name='r-base1')
                .stroke(self.wire_hole_h, -90, name='r-wire-hole'))
        if self.with_lower_wire_cavity:
            (builder
                .stroke(2, 50, name='cavity-hole-top')
                .stroke(self.wire_hole_h, 70, name='l-wire-hole')
                .line((6, 0), 'r-base2'))
        else:
            (builder
                .stroke(self.wire_hole_w, 90, name='wire-hole-top')
                .stroke(self.wire_hole_h, 90, name='l-wire-hole')
                .line((self.foot_w, 0), 'r-base2'))
        
        return builder.build()


@ad.shape
@ad.datatree
class HolderOutline(ad.CompositeShape):
    '''
    Outline of holder
    '''
    path_builder: ad.Node = ad.ShapeNode(HolderProfilePathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(50, doc='Height of the shape')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('holder_outline').at()
        return maker


@ad.shape
@ad.datatree
class HolderSupported(ad.CompositeShape):
    '''
    Holder fully filled in.
    '''
    lens_outline_node: ad.Node[Lens] = ad.ShapeNode(
        Lens, 
        {'h': 'h', 'with_wire_cavity': 'with_wire_cavity'}, 
        prefix='lens_', 
        expose_all=True)
    
    lens_shape: Lens = ad.dtfield(self_default=lambda s: s.lens_outline_node())
    
    with_wire_cavity: bool = True
    with_lower_wire_cavity: bool = False
    with_lens_cavity: bool = True
    
    outline_node: ad.Node[HolderOutline] = ad.ShapeNode(
        HolderOutline, 
        {'h': 'h', 'lens_shape': 'lens_shape', 'with_lower_wire_cavity': 'with_lower_wire_cavity'}, 
        prefix='outline_', 
        expose_all=True)
    outline: HolderOutline = ad.dtfield(self_default=lambda s: s.outline_node())
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32, h=10, with_wire_cavity=False, with_lens_cavity=True)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        shape = self.outline
        maker = shape.solid('holder_supported').at()
        
        if self.with_lens_cavity:
            lens_outline = self.lens_shape.outline
            shape_maker = lens_outline.hole('lens_outline').at('top', 0)
            maker.add_at(shape_maker, 'lens-top', 0)
        
        return maker
    
def item(wire_cavity: bool | None = None, 
         lens_cavity: bool | None = None, 
         lower_wire_cavity: bool | None = None,
         h: float | None = None) -> tuple[bool, bool, bool, float]:
    return wire_cavity, lens_cavity, lower_wire_cavity, h

@ad.shape
@ad.datatree
class LedStripMountScrewHole(ad.CompositeShape):

    screw_hole_size_name: str='M2.6'
    screw_hole_shaft_overall_length: float=ad.dtfield(25, doc='Overall screw length')
    screw_hole_shaft_thru_length: float=ad.dtfield(5)

    
    screw_hole: ad.Node=ad.dtfield(ad.ShapeNode(CountersunkScrew, prefix='screw_hole_'))
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32, screw_hole_as_solid=True)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
    )
    
    def build(self) -> ad.Maker:
        shape = self.screw_hole()
        maker = shape.composite('screw_hole').at()
        return maker

@ad.shape
@ad.datatree
class LedStripHolder(ad.CompositeShape):
    '''
    Holder for LED strip.
    '''
    holder_node: ad.ShapeNode[HolderSupported]
    screw_hole_node: ad.ShapeNode[LedStripMountScrewHole]
    
    start_r: float = 0
    
    sequence: tuple[tuple[bool | None, bool | None, bool | None, float | None], ...] = (
        item(wire_cavity=False, lower_wire_cavity=False, lens_cavity=False, h=2),
        item(lower_wire_cavity=True, h=6),
        item(lower_wire_cavity=True, lens_cavity=True, h=3),
        item(wire_cavity=True, h=5),
        item(wire_cavity=False, lower_wire_cavity=False, h=50 + 138 + 30),
        item(wire_cavity=True, lower_wire_cavity=True, h=5),
        item(wire_cavity=False, h=3),
        item(lens_cavity=False, h=6),
        item(lower_wire_cavity=False, h=2),
    )
    
    side_wire_cavity_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (s.outline_wire_hole_w, 
                                s.outline_wire_hole_h, 
                                20))
    
    side_wire_cavity_node: ad.ShapeNode[ad.Box] = ad.ShapeNode(ad.Box, prefix='side_wire_cavity_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32, screw_hole_as_solid=False)
    EXAMPLE_ANCHORS=(
        ad.surface_args(('segment', 0), 'l-base'),
        ad.surface_args(('segment', 1), 'l-base'),
        ad.surface_args(('segment', 2), 'l-base'),
        ad.surface_args(('segment', 3), 'l-base'),
        ad.surface_args(('segment', 4), 'l-base'),
    )
    
    def build(self) -> ad.Maker:
        
        def segment_sequence(sequence: tuple[tuple[bool | None, bool | None, float | None], ...]) -> tuple[tuple[bool, bool, float], ...]:
            iterator = iter(sequence)
            wire_cavity, lens_cavity, lower_wire_cavity, h = next(iterator)
            result = {
                'with_wire_cavity': wire_cavity,
                'with_lens_cavity': lens_cavity,
                'with_lower_wire_cavity': lower_wire_cavity,
                'h': h,
            }
            yield result
            for new_wire_cavity, new_lens_cavity, new_lower_wire_cavity, new_h in iterator:
                if new_wire_cavity is not None:
                    wire_cavity = new_wire_cavity
                if new_lens_cavity is not None:
                    lens_cavity = new_lens_cavity
                if new_lower_wire_cavity is not None:
                    lower_wire_cavity = new_lower_wire_cavity
                if new_h is not None:
                    h = new_h
                result = {
                    'with_wire_cavity': wire_cavity,
                    'with_lens_cavity': lens_cavity,
                    'with_lower_wire_cavity': lower_wire_cavity,
                    'h': h,
                }
                yield result
            return
        
        maker: ad.Maker | None = None
        
        lens_len = 0
        overall_len = 0
        
        for segment_no, segment_kwds in enumerate(segment_sequence(self.sequence)):
            if segment_kwds['with_lens_cavity']:
                lens_len += segment_kwds['h']
            overall_len += segment_kwds['h']
            if maker is None:
                maker = self.holder_node(**segment_kwds).solid(('segment', segment_no)).at()
            else:
                #colour = (segment_no / (1 + len(self.sequence)), 0., 0.5)
                maker = maker.add_at(
                    self.holder_node(**segment_kwds)
                        .solid(('segment', segment_no))
                        #.colour(colour)
                        .at('l-base', 0),
                    ('segment', segment_no - 1),'l-base', 0, rh=1
                    )
                
        print(f'lens_len: {lens_len}, overall_len: {overall_len}')
        
        side_wire_cavity = self.side_wire_cavity_node()
        side_wire_cavity_maker = side_wire_cavity.hole('side_wire_cavity-start') \
            .colour("green") \
            .at('face_corner', 'base', 1)
        
        maker.add_at(side_wire_cavity_maker, 
                     ('segment', 0), 'r-side', 1, rh=1,
                     post=ad.ROTY_180 * ad.tranZ(-2))

        side_wire_cavity_maker = side_wire_cavity.hole('side_wire_cavity-end') \
            .colour("indigo") \
            .at('face_corner', 'base', 1)
        
        maker.add_at(side_wire_cavity_maker, 
                     ('segment', len(self.sequence) - 2), 'r-side', 1, rh=0.5,
                     post=ad.ROTY_180 * ad.tranZ(-2))
        
        screw_hole = self.screw_hole_node()
        num_holes = 4
        offset = (lens_len - 20) / num_holes
        for i in range(num_holes):
            shape_maker = screw_hole.composite(('screw_hole', i)).at('top')
            maker.add_at(
                shape_maker, 
                ('segment', 4),
                'r-base1', 0, 
                post=ad.translate((10, 30 + i * offset, 4.5))
                )
        
        return maker
    
    
    
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
