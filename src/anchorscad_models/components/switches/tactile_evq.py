'''
Created on 31 Aug 2024

@author: gianni

Model for the EVQ series (EVQP0, EVQP1 and EVQ9P) of tactile switches from Panasonic.

These are long travel (1.3mm) with a 1.6N to 3.5N operating force in a 6x6x5mm package.
'''

from typing import Tuple
import anchorscad as ad
import numpy as np


@ad.shape
@ad.datatree(frozen=True)
class Plunger(ad.CompositeShape):

    tab_w: float = 1
    tab_d: float = 5.2
    plunger_h: float = 5 - 3.6
    plunger_r: float = 4.65 / 2
    
    tab_size: Tuple[float, ...] = ad.dtfield(
        self_default=lambda s: (s.tab_w, s.tab_d, s.plunger_h))
    tab_node: ad.Node = ad.dtfield(ad.ShapeNode(ad.Box, prefix='tab_'))
    
    plunger_node: ad.Node = ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='plunger_', expose_all=True))
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)
    
    def build(self) -> ad.Maker:
        plunger_shape = self.plunger_node()
        maker = plunger_shape.solid('plunger').at('centre')
        tab_maker = self.tab_node().solid('tab').at('centre')
        maker.add(tab_maker)
        return maker
    

@ad.shape
@ad.datatree(frozen=True)
class PostOutline(ad.CompositeShape):
    
    w: float = 6
    block2_w: float = 5.7
    h: float = 3.55 - 2.2
    s1: float = 3
    s2: float = 2
    
    block1_size: Tuple[float, ...] = ad.dtfield(
        self_default=lambda s: (s.w, s.s1, s.h))
    block1_node: ad.Node = ad.dtfield(ad.ShapeNode(ad.Box, prefix='block1_'))
    
    block2_size: Tuple[float, ...] = ad.dtfield(
        self_default=lambda s: (s.s2, s.block2_w / 2, s.h))
    block2_node: ad.Node = ad.dtfield(ad.ShapeNode(ad.Box, prefix='block2_'))
    
    post_cyl_r: float = ad.dtfield(5.2 / 2)
    post_cyl_node: ad.Node = ad.dtfield(
        ad.ShapeNode(ad.Cylinder, {'h': 'h'}, prefix='post_cyl_', expose_all=True))
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)
    
    def build(self) -> ad.Maker:
        cyl_shape = self.post_cyl_node()
        maker = cyl_shape.solid('master').at('centre')
        block1_maker = self.block1_node().solid('block1').at('centre')
        maker.add(block1_maker)
        b2offs = self.s2 / 2 - 0.5 - (self.post_cyl_r - 4.65 / 2)
        block2_maker_0 = self.block2_node().solid(('block2', 0)).at(
            'face_centre', 'front', post=ad.ROTX_90 * ad.tranX(b2offs))
        block2_maker_1 = self.block2_node().solid(('block2', 1)).at(
            'face_centre', 'front', post=ad.ROTX_180 * ad.ROTX_90 * ad.tranX(-b2offs))
        maker.add(block2_maker_0)
        maker.add_at(block2_maker_1)
        return maker
    
    _EDGE_ANCHOR_MAPPING = (
            ('block1', 'right', 2),
            (('block2', 0), 'back', 2),
            ('block1', 'left', 2),
            (('block2', 1), 'back', 0),)
    
    @ad.anchor('edge of post')
    def edge(self, index:int, rh: float=0.5, t: float=0.0) -> ad.GMatrix:
        '''An anchor for the edge of the square outer sections of thepost.'''
        block_name, face, edge_num = self._EDGE_ANCHOR_MAPPING[index]
        
        h = self.h * rh

        return self.maker.at(block_name, 'face_edge', face, edge_num, t) * ad.tranY(h)
        
    @ad.anchor('edge of post')
    def corner(self, index:int, rh: float=0., t: float=0.0) -> ad.GMatrix:
        '''An anchor for the corner of the square outer sections of the post.'''
        return self.edge(index, rh=rh, t=t)
    

@ad.datatree
class PostAnchorSequenceContext:
    index: int = 0
    t: float = 0
    count: int = 0
    offs: float = 0.5
    
    def next(self) -> Tuple[int, float, int]:
        c = self.count
        self.count += 1
        if self.t == 0:
            self.t = 1
            return self.index, 0.0, -self.offs, c 
        self.t = 0
        self.index += 1
        return self.index - 1, 1.0, self.offs, c 
    
    def is_last(self) -> bool:
        return self.index == 4
    
