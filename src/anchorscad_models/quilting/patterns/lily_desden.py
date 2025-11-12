'''
A quilt pattern of concentric 'eye' shapes.


'''

import anchorscad as ad
import numpy as np
import anchorscad_models.quilting.patterns.pat_utils as pu



@ad.datatree
class LilyDresden:
    
    pnts: int = 16
    outer_r: float = 325 / 2
    inner_r: float = 280 / 2
    
    def border(self, c: ad.PathBuilderPrimitives):
                
        v_outer = ad.GVector((self.outer_r, 0, 0))
        v_inner = ad.GVector((self.inner_r, 0, 0)) 
        step_ang = 360 / self.pnts
        half_step_ang = ad.angle(step_ang / 2)
        first = True
        for i in range(self.pnts):
            ang1 = ad.angle(i * step_ang)
            ang2 = ang1 + half_step_ang
            
            v_r_outer = ang2.rotZ * v_outer
            v_r_inner = ang1.rotZ * v_inner

            if first:
                c.move(v_r_inner.A2)
                first = False
            else:
                c.line(v_r_inner.A2, ('outer-inner', i))
            
            c.line(v_r_outer.A2, ('inner-outer', i))
        c.line(v_inner.A2, ('outer-inner', self.pnts))

    def build(self) -> ad.Path:
        
        builder = ad.PathBuilder(multi=True)
     
        with builder.construction() as c:
            self.border(c)
           
        step_ang = 360 / self.pnts
        half_step_ang = ad.angle(step_ang / 2)
        
        v_outer = ad.GVector((self.outer_r, 0, 0))
        v_inner = ad.GVector((self.inner_r, 0, 0)) 
                
        builder.move((0, 0))
        builder.line((self.outer_r, 0), 'A')
        builder.line((self.outer_r, self.outer_r), 'B')
        builder.line((0, self.outer_r), 'C')
        
        path = builder.build()
        
        return path
    
    
if __name__ == '__main__':
    pu.main(LilyDresden().build(), ['--csq'])