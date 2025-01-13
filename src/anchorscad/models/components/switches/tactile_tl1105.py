'''
Created on 7 Jan 2022

@author: gianni
'''

import anchorscad as ad
import numpy as np

# Helper for convering a list of 2 or 3 floats to a numpy array.
LIST_2_FLOAT = ad.list_of(ad.strict_float, len_min_max=(2, 3), fill_to_min=0.0)
EPSILON=1.0e-3

def _vlen(v: np.ndarray):
    '''Vector length. Assumes v is a numpy array.'''
    return np.sqrt(np.sum(v**2))

def _normal_len(v):
    '''Normalise a vector and return the normalised vector and its length.'''
    v = np.array(LIST_2_FLOAT(v))
    vlen = _vlen(v)
    return v / vlen, vlen

@ad.shape
@ad.datatree
class TactileSwitchTL1105Lead(ad.CompositeShape):
    '''Lead for TL1105 tactile switch.'''
    # Numbers taken from datasheet (mostly).
    max_w: float=7.90
    end_w: float=6.5
    lx_bend1: float=0.7
    lx_bend2: float=1.8
    lx_tail: float=0.5
    lx_body: float=1.3
    thickness: float=0.30
    h: float=0.7
    metadata: object=ad.EMPTY_ATTRS.with_fn(6)
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, 'h')
    cage_node: ad.Node=ad.CageOfNode()
    cage_size: tuple=None
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False)
    EXAMPLE_ANCHORS=(ad.surface_args('body_edge', scale_anchor=0.2),
                     ad.surface_args('cage', 'face_centre', 5, scale_anchor=0.2),)

    def build(self) -> ad.Maker:
        bend_y = self.max_w - self.end_w - self.thickness / 2
        bend_x = self.lx_bend2 - self.lx_bend1
        norm_bend, vlen = _normal_len((-bend_x, bend_y))
        rot = ad.rotZSinCos(norm_bend[0], norm_bend[1])
        rotI = rot.I
        rotI2 = rotI * rotI
        rot2 = rot * rot
        norm_bend_back_x2 = (rot2[1, 0], rot2[0, 0])
        
        path = (ad.PathBuilder()
                .move((0, 0), direction=(1, 0))
                .stroke(self.lx_bend1, 180, name='b0')
                .arc_tangent_radius_sweep(
                    self.thickness, 
                    sweep_angle=ad.angle(sinr_cosr=norm_bend),
                    sweep_direction=False,
                    metadata=self.metadata,
                    name='bc1')
                .stroke(vlen, name='b1')
                .stroke(vlen, xform=rotI2, name='b2')
                .arc_tangent_radius_sweep(
                    self.thickness, 
                    sweep_angle=ad.angle(sinr_cosr=norm_bend),
                    sweep_direction=False,
                    metadata=self.metadata,
                    name='bc3')
                .stroke(self.lx_tail, name='b3')
                .stroke(self.thickness, xform=ad.ROTZ_270, name='end')
                .stroke(self.lx_tail, xform=ad.ROTZ_270, name='t3')
                .stroke(vlen, xform=rotI, name='t2')
                .arc_tangent_radius_sweep(
                    self.thickness, 
                    sweep_angle=ad.angle(sinr_cosr=norm_bend_back_x2),
                    sweep_direction=False,
                    metadata=self.metadata,
                    name='tc1')
                .stroke(vlen, name='t1')
                .stroke(self.lx_bend1 + self.lx_body, xform=rotI, name='t0')
                .stroke(self.thickness, xform=ad.ROTZ_270, name='top_end')
                .stroke(self.lx_body, xform=ad.ROTZ_270, name='bb')
                .build())
        shape = self.extrude_node(path)
        maker = shape.solid('terminal').at()
        
        extents = path.extents()
        cage_size = (extents[1][0] - extents[0][0], 
                     extents[1][1] - extents[0][1], 
                     self.h)
        self.cage_size = cage_size
        cage_shape = ad.Box(cage_size)
        maker.add_at(self.cage_node(cage_shape).at('face_edge', 2, 0, 1),
                     'top_end', 1, rh=1, post=ad.ROTX_180)
        return maker

    @ad.anchor('Body edge.')
    def body_edge(self, rh=0.5):
        return self.maker.at('b0', rh=rh) * ad.ROTZ_90
    
    @ad.anchor('Centre of hole for lead.')
    def lead_hole_pos(self, at_end=False):
        if at_end:
            tran = 0
            face = 5
        else:
            tran = -self.lx_body
            face=2
        return self.maker.at('cage', 'face_centre', face,
                             ) * ad.tranZ(tran) * ad.ROTZ_90
    

