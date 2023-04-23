'''
Created on 30 Sep 2021

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class SpoolHolder(ad.CompositeShape):
    '''
    A Gammill quilting machine spool holder taking a 6mm rod.
    Allows for bobbins to be placed on the spool holder.
    '''
    h: float=ad.dtfield(28.6, 'Height of holder')
    shaft_r: float=ad.dtfield(6.5 / 2, 'Radius of vertical shaft (bolt).')
    
    shaft_node_cage: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 'h', {'r': 'shaft_r'}),
        'Cage shape for main vertical shaft (for bolt)')
    shaft_cage_of_node: ad.Node=ad.Node(ad.cageof, prefix='shaft_cage_')
    shaft_hole_h: float=ad.dtfield(
        self_default=lambda s: s.h + 2 * s.epsilon,
        doc='Shaft hole overall height. Computed default h + 2 * epsilon.')
    shaft_hole_r: float=ad.dtfield(
        self_default=lambda s: s.shaft_r + s.shrink_r,
        doc='Shaft hole radius.  Computed default shaft_r + shrink_r')
    shaft_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='shaft_hole_'),
        'Shaft hole shape factory node.')
    
    rod_r: float=ad.dtfield(6.0 / 2, 'Spool holder rod radius.')
    rod_hole_base_r: float=ad.dtfield(5.9 / 2, 'Rod base radius. Should cause interference.')
    rod_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 'h', {'r': 'rod_r'}), 'Rod hole shape node.')
    
    shrink_r: float=ad.dtfield(
        0.15 / 2, 'Radius compensation size. Compensates for 3D printer overshoot.')
    
    holder_r: float=ad.dtfield(19 / 2, 'Holder overall radius.')
    holder_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 'h', {'r': 'holder_r'}), 'Main holder cylinder shape.')
    
    rod_sup_h: float=ad.dtfield(25, 'Rod support cone length.')
    rod_sup_r_top: float=ad.dtfield(12 / 2, 'Rod support cone outer radius.')
    rod_sup_r_base: float=ad.dtfield(19 / 2, 'Rod support cone inner radius.')
    rod_sup_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, prefix='rod_sup_'), 'Rod support cone shape.')
    
    rod_sup_hole_h: float=ad.dtfield(
        self_default=lambda s: s.rod_sup_h + 2 * s.epsilon,
        doc='Support rod hole.')
    rod_sup_hole_r_top: float=ad.dtfield(
        self_default=lambda s: s.rod_r + s.shrink_r,
        doc='Support rod top radius')
    rod_sup_hole_r_base: float=ad.dtfield(
        self_default=lambda s: s.rod_hole_base_r + s.shrink_r,
        doc='Support rod base radius')
    rod_sup_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, prefix='rod_sup_hole_'),
        doc='Rod support hole shape.')
    rod_angle: float=ad.dtfield(0.75, 'Rod up slant in degrees.')
    
    holder_cut: float=ad.dtfield(1.5, 'Holder cut size to allow for bed adhesion.')
    cut_box_size: tuple=ad.dtfield(
        self_default=lambda s: (
             s.holder_r * 2, s.holder_cut, s.h + 2 * s.epsilon),
        doc='Size of cut Box hole.')
    cut_box_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Box, prefix='cut_box_'), 'Box for cutting flat surface on shaft.')
    
    epsilon: float=ad.dtfield(
        0.001, 'Added to holes to eliminate floating point noise aliasing.')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    NOEXAMPLE_ANCHORS=(ad.surface_args('base'),)
    
    def build(self) -> ad.Maker:
        maker = self.shaft_cage_of_node(self.shaft_node_cage()).at('base')
            
        shaft_hole = self.shaft_hole_node().hole('shaft_hole').at('centre')    
        maker.add_at(shaft_hole, 'centre')
        
        holder = self.holder_node().solid('holder').at('centre')    
        maker.add_at(holder, 'centre')
        
        # Cut the rod support cone extending beyond the end of the holder.
        holder_cutter = self.holder_node(h=self.rod_sup_r_base / 2).hole(
            'holder_cutter').at('base') 
        maker. add_at(holder_cutter, 'base', h=-self.epsilon, rh=1)
        
        rod_support_shape = self.rod_sup_node().solid(
            'rod_support').colour([0, 1, 0, 1]).at('base')
        maker.add_at(rod_support_shape, 'base', rh=0.71, 
                     post=ad.rotX(90 - self.rod_angle))
        
        holder = self.rod_sup_hole_node().hole(
            'rod_hole').at('centre')    
        maker.add_at(holder, 'rod_support', 'centre')
        
        cut_box = self.cut_box_node().hole('cut_box').at('face_centre', 3)
        maker.add_at(cut_box, 'holder', 'surface', 0, 90, rh=0.5)
        
        return maker


@ad.shape
@ad.datatree
class SpoolHolderCap(ad.CompositeShape):
    '''
    End caps for spool holder.
    These should fit on the shaft with an interference fit hence the split
    hole on one side to allow for expansion.
    '''
    r: float= ad.dtfield(
        self_default=lambda s:s.shaft_r + s.shrink_r,
        doc='Radius of shaft hole. Computed default shaft_r + shrink_r.')
    h: float=ad.dtfield(11.3, 'Overall height of spool holder.')
    
    shaft_r: float=ad.dtfield(6.0 / 2, 'Nominal radius of shaft.')
    shaft_cage_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 'h', {'r': 'shaft_r'}),
        'Cage of shaft. Dims are nominal sizes (not compensated for shrinking)')
    
    shrink_r: float=ad.dtfield(0.15 / 2, 'Shaft radius shrink allowance.')
    
    washer_h: float=ad.dtfield(3, 'Height of washer component of holder.')
    washer_r: float=ad.dtfield(23.0 / 2, 'Radius of washer component of holder.')
    washer_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='washer_'),
        'Washer shape.')
    
    washer_hole_h: float=ad.dtfield(
        self_default=lambda s: s.washer_h + 2 * s.epsilon,
        doc='Height of washer hole. Computed as washer_h + 2 * epsilon.')
    washer_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 'r', {'h': 'washer_hole_h'}),
        'Hole for washer.')
    
    stem_top_rd: float=ad.dtfield(1.5, 'Size of outer stem wall.')
    stem_base_rd: float=ad.dtfield(2.5, 'Size of base of stem wall.')
    stem_h: float= ad.dtfield(
        self_default=lambda s:s.h - s.washer_h,
        doc='Stem height. Computed as h - washer_h.')
    stem_r_top: float=ad.dtfield(
        self_default=lambda s:s.stem_top_rd + s.shaft_r,
        doc='Stem outer radius. Computed as stem_top_rd + shaft_r')
    stem_r_base: float=ad.dtfield(
        self_default=lambda s:s.stem_base_rd + s.shaft_r,
        doc='Stem base radius. Computed as stem_base_rd + shaft_r')  
    stem_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, prefix='stem_'), 'Stem shape')
    
    top_hole_h: float= ad.dtfield(
        self_default=lambda s:s.stem_h + 2 * s.epsilon,
        doc='Stem hole. Computed as stem_h + 2 * epsilon.')
    top_r_delta: float=ad.dtfield(0.04 / 2, 'Shrink delta for top radius of stem hole.')
    top_hole_r_top: float=ad.dtfield(
        self_default=lambda s:s.r - s.top_r_delta,
        doc='Radius of hole at top of stem. Computed as r - top_r_delta.') 
    top_hole_r_base: float=ad.dtfield(
        self_default=lambda s:s.r,
        doc='Radius of hole at top of stem. Computed as r.') 
    top_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, prefix='top_hole_'),
        'Shaft hole for stem.')
    
    slicer_width: float=ad.dtfield(0.2, 'Width of split to allow for expansion.')
    slicer_size: tuple=ad.dtfield(
        self_default=lambda s: (
             s.slicer_width, 
             s.washer_r + s.epsilon, 
             s.h + 2 * s.epsilon),
        doc='Size of slicing hole.')
    slicer_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Box, prefix='slicer_'), 'Slicer shape.')
    
    epsilon: float=ad.dtfield(
        0.001, 
        'A small number used as a hole extender for eliminating aliasing from '
        'floating point noise.')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    NOEXAMPLE_ANCHORS=(ad.surface_args('base'),)
    
    def build(self) -> ad.Maker:
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
             
        maker.add_at(slicer, 'shaft_cage', 'base', rh=0.5, post=ad.ROTX_90)
        
        return maker


MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
