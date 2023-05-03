'''
Created on 22 Aug 2021

@author: gianni
'''


import anchorscad as ad
from anchorscad.models.screws.dims import SHAFT_MAP, ShaftDimensions, \
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
    include_tap_shaft: bool=False
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

    
    EXAMPLE_SHAPE_ARGS=ad.args(
        shaft_overall_length=20, 
        shaft_thru_length=14, 
        size_name="M6",
        include_tap_shaft=False,
        include_thru_shaft=True,
        tap_shaft_dia_delta=6 - 2.6,
        fn=36)
    
    EXAMPLE_ANCHORS=(
                ad.surface_args('screw_cage', 'base'),
                ad.surface_args('access_hole', 'top'),
                ad.surface_args('screw_hole', 'head_mid', 0.5),)
    
    def build(self) -> ad.Maker:
        if not self.shaft_dims:
            self.shaft_dims = SHAFT_MAP[self.size_name]
        
        if not self.head_dims:
            self.head_dims = self.createHeadDims(self.shaft_dims)
        
        shaft_dims = self.shaft_dims
        maker = self.cone_node(
            h=self.shaft_overall_length,
            r_base=shaft_dims.thru_d / 2,
            r_top=shaft_dims.thru_d / 2,
            ).cage('screw_cage').at('base')
            
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
        tap_shaft_func = (tap_shaft_shape.solid 
                          if self.include_tap_shaft
                          else tap_shaft_shape.cage)

        maker.add_at(tap_shaft_func('tap_shaft').at('base'), 'base')
        
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
        
        return HeadDimensions(
            head_top_d=(self.head_depth_factor + 1) * shaft_dims.tapping_d,
            head_bot_d=shaft_dims.tapping_d,
            head_protrusion_height=0.0,
            head_mid_depth=self.head_sink_factor * shaft_dims.tapping_d,
            head_countersink_depth=self.head_depth_factor * shaft_dims.tapping_d / 2)


@ad.shape
@ad.datatree(chain_post_init=True)
class FlatSunkScrew(CountersunkScrew):

    def createHeadDims(self, shaft_dims):
        '''Creates a default set of flat sunk screw set of head dimensions.'''
        head_dia = (self.head_depth_factor + 1) * shaft_dims.tapping_d
        return HeadDimensions(
            head_top_d=head_dia,
            head_bot_d=head_dia,
            head_protrusion_height=0.0,
            head_mid_depth=self.head_sink_factor * shaft_dims.tapping_d,
            head_countersink_depth=self.head_depth_factor * shaft_dims.tapping_d / 2)


if __name__ == "__main__":
    ad.anchorscad_main(False)
        
    