@ad.shape
@ad.datatree
class TactileSwitchTL1105(ad.CompositeShape):
    '''
    A TL1105 tactile switch model. 
    '''
    body_size: tuple=(6.2, 6.2, 3.6)
    shaft_r_base: float=3.5 / 2
    shaft_r_top: float=3.08 / 2
    shaft_h: float=6.3
    between_leads: float=3.5
    shaft_node: ad.Node=ad.ShapeNode(ad.Cone, prefix='shaft_')
    leada_node: ad.Node=ad.dtfield(
        init=True,
        default=ad.ShapeNode(TactileSwitchTL1105Lead, prefix='leada_'))
    leads_hide_cages: bool=False

    leadx_cage_node: ad.Node=ad.CageOfNode(prefix='leadx_cage_')
    fn: int=32
    
    EXAMPLE_SHAPE_ARGS=ad.args(leadx_cage_hide_cage=True,
                                 leada_hide_cage=True,
                                 leads_hide_cages=False)
    EXAMPLE_ANCHORS=tuple(ad.surface_args('lead_hole', i + 1, at_end=True,
                                       scale_anchor=0.3) for i in range(4))
    
    LEADS_COUNT=4
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.body_size).solid('body').at('centre')
        
        shaft = self.shaft_node()
        maker.add_at(shaft.solid('shaft').at('base'),
                     'face_centre', 4, post=ad.ROTX_180)
        
        lead_shape = self.leada_node()
        
        lead_pos_cage = ad.Box([self.between_leads, 1, 1])
        
        leads_mode = (ad.ModeShapeFrame.CAGE 
                      if self.leads_hide_cages 
                      else ad.ModeShapeFrame.SOLID)
        faces = (('face_edge', 0, 0), ('face_edge', 3, 2))
        for i, f in enumerate(faces):
            maker.add_at(self.leadx_cage_node(
                            lead_pos_cage, 
                            cage_name=('lead_pos_cage', i)).at('face_edge', 0, 0),
                         *f, post=ad.ROTX_90)
            for j in range(2):
                # Map the lead number to shown on the datasheet.
                # Leads 1&2 are connected, so are 3&4.
                # lead_no = (3, 1, 2, 4)[j + i * 2]
                lead_no = 1 + i + 2 * (i == j)
                maker.add_at(lead_shape.named_shape(
                                ('lead', lead_no), leads_mode)
                             .at('body_edge', rh=1 - j),
                             ('lead_pos_cage', i), 'face_edge', 0, 0, j, 
                             post=ad.ROTX_270)
        
        return maker
        

    @ad.anchor('The hole location for the specified lead number.')
    def lead_hole(self, lead_no, at_end=False):
        return self.maker.at(('lead', lead_no), 'lead_hole_pos', at_end=True)
    
    @ad.anchor('The hole location for the specified lead number.')
    def switch_top(self):
        return self.maker.at('face_centre', 4)
    
    @ad.anchor('The base of the switch.')
    def switch_base(self):
        return self.maker.at('face_centre', 1)


@ad.shape
@ad.datatree
class TactileSwitchTL59Lead(ad.CompositeShape):
    '''Lead for TL59 tactile switch.'''
    # Numbers taken from datasheet (mostly).
    size: tuple=(9.45 - 3.92, 0.30, 0.7)
    cage_size: tuple=None
    
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
     
    def build(self) -> ad.Maker:
        shape = ad.Box(self.size)
        maker = shape.solid('terminal').at()
        return maker

    @ad.anchor('Body edge.')
    def body_edge(self, rh=0.5):
        return self.maker.at('face_edge', 2, 0, rh=rh)
    
    @ad.anchor('Centre of hole for lead.')
    def lead_hole_pos(self, at_end=False):
        return self.maker.at('face_centre', 5 if at_end else 2)    


