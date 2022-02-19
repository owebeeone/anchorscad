'''
Created on 7 Jan 2022

@author: gianni
'''

import ParametricSolid.core as core
import ParametricSolid.extrude as e
from ParametricSolid.datatree import datatree, Node
import ParametricSolid.linear as l
import numpy as np

LIST_2_FLOAT = l.list_of(l.strict_float, len_min_max=(2, 3), fill_to_min=0.0)
EPSILON=1.0e-3

def _vlen(v):
    return np.sqrt(np.sum(v**2))

def _normal_len(v):
    v = np.array(LIST_2_FLOAT(v))
    vlen = _vlen(v)
    return v / vlen, vlen

@core.shape('anchorscad.models.components.switches.tactile_tl1105_leg')
@datatree
class TactileSwitchTL1105Lead(core.CompositeShape):
    
    # Numbers taken from datasheet (mostly).
    max_w: float=7.90
    end_w: float=6.5
    lx_bend1: float=0.7
    lx_bend2: float=1.8
    lx_tail: float=0.5
    lx_body: float=1.3
    thickness: float=0.30
    h: float=0.7
    metadata: object=core.EMPTY_ATTRS.with_fn(6)
    extrude_node: Node=core.ShapeNode(e.LinearExtrude, 'h')
    cage_node: Node=core.CageOfNode()
    cage_size: tuple=None
    
    
    EXAMPLE_SHAPE_ARGS=core.args(as_cage=False)
    EXAMPLE_ANCHORS=(core.surface_args('body_edge', scale_anchor=0.2),
                     core.surface_args('cage', 'face_centre', 5, scale_anchor=0.2),)
     
    def __post_init__(self):
        
        bend_y = self.max_w - self.end_w - self.thickness / 2
        bend_x = self.lx_bend2 - self.lx_bend1
        norm_bend, vlen = _normal_len((-bend_x, bend_y))
        rot = l.rotZSinCos(norm_bend[0], norm_bend[1])
        rotI = rot.I
        rotI2 = rotI * rotI
        rot2 = rot * rot
        norm_bend_back_x2 = (rot2[1, 0], rot2[0, 0])
        
        path = (e.PathBuilder()
                .move((0, 0), direction=(1, 0))
                .stroke(-self.lx_bend1, name='b0')
                .arc_tangent_radius_sweep(
                    self.thickness, 
                    sweep_sinr_cosr=norm_bend,
                    sweep_direction=False,
                    metadata=self.metadata,
                    name='bc1')
                .stroke(vlen, name='b1')
                .stroke(vlen, xform=rotI2, name='b2')
                .arc_tangent_radius_sweep(
                    self.thickness, 
                    sweep_sinr_cosr=norm_bend,
                    sweep_direction=False,
                    metadata=self.metadata,
                    name='bc3')
                .stroke(self.lx_tail, name='b3')
                .stroke(self.thickness, xform=l.ROTZ_270, name='end')
                .stroke(self.lx_tail, xform=l.ROTZ_270, name='t3')
                .stroke(vlen, xform=rotI, name='t2')
                .arc_tangent_radius_sweep(
                    self.thickness, 
                    sweep_sinr_cosr=norm_bend_back_x2,
                    sweep_direction=False,
                    metadata=self.metadata,
                    name='tc1')
                .stroke(vlen, name='t1')
                .stroke(self.lx_bend1 + self.lx_body, xform=rotI, name='t0')
                .stroke(self.thickness, xform=l.ROTZ_270, name='top_end')
                .stroke(self.lx_body, xform=l.ROTZ_270, name='bb')
                .build())
        shape = self.extrude_node(path)
        maker = shape.solid('terminal').at()
        
        extents = path.extents()
        cage_size = (extents[1][0] - extents[0][0], 
                     extents[1][1] - extents[0][1], 
                     self.h)
        self.cage_size = cage_size
        cage_shape = core.Box(cage_size)
        maker.add_at(self.cage_node(cage_shape).at('face_edge', 2, 0, 1),
                     'top_end', 1, rh=1, post=l.ROTX_180)
        
        self.maker = maker 

    @core.anchor('Body edge.')
    def body_edge(self, rh=0.5):
        return self.maker.at('b0', rh=rh) * l.ROTZ_90
    
    @core.anchor('Centre of hole for lead.')
    def lead_hole_pos(self, at_end=False):
        if at_end:
            tran = 0
            face = 5
        else:
            tran = -self.lx_body
            face=2
        return self.maker.at('cage', 'face_centre', face,
                             ) * l.tranZ(tran) * l.ROTZ_90
    

