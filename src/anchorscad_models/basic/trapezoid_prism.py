'''
Created on 27 Dec 2023

@author: gianni
'''

import anchorscad as ad
import numpy as np


ad.datatree
class TrapezoidPrismPath:
    base_w: float=71
    side_l: float=105
    top_w: float=61
    
    def build(self) -> ad.Path:
        
        tri_base = (self.base_w - self.top_w) / 2
        
        sinr = -tri_base / self.side_l
        cosr = np.sqrt(1 - sinr**2)
        
        builder = (ad.PathBuilder()
                   .move((0, 0))
                   .line((self.base_w, 0), 'path_base')
                   .stroke(self.side_l, angle=ad.angle(sinr_cosr=(cosr, sinr)), name='right')
                   
                   .stroke(self.top_w, angle=ad.angle(sinr_cosr=(cosr, -sinr)), name='path_top')
                   .line((0, 0), 'left'))
        
        return builder.build()


@ad.shape
@ad.datatree
class TrapezoidPrism(ad.CompositeShape):
    '''
    A trapezoid prism.
    '''
    path_node: ad.Node=ad.dtfield(ad.Node(TrapezoidPrismPath))
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_node().build())
    
    h: float=ad.dtfield(20, 'Depth of prism')
    
    extrude_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.LinearExtrude))
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base'),)
    
    def build(self) -> ad.Maker:
        
        maker = self.extrude_node().solid('prism').at('path_base')
        
        return maker
    
    @ad.anchor('centre of the trapzoid')
    def centre(self, h=0, rh=0.5):
        h = h + self.h * rh
        extents = self.path.extents()
        y = (extents[0][1] + extents[1][1]) / 2
        return self.maker.at('path_base', 0.5) * ad.translate((0, h, -y)) * ad.ROTX_270
    
    @ad.anchor('top of the trapzoid')
    def top(self, h=0, rh=0):
        return self.centre(h=-h, rh=1 - rh)
    
    @ad.anchor('base of the trapzoid')
    def base(self, h=0, rh=0):
        return self.centre(h=h, rh=rh) * ad.ROTX_180
        
        
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
