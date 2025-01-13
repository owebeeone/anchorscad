'''
Created on 12 Jul 2022

@author: gianni
'''

import anchorscad as ad
from anchorscad.core import Cylinder
from anchorscad_models.screws.CountersunkScrew import FlatSunkScrew
from anchorscad_models.hinges.Hinge import Hinge
from anchorscad_models.basic.TriangularPrism import TriangularPrism

@ad.datatree
class LidPath:
    big_lid_r: float=ad.dtfield(80, 'Radius of big lid')
    small_lid_h: float=ad.dtfield(24.7, 'Depth of small lid')
    big_lid_w: float=ad.dtfield(130 / 2, 'Half the width of big lid flat')
    small_lid_w: float=ad.dtfield(103.7 / 2, 'Half the width of small lid flat')

    def build(self) -> ad.Path:
        builder = (
            ad.PathBuilder()
            .move((0, 0))
            .line((-self.small_lid_w, 0), 'origin_to_lip')
            .arc_points(middle=(0, self.small_lid_h),
                        last=(self.small_lid_w, 0),
                        direction=False,
                        name='small_lid_arc')
            .line((self.big_lid_w, 0), 'lip_rhs')
            .arc_points_radius((-self.big_lid_w, 0),
                               radius=self.big_lid_r,
                               name='big_lid_arc')
            .line((-self.small_lid_w, 0), 'lip_lhs')
            )
        return builder.build()

@ad.shape
@ad.datatree
class LidExtrusion(ad.CompositeShape):
    path_node: ad.Node=ad.Node(LidPath)
    h: float=ad.dtfield(12, 'Thickness of the lid')
    path: ad.Path=ad.dtfield(
            self_default=lambda s: s.path_node().build(), 
            doc='Lid polygon',
            init=False)
    extrude_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.LinearExtrude, 
                     {'fn': 'lid_fn'},
                     expose_all=True),
            init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(lid_fn=128)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('lid').at()
        return maker
    
 
@ad.shape
@ad.datatree
class LidWithScrewHoles(ad.CompositeShape):
    lid_extrusion_node: ad.Node=ad.ShapeNode(LidExtrusion)
    
    screw_spacing: float=ad.dtfield(
                                (35.6 + 30.1) / 2,
                                'Space betweeen screwholes')
    screwhole_d: float=ad.dtfield(1.9, 'Diameter of screwhole')
    
    screw_shaft_overall_length: float=ad.dtfield(16,
                                                 'Overall screw length')
    screw_shaft_thru_length: float=ad.dtfield(16,
                                              'Screwhole depth')
    screw_tap_shaft_dia_delta: float=0
    screw_size_name: float="M2.6"
    screw_head_depth_factor: float=1.1
    screw_include_tap_shaft: float=False
    screw_include_thru_shaft: float=False
    screw_as_solid: float=False
    screw_screw_node : ad.Node=ad.dtfield(
        ad.ShapeNode(FlatSunkScrew, 
                     {'fn': 'screw_fn',
                      'fa': 'screw_fa',
                      'fs': 'screw_fs'},
                     expose_all=True,
                     prefix='screw_'),
        init=False)
    
    x_fac: float=ad.dtfield(
            self_default=lambda s : s.screw_spacing / 2,
            doc='X translation factor')
    y_fac: float=ad.dtfield(
            self_default=lambda s : s.h - 4.2 - s.screwhole_d / 2,
            doc='Y translation factor')
    z_fac: float=ad.dtfield(-8, 'Z translation factor')
    
    wedge_size: tuple=ad.dtfield(
            self_default=lambda s: (
                s.h * 0.5,
                s.h * 0.75,
                50),
            doc='Size of wedge removed big lid at lips')
    wedge_node: ad.Node=ad.dtfield(
            ad.ShapeNode(TriangularPrism, prefix='wedge_'),
            init=False)
    
    epsilon: float=0.01
    
    EXAMPLE_SHAPE_ARGS=ad.args(lid_fn=128, screw_as_solid=False)
    EXAMPLE_ANCHORS=(ad.surface_args('sh2', 'top'),
                     ad.surface_args('lip_lhs', 1),
                     ad.surface_args('lip_rhs', 0),
                     ad.surface_args('wedge_rhs', 'face_centre', 'front'),
                     ad.surface_args('wedge_rhs', 'face_centre', 'base'))
    
    def build(self) -> ad.Maker:
        screwhole = self.screw_screw_node()
        screwhole_assembly = screwhole.composite('sh1').at(
                'centre', post=ad.translate((self.x_fac,
                                             self.y_fac,
                                             self.z_fac)))
        screwhole_assembly.add_at(screwhole.composite('sh2').at(
                'centre', post=ad.translate((-self.x_fac,
                                             self.y_fac,
                                             self.z_fac))))
        
        shape = self.lid_extrusion_node()
        maker = shape.solid('lid').at()
        
        maker.add_at(screwhole_assembly,
                     'small_lid_arc', 0.5, rh=1)
        
        wedge_shape = self.wedge_node()
        maker.add_at(wedge_shape.hole('wedge_lhs')
                     .at('face_edge', 'front', 3, 0), 
                     'lip_lhs', 1, post=ad.ROTY_180 * ad.translate((0, 
                                                      -self.epsilon, 
                                                      self.epsilon)))
        maker.add_at(wedge_shape.hole('wedge_rhs')
                     .at('face_edge', 'front', 3, 1), 
                     'lip_rhs', 0, post=ad.ROTY_180 * ad.translate((0, 
                                                      -self.epsilon, 
                                                      self.epsilon)))
        return maker
    
    
