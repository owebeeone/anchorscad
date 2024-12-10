'''
Created on 7-Dec-2024

@author: gianni
'''

from typing import Tuple
import anchorscad as ad

from anchorscad.models.basic.box_side_bevels import BoxSideBevels
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew
from anchorscad.models.screws.tnut import Tnut

@ad.datatree
class VesaInnerSpec:
    '''The inner VESA specification specifies the size (centres) and
    the offset of the inner VESA mount.
    '''
    centres: float = 100
    offset: Tuple[float, float] = (0, 0)
    
    def offs(self) -> Tuple[float, float, float]:
        return self.offset + (0,)


@ad.shape
@ad.datatree
class VesaAdapter(ad.CompositeShape):
    '''
    A flat plate for adapting a VESA mount to a smaller VESA mount.
    '''
    outer_vesa_centres: float = 200
    inners: Tuple[VesaInnerSpec, ...] = (VesaInnerSpec(100, (0, -30)), 
                                         VesaInnerSpec(75, (0, -30)))
    
    t: float = ad.dtfield(8, doc='Thickness of the adapter')
    
    bsb_bevel_radius=ad.dtfield(10, doc='Plate bevel radius')
    bsb_size: tuple = ad.dtfield(
        doc='The (x,y,z) size of vesa adapter',
        self_default=lambda s: (
            s.outer_vesa_centres + s.bsb_bevel_radius * 2, 
            s.outer_vesa_centres + s.bsb_bevel_radius * 2, 
            s.t))
    bsb_node: ad.Node=ad.dtfield(ad.ShapeNode(BoxSideBevels, prefix='bsb_'))
    
    outer_screw_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: s.t)
    outer_screw_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.t)
    outer_screw_tap_shaft_dia_delta: float=0
    outer_screw_size_name: str="M6"
    outer_screw_head_depth_factor: float=1.1
    outer_screw_include_thru_shaft: bool=False
    outer_screw_as_solid: bool=False
    outer_screw_hole_node: ad.Node=ad.ShapeNode(
        CountersunkScrew, prefix='outer_screw_')
    screw_cage_size: tuple=ad.dtfield(
        self_default=lambda s: (
            s.outer_vesa_centres, 
            s.outer_vesa_centres, 
            s.t)) 
    outer_screw_cage_node: ad.Node=ad.ShapeNode(ad.Box, prefix='screw_cage_')
    
    
    tnut_node: ad.Node=ad.ShapeNode(Tnut, {})
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'top'),
        ad.surface_args('screw_cage', 'face_corner', 'top', 0),)

    def build(self) -> ad.Maker:
        shape = self.bsb_node()
        maker = shape.solid('adapter').at('centre')
        
        screw_cage = self.outer_screw_cage_node(self.screw_cage_size)
        maker.add_at(screw_cage.cage('screw_cage').at('centre'), 'centre')
        
        screw_shape = self.outer_screw_hole_node()
        
        for i in range(4):
            maker.add_at(
                screw_shape.composite(('outer_screw', i)).at('top'), 'screw_cage', 'face_corner', 'top', i)
        
        tnut_shape = self.tnut_node()
        for j, inner_spec in enumerate(self.inners):
            inner_size = (inner_spec.centres, inner_spec.centres, self.t)
            inner_cage = ad.Box(size=inner_size).cage(('inner_cage', j)).at('centre')
            maker.add_at(inner_cage, 'centre', post=ad.translate(inner_spec.offs()))

            for i in range(4):          
                tnut_maker = tnut_shape.hole(('tnut', j, i)).at('base')
                maker.add_at(tnut_maker, ('inner_cage', j), 'face_corner', 'base', i)
            
            
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
