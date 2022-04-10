'''
Created on 30 Sep 2021

@author: gianni
'''

from anchorscad import Box, Cone, Cylinder, Maker, core, \
                       datatree, Node, ShapeNode, l, dtfield


@core.shape('anchorscad.models.quilting.machne.SpoolHolder')
@datatree
class SpoolHolder(core.CompositeShape):
    '''
    A Gammill quilting machine spool holder taking a 6mm rod.
    Allows for bobbins to be placed on the spool holder.
    '''
    h: float=28.6
    shaft_r: float=6.5 / 2
    shaft_node_cage: Node=ShapeNode(Cylinder, 'h', {'r': 'shaft_r'})
    shaft_node: Node=ShapeNode(Cylinder, 'h', {'r': 'shaft_r'})
    shaft_hole_h: float=dtfield(self_default=lambda s: s.h + 2 * s.epsilon)
    shaft_hole_r: float=dtfield(self_default=lambda s: s.shaft_r + s.shrink_r)
    shaft_hole_node: Node=ShapeNode(Cylinder, prefix='shaft_hole_')
    rod_r: float=6.0 / 2
    rod_hole_base_r: float=5.9 / 2
    rod_node: Node=ShapeNode(Cylinder, 'h', {'r': 'rod_r'})
    shrink_r: float=0.15 / 2
    holder_r: float=19 / 2
    holder_node: Node=ShapeNode(Cylinder, 'h', {'r': 'holder_r'})
    holder_cut: float=1.5
    top_r_delta: float=0.04 / 2
    rod_sup_h: float=25
    rod_sup_r_top: float=12 / 2
    rod_sup_r_base: float=19 / 2
    rod_sup_node: Node=ShapeNode(Cone, prefix='rod_sup_')
    rod_sup_hole_node: Node=ShapeNode(Cone, {})
    rod_angle: float=0.75  # Degrees
    
    
    epsilon: float=0.001
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(core.surface_args('base'),)
    
    def build(self) -> Maker:
        maker = self.shaft_node_cage().cage('shaft_cage').at('base')
            
        epsi2 = 2 * self.epsilon
        shaft_hole = self.shaft_hole_node().hole('shaft_hole').at('centre')    
        maker.add_at(shaft_hole, 'centre')
        
        holder = self.holder_node().solid('holder').at('centre')    
        maker.add_at(holder, 'centre')
        
        holder_cutter = self.holder_node(h=self.rod_sup_r_base / 2).hole(
            'holder_cutter').at('base') 
        maker. add_at(holder_cutter, 'base', h=-self.epsilon, rh=1)
        
        rod_suppoort_shape = self.rod_sup_node().solid(
            'rod_support').colour([0, 1, 0, 1]).at('base')
        maker.add_at(rod_suppoort_shape, 'base', rh=0.71, 
                     post=l.rotX(90 - self.rod_angle))
        
        holder = self.rod_sup_hole_node(
            h=self.rod_sup_h + epsi2,  
            r_top=self.rod_r + self.shrink_r, 
            r_base=self.rod_hole_base_r + self.shrink_r).hole(
            'rod_hole').at('centre')    
        maker.add_at(holder, 'rod_support', 'centre')
        
        cut_box = core.Box([self.holder_r * 2, self.holder_cut, self.h + epsi2]
                           ).hole('cut_box').at('face_edge', 3, 0)
        
        maker.add_at(cut_box, 'holder', 'surface', 0, 90)
        
        return maker


