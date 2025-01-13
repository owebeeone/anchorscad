'''
Created on 4-Jun-2023

@author: gianni
'''

import anchorscad as ad
import anchorscad_models.screws.tnut as tnut


@ad.shape
@ad.datatree
class TnutWasherInner(ad.CompositeShape):
    '''
    Using a tnut as low provide nut and washer, this shape will
    provide an interference between the item being fastened and
    the tnut base. When printed in TPU or similar softer material
    it can provide a shock absorbing effect and also reduce the 
    possibility of fracturing the material being fastened.
    '''
    
    outer_size: tuple=(34.3, 34.3, 3)
    outer_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='outer_'))
    
    base_size: tuple=ad.dtfield(self_default=lambda s: 
            (28.3 - 1.05, 25, s.wing_size[2]))
    base_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='base_'))
    
    wall_h: float=29.7 - 24 # The wall space between the base and the outer.
    base_overlap: float=0.5
    
    outer_h: float=ad.dtfield(self_default=lambda s: s.wall_h + s.base_overlap)
    outer_r: float=5
    outer_cyl_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='outer_'))
    
    d_hole: float=10
    
    tnut_node: ad.Node=ad.dtfield(ad.ShapeNode(tnut.Tnut))
    
    epsilon: float=0.01
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        
        base_shape = self.base_node()
        maker = base_shape.solid('base').at('face_centre', 'base')
        
        
        shape = self.tnut_node()
        maker.add_at(shape.hole('tnut_outline').at('base'),
                        'base', 'face_centre', 'base', post=ad.tranZ(self.epsilon))
        
        cyl_overlap_shape = self.outer_cyl_node(h=self.base_overlap)
        maker.add_at(cyl_overlap_shape.hole('overlap').at('base'),
                     'face_centre', 'top', post=ad.tranZ(self.epsilon))
        
        return maker


@ad.shape
@ad.datatree
class TnutWasherOuter(ad.CompositeShape):
    '''
    The outer portion of the tnut washer.
    '''
    
    inner_washer_node: ad.Node=ad.dtfield(ad.ShapeNode(TnutWasherInner))
    
    tnut_shaft_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, suffix='_shaft'))
    
    overlap: float=2
    r_small_shaft: float=6.2 /2
    tnut_small_shaft_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, suffix='_small_shaft'))
    
    offset: float=0
    
    epsilon: float=0.01
    fn: int=64
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        
        # Create the inner washer to get the nodes to create the outer washer.
        inner_washer = self.inner_washer_node()
        
        outer_shape = inner_washer.outer_node()
        
        maker = outer_shape.solid('outer').at('face_centre', 'base')
        
        
        outer_cyl = inner_washer.outer_cyl_node()
        maker.add_at(outer_cyl.solid('outer_cyl').at('base', rh=1),
                     'face_centre', 'top', post=ad.tranX(self.offset))
        
        
        overall_len = self.h_shaft + self.wall_h
        shaft_cyl_cage = self.tnut_shaft_node(h=overall_len)
        
        shaft_maker = shaft_cyl_cage.cage('shaft_cyl_cage').at()
        
        shaft_cyl = self.tnut_shaft_node(h=self.overlap + self.epsilon)
        shaft_maker.add_at(shaft_cyl.solid('large').at('base'), 'base')
        
        small_shaft_cyl = self.tnut_small_shaft_node(h=overall_len - self.overlap + self.epsilon)
        shaft_maker.add_at(small_shaft_cyl.solid('small').at('top'), 'top')
        
        
        maker.add_at(shaft_maker.hole('shaft').at('base'),
                     'outer_cyl', 'base', 
                     post=ad.tranZ(self.epsilon))
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