@core.shape('anchorscad.models.components.switches.tactile_switch_tl1105')
@datatree
class TactileSwitchTL1105(core.CompositeShape):
    '''
    <description>
    '''
    body_size: tuple=(6, 6, 3.6)
    shaft_r_base: float=3.5 / 2
    shaft_r_top: float=3.08 / 2
    shaft_h: float=6.3
    between_leads: float=3.5
    shaft_node: Node=core.ShapeNode(core.Cone, prefix='shaft_')
    leada_node: Node=core.ShapeNode(TactileSwitchTL1105Lead, prefix='leada_')
    leads_as_cages: bool=False

    leadx_cage_node: Node=core.CageOfNode(prefix='leadx_cage_')
    fn: int=32
    
    EXAMPLE_SHAPE_ARGS=core.args(leadx_cage_as_cage=True,
                                 leada_as_cage=True,
                                 leads_as_cages=False)
    EXAMPLE_ANCHORS=tuple(core.surface_args('lead_hole', i + 1, at_end=True,
                                       scale_anchor=0.3) for i in range(4))
    
    LEADS_COUNT=4
    
    def __post_init__(self):
        maker = core.Box(self.body_size).solid('body').at('centre')
        
        shaft = self.shaft_node()
        maker.add_at(shaft.solid('shaft').at('base'),
                     'face_centre', 4, post=l.ROTX_180)
        
        lead_shape = self.leada_node()
        
        lead_pos_cage = core.Box([self.between_leads, 1, 1])
        
        leads_mode = (core.ModeShapeFrame.CAGE 
                      if self.leads_as_cages 
                      else core.ModeShapeFrame.SOLID)
        faces = (('face_edge', 0, 0), ('face_edge', 3, 2))
        for i, f in enumerate(faces):
            maker.add_at(self.leadx_cage_node(
                            lead_pos_cage, 
                            cage_name=('lead_pos_cage', i)).at('face_edge', 0, 0),
                         *f, post=l.ROTX_90)
            for j in range(2):
                # Map the lead number to shown on the datasheet.
                # Leads 1&2 are connected, so are 3&4.
                # lead_no = (3, 1, 2, 4)[j + i * 2]
                lead_no = 1 + i + 2 * (i == j)
                maker.add_at(lead_shape.named_shape(
                                ('lead', lead_no), leads_mode)
                             .at('body_edge', rh=1 - j),
                             ('lead_pos_cage', i), 'face_edge', 0, 0, j, 
                             post=l.ROTX_270)
        
        self.maker = maker
        

    @core.anchor('The hole location for the specified lead number.')
    def lead_hole(self, lead_no, at_end=False):
        return self.maker.at(('lead', lead_no), 'lead_hole_pos', at_end=True)
    
    @core.anchor('The hole location for the specified lead number.')
    def switch_top(self):
        return self.maker.at('face_centre', 4)
    
    @core.anchor('The base of the switch.')
    def switch_base(self):
        return self.maker.at('face_centre', 1)


@core.shape('anchorscad.models.components.switches.tactile_tl59_lead')
@datatree
class TactileSwitchTL59Lead(core.CompositeShape):
    
    # Numbers taken from datasheet (mostly).
    size: tuple=(9.45 - 3.92, 0.30, 0.7)
    cage_size: tuple=None
    
    
    EXAMPLE_SHAPE_ARGS=core.args()
    EXAMPLE_ANCHORS=()
     
    def __post_init__(self):
        shape = core.Box(self.size)
        maker = shape.solid('terminal').at()
        self.maker = maker 

    @core.anchor('Body edge.')
    def body_edge(self, rh=0.5):
        return self.maker.at('face_edge', 2, 0, rh=rh)
    
    @core.anchor('Centre of hole for lead.')
    def lead_hole_pos(self, at_end=False):
        return self.maker.at('face_centre', 5 if at_end else 2)    


