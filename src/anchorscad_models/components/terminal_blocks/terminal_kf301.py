'''
Created on 12 Jan 2022

@author: gianni
'''


import anchorscad as ad

EPSILON=0.001

@ad.shape
@ad.datatree
class TerminalKF301Terminal(ad.CompositeShape):
    '''Access hole cutout for a KF301 terminal block.
    This includes holes for the pin, terminal wire and screwdriver access.
    '''
    h: float=10
    w: float=7.6
    pin_pitch: float=5.08
    
    block_x_offs: float=1.
    pin_r: float=0.5
    pin_h: float=4.5
    pin_x: float=3.3
    term_size: tuple=((3.25 + 0.5 - 1.6) * 2 , 4.34, 5.16)
    
    term_hole_r: float=2.9 / 2
    term_hole_y: float=0.5
    term_hole_fn: int=32
    term_hole_node: ad.Node=ad.Node(ad.Cylinder, 
                                   {'r': 'term_hole_r', 'fn': 'term_hole_fn'})
    
    pin_fn: int=8
    pin_node: ad.Node=ad.Node(ad.Cylinder, 
                                   {'r': 'pin_r', 'fn': 'pin_fn'})
    
    screw_fn: int=32
    screw_r: float=3.35 / 2
    screw_h: float=10
    screw_node: ad.Node=ad.Node(ad.Cylinder, 
                                   {'r': 'screw_r', 
                                    'h': 'screw_h', 
                                    'fn': 'screw_fn'})
    screw_access_as_hole: bool=False
    
    block_access_size: tuple=(10, term_size[1] - 0.9, term_size[2] - 0.9)
    block_access_as_hole: bool=False
    
    pin_xyz_offs: tuple=(0, block_x_offs, -0.8)
    
    cage_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False)
    EXAMPLE_ANCHORS=(ad.surface_args('face_edge', 1, 0, scale_anchor=0.3),
                     ad.surface_args('pin', 'top', scale_anchor=0.3),)
    
    def build(self) -> ad.Maker:
        size = (self.w, self.pin_pitch, self.h)
        maker = self.cage_node(ad.Box(size)).at('face_edge', 1, 0, post=ad.ROTY_180)
        
        block_shape = ad.Box(self.term_size)
        
        maker.add_at(block_shape.solid('block').at('face_edge', 1, 3),
                     'face_edge', 1, 3, post=ad.translate(self.pin_xyz_offs))
        
        term_hole = self.term_hole_node(h=self.term_size[0] + 2 * EPSILON)
        
        maker.add_at(term_hole.hole('term_hole').at('surface'),
                     'block', 'face_edge', 1, 3, 
                     post=ad.translate([0, -EPSILON, -0.5]))
        
        pin_h = self.pin_h - self.pin_xyz_offs[2]
        pin_shape = self.pin_node(h=pin_h)
        
        maker.add_at(pin_shape.solid('pin').at('base', rh=1),
                     'block', 'face_centre', 1)
        
        screw_access_shape = self.screw_node()
        
        maker.add_at(screw_access_shape
                     .solid_hole('screw_access', self.screw_access_as_hole)
                     .at('base', rh=1),
                     'block', 'face_centre', 4)
        
        block_access_shape = ad.Box(self.block_access_size)
        maker.add_at(block_access_shape
                     .solid_hole('block_access', self.block_access_as_hole)
                     .at('face_centre', 2),
                     'block', 'face_centre', 2, post=ad.ROTY_180)
        
        return maker

@ad.shape
@ad.datatree
class TerminalKF301Body(ad.CompositeShape):
    '''
    Based on the specs for Handson Technologu KF301.
    '''
    h: float=10
    w: float=7.6
    pin_pitch: float=5.08
    
    trap_p0: float=6.5
    trap_p1: float=2.0
    trap_p2: float=1.0
    
    count: int=3
    cage_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=True)
    EXAMPLE_ANCHORS=(ad.surface_args('face_edge', 1, 0),)
    
    def build(self) -> ad.Maker:
        
        length = self.count * self.pin_pitch
        cage_shape = ad.Box((self.w, length, self.h))
        
        maker = self.cage_node(cage_shape).at('face_edge', 1, 0, post=ad.ROTY_180)
        
        trap_y = self.h - self.trap_p0
        path = (ad.PathBuilder()
                .move((0, 0), direction=(-1, 0))
                .stroke(self.w / 2, name='base_lhs')
                .stroke(self.trap_p0, angle=ad.angle(sinr_cosr=(-1, 0)), name='lower_lhs')
                .relative_line((self.trap_p1, trap_y), name='upper_lhs')
                .line((0, self.h), 'top_lhs')
                .line((self.w / 2 -self.trap_p2, self.h), 'top_rhs')
                .line((self.w / 2, self.trap_p0), 'upper_rhs')
                .line((self.w / 2, 0), 'lower_rhs')
                .line((0, 0), 'base_rhs')
                .build())
        
        shape = ad.LinearExtrude(path, length)
        maker.add_at(shape.solid('terminal').at('base_lhs', rh=1),
                     'face_edge', 1, 0, post=ad.ROTY_180 * ad.ROTZ_180)

        return maker

    @ad.anchor('An example anchor specifier.')
    def side(self, *args, **kwds):
        return self.maker.at('face_edge', *args, **kwds)
    

@ad.shape
@ad.datatree
class TerminalKF301(ad.CompositeShape):
    '''
    Based on the specs for Handson Technology KF301.
    '''
    count: int=2
    
    body_node: ad.Node=ad.ShapeNode(TerminalKF301Body)
    
    terminal: ad.Node=ad.ShapeNode(TerminalKF301Terminal)
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=True, 
                               block_access_as_hole=False,
                               screw_access_as_hole=False)
    EXAMPLE_ANCHORS=(ad.surface_args('face_edge', 1, 0),)
    
    def build(self) -> ad.Maker:
        maker = self.body_node().solid('body').at()
        
        terminal_shape = self.terminal()
        for i in range(self.count):
            maker.add_at(terminal_shape.composite(('terminal', i + 1))
                         .at('face_edge', 3, 0), 
                         'face_edge', 3, 0, post=ad.tranZ(-i * self.pin_pitch))
        return maker


MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
