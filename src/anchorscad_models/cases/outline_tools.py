'''
Created on 13 Nov 2021

Tools for building outlines and access holes.

@author: Gianni Mariani
'''

from dataclasses import dataclass

from anchorscad import datatree, tranZ, ROTX_180, \
                        ROTY_180, translate, GVector
import anchorscad as ad
import anchorscad_models.basic.connector.hdmi.hdmi_outline as hdmi
from anchorscad_models.screws.holes import SelfTapHole
import anchorscad_models.basic.box_side_bevels as bbox


Z_DELTA=tranZ(-0.01)

def box_expander(expansion_size=None, actual_size=None, post=None):
    '''
    '''
    def expander(maker, name, anchor, box):
        if actual_size:
            expanded_size = GVector(actual_size)
        else:
            expanded_size = GVector(expansion_size) + box.size
        new_shape = ad.Box(expanded_size.A3)
        post_xform = Z_DELTA * ROTX_180
        if post:
            post_xform = post *  post_xform
        maker.add_at(new_shape.solid((name, 'outer')).at(*anchor[0], **anchor[1]),
                     name, *anchor[0], **anchor[1], post=post_xform)
    return expander


def cyl_expander(expansion_r, post=None):
    def expander(maker, name, anchor, cyl):
        expanded_r = expansion_r + cyl.r_base
        params = ad.non_defaults_dict(cyl, include=('fn', 'fa', 'fs'))
        new_shape = ad.Cylinder(h=cyl.h, r=expanded_r, **params)
        post_xform = Z_DELTA * ROTX_180
        if post:
            post_xform = post *  post_xform
        maker.add_at(new_shape.solid((name, 'outer')).at(*anchor[0], **anchor[1]),
                     name, *anchor[0], **anchor[1], post=post_xform)
    return expander

def no_op(*args):
    pass

@dataclass
class ShapeFactory:
    clazz: type
    shape_args: tuple
    offset: tuple
    anchor1: tuple
    anchor2: tuple
    expander: tuple
    
    def create(self, extra_params: dict):
        params = (dict(((k, v) 
                        for k, v in extra_params.items() 
                        if hasattr(self.clazz, k))))
        
        params.update(self.shape_args[1])
        return self.clazz(*self.shape_args[0], **params)
    
    
SIDE_ANCHOR=ad.args('face_corner', 4, 0)
FRONT_ANCHOR=ad.args('face_corner', 4, 1)
BOX_ANCHOR=ad.args('face_edge', 1, 0)
OBOX_ANCHOR=ad.args('face_centre', 3)
IBOX_ANCHOR=ad.args('face_centre', 4)
CYL_ANCHOR=ad.args('surface', 0, -90)
OCYL_ANCHOR=ad.args('base')
        
ETHERNET = ShapeFactory(
    ad.Box, ad.args([16.2, 21.25, 13.7]), 
    [0, 3.0, 0], 
    BOX_ANCHOR, 
    OBOX_ANCHOR, 
    box_expander([0.3] * 3))

POWER_SW = ShapeFactory(
    ad.Cylinder, ad.args(r=2, h=4), 
    [0, 2.7, 1], 
    CYL_ANCHOR, 
    OCYL_ANCHOR, 
    cyl_expander(1))

USBA=ShapeFactory(
    ad.Box, ad.args([15,  17.5, 16.4]), 
    [0, 3.0, 0], 
    BOX_ANCHOR,
    OBOX_ANCHOR, 
    box_expander([0.3] * 3))

MICRO_HDMI=ShapeFactory(
    ad.Box, ad.args([7.1,  8, 3.6]), 
    [0, 1.8, -0.5], 
    BOX_ANCHOR, 
    OBOX_ANCHOR, 
    box_expander([5, 0, 4.5]))

HDMI_A=ShapeFactory(
    hdmi.HdmiOutline, ad.args(), 
    [0, 1.8, 0.2], 
    BOX_ANCHOR, 
    OBOX_ANCHOR, 
    box_expander(actual_size=[21, 10, 10.6]))

USBC=ShapeFactory(
    ad.Box, ad.args([9,  7.5, 3.3]), 
    [0, 1.8, -(4.14 - 2.83 - 1.44)], 
    BOX_ANCHOR, 
    OBOX_ANCHOR, 
    box_expander([5, 0, 4]))

USBMICRO=ShapeFactory(
    ad.Box, ad.args([8.0, 5.6, 3]), 
    [0, 1.8, 0], 
    BOX_ANCHOR, 
    OBOX_ANCHOR, 
    box_expander([5, 0, 4]))

AUDIO=ShapeFactory(
    ad.Cylinder, ad.args(h=15, r=3), 
    [0, 2.7, 0], 
    CYL_ANCHOR, 
    OCYL_ANCHOR, 
    cyl_expander(2))