@core.shape('anchorscad.models.quilting.machne.SpoolHolderCap')
@datatree
class SpoolHolderCap(core.CompositeShape):
    '''
    End caps for spool holder.
    These should fit on the shaft with an interference fit hence the split
    hole on one side to allow for expansion.
    '''
    r: float= dtfield(
        self_default=lambda s:s.shaft_r + s.shrink_r,
        doc='Radius of shaft hole. Computed default shaft_r + shrink_r.')
    h: float=dtfield(11.3, 'Overall height of spool holder.')
    
    shaft_r: float=dtfield(6.0 / 2, 'Nominal radius of shaft.')
    shaft_cage_node: Node=dtfield(
        ShapeNode(Cylinder, 'h', {'r': 'shaft_r'}),
        'Cage of shaft. Dims are nominal sizes (not compensated for shrinking)')
    
    shrink_r: float=dtfield(0.15 / 2, 'Shaft radius shrink allowance.')
    
    washer_h: float=dtfield(3, 'Height of washer component of holder.')
    washer_r: float=dtfield(23.0 / 2, 'Radius of washer component of holder.')
    washer_node: Node=dtfield(
        ShapeNode(Cylinder, prefix='washer_'),
        'Washer shape.')
    
    washer_hole_h: float=dtfield(
        self_default=lambda s: s.washer_h + 2 * s.epsilon,
        doc='Height of washer hole. Computed as washer_h + 2 * epsilon.')
    washer_hole_node: Node=dtfield(
        ShapeNode(Cylinder, 'r', {'h': 'washer_hole_h'}),
        'Hole for washer.')
    
    stem_top_rd: float=dtfield(1.5, 'Size of outer stem wall.')
    stem_base_rd: float=dtfield(2.5, 'Size of base of stem wall.')
    stem_h: float= dtfield(
        self_default=lambda s:s.h - s.washer_h,
        doc='Stem height. Computed as h - washer_h.')
    stem_r_top: float=dtfield(
        self_default=lambda s:s.stem_top_rd + s.shaft_r,
        doc='Stem outer radius. Computed as stem_top_rd + shaft_r')
    stem_r_base: float=dtfield(
        self_default=lambda s:s.stem_base_rd + s.shaft_r,
        doc='Stem base radius. Computed as stem_base_rd + shaft_r')  
    stem_node: Node=dtfield(
        ShapeNode(Cone, prefix='stem_'), 'Stem shape')
    
    top_hole_h: float= dtfield(
        self_default=lambda s:s.stem_h + 2 * s.epsilon,
        doc='Stem hole. Computed as stem_h + 2 * epsilon.')
    top_r_delta: float=dtfield(0.04 / 2, 'Shrink delta for top radius of stem hole.')
    top_hole_r_top: float=dtfield(
        self_default=lambda s:s.r - s.top_r_delta,
        doc='Radius of hole at top of stem. Computed as r - top_r_delta.') 
    top_hole_r_base: float=dtfield(
        self_default=lambda s:s.r,
        doc='Radius of hole at top of stem. Computed as r.') 
    top_hole_node: Node=dtfield(
        ShapeNode(Cone, prefix='top_hole_'),
        'Shaft hole for stem.')
    
    slicer_width: float=dtfield(0.2, 'Width of split to allow for expansion.')
    slicer_size: tuple=dtfield(
        self_default=lambda s: (
             s.slicer_width, 
             s.washer_r + s.epsilon, 
             s.h + 2 * s.epsilon),
        doc='Size of slicing hole.')
    slicer_node: Node=dtfield(
        ShapeNode(Box, prefix='slicer_'), 'Slicer shape.')
    
    epsilon: float=dtfield(
        0.001, 
        'A small number used as a hole extender for aliasing reduction from '
        'floating point noise.')
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(core.surface_args('base'),)
    
    def build(self) -> Maker:
        '''Builds SpoolHolderCap shape.'''
        maker = self.shaft_cage_node().cage(
            'shaft_cage').colour([1, 1, 0, 0.5]).at('base')
            
        washer_shape = self.washer_node().solid(
            'washer').colour([0, 1, 0, 0.5]).at('base')
        maker.add_at(washer_shape, 'base')
            
        washer_hole = self.washer_hole_node().hole(
            'washer_hole').colour([0, 1, 1, 0.5]).at('centre')
        maker.add_at(washer_hole, 'washer', 'centre')
            
        stem_shape = self.stem_node().solid('stem').colour(
            [0, 0.5, 1, 0.5]).at('base')
        maker.add_at(stem_shape, 'washer', 'base', rh=1)
            
        top_hole = self.top_hole_node().hole(
            'top_hole').colour([0, 1, 1, 0.5]).at('base')
        maker.add_at(top_hole, 'stem', 'base')

        slicer = self.slicer_node().hole('slicer').colour(
                 [0, 0, 1, 1]).at('face_centre', 0)
             
        maker.add_at(slicer, 'shaft_cage', 'base', rh=0.5, post=l.ROTX_90)
        
        return maker


if __name__ == '__main__':
    core.anchorscad_main(False)
    help(SpoolHolderCap)
