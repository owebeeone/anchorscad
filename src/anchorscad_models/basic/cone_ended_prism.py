'''
A triangular prism ended with 2 cones on eiher side. Contains both solid and 
hull shapes.

Created on 5 Oct 2021

@author: gianni
'''

import anchorscad as ad
import numpy as np


@ad.shape
@ad.datatree
class ConeEndedPrism(ad.CompositeShape):
    '''
    Two cones with a trapezoid connection. Similar to a hull operation
    of two cones.
    Args:
        h: Height of the shape.
        w: Width of the flat section of ConeEndedPrism.
        r_base: Base radius (open end).
        r_top: Top radius.
    '''
    h: float=110
    w: float=50
    r_base: float=33 * 4 / np.pi
    r_top: float = 5
    cone_node: ad.Node=ad.ShapeNode(ad.Cone)
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, {'h': 'w'})
    box_cage_node: ad.Node=ad.Node(ad.cageof, prefix='box_cage_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        110, 50, 33 * 4 / np.pi, 5, box_cage_hide_cage=False)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base'),
        ad.surface_args('cone1', 'top'),
        ad.surface_args('cone1', 'base'),
        ad.surface_args('cage', 'face_edge', 'front', 0),
        )
    
    def build(self) -> ad.Maker:
        
        r_max= (self.r_base
                if self.r_base > self.r_top
                else self.r_top)
        size = (r_max * 2, r_max * 2 + self.w, self.h)
        maker = self.box_cage_node(ad.Box(size)).at('centre')
        size_inner = (r_max * 2, self.w, self.h)
        box_inner = ad.Box(size_inner).cage('inner_cage').at('centre')
        maker.add(box_inner)
            
        cone = self.cone_node()
        
        maker.add_at(cone.solid('cone1').at('base'), 
                     'inner_cage', 'face_edge', 0, 0, post=ad.ROTX_90)
        maker.add_at(cone.solid('cone2').at('base'), 
                     'inner_cage', 'face_edge', 3, 2, post=ad.ROTX_90)
        
        path = (ad.PathBuilder()
                    .move((0., 0))
                    .line((-self.r_base, 0), name='lbase')
                    .line((-self.r_top, self.h), name='lside')
                    .line((0, self.h), name='ltop')
                    .line((self.r_top, self.h), name='r_top')
                    .line((self.r_base, 0), name='rside')
                    .line((0, 0), name='rbase')
                    .build())
       
        prism = self.extrude_node(path=path)
        
        maker.add_at(prism.solid('prism').at('lbase', 0), 
                     'cone1', 'base', post=ad.ROTX_180)
        
        return maker

    @ad.anchor('top of the shape')
    def top(self):
        return self.at('cage', 'face_centre', 4)

    @ad.anchor('base of the shape')
    def base(self):
        return self.at('cage', 'face_centre', 1)


@ad.shape
@ad.datatree
class ConeEndedHull(ad.CompositeShape):
    '''
    A "hull" made from ConeEndedPrism.
    Args:
        h: Height of the shape.
        w: Width of the flat section of ConeEndedPrism.
        r_base: Base radius (open end).
        r_top: Top radius.
        t: Thickness of hull wall.
        t_top: Thickness of hull at top.
    '''

    cep_node: ad.Node=ad.ShapeNode(ConeEndedPrism)
    t: float=1.5
    inner_cep_node: ad.Node=ad.ShapeNode(ConeEndedPrism, 'w')
    t_top: float=0
    epsilon: float=0.005
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        h=110, w=50, r_base=33 * 4 / np.pi, r_top=4.5, t=3, t_top=1.5, fn=32)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        
        outer = self.cep_node()
        self.outer = outer
        
        t = self.t
        ratio = (self.r_base - self.r_top) / self.h
        if self.t_top:
            inner_r_top = self.r_top + ratio * self.t_top - t
        else:
            inner_r_top = self.r_top - t
        
        epsilon = self.epsilon
        inner = self.inner_cep_node(
            h=self.h - self.t_top + epsilon * 2, 
            r_base=self.r_base -t, r_top=inner_r_top)
        self.inner = inner
        
        maker = outer.solid('outer').at('centre')
        
        maker.add_at(inner.hole('inner').at('cone1', 'base'),
                     'cone1', 'base', post=ad.tranZ(epsilon))

        return maker


MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