@ad.shape
@ad.datatree(frozen=True)
class TactileSwitchTL59(ad.CompositeShape):
    '''
    A TL59 tactile switch.
    '''
    body_size: tuple=(6.2, 6.2, 3.6)
    shaft_r_base: float=3.5 / 2
    shaft_r_top: float=3.08 / 2
    shaft_h: float=6.3
    between_leads: float=5.0
    between_lead_centres: float=5.0
    shaft_node: ad.Node=ad.ShapeNode(ad.Cone, prefix='shaft_')
    leada_node: ad.Node=ad.dtfield(
        init=True,
        default=ad.ShapeNode(TactileSwitchTL59Lead, prefix='leada_'))
    leads_hide_cages: bool=False

    leadx_cage_node: ad.Node=ad.CageOfNode(prefix='leadx_cage_')
    fn: int=32
    
    EXAMPLE_SHAPE_ARGS=ad.args(leadx_cage_hide_cage=True)
    EXAMPLE_ANCHORS=tuple(ad.surface_args('lead_hole', i + 1, at_end=True, 
                                       scale_anchor=0.3) for i in range(2))
    
    LEADS_COUNT=2
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.body_size).solid('body').at('centre')
        
        shaft = self.shaft_node()
        maker.add_at(shaft.solid('shaft').at('base'),
                     'face_centre', 4, post=ad.ROTX_180)
        
        lead_pos_cage = ad.Box([self.between_leads, 1, 1])
        
        lead_shape = self.leada_node()
        leads_mode = (ad.ModeShapeFrame.CAGE 
                      if self.leads_hide_cages 
                      else ad.ModeShapeFrame.SOLID)
        maker.add_at(self.leadx_cage_node(
                        lead_pos_cage, 
                        cage_name=('lead_pos_cage', 0)).at('face_centre', 0),
                     'face_centre', 1, post=ad.ROTX_180)

        for i in range(2):
            lead_no = 1 + i
            maker.add_at(lead_shape.named_shape(
                            ('lead', lead_no), leads_mode)
                         .at('lead_hole_pos'),
                         ('lead_pos_cage', 0), 'face_edge', 2 + 3 * i, 1 + 2 * i, 
                         post=ad.ROTX_90)
        return maker

    @ad.anchor('The hole location for the specified lead number.')
    def lead_hole(self, lead_no, at_end=False):
        return self.maker.at(('lead', lead_no), 'lead_hole_pos', at_end=at_end)
    
    @ad.anchor('The hole location for the specified lead number.')
    def switch_top(self):
        return self.maker.at('face_centre', 4) * ad.ROTZ_90
    
    @ad.anchor('The base of the switch.')
    def switch_base(self):
        return self.maker.at('face_centre', 1) * ad.ROTZ_90
    

@ad.shape
@ad.datatree(frozen=True)
class TactileSwitchOutline(ad.CompositeShape):
    '''
    Hole for a tactile switch. Using this model as a hole will provide an outline
    for leads and switch access from the base of the switch.
    '''
    
    leads_hide_cages: bool=True
    switch_shape: ad.Shape=TactileSwitchTL59()
    lead_hole_h: float=10
    lead_hole_r: float=1.4
    lead_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, 'h', 'r', prefix='lead_hole_')
    lead_hole_scale: ad.GMatrix=ad.scale((0.7, 1, 1))
    add_push_hole: bool=True
    push_hole_h: float=10
    push_hole_r: float=1.4
    push_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, 'h', 'r', prefix='push_hole_')

    fn: int=16
    
    EXAMPLE_SHAPE_ARGS=ad.args(switch_shape=TactileSwitchTL1105())
    EXAMPLE_ANCHORS=tuple(ad.surface_args('lead_hole', i + 1, at_end=True, 
                                       scale_anchor=0.3) for i in range(2))
    
    def build(self) -> ad.Maker:
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
                'switch_base', post=ad.ROTX_180 * ad.tranZ(EPSILON))
            
        return maker


MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