@ad.datatree(frozen=True)
class CentrePlateOutline:
    '''Outline of the centre plate of the EVQ series of tactile switches.'''
    post_outline: PostOutline = PostOutline()
    
    def pos(self, index, xoffs, t=0) -> np.array:
        return (self.post_outline.at('corner', index, t=t) * ad.tranX(xoffs)).get_translation().A2
    
    def corner_sequence(self, seqence: PostAnchorSequenceContext) -> np.array:
        while not seqence.is_last():
            index, t, offs, c = seqence.next()
            yield self.pos(index, xoffs=offs, t=t), c
    
    def build(self) -> ad.Path:
        ctxt = self.corner_sequence(PostAnchorSequenceContext())
        builder = ad.PathBuilder()
        
        start = next(ctxt)
        
        # Just an approximation of the shape for now. The segments between the corners
        # are not correct, they should be arcs and offsets applied.
        builder.move(start[0])
        for p, c in ctxt:
            builder.line(p, ('corner', c))
        
        builder.line(start[0], ('corner', 0)) # Close the path
        
        return builder.build()
        

@ad.shape
@ad.datatree(frozen=True)
class CentrePlate(ad.CompositeShape):
    '''Assembly of the Panasonic EVQ tavtile switch model.'''
    
    outline_node: ad.Node = ad.ShapeNode(CentrePlateOutline)
    centre_plate_path: ad.Path = ad.dtfield(self_default=lambda s: s.outline_node().build())
    
    centre_plate_h: float = 2.22 - 1.54
    
    linear_extrude_node: ad.Node = ad.ShapeNode(ad.LinearExtrude, prefix='centre_plate_')
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)
    EXAMPLE_ANCHORS = (
        ad.surface_args('top_centre', scale_anchor=0.1),
        ad.surface_args('base_centre', scale_anchor=0.1),)

    def build(self) -> ad.Maker:
    
        maker = self.linear_extrude_node().solid('centre_plate').at(('corner', 1))
        
        return maker
    
    @ad.anchor('centre of base of centre plate')
    def base_centre(self) -> ad.GMatrix:
        return ad.translate(
            (self.maker.at(('corner', 1), rh=0).get_translation()
            + self.maker.at(('corner', 5), rh=0).get_translation()) / 2) * ad.ROTX_90
        
    @ad.anchor('centre of top of centre plate')
    def top_centre(self) -> ad.GMatrix:
        return ad.translate(
            (self.maker.at(('corner', 1), rh=1).get_translation()
            + self.maker.at(('corner', 5), rh=1).get_translation()) / 2) * ad.ROTX_270
        
    
@ad.shape
@ad.datatree(frozen=True)
class EvqTerminal(ad.CompositeShape):
    '''Assembly of the Panasonic EVQ tactile switch terminal.
    
    Four of these terminals are used in the EVQ series of tactile switches, they
    are mounted on the base plate and are used to solder the switch to the PCB.'''
    
    terminal_w: float = 0.75
    terminal_h: float = 1.15
    terminal_d: float = 1.6
    
    terminal_ref_d: float = 0.5
    
    terminal_size: Tuple[float, ...] = ad.dtfield(
        self_default=lambda s: (s.terminal_w, s.terminal_d, s.terminal_h))
    terminal_node: ad.Node = ad.dtfield(ad.ShapeNode(ad.Box, prefix='terminal_'))
    
    EXAMPLE_SHAPE_ARGS = ad.args()
    EXAMPLE_ANCHORS = (
        ad.surface_args('reference', scale_anchor=0.1),)
    
    def build(self) -> ad.Maker:
        maker = self.terminal_node().solid('terminal').colour('silver').at('centre')
        return maker
    
    @ad.anchor('centre of top of centre plate')
    def reference(self) -> ad.GMatrix:
        return self.maker.at('face_edge', 'base', 0) * ad.tranY(self.terminal_ref_d)

    
