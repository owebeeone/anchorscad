'''
Created on 12 May 2022

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.torus import Torus 


@ad.shape
@ad.datatree
class AnchorArm(ad.CompositeShape):
    '''
    A basic ship's anchor arm shape.
    '''
    w: float=ad.dtfield(40, 'Width of arm')
    l: float=ad.dtfield(400, 'length of arm')
    d_large: float=ad.dtfield(40, 'depth of arm at largest point')
    d_small: float=ad.dtfield(15, 'depth of arm at smallest point')
    
    epsilon: float=0.001
    
    def build(self) -> ad.Maker:
        
        #angle = 
        maker = ad.Box([10, 10, 10]).solid('temporary will go').at()
        
        return maker
    


@ad.shape
@ad.datatree
class Anchor(ad.CompositeShape):
    '''
    A basic ship's anchor shape.
    '''
    ring_hole_r: float= 20
    ring_thickness: float=20
    ring_r: float=ad.dtfield(
        self_default=lambda s: s.ring_thickness / 2,
        init=False)
    ring_path_fn: float=ad.dtfield(
        self_default=lambda s: s.fn if s.fn else 16)
    ring_fn: float=ad.dtfield(
        self_default=lambda s: s.fn * 2 if s.fn else 64)
    ring_node: ad.Node=ad.dtfield(
        ad.ShapeNode(Torus, {
            'r_hole': 'ring_hole_r',
            'r_section': 'ring_r',
            'path_fn': 'ring_path_fn',
            'fn': 'ring_fn'}),
        init=False)
    stock_h: float=ad.dtfield(400, 'Length of stock.')
    stock_r: float=ad.dtfield(10, 'Radius of stock.')
    stock_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='stock_'), 
        init=False)
    stock_offs: float=ad.dtfield(
        self_default=lambda s: s.ring_r * 2)
    
    stock_end_r: float=15
    stock_end_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Sphere, prefix='stock_end_'), 
        init=False)
    
    shank_h: float=ad.dtfield(500, 'Length of shank.')
    shank_r: float=ad.dtfield(10, 'Radius of shank.')
    shank_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='stock_'), 
        init=False)
    
    head_r: float=25
    head_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Sphere, prefix='head_'), 
        init=False)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=128)
    EXAMPLE_ANCHORS=(
        ad.surface_args(
            'surface',
            post=ad.tranZ(-10),
            scale_anchor=2),)

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        ring_shape = self.ring_node()
        maker = ring_shape.solid('ring').at('surface')
        
        shank_shape = self.shank_node()
        
        maker.add_at(shank_shape.solid('shank').at('top'),
                     'surface', post=ad.tranZ(-self.ring_r))
        
        stock_shape = self.stock_node()
        
        offs_xform = ad.tranZ(-self.stock_offs) * ad.ROTX_90
        maker.add_at(stock_shape.solid('stock').at('base', rh=0.5),
                     'shank', 'top', post=offs_xform)
        
        stock_end_shape = self.stock_end_node()
        maker.add_at(stock_end_shape.solid('stock_end_0')
                        .at('centre'),
                     'stock', 'top')
        maker.add_at(stock_end_shape.solid('stock_end_1')
                        .at('centre'),
                     'stock', 'base')
        
        head_shape = self.head_node()
        maker.add_at(head_shape.solid('head').at('centre'),
                     'shank', 'top', post=offs_xform)

        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
