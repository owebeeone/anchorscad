'''
Created on 27 Oct 2021

@author: gianni
'''

import anchorscad as ad
import anchorscad.models.basic.box_side_bevels as bsb

epsilon=0.001
epsilon2=2 * epsilon

@ad.shape
@ad.datatree
class Tnut(ad.CompositeShape):
    
    r_t: float=17.6 / 2
    h_t: float=1.2
    r_shaft: float=7.4 / 2
    h_shaft: float=8.5
    bevel_shaft: float=8.5 - 6.3
    h_shaft_extension: float=10
    wing_size: tuple=(3.5, 1.2, 6.5)
    wing_angle: float=70
    left_handed: bool=True
    fn: int=32
    fa: float=None
    fs: float=None
    cyliner_node: ad.Node=ad.ShapeNode(ad.Cylinder, {})
    cone_node: ad.Node=ad.ShapeNode(ad.Cone, {})
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    
    def build(self) -> ad.Maker:
        shaft_cage_shape = self.cyliner_node(
            h=self.h_shaft, r=self.r_shaft)
        
        maker = shaft_cage_shape.cage('cage').at('base')
        
        base_shape = self.cyliner_node(h=self.h_t, r=self.r_t)
        
        maker.add_at(base_shape.solid('flat').at('base'),
                     'base')
        bevel_shape = self.cone_node(h=self.bevel_shaft + epsilon2, 
                                r_base=self.r_shaft + self.bevel_shaft, 
                                r_top=self.r_shaft)
        maker.add_at(bevel_shape.solid('bevel').at('base'),
                     'flat', 'base', rh=1, h=-epsilon)
        
        h_shaft = self.h_shaft - self.bevel_shaft - self.h_t
        
        shaft_cage_shape = self.cyliner_node(
            h=h_shaft, r=self.r_shaft)
        
        maker.add_at(shaft_cage_shape.solid('shaft').at('base'),
                     'bevel', 'base', rh=1, h=-epsilon)
        
        shaft_extension = self.cyliner_node(
            h=h_shaft, r=self.r_shaft)
        
        maker.add_at(shaft_extension.solid('shaft_extension')
                     .colour((1, 0, 0))
                     .at('base'),
                     'shaft', 'base', rh=1, h=-epsilon)
        
        wing_shape = ad.Box(self.wing_size)
        angle_shift = (-self.wing_angle 
                       if self.left_handed
                       else self.wing_angle - 180)
        
        for i in range(4):
            maker.add_at(wing_shape.solid(('wing', i))
                         .colour((1, 0, 1))
                         .at('face_corner', 0, 0, 
                             pre=ad.rotZ(angle_shift) * ad.tranZ(-epsilon)),
                         'flat', 'surface', degrees=i * 360 / 4
                         )
        
        return maker
        

    @ad.anchor('An example anchor')
    def origin(self):
        return self.maker.at('centre')


@ad.shape
@ad.datatree
class TnutExample(ad.CompositeShape):
    offs: float=4
    fn: int=128
    fa: float=None
    fs: float=None
    tnut_node: ad.Node=ad.ShapeNode(Tnut, {})
    bsb_node: ad.Node=ad.ShapeNode(bsb.BoxSideBevels, {})
    
    def build(self) -> ad.Maker:
        tnut = self.tnut_node()
        
        sizexy = tnut.r_t * 2 + self.offs

        maker = self.bsb_node(
            (sizexy, sizexy, tnut.h_shaft), self.offs)\
                .solid('model').at('centre')
                
        maker.add_at(tnut.hole('tnut').at('base'),
                     'face_centre', 4,
                     post=ad.tranZ(epsilon))
        return maker

MAIN_DEFAULT=ad.ModuleDefault(write_files=True, write_path_files=True)

if __name__ == "__main__":
    ad.anchorscad_main(False)
    
    
