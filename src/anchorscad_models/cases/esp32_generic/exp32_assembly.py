
import anchorscad as ad
from anchorscad_models.cases.esp32_generic.esp32_outline import Esp32Outline
from anchorscad_models.cases.esp32_generic.prototype_pcb import PrototypePcbOutline
from anchorscad_models.components.switches.tactile_tl1105 import TactileSwitchTL59





@ad.shape
@ad.datatree
class Exp32Assembly(ad.CompositeShape):

    esp32_outline_node: ad.Node[Esp32Outline]=ad.ShapeNode(Esp32Outline, prefix='esp32_')
    pcb_outline_node: ad.Node[PrototypePcbOutline]=ad.ShapeNode(PrototypePcbOutline, prefix='pcb_')
    tactile_switch_node: ad.Node[TactileSwitchTL59]=ad.ShapeNode(TactileSwitchTL59, prefix='tactile_switch_')
    
    fn: int=32
    
    EXAMPLE_ANCHORS=(ad.surface_args('mount_hole', 0, 'base'),)
    
    def build(self) -> ad.Maker:
        
        pcb_outline = self.pcb_outline_node()
        
        maker = pcb_outline.solid('pcb').at('face_centre', 'base', post=ad.ROTX_180)
        
        esp32_outline = self.esp32_outline_node()
        
        maker.add_at(
            esp32_outline.solid('esp32').at('face_corner', 'front', 0),
            'face_corner', 'front', 0, pre=ad.translate([7.41 - 0.19, 4.85 - 7.74, 12.53])
            )
        
        tactile_switch = self.tactile_switch_node()
        
        for i in range(3):
            offs = 10.1 + i * 2.54 * 3
            maker.add_at(
                tactile_switch.solid(('tactile_switch', i)).at('face_corner', 'base', 1),
                'face_corner', 'base', 2, 
                post=ad.translate((2.6, offs, 0)) * ad.ROTZ_90 * ad.ROTX_180
                )
        
        return maker
        
    @ad.anchor('PCB mounting hole.')
    def mount_hole(self, corner: int, *args, **kwargs):
        return self.maker.at('pcb', ('mount_hole', corner), *args, **kwargs)

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)    

if __name__ == "__main__":
    ad.anchorscad_main()