@ad.shape
@ad.datatree(frozen=True)
class TactileEvq(ad.CompositeShape):
    '''Assembly of the Panasonic EVQ tactile switch model.'''
    
    post_node: ad.Node = ad.ShapeNode(PostOutline)
    # post_outline is shared between the post and the centre plate.
    post_outline: PostOutline = ad.dtfield(self_default=lambda s: s.post_node())
    
    plunger: ad.Node = ad.ShapeNode(Plunger)
    centre_plate: ad.Node = ad.ShapeNode(CentrePlate) 
    
    base_plate_h: float = 1.54
    base_plate_size: Tuple[float, ...] = ad.dtfield(
        self_default=lambda s: (s.w, s.w, s.base_plate_h))
    base_plate_node: ad.Node = ad.ShapeNode(ad.Box, prefix='base_plate_')
    
    terminal_sep: float = 4.5 / 2
    terminal_node: ad.Node = ad.ShapeNode(EvqTerminal)
    
    epsilon: float = 0.01
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)
    
    EXAMPLE_ANCHORS = (
        ad.surface_args('corner', 0, rh=1, scale_anchor=0.1),
        ad.surface_args('corner', 0, t=1, scale_anchor=0.1),
        ad.surface_args('edge', 1, t=0, scale_anchor=0.1),
        ad.surface_args('edge', 1, t=1, scale_anchor=0.1),
        ad.surface_args('edge', 2, t=0, scale_anchor=0.1),
        ad.surface_args('edge', 2, t=1, scale_anchor=0.1),
        ad.surface_args('edge', 3, t=0, scale_anchor=0.1),
        ad.surface_args('edge', 3, t=1, scale_anchor=0.1),
        ad.surface_args('base_plate', 'face_edge', 'base', 0, scale_anchor=0.1),
                       )
    
    def build(self) -> ad.Maker:
        
        maker = self.post_outline.solid('post').at('base', post=ad.ROTX_180)
        plunger_maker = self.plunger().solid('plunger').at('base')
        maker.add_at(plunger_maker, 'base', rh=1, post=ad.tranZ(-self.epsilon))
        
        centre_plate_maker = self.centre_plate().solid('centre_plate').at('base_centre', post=ad.ROTZ_90)
        maker.add_at(centre_plate_maker, 'base', post=ad.ROTX_180 * ad.tranZ(self.epsilon))
        
        base_plate_maker = self.base_plate_node().solid('base_plate').at('face_centre', 'base', rh=1)
        maker.add_at(base_plate_maker, 'centre_plate', 'top_centre', post=ad.tranZ(-self.epsilon))
        
        i = 0
        for side in (0, 2):
            for offset in (-1, 1):
                maker.add_at(
                    self.terminal_node().solid(('terminal', i)).at('reference'), 
                    'base_plate', 'face_edge', 'base', side, post=ad.tranX(offset * self.terminal_sep))
                i += 1
        
        return maker


@ad.shape
@ad.datatree(frozen=True)
class TactileEvqHole(ad.CompositeShape):
    '''A hole to hold an EVQ button.'''

    evq_node: ad.Node = ad.ShapeNode(TactileEvq)
    
    terminal_hole_r: float = 1.5
    terminal_hole_h: float = 6
    terminal_hole_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='terminal_hole_')
    
    xy_scale: float = 1 - 0.4 / 6
    
    scale: ad.GMatrix = ad.dtfield(
        self_default=lambda s: ad.scale((s.xy_scale, s.xy_scale, 1)))
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)
    EXAMPLE_ANCHORS = (ad.surface_args('top'),)
    
    def build(self) -> ad.Maker:
        evq_shape = self.evq_node()
        maker = evq_shape.solid('evq').at('base', post=ad.ROTX_180)
        
        hole_shape = self.terminal_hole_node()
        
        for i in range(4):
            maker.add_at(hole_shape.solid(('terminal_hole', i)).at('top'), 
                         ('terminal', i), 'face_centre', 'top')
        return maker


@ad.shape
@ad.datatree(frozen=True)
class TactileEvqHoleTest(ad.CompositeShape):
    '''A test hole to hold an EVQ button.'''    
    
    evq_hole_node: ad.Node = ad.ShapeNode(TactileEvqHole)
    
    test_plate_size: Tuple[float, ...] = ad.dtfield((15, 15, 2.5))
    test_plate_node: ad.Node = ad.ShapeNode(ad.Box, prefix='test_plate_')
    
    EXAMPLE_SHAPE_ARGS = ad.args(fn=64)
    
    def build(self) -> ad.Maker:
        
        maker = self.test_plate_node().solid('test_plate').at('face_centre', 'base', post=ad.ROTX_180)
        
        # Scaled to compensate for the 3D printer's shrinkage.
        evq_hole = self.evq_hole_node()
        maker.add_at(evq_hole.hole('evq_hole')
                     .at('base', post=evq_hole.scale), 'centre')
        
        return maker

    
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