@core.shape('anchorscad.models.components.switches.tactile_switch_tl59')
@datatree
class TactileSwitchTL59(core.CompositeShape):
    '''
    <description>
    '''
    body_size: tuple=(6, 6, 3.6)
    shaft_r_base: float=3.5 / 2
    shaft_r_top: float=3.08 / 2
    shaft_h: float=6.3
    between_leads: float=5.0
    between_lead_centres: float=5.0
    shaft_node: Node=core.ShapeNode(core.Cone, prefix='shaft_')
    leada_node: Node=core.ShapeNode(TactileSwitchTL59Lead, prefix='leada_')
    leads_as_cages: bool=False

    leadx_cage_node: Node=core.CageOfNode(prefix='leadx_cage_')
    fn: int=32
    
    EXAMPLE_SHAPE_ARGS=core.args(leadx_cage_as_cage=True)
    EXAMPLE_ANCHORS=tuple(core.surface_args('lead_hole', i + 1, at_end=True, 
                                       scale_anchor=0.3) for i in range(2))
    
    LEADS_COUNT=2
    
    def __post_init__(self):
        maker = core.Box(self.body_size).solid('body').at('centre')
        
        shaft = self.shaft_node()
        maker.add_at(shaft.solid('shaft').at('base'),
                     'face_centre', 4, post=l.ROTX_180)
        
        lead_pos_cage = core.Box([self.between_leads, 1, 1])
        
        lead_shape = self.leada_node()
        leads_mode = (core.ModeShapeFrame.CAGE 
                      if self.leads_as_cages 
                      else core.ModeShapeFrame.SOLID)
        maker.add_at(self.leadx_cage_node(
                        lead_pos_cage, 
                        cage_name=('lead_pos_cage', 0)).at('face_centre', 0),
                     'face_centre', 1, post=l.ROTX_180)

        for i in range(2):
            lead_no = 1 + i
            maker.add_at(lead_shape.named_shape(
                            ('lead', lead_no), leads_mode)
                         .at('lead_hole_pos'),
                         ('lead_pos_cage', 0), 'face_edge', 2 + 3 * i, 1 + 2 * i, 
                         post=l.ROTX_90)
        self.maker = maker

    @core.anchor('The hole location for the specified lead number.')
    def lead_hole(self, lead_no, at_end=False):
        return self.maker.at(('lead', lead_no), 'lead_hole_pos', at_end=at_end)
    
    @core.anchor('The hole location for the specified lead number.')
    def switch_top(self):
        return self.maker.at('face_centre', 4) * l.ROTZ_90
    
    @core.anchor('The base of the switch.')
    def switch_base(self):
        return self.maker.at('face_centre', 1) * l.ROTZ_90
    

@core.shape('anchorscad.models.components.switches.tactile_switch_outline')
@datatree
class TactileSwitchOutline(core.CompositeShape):
    '''
    <description>
    '''
    
    leads_as_cages: bool=True
    switch_shape: core.Shape=TactileSwitchTL59()
    lead_hole_h: float=10
    lead_hole_r: float=1.4
    lead_hole_node: Node=core.ShapeNode(core.Cylinder, 'h', 'r', prefix='lead_hole_')
    lead_hole_scale: l.GMatrix=l.scale((0.7, 1, 1))
    add_push_hole: bool=True
    push_hole_h: float=10
    push_hole_r: float=1.4
    push_hole_node: Node=core.ShapeNode(core.Cylinder, 'h', 'r', prefix='push_hole_')

    fn: int=16
    
    EXAMPLE_SHAPE_ARGS=core.args(switch_shape=TactileSwitchTL1105())
    EXAMPLE_ANCHORS=tuple(core.surface_args('lead_hole', i + 1, at_end=True, 
                                       scale_anchor=0.3) for i in range(2))
    
    def __post_init__(self):
        shape = self.switch_shape
        
        maker = shape.solid('switch').at()
        
        lead_hole_shape = self.lead_hole_node()
        
        scale_xform=self.lead_hole_scale
        for i in range(shape.LEADS_COUNT):
            maker.add_at(
                lead_hole_shape.solid(('lead_hole_shape', i)).at('top'),
                'lead_hole', i + 1, at_end=True, post=scale_xform)
            
        if self.add_push_hole:
            push_hole_shape = self.push_hole_node()
            maker.add_at(
                push_hole_shape.solid('push_hole_shape').at('top'), 
                'switch_base', post=l.ROTX_180 * l.tranZ(EPSILON))
            
        self.maker = maker


if __name__ == '__main__':
    core.anchorscad_main(False)
