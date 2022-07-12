'''
Created on 12 Jul 2022

@author: gianni
'''

import anchorscad as ad
from anchorscad.core import Cylinder
from distutils.command.build import build

@ad.datatree
class LidPath:
    big_lid_r: float=ad.dtfield(75, 'Radius of big lid')
    small_lid_h: float=ad.dtfield(24.7, 'Depth of small lid')
    big_lid_w: float=ad.dtfield(127.4 / 2, 'Half the width of big lid flat')
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
            .arc_points_radius(last=(-self.big_lid_w, 0),
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
            ad.ShapeNode(ad.LinearExtrude),
            init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=128)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('lid').at()
        return maker
    
 
@ad.shape
@ad.datatree
class LidWithScrewHoles(ad.CompositeShape):
    lid_extrusion_node: ad.Node=ad.ShapeNode(LidExtrusion)
#     screw_spacing: 
#      
    def build(self) -> ad.Maker:
        shape = self.lid_extrusion_node()
        maker = shape.solid('lid').at()
        return maker
    
    
@ad.shape
@ad.datatree
class SplitLid(ad.CompositeShape):    
    lid_node: ad.Node=ad.ShapeNode(LidWithScrewHoles)
    lid_side: bool=False
    
    cut_box_size: tuple=ad.dtfield(
            self_default=lambda s: (
                s.small_lid_w * 2,
                s.small_lid_h,
                s.h + s.epsilon * 2), 
            doc='Size of cutbox')
    cut_box_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cut_box_')
    
    epsilon: float=0.01
        
    _GEN_TEST_ARGS = lambda lid_side: \
        ad.args(fn=128, lid_side=lid_side)
    
    EXAMPLE_SHAPE_ARGS=_GEN_TEST_ARGS(False)
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={
        'example2': ad.ExampleParams(
            shape_args=_GEN_TEST_ARGS(True))}

     
    def build(self) -> ad.Maker:
        return ad.make_intersection_or_hole( 
            self.lid_side,
            self.lid_node(),
            ad.surface_args('origin_to_lip', post=ad.ROTY_180 * ad.tranY(-self.epsilon)),
            self.cut_box_node(),
            ad.surface_args('face_edge', 'front', 0),
            ('lid_part', self.lid_side))

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()