
import anchorscad as ad
from anchorscad.fab.config.printers.printers import PrinterConfig
from anchorscad.fab.config.printers.prusa.fdm import Mk3


@ad.shape
@ad.datatree
class BuildVolume(ad.CompositeShape):
    '''Build volume model for a 3D printer'''
    
    printer: PrinterConfig = ad.dtfield(doc='Configuration for the printer')
    volume_colour: str = ad.dtfield(ad.Colour('aquamarine', 0.3), doc='Colour of the build volume')
    plate_depth: float = ad.dtfield(4, doc='Depth of the build plate in mm')
    plate_colour: str = ad.dtfield(ad.Colour('brown', 0.3), doc='Colour of the build plate')
    
    EXAMPLE_SHAPE_ARGS = ad.args(Mk3)
    
    EPSILON = 0.005  # To avoid Z-fighting
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.printer.size) \
            .solid('volume').transparent(True).colour(self.volume_colour).at()
            
        plate = ad.Box((self.printer.size[0], self.printer.size[1], self.plate_depth))
        maker.add_at(plate.solid('plate')
                     .transparent(True)
                     .colour(self.plate_colour)
                     .at('face_centre', 'top', post=ad.ROTX_180 * ad.tranZ(-self.EPSILON)), 
                     'volume', 'face_centre', 'base')
        
        return maker
    
    @ad.anchor('The default model origin is the center of the build volume')
    def model_origin(self) -> ad.GMatrix:
        return self.maker.at('face_centre', 'base')


@ad.shape
@ad.datatree
class BuildVolumeVisual(ad.CompositeShape):
    
    printer: PrinterConfig = ad.dtfield(doc='Configuration for the printer')
    build_volume: ad.Node = ad.dtfield(
        ad.ShapeNode(BuildVolume), doc='Build volume to render')
    
    model_to_render: ad.Shape = ad.dtfield(
        default_factory=lambda: ad.Cone.example()[0],
        doc='Shape to render in the build volume')
    
    EXAMPLE_SHAPE_ARGS = ad.args(Mk3, model_to_render=ad.Cone.example()[0])
    
    
    def build(self) -> ad.Maker:
        maker = self.build_volume().solid('volume').at()
        
        maker.add_at(self.model_to_render.solid('model').at('base'), 'model_origin')
        
        return maker
    
    
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == "__main__":
    ad.anchorscad_main()
    