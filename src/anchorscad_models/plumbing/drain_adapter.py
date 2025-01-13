'''
Created on 27-Jul-2024

@author: gianni

A drain adapter for providing a small drain port for a reverse osmosis 
system. Reverse osmosis systems are often installed under a sink, and
they require a waste water drain. The drain pipe from the reverse osmosis
system is typically 1/4" OD tubing, and the drain adapter allows the 
connection of this tubing to a standard 2" sink drain pipe. 

The design is fully parametric so it will work for various pipe, bolt and
pipe sizes. 

These types of adapters are often have an dual sided adhesive pad on drain
port interfacing between the inner surface of the adapter and the outer
surface of the sink drain pipe.

'''

import anchorscad as ad
from anchorscad.core import Maker
from anchorscad_models.basic.pipe import Pipe
from anchorscad_models.basic.regular_prism import RegularPrism


@ad.datatree
class DrainAdapterTabProfileBuilder:
    '''Builds one tab, 4 of these are used in the final design.'''
    
    thickness: float=ad.dtfield(5, doc='Width of block')
    inside_r: float=ad.dtfield(51 / 2, doc='Radius of inner pipe')
    tab_w: float=ad.dtfield(15, doc='Width of tab')
    tab_d: float=ad.dtfield(10, doc='Depth of tab')
    skew: float=ad.dtfield(-1, doc='Skew of tab')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((self.inside_r, 0))
                .line((self.inside_r + self.tab_w, 0), 'tab_base')
                .stroke(self.tab_d, 90, name='outer_tab')
                .line((0, self.inside_r - self.skew), 'tab_top')
            )

                    
        return builder.build()


@ad.shape
@ad.datatree
class DrainAdapterTab(ad.CompositeShape):
    '''One tab of the drain adapter.'''
    path_builder: ad.Node = ad.ShapeNode(DrainAdapterTabProfileBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(15, doc='Height of the shape')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('extrusion').at('tab_base', 0.5)
        return maker


@ad.shape
@ad.datatree
class DrainAdapterBoltHole(ad.CompositeShape):
    '''A hole for a fastener for the drain adapter. Includes optional hex head
    or flat head.'''

    bolt_r: float=ad.dtfield(6.1 / 2, doc='Radius of bolt hole')
    h: float=ad.dtfield(35, doc='Height of bolt hole')
    
    head_r: float=ad.dtfield(12 / 2, doc='Radius of head of bolt')
    head_h: float=ad.dtfield(20, doc='Height of head of bolt')
    hex_r: float=ad.dtfield(11.3 / 2, doc='Radius of hex part of bolt')
    hex_h: float=ad.dtfield(20, doc='Radius of hex part of bolt')
    hex_nsides: int=ad.dtfield(6, doc='Number of sides of hex part of bolt')
    
    cyl_node: ad.Node=ad.ShapeNode(ad.Cylinder, 'h', {'r': 'bolt_r'})
    
    head_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='head_')
    
    hex_node: ad.Node=ad.ShapeNode(RegularPrism, prefix='hex_')
    
    is_nut: bool=ad.dtfield(True, doc='Is this hole for a hex nut?')
    
    epsilon: float=ad.dtfield(0.01, doc='Offset of nut from bolt')
    
    EXAMPLE_SHAPE_ARGS=ad.args(is_nut=True, fn=64)
    EXAMPLES_EXTENDED={
        'as_bolt': ad.ExampleParams(shape_args=ad.args(is_nut=False, fn=64))
    }
    
    def build(self) -> Maker:
        
        shape = self.cyl_node()
        
        maker = shape.solid('bolt_hole').at('top')
        
        if self.is_nut:
            hex_shape = self.hex_node()
            
            maker.add_at(
                hex_shape.solid('nut').at('base'),
                'base', rh=1, post=ad.tranZ(self.epsilon))
        else:
            head_shape = self.head_node()
            
            maker.add_at(
                head_shape.solid('nut').at('base'),
                'base', rh=1, post=ad.tranZ(self.epsilon))
        
        return maker
    
