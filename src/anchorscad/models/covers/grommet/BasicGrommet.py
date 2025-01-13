'''
Created on 4 June 2022

@author: gianni
'''

import anchorscad as ad
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew


@ad.shape
@ad.datatree
class SealedGrommet(ad.CompositeShape):
    '''
    A grommet with a no opening. The model is intended to be 3D printed in TPU
    and a slit is cut in the top to allow for cables to be inserted creating a
    partial seal.
    '''
    stock_hole_r: float=86 / 2
    stock_depth: float=3
    
    cover_radius_delta: float=15
    overhang_radius_delta: float=6
    epsilon: float=0.01
    
    stock_size: tuple=ad.dtfield(
        doc='The (x,y,z) size of hole template',
        self_default=lambda s: (
            2 * (s.stock_hole_r + s.cover_radius_delta), 
            2 * (s.stock_hole_r + s.cover_radius_delta),
            s.stock_depth))
    
    stock_depth_w_epsilon: tuple=ad.dtfield(
        doc='The depth of the stock with epsilon added',
        self_default=lambda s: s.stock_depth + s.epsilon)
    stock_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, {'size' : 'stock_size'}), init=False)
    stock_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 
                     {'r' : 'stock_hole_r',
                      'h' : 'stock_depth_w_epsilon'}), init=False)
    
    grommet_outer_h_above: float=8
    grommet_outer_h: float=ad.dtfield(
        doc='Overall depth of outer grommet',
        self_default=lambda s: s.stock_depth + s.grommet_outer_h_above)
    
    grommet_outer_r_delta: float=3
    
    grommet_outer_r_base: float=ad.dtfield(
        doc='base radius of outer part of grommet.',
        self_default=lambda s: s.stock_hole_r + s.cover_radius_delta)
    grommet_outer_r_top: float=ad.dtfield(
        doc='top radius of outer part of grommet',
        self_default=lambda s: s.stock_hole_r + s.cover_radius_delta - s.grommet_outer_r_delta)
    
    grommet_outer_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, prefix='grommet_outer_'), init=False)
    
    grommet_inner_thickness: float=4
    grommet_inner_hole_h: float=ad.dtfield(
        doc='inner grommet hole height.',
        self_default=lambda s: s.grommet_outer_h - s.grommet_inner_thickness)
    grommet_inner_hole_r_base: float=ad.dtfield(
        doc='base radius of outer part of grommet.',
        self_default=lambda s: s.stock_hole_r - s.overhang_radius_delta)
    grommet_inner_hole_r_top: float=ad.dtfield(
        doc='top radius of outer part of grommet',
        self_default=lambda s: s.stock_hole_r - s.overhang_radius_delta - s.grommet_outer_r_delta)
    
    
    grommet_inner_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, prefix='grommet_inner_hole_'), init=False)
    
    screw_shaft_overall_length: float=ad.dtfield(
        doc='Overall screw length',
        self_default=lambda s: s.grommet_outer_h + 10)
    screw_shaft_thru_length: float=ad.dtfield(
        doc='Overall screw length',
        self_default=lambda s: s.grommet_outer_h + 10)
    screw_tap_shaft_dia_delta: float=0
    screw_size_name: float="M6"
    screw_head_depth_factor: float=1.1
    screw_include_tap_shaft: float=False
    screw_include_thru_shaft: float=False
    screw_as_solid: float=False
    screw_screw_node : ad.Node=ad.dtfield(
        ad.ShapeNode(CountersunkScrew, prefix='screw_'))
    screw_count: int=6
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64, screw_count=6)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        stock_shape = self.stock_node()
        stock = stock_shape.solid('stock_node').at('centre')
        stock.add_at(self.stock_hole_node().hole('hole').at('centre'), 'centre')
        
        maker = stock.hole('stock').at()
        
        outer_shape = self.grommet_outer_node()
        
        maker.add_at(outer_shape.solid('grommet_outer').at('base'),
                     'face_centre', 'base', post=ad.tranZ(-self.epsilon))
        
        inner_hole_shape = self.grommet_inner_hole_node()
        
        
        maker.add_at(inner_hole_shape.hole('grommet_hole').at('base'),
                     'face_centre', 'base', post=ad.tranZ(2 * self.epsilon))
        
        screw_shape = self.screw_screw_node()
        
        for i in range(self.screw_count):
            maker.add_at(screw_shape.composite(('screw_hole', i)).at('top'),
                         'grommet_outer', 'surface', 
                         tangent=False, 
                         rh=1,
                         angle=i * 360 / self.screw_count,
                         radius_delta=-self.cover_radius_delta / 2, 
                         post=ad.ROTX_270)
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
