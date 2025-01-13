'''
Created on 22 Aug 2021

@author: gianni
'''


import anchorscad as ad
from anchorscad_models.screws.dims import HEAD_MAP, SHAFT_MAP, ShaftDimensions, \
  HeadDimensions


@ad.shape
@ad.datatree
class CountersunkScrew(ad.CompositeShape):
    '''
    Generic countersunk screw shaped hole including optional shaft solid 
    sections and access hole.
    
    Three cylinders are added as "cages", 2 of which may optionally be added
    as solids and an optional "access hole" above the screw for allowing access
    to the screw hole.
    
    Component Shapes:
    'screw_cage' covers the entire screw length.
    'tap_shaft' a cage or solid that covers the shaft component that is used 
        for self tapping screws to tap into.
    'thru_shaft' a cage or a solid that covers the screw but is sized so the
        screw can easily pass.
    'access_hole' a cylindrical hole directly above the screw head hold that
        is sized larger than the screw head for cutting access holes in 
        surrounding model parts that would block access.
    'screw_hole' A hole for the screw that allows for head space. 

    '''
    
    shaft_overall_length: float
    shaft_thru_length: float
    size_name: str
    include_thru_shaft: bool=False
    tap_shaft_dia_delta: float=None
    access_hole_depth: float=10
    shaft_taper_length: float=0
    shaft_dims: ShaftDimensions=None
    head_dims: HeadDimensions=None
    head_depth_factor: float=0.5
    head_sink_factor: float=0.1
    as_solid: bool=False
    cone_node: ad.Node=ad.ShapeNode(ad.Cone, {})
    rotate_extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, {})
    cage_of_node: ad.Node=ad.CageOfNode()
    shaft_cage_of_node: ad.Node=ad.CageOfNode(prefix='shaft_')

    
    EXAMPLE_SHAPE_ARGS=ad.args(
        shaft_overall_length=20, 
        shaft_thru_length=14, 
        size_name="BUGLE_14g-10",
        include_thru_shaft=True,
        tap_shaft_dia_delta=6 - 2.6,
        as_solid=True,
        hide_cage=False,
        fn=36)
    
    EXAMPLE_ANCHORS=(
                ad.surface_args('screw_cage', 'base'),
                ad.surface_args('access_hole', 'top'),
                ad.surface_args('screw_hole', 'head_mid', 0.5),)
    
    EXAMPLES_EXTENDED={
        'show_cage': ad.ExampleParams(
            shape_args=ad.args(shaft_overall_length=25, 
                                shaft_thru_length=14, 
                                size_name="BUGLE_14g-10",
                                include_thru_shaft=True,
                                shaft_hide_cage=True,
                                as_solid=False,
                                hide_cage=True,
                                fn=64),
            anchors=())
        }
    
    def diameter(self) -> float:
        return self.shaft_dims.actual
    
    def head_diameter(self) -> float:
        return self.head_dims.head_top_d
    
    def build(self) -> ad.Maker:
        if not self.shaft_dims:
            self.shaft_dims = SHAFT_MAP[self.size_name]
        
        if not self.head_dims:
            self.head_dims = self.createHeadDims(self.shaft_dims)
        
        shaft_dims = self.shaft_dims
        cage_shape = self.cone_node(
            h=self.shaft_overall_length,
            r_base=shaft_dims.thru_d / 2,
            r_top=shaft_dims.thru_d / 2,
            )
        maker = self.cage_of_node(cage_shape, cage_name='screw_cage').at('base')
            
        head_dims = self.head_dims
        if not self.tap_shaft_dia_delta:
            self.tap_shaft_dia_delta = head_dims.head_top_d - shaft_dims.actual 
        
        tap_y = (self.shaft_overall_length 
                       - self.shaft_thru_length
                       - self.shaft_taper_length)
        taper_y = tap_y + self.shaft_taper_length
        
        tap_shaft_dia = self.tap_shaft_dia_delta + shaft_dims.actual
        tap_shaft_shape = self.cone_node(
            h=taper_y,
            r_base=tap_shaft_dia / 2,
            r_top=tap_shaft_dia / 2)
        
        tap_shaft_shape = self.shaft_cage_of_node(tap_shaft_shape, cage_name='tap_shaft')

        maker.add_at(tap_shaft_shape.at('base'), 'base')
        
        thru_shaft_shape = self.cone_node(
            h=self.shaft_overall_length - taper_y,
            r_base=tap_shaft_dia / 2,
            r_top=tap_shaft_dia / 2)
        
        # Add the through shaft as a solid or cage.
        thru_shaft_func = (thru_shaft_shape.solid 
                          if self.include_thru_shaft
                          else thru_shaft_shape.cage)
            
        maker.add_at(thru_shaft_func('thru_shaft').at('top'), 
                     'top')
        
        if self.access_hole_depth > 0:
            access_hole_shape = self.cone_node(
                h=self.access_hole_depth,
                r_base=head_dims.head_top_d / 2.0,
                r_top=head_dims.head_top_d / 2.0)
            
            access_hole_func = (access_hole_shape.solid 
                                if self.as_solid else access_hole_shape.hole)
            
            maker.add_at(access_hole_func('access_hole').at('base'), 
                     'top', post=ad.rotX(180) * ad.translate([0, 0, 0.001]))
        
        head_bot_y = (self.shaft_overall_length 
                      - head_dims.overall_screw_head_height())
        head_mid_y = head_bot_y + head_dims.head_countersink_depth
        head_top_y = self.shaft_overall_length
        
        path = (ad.PathBuilder()
            .move([0, 0])
            .line([-shaft_dims.tapping_d / 2.0, 0], 'base_edge')  
            .line([-shaft_dims.tapping_d / 2.0, tap_y], 'tapping_edge')  
            .line([-shaft_dims.thru_d / 2.0, taper_y], 'taper_edge')    
            .line([-shaft_dims.thru_d / 2.0, head_bot_y], 'head_bot')   
            .line([-head_dims.head_bot_d / 2.0, head_bot_y], 'head_bot_base')   
            .line([-head_dims.head_top_d / 2.0, head_mid_y], 'head_mid') 
            .line([-head_dims.head_top_d / 2.0, head_top_y], 'head_top') 
            .line([0, head_top_y], 'top_edge')  
            .line([0, 0], 'centre_edge') 
            .build()
            )
        
        shape = self.rotate_extrude_node(path)
        
        shape_func = shape.solid if self.as_solid else shape.hole
        
        maker.add_at(shape_func('screw_hole').at('base_edge', 0),
                     'base', post=ad.rotY(180))
        
        return maker

    def createHeadDims(self, shaft_dims):
        '''Creates a default set of countersunk screw set of head dimensions.'''
        
        if self.size_name in HEAD_MAP:
            return HEAD_MAP[self.size_name]
        
        return HeadDimensions(
            head_top_d=(self.head_depth_factor + 1) * shaft_dims.tapping_d,
            head_bot_d=shaft_dims.tapping_d,
            head_protrusion_height=0.0,
            head_mid_depth=self.head_sink_factor * shaft_dims.tapping_d,
            head_countersink_depth=self.head_depth_factor * shaft_dims.tapping_d / 2)


