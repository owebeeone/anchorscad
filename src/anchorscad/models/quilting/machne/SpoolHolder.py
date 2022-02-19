'''
Created on 30 Sep 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.linear as l


@core.shape('anchorscad.models.quilting.machne.SpoolHolder')
@dataclass
class SpoolHolder(core.CompositeShape):
    '''
    <description>
    '''
    h: float=28.6
    shaft_r: float=6.5 / 2
    rod_r: float=6.0 / 2
    rod_hole_base_r: float=5.9 / 2
    shrink_r: float=0.15 / 2
    holder_r: float=19 / 2
    holder_cut: float=1.5
    top_r_delta: float=0.04 / 2
    rod_sup_len: float=25
    rod_sup_r_top: float=12 / 2
    rod_sup_r_base: float=19 / 2
    rod_angle: float=0.75  # Degrees
    epsilon: float=0.001
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(core.surface_args('base'),)
    
    def __post_init__(self):
        
        maker = core.Cylinder(h=self.h, r=self.shaft_r, fn=self.fn).cage(
            'shaft_cage').at('base')
            
        epsi2 = 2 * self.epsilon
        shaft_hole = core.Cylinder(h=self.h + epsi2, 
                                   r=self.shaft_r + self.shrink_r, 
                                   fn=self.fn).hole(
            'shaft_hole').at('centre')    
        maker.add_at(shaft_hole, 'centre')
        
        holder = core.Cylinder(h=self.h, 
                               r=self.holder_r, 
                               fn=self.fn).solid(
            'holder').at('centre')    
        maker.add_at(holder, 'centre')
        
        holder_cutter = core.Cylinder(h=self.rod_sup_r_base / 2, 
                               r=self.holder_r, 
                               fn=self.fn).hole(
            'holder_cutter').at('base') 
        maker. add_at(holder_cutter, 'base', h=-self.epsilon, rh=1)
        
        rod_suppoort_shape = core.Cone(
            h=self.rod_sup_len, 
            r_top=self.rod_sup_r_top, 
            r_base=self.rod_sup_r_base, 
            fn=self.fn).solid(
            'rod_support').colour([0, 1, 0, 1]).at('base')
        maker.add_at(rod_suppoort_shape, 'base', rh=0.71, 
                     post=l.rotX(90 - self.rod_angle))
        
           
        holder = core.Cone(h=self.rod_sup_len + epsi2,  
                               r_top=self.rod_r + self.shrink_r, 
                               r_base=self.rod_hole_base_r + self.shrink_r,
                               fn=self.fn).hole(
            'rod_hole').at('centre')    
        maker.add_at(holder, 'rod_support', 'centre')
        
        cut_box = core.Box([self.holder_r * 2, self.holder_cut, self.h + epsi2]
                           ).hole('cut_box').at('face_edge', 3, 0)
        
        maker.add_at(cut_box, 'holder', 'surface', 0, 90)
        
        self.maker = maker


@core.shape('anchorscad.models.quilting.machne.SpoolHolderCap')
@dataclass
class SpoolHolderCap(core.CompositeShape):
    '''
    <description>
    '''
    h: float=11.3
    shaft_r: float=6.0 / 2
    shrink_r: float=0.15 / 2
    top_r_delta: float=0.04 / 2
    washer_h: float=3
    washer_r: float=23.0 / 2
    stem_top_rd: float=1.5
    stem_base_rd: float=2.5
    slicer_width: float=0.2
    epsilon: float=0.001
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=core.args()
    NOEXAMPLE_ANCHORS=(core.surface_args('base'),)
    
    def __post_init__(self):
        
        maker = core.Cylinder(h=self.h, r=self.shaft_r, fn=self.fn).cage(
            'shaft_cage').colour([1, 1, 0, 0.5]).at('base')
            
        washer_shape = core.Cylinder(
            h=self.washer_h, r=self.washer_r, fn=self.fn).solid(
            'washer').colour([0, 1, 0, 0.5]).at('base')
        maker.add_at(washer_shape, 'base')
            
        r = self.shaft_r + self.shrink_r
        epsi2 = 2 * self.epsilon
        base_hole = core.Cylinder(h=self.washer_h + epsi2, r=r, fn=self.fn).hole(
            'base_hole').colour([0, 1, 1, 0.5]).at('centre')
        maker.add_at(base_hole, 'washer', 'centre')
            
        stem_h = self.h - self.washer_h
        stem_shape = core.Cone(
            h=stem_h,
            r_top=self.stem_top_rd + self.shaft_r, 
            r_base=self.stem_base_rd + self.shaft_r, 
            fn=self.fn).solid(
            'stem').colour([0, 0.5, 1, 0.5]).at('base')
        maker.add_at(stem_shape, 'washer', 'base', rh=1)
            
        rtop = r - self.top_r_delta
        top_hole = core.Cone(
            h=stem_h + epsi2, r_base=r, r_top=rtop, fn=self.fn).hole(
            'top_hole').colour([0, 1, 1, 0.5]).at('base')
        maker.add_at(top_hole, 'stem', 'base')

        epsi2 = 2 * self.epsilon
        slicer = core.Box(
            [self.slicer_width, 
             self.washer_r + self.epsilon, 
             self.h + epsi2]).hole('slicer').colour(
                 [0, 0, 1, 1]).at('face_centre', 0)
             
        maker.add_at(slicer, 'shaft_cage', 'base', rh=0.5, post=l.ROTX_90)
        
        self.maker = maker

if __name__ == '__main__':
    core.anchorscad_main(False)
