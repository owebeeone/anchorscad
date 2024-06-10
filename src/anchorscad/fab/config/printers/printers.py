

from typing import Tuple
import anchorscad as ad


@ad.datatree
class PrinterConfig:
    '''Configuration for a 3D printer'''
    
    size: Tuple[float, float, float] = ad.dtfield(doc='Size of the build volume in mm')
    printer_origin: ad.GMatrix = ad.dtfield(ad.IDENTITY, 
        doc='Origin of the build volume in mm') 
    model_origin: ad.GMatrix = ad.dtfield(
        self_default=lambda s: s.printer_origin * ad.translate((ad.GVector(s.size) / 2)), 
        doc='The default model origin is the center of the build volume')