@ad.shape
@ad.datatree
class SplitLid(ad.CompositeShape):    
    lid_node: ad.Node=ad.dtfield(
            ad.ShapeNode(LidWithScrewHoles), init=False)
    lid_side: bool=False
    
    cut_box_size: tuple=ad.dtfield(
            self_default=lambda s: (
                s.big_lid_w * 2,
                s.sep,
                s.h + s.epsilon * 2), 
            doc='Size of cutbox')
    cut_box_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cut_box_')
    
    sep: float=ad.dtfield(0.2, 'Separation factor for the two lid parts')
    
    epsilon: float=0.01
        
    _GEN_TEST_ARGS = lambda lid_side: \
        ad.args(lid_fn=128, lid_side=lid_side)
    
    EXAMPLE_SHAPE_ARGS=_GEN_TEST_ARGS(False)
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={
        'example2': ad.ExampleParams(
            shape_args=_GEN_TEST_ARGS(True))}

     
    def build(self) -> ad.Maker:
        maker = self.lid_node().solid('lid').at()
        maker.add_at(self.cut_box_node().hole('cut_box')
                     .at('face_edge', 'front', 0), 
                     'origin_to_lip', post=ad.ROTY_180 * ad.tranY(-self.epsilon))
        return maker


@ad.shape
@ad.datatree
class HingedLid(ad.CompositeShape):  
    '''Vintage depression glass salt pig lid. 
    
    Original lids were wooden and virtually all of them are degraded
    and unusable. This model is a one piece hinged lid. The washers
    (see the model below) are shaped to fit in the hole provided 
    at the rear of the salt pig.
    
    See link below for a similar (if not identical salt pig) this was
    designed to it.
    https://www.antiquesnavigator.com/d-225708/vintage-depression-glass-salt-box-salt-pig.html
    '''
    lid_node: ad.Node=ad.dtfield(
            ad.ShapeNode(SplitLid), init=False)
    
    hinge_bar_h: float=ad.dtfield(
            self_default=lambda s: s.small_lid_w * 2 - 20,
            doc='Length of hinge component')  
    hinge_node: ad.Node=ad.dtfield(
            ad.ShapeNode(Hinge, {'sep': 'sep'},
                         prefix='hinge_',
                         expose_all=True), 
            init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(
            sep=0.2,
            hinge_seg_count=14,
            lid_fn=512,
            screw_fn=32,
            fn=128)

    EXAMPLE_ANCHORS=()
    
    EXAMPLES_EXTENDED={
        # This example has minimal complexity making it easier
        # to inspect the model in OpenSCAD.
        'example2': ad.ExampleParams(
                shape_args=ad.args(
                        sep=0.2,
                        hinge_seg_count=5,
                        lid_fn=20,
                        screw_fn=3,
                        fn=16),
                anchors=())
        }  
      
    def build(self) -> ad.Maker:
        lid_shape = self.lid_node()
        maker = lid_shape.solid('lid').at()
        hinge_shape = self.hinge_node()
        maker.add_at(hinge_shape.composite('hinge').at('centre'),
                     'cut_box', 'face_centre', 'top',
                     post=ad.ROTY_90)
        return maker


@ad.shape
@ad.datatree
class HingedLidLabel(ad.CompositeShape):
    
    hinged_lid_node: ad.Node=ad.ShapeNode(HingedLid)
    hinged_lid: ad.Maker=ad.dtfield(self_default=lambda s: s.hinged_lid_node())

    label_text: str=ad.dtfield('SALT', 'Label for the model')
    label_fn: int=ad.dtfield(32, 'Number of facets for the text')
    label_halign: str=ad.dtfield('centre', 'Horizontal alignment of text')
    label_depth: float=ad.dtfield(0.3, 'Height of text')
    label_node: ad.Node=ad.ShapeNode(
        ad.Text, {'fn': 'label_fn'}, expose_all=True, prefix='label_')
    label_size: float=ad.dtfield(
        self_default=lambda s: s.big_lid_w * 0.6,
        doc='Size of text')
    label_boss: float=ad.dtfield(0.2, 'Height of boss for label')
        
    EXAMPLE_SHAPE_ARGS=ad.args(
            sep=0.2,
            hinge_seg_count=14,
            lid_fn=512,
            screw_fn=32,
            fn=128)
    
    def build(self) -> ad.Maker:
        maker = self.hinged_lid.solid('lid').at()

        maker.add_at(self.label_node().solid('text').colour((1, 0, 0)).at('default'),
                     'big_lid_arc', 0.5, rh=1,
                     post=ad.ROTY_180 
                        * ad.ROTX_270 
                        * ad.tranZ(-self.label_depth + self.label_boss)
                        * ad.tranY(self.big_lid_w * 0.75))
        return maker

    
@ad.shape
@ad.datatree
class LidScrewWashers(ad.CompositeShape): 
    '''Washer for "Salt Pig" for lid fastening HingedLid to jar.

    This should be printed in TPU or flexible material. Do not
    make it a tolerance fit as it's important not to apply forces
    that cause tension cracks in the glass jar.
    '''
    
    big_cone_r_base: float=ad.dtfield(12.8 / 2 - 0.2, 'Base radius of big cone')
    big_cone_r_top: float=ad.dtfield(12.1 / 2 - 0.2, 'Top radius of big cone')
    big_cone_h: float=ad.dtfield(4.6, 'Height of big cone')
    big_cone_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cone, prefix='big_cone_'), init=False)
    
    hole_cyl_r: float=ad.dtfield(3 / 2, 'Radius of through hole')
    hole_cyl_h: float=ad.dtfield(9.4, 'Height of through hole')
    hole_cyl_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cylinder, prefix='hole_cyl_'), init=False)
    
    small_cone_r_base: float=ad.dtfield(7.9 / 2 - 0.2, 'Base radius of small cone')
    small_cone_r_top: float=ad.dtfield(5.9 / 2 - 0.2, 'Top radius of small cone')
    small_cone_h: float=ad.dtfield(
            self_default=lambda s: s.hole_cyl_h - s.big_cone_h - s.epsilon,
            doc='Height of small cone')
    small_cone_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cone, prefix='small_cone_'), init=False)
    
    epsilon: float=ad.dtfield(
            0.01, 
            'Fudge factor to eliminate tearing in the final model')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        maker = self.big_cone_node().solid('big_cone').at('base')
        maker.add_at(self.small_cone_node().solid('small_cone')
                    .at('base'),
                    'big_cone', 'base', rh=1)
        maker.add_at(self.hole_cyl_node().hole('hole_cyl')
                     .at('base', h=self.epsilon / 2), 'base')
        
        return maker
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()