MICRO_SD=ShapeFactory(
    ad.Box, ad.args([12,  11.35, 1.4]), 
    [0, -3, 0], 
    BOX_ANCHOR, 
    OBOX_ANCHOR, 
    box_expander([1, 1, 6], post=translate([0, -3, 0])))

CPU_PACKAGE=ShapeFactory(
    ad.Box, 
    ad.args([15,  15, 2.4]),
    [0, 0, 0], 
    ad.args('face_edge', 1, 0, 1), 
    IBOX_ANCHOR, 
    no_op)

CPU_PACKAGE_PI5=ShapeFactory(
    ad.Box, 
    ad.args([17,  17, 2.4]),
    [0, 0, 0], 
    ad.args('face_edge', 1, 0, 1), 
    IBOX_ANCHOR, 
    no_op)

HEADER_100=ShapeFactory(
    ad.Box, 
    ad.args([51,  5.1, 8.7]), [0, -1.75, 0], 
    ad.args('face_edge', 1, 0, 1), 
    IBOX_ANCHOR, 
    no_op)

HEADER_100_CENTRE=ShapeFactory(
    ad.Box, 
    ad.args([51,  5.1, 8.7]), [0, -1.75, 0], 
    ad.args('face_edge', 1, 0), 
    IBOX_ANCHOR, 
    no_op)

DELTA=0.02

@dataclass
class OutlineLayout:
    main_anchor: ad.AnchorArgs
    accessor_specs: tuple
    
@dataclass
class OutlineHoleSpec:
    r: float
    r_support: float
    base_anchor_args: ad.AnchorArgs
    
    
    def mount_hole(self, depth, params):
        return ad.Cylinder(h=depth * 2 * DELTA, r=self.r, **params)
    
    def screw_hole(self, tap_len, dia, thru_len, params):
        return SelfTapHole(
            thru_len=thru_len, 
            tap_len=tap_len,
            outer_dia=self.r_support * 2,
            dia=dia,
            **params)

@dataclass
class OutlineHolePos:
    spec: OutlineHoleSpec
    p: tuple
    

@datatree
class BaseOutline(ad.CompositeShape):
    '''
    A generic board outline.
    '''
    board_size: tuple=ad.dtfield(None, 'The board size in mm')
    bevel_radius: float=ad.dtfield(None, 'The bevel radius in mm')
    box_node: ad.Node=ad.dtfield(
        ad.ShapeNode(bbox.BoxSideBevels,
                       'bevel_radius',
                       {'size': 'board_size'}),
        doc='The board shape node',
        init=False)
    
    HOLE_POSITIONS=()
    
    ALL_ACCESS_ITEMS=()
    
    @classmethod
    def make_access_anchors(cls, all_items):
        anchor_specs = []
        for outline_layout in all_items:
            for name, model, xform in outline_layout.accessor_specs:
                o_anchor = model.anchor2
                anchor_specs.append(
                    ad.surface_args(name, *o_anchor[0], **o_anchor[1]))
        return tuple(anchor_specs)
    
    @classmethod
    def mount_hole_anchor_spec(cls, i):
        return ad.surface_args(('mount_hole', i), 'top')
    
    @classmethod
    def get_default_example_params(cls):
        return ad.ExampleParams(
                cls.EXAMPLE_SHAPE_ARGS,
                tuple(
                    cls.mount_hole_anchor_spec(i)
                      for i in range(len(cls.HOLE_POSITIONS))
                ) + cls.make_access_anchors(cls.ALL_ACCESS_ITEMS))

    def build(self) -> ad.Maker:
        board_shape = self.box_node()
        maker = board_shape.solid('board').at('face_centre', 'top')

        params = ad.non_defaults_dict_include(self, include=('fn', 'fa', 'fs'))

        for i, t in enumerate(self.HOLE_POSITIONS):
            mount_hole = t.spec.mount_hole(self.board_size[2], params)
            anchor_args = t.spec.base_anchor_args.args
            
            maker.add_at(
                mount_hole.hole(self.mount_hole_anchor_spec(i).name).at('base'), 
                *anchor_args[0], **anchor_args[1], 
                post=translate(t.p + (DELTA,)))

        for outline_layout in self.ALL_ACCESS_ITEMS:
            for name, model, xform in outline_layout.accessor_specs:
                shape = model.create(params)
                maker.add_at(
                    shape.solid(name).colour([0, 1, 0.5]).at(
                        args=model.anchor1, post=translate(model.offset)),
                    args=outline_layout.main_anchor.args, post=xform * ROTY_180
                    )
                # Add the outer hole.
                model.expander(maker, name, model.anchor2, shape)

        return maker