@ad.shape
@ad.datatree
class DrainAdapterPort(ad.CompositeShape):
    '''The port for the drain adapter. This is just a tab for a press fit 
    pipe. Some adhesive will likely be needed to keep pipe water proof.'''
    
    # Shared with all the other components.
    h: float=ad.dtfield(10, doc='Height of port')
    
    port_w: float=ad.dtfield(15, doc='Width of port')
    
    port_d: float=ad.dtfield(15, doc='Depth of port')
    
    port_size: float=ad.dtfield(
        self_default=lambda s: (s.h, s.port_w, s.port_d))

    port_adapter_node: ad.Node=ad.ShapeNode(ad.Box, prefix='port_')    
    
    port_hole_r: float=ad.dtfield(6.45 / 2, doc='Radius of port hole')
    
    port_hole_overlap: float=ad.dtfield(5, doc='Overlap of port hole')
    
    port_hole_h: float=ad.dtfield(
        self_default=lambda s: s.port_d + s.port_hole_overlap, 
        doc='Height of port hole')
    
    port_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='port_hole_')
    
    epsilon: float=ad.dtfield(0.01, doc='Offset of nut from bolt')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    
    def build(self) -> Maker:
        
        shape = self.port_adapter_node()
        
        maker = shape.solid('port').at('face_centre', 'front')
        
        hole_shape = self.port_hole_node()
        
        maker.add_at(
            hole_shape.hole('port_hole').at('base'),
            'face_centre', 'top', post=ad.tranZ(self.port_hole_overlap / 2 + self.epsilon))
                
        return maker


@ad.shape
@ad.datatree
class DrainAdapter(ad.CompositeShape):
    '''One side of the drain adapter. Can be configured to have a drain port or
    hex nut hole vs a flat head bolt hole.'''
    
    tab_node: ad.Node = ad.ShapeNode(DrainAdapterTab)
    
    sweep_angle: float=ad.dtfield(179, doc='Angle of the pie slice')
    
    outside_r: float=ad.dtfield(
        self_default=lambda s: s.inside_r + s.thickness, 
        doc='Outer radius of adaper')
    pipe_node: ad.Node=ad.ShapeNode(Pipe)
    
    
    bolt_node: ad.Node=ad.ShapeNode(DrainAdapterBoltHole)
    
    bolt_offset: float=ad.dtfield(6, doc='Offset of bolt hole from tab')
    
    with_drain_port: bool=ad.dtfield(True, doc='Include drain port')
    
    angle_offset: float=ad.dtfield(1, doc='Angle offset of between tabs')
    
    port_node: ad.Node=ad.ShapeNode(DrainAdapterPort)
    
    port_angle_position: float=ad.dtfield(65, doc='Angle position of port')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=128, is_nut=False)
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={
        'upper': ad.ExampleParams(shape_args=ad.args(
            fn=128, is_nut=True, with_drain_port=False)),
        'lower': ad.ExampleParams(shape_args=ad.args(
            fn=128, is_nut=False, with_drain_port=True)),
    }

    def build(self) -> ad.Maker:
        tab_shape = self.tab_node()
        
        bolt_shape = self.bolt_node()
        tab_assembly = tab_shape.solid('tab').at('tab_base', rh=0.5)
        tab_assembly.add_at(
            bolt_shape.hole('bolt').at('base', rh=1, post=ad.ROTZ_90),
            post=ad.tranX(self.bolt_offset) * ad.tranZ(-10))
        
        pipe_shape = self.pipe_node()
        
        maker = pipe_shape.composite('outer').at('base', rh=1)
        
        maker.add_at(
            tab_assembly.composite(('tab', 0)).at('tab_base', 0, rh=0.5),
            'inner_surface', angle=0, rh=0.5, post=ad.ROTY_90 * ad.ROTX_180
            )
        maker.add_at(
            tab_assembly.composite(('tab', 1)).at('tab_base', 0, rh=0.5),
            'inner_surface', angle=self.sweep_angle, rh=0.5, post=ad.ROTY_90
            )
        
        if self.with_drain_port:
            port_shape = self.port_node()
            maker.add_at(
                port_shape.composite('port').at('face_centre', 'top'),
                'inner_surface', angle=self.port_angle_position, rh=0.5, post=ad.ROTZ_90
                )
        
        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