@ad.shape
@ad.datatree(chain_post_init=True)
class FlatSunkScrew(CountersunkScrew):
    '''For screws that are flat and sunk into the surface.'''

    def createHeadDims(self, shaft_dims):
        '''Creates a default set of flat sunk screw set of head dimensions.'''
        head_dia = (self.head_depth_factor + 1) * shaft_dims.tapping_d
        return HeadDimensions(
            head_top_d=head_dia,
            head_bot_d=head_dia,
            head_protrusion_height=0.0,
            head_mid_depth=self.head_sink_factor * shaft_dims.tapping_d,
            head_countersink_depth=self.head_depth_factor * shaft_dims.tapping_d / 2)
        
@ad.shape
@ad.datatree(chain_post_init=True)
class FlatHeadScrew(CountersunkScrew):
    '''For screws that are flat and flush with the surface.'''

    def createHeadDims(self, shaft_dims):
        '''Creates a default set of flat sunk screw set of head dimensions.'''
        head_dia = (self.head_depth_factor + 1) * shaft_dims.tapping_d
        return HeadDimensions(
            head_top_d=head_dia,
            head_bot_d=head_dia,
            head_protrusion_height=0.0,
            head_mid_depth=self.head_sink_factor * shaft_dims.tapping_d,
            head_countersink_depth=self.head_depth_factor * shaft_dims.tapping_d / 2)
    
    @ad.anchor('Screw head surface interface top')
    def top(self) -> ad.GMatrix:
        head_height = self.head_dims.overall_screw_head_height()
        return self.maker.at('top') * ad.tranZ(-head_height)

        
@ad.shape
@ad.datatree(chain_post_init=True)
class TestCountersunkScrew(ad.CompositeShape):
    screw_node: ad.Node = ad.ShapeNode(CountersunkScrew)
    
    screw_shape: ad.Shape = ad.dtfield(self_default=lambda s: s.screw_node())
    
    test_margin: float = ad.dtfield(5, 'The margin around the screw hole.')
    
    test_size: tuple = ad.dtfield(
        self_default=lambda s: (
            s.screw_shape.head_diameter() + s.test_margin * 2,
            s.screw_shape.head_diameter() + s.test_margin * 2,
            s.screw_shape.shaft_overall_length),
        doc='The size of the test box.')
    
    box_node: ad.Node = ad.ShapeNode(ad.Box, prefix='test_')
    
    
    test_cut_size: tuple = ad.dtfield(
        self_default=lambda s: (
            s.test_size[0] / 2 + s.epsilon,
            s.test_size[1] / 2 + s.epsilon,
            s.test_size[2] + s.epsilon),
        doc='The size of the test box.')
    cut_box_node: ad.Node = ad.ShapeNode(ad.Box, prefix='test_cut_')

    epsilon: float = ad.dtfield(0.01, 'The epsilon value for cutting the test box.')    
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        shaft_overall_length=25,
        shaft_thru_length=25,
        size_name='DECK_10g-10',
        include_thru_shaft=False,
        shaft_hide_cage=False,
        as_solid=False,
        hide_cage=False,
        fn=128)

    def build(self) -> ad.Maker:
        
        maker = self.box_node().solid('test_box').at('centre')
        
        cut_box = self.cut_box_node().hole('test_cut_box').colour('green')\
            .at('face_edge', 'front', 3, post=ad.ROTY_90)
        
        maker.add_at(cut_box, 'centre')
        
        maker.add_at(self.screw_shape.composite('screw').at('top'),
                        'face_centre', 'top')

        # Add any additional testing or modifications here

        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main(False)
        
    