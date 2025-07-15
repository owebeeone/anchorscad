'''
Created on 2025-07-14

@author: gianni
'''

import anchorscad as ad

from anchorscad_models.basic.angle_extrusion import AngleExtrusion
from anchorscad_models.screws.CountersunkScrew import CountersunkScrew
from anchorscad_models.screws.tnut import Tnut

SMALL="20x3"
LARGE="40x3.2"

@ad.datatree
class BlockPathBuilder:
    '''A rectangular path with bevels at the top.'''
    
    w: float=ad.dtfield(50, doc='Width of block')
    d: int=ad.dtfield(25, doc='depth of block')
    r: float=ad.dtfield(4, doc='Radius of bevels')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((0, 0))
                .line((0, self.d - self.r), 'left-side')
                .arc_tangent_radius_sweep(self.r, sweep_angle=-90, name=('bevel', 0))
                .stroke(self.w - 2 * self.r)
                .arc_tangent_radius_sweep(self.r, sweep_angle=-90, name='top')
                .stroke(self.d - self.r)
                .line((0, 0), 'base')
                )
        
                    
        return builder.build()


@ad.shape
@ad.datatree
class SluiceBracketBlock(ad.CompositeShape):
    '''
    <description>
    '''
    path_builder: ad.Node = ad.ShapeNode(BlockPathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(10, doc='Height of the block')
    extrude_node: ad.Node[ad.LinearExtrude]=ad.ShapeNode(ad.LinearExtrude)
    
    cage_size: tuple=ad.dtfield(
        doc='The (x,y,z) size of cage',
        self_default=lambda s: (s.w, s.h, s.d))
    cage_node: ad.Node[ad.Box]=ad.ShapeNode(ad.Box, prefix="cage_")
   
    
    brace_h: float = ad.dtfield(100, doc='Height of the brace')
    brace_d: float = ad.dtfield(20.4, doc='Depth of the brace')
    brace_w: float = ad.dtfield(20.4, doc='Width of the brace')
    brace_t: float = ad.dtfield(3.3, doc='Thickness of the brace')
    brace_ibr: float = ad.dtfield(0.1, doc='Inner bevel radius of the brace')
    brace_obr: float = ad.dtfield(0.1, doc='Outer bevel radius of the brace')
    brace_ocbr: float = ad.dtfield(0.1, doc='Outer corner bevel radius of the brace')
    brace_icbr: float = ad.dtfield(1.0, doc='Inner corner bevel radius of the brace')
    
    angle_node: ad.Node[AngleExtrusion]=ad.ShapeNode(AngleExtrusion, prefix="brace_")
    brace_angle: float | ad.Angle = ad.dtfield(120, doc='Angle of the brace')
    
    tnut_node: ad.Node[Tnut]=ad.ShapeNode(Tnut, prefix="tnut_")
    
    screw_shaft_overall_length: float = ad.dtfield(25, doc='Overall length of the screw shaft')
    screw_shaft_thru_length: float = ad.dtfield(25, doc='Thru length of the screw shaft')
    screw_size_name: str = ad.dtfield('9g', doc='Size name of the screw')
    screw_include_thru_shaft: bool = ad.dtfield(False, doc='Include thru shaft')
    screw_shaft_hide_cage: bool = ad.dtfield(False, doc='Hide cage of the screw shaft')
    screw_as_solid: bool = ad.dtfield(False, doc='As solid')
    screw_hide_cage: bool = ad.dtfield(False, doc='Hide cage')
    
    screw_node: ad.Node[CountersunkScrew] = ad.ShapeNode(CountersunkScrew, prefix="screw_")
    
    provide_front_tnut: bool = ad.dtfield(True, doc='Provide front tnut')
    provide_back_tnut: bool = ad.dtfield(True, doc='Provide back tnut')
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()
    
    EXAMPLES_EXTENDED={
        'front_tnut': ad.ExampleParams(
            shape_args=ad.args(provide_front_tnut=True, provide_back_tnut=False, fn=64),
            anchors=()),
        'back_tnut': ad.ExampleParams(
            shape_args=ad.args(provide_front_tnut=False, provide_back_tnut=True, fn=64),
            anchors=()),
        'both_tnuts': ad.ExampleParams(
            shape_args=ad.args(provide_front_tnut=True, provide_back_tnut=True, fn=64),
            anchors=())
    }

    def build(self) -> ad.Maker:
        maker = self.cage_node().cage('cage').colour("red", 0.5).transparent(True) \
            .at('face_centre', 'base', post=ad.rotX(180))
        shape = self.extrude_node()
        extrude_maker = shape.solid('extrusion').at('base', 0.5, rh=0.5)
        maker.add_at(
            extrude_maker,
            "face_centre",
            'base',
            post=ad.rotX(180)
        )
        
        brace_shape = self.angle_node()
        
        brace_maker = brace_shape.hole('brace').colour("green").at('construct-base', 1, post=ad.rotY(self.brace_angle))
        
        maker.add_at(
            brace_maker,
            "face_edge",
            'base',
            0,
            0.55,
            post=ad.tranZ(3)
        )
        
        tnut_shape = self.tnut_node()
        tnut_maker = tnut_shape.hole('tnut-front').at('flat', 'top', 1, post=ad.rotX(180))
        
        if self.provide_front_tnut:
            maker.add_at(
                tnut_maker,
                "face_centre",
                'front',
                post=ad.translate((-1, 3, 0))
            )
        
        tnut_maker = tnut_shape.hole('tnut-back').at('flat', 'top', 1, post=ad.rotX(180))
                
        if self.provide_back_tnut:
            maker.add_at(
                tnut_maker,
                "face_centre",
                'back',
                post=ad.translate((-1, -3, 0))
            )
        
        screw_shape = self.screw_node()
        screw_maker = screw_shape.composite('screw').at('top', post=ad.ROTX_180)
        
        maker.add_at(
            screw_maker,
            "face_centre",
            'base',
            post=ad.tranX(-9)
        )
        
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
