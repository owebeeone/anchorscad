'''
Created on 27-Sep-2024

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.regular_prism import RegularPrism

@ad.shape
@ad.datatree
class HeaderPin(ad.CompositeShape):

    l: float=11.25  # noqa: E741
    w: float=0.64
    taper_l: float=0.65
    
    mid_l: float=ad.dtfield(self_default=lambda s: s.l - 2 * s.taper_l)
    nsides: int=ad.dtfield(4, init=False)
    mid_node: ad.Node=ad.ShapeNode(
        RegularPrism, {'side_l': 'w', 'h': 'mid_l'}, 'nsides')
    
    scale: tuple=ad.dtfield((0.6, 0.6), init=False)
    end_node: ad.Node=ad.ShapeNode(
        RegularPrism, {'side_l': 'w', 'h': 'taper_l'}, 'nsides', 'scale')
    
    EXAMPLE_ANCHORS=(ad.surface_args('base', scale_anchor=0.1),
                     ad.surface_args('top', scale_anchor=0.1),
                     ad.surface_args('centre', scale_anchor=0.1),
                     ad.surface_args('side', 0, rh=0.5, scale_anchor=0.1),
                     ad.surface_args('side', 3, rh=0.5, scale_anchor=0.1),)
    
    def build(self) -> ad.Maker:
        
        mid_shape_cage = self.mid_node(h=self.l)
        
        maker = mid_shape_cage.cage('cage').transparent(True).at('centre', align=0)
        
        mid_shape = self.mid_node()
        mid_shape_maker = mid_shape.solid('mid').at('centre', align=0)
        maker.add_at(mid_shape_maker, 'centre', align=0)
        
        end_shape = self.end_node()
        top_end = end_shape.solid('upper').at('base', align=0, post=ad.ROTX_180)
        maker.add_at(top_end, 'mid', 'top', align=0)
        
        base_end = end_shape.solid('lower').at('base', align=0, post=ad.ROTX_180)
        maker.add_at(base_end, 'mid', 'base', align=0)
        
        return maker
    
    @ad.anchor('Top of pin')
    def top(self) -> ad.GMatrix:
        return self.maker.at('top', align=0)
    
    @ad.anchor('Base of pin')
    def base(self) -> ad.GMatrix:
        return self.maker.at('base', align=0)
    

@ad.shape
@ad.datatree
class HeaderBase(ad.CompositeShape):

    pitch: float=2.54
    w: float=2.54
    h: float=2.5
    c: float=0.25
    
    path: ad.Path=ad.dtfield(
        self_default=lambda s: ad.PathBuilder()
                .move((0, s.c))
                .line((s.c, 0), 'front-right-chamfer')
                .line((s.w - s.c, 0), 'right')
                .line((s.w, s.c), 'back-right-chamfer')
                .line((s.w, s.pitch - s.c), 'back')
                .line((s.w - s.c, s.pitch), 'back-left-chamfer')
                .line((s.c, s.pitch), 'left')
                .line((0, s.pitch - s.c), 'front-left-chamfer')
                .line((0, s.c), 'front')
                .build(),
        doc='The path of the base of the header')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    def build(self) -> ad.Maker:
        return self.extrude_node().solid('base').at()
    
    @ad.anchor('Centre of header')
    def centre(self) -> ad.GMatrix:
        return ad.translate((self.w / 2, self.pitch / 2, self.h / 2))
    
    @ad.anchor('Top of header')
    def top(self) -> ad.GMatrix:
        return ad.translate((self.w / 2, self.pitch / 2, self.h))
    
    @ad.anchor('Base of header')
    def base(self) -> ad.GMatrix:
        return ad.translate((self.w / 2, self.pitch / 2, 0)) * ad.ROTX_180
    

    
@ad.shape
@ad.datatree
class Header(ad.CompositeShape):
    '''A standard PCB header'''
    pitch: float=2.54
    solder_side_l: float=3
    pins_x: int=2
    pins_y: int=3
    
    pin_node: ad.Node=ad.ShapeNode(HeaderPin)
    base_node: ad.Node=ad.ShapeNode(
        HeaderBase, {'pitch': 'pitch'}, prefix='base_', expose_all=True)
    
    cage_size: tuple=ad.dtfield(
        self_default=lambda s: (s.pins_x * s.pitch, s.pins_y * s.pitch, s.base_h))

    cage_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(pins_x=2, pins_y=3)
    EXAMPLE_ANCHORS=(ad.surface_args(('pin', 1, 1), 'base', scale_anchor=0.3),)

    def build(self) -> ad.Maker:
        pin_shape = self.pin_node()
        base_shape = self.base_node()
        
        base_shape_maker = base_shape.solid('base').at('base')
        pin_shape_maker = pin_shape.solid('pin').at('base', post=ad.tranZ(-self.solder_side_l))
        
        base_shape_maker.add_at(pin_shape_maker, 'base')
        
        cage_shape = self.cage_node() 
        maker = cage_shape.cage('cage').at('face_centre', 'base', post=ad.ROTX_180)
        for nx in range(self.pins_x):
            x = self.pins_x - nx
            for y in range(1, self.pins_y + 1):
                pin_xy = base_shape_maker.solid(('pin', x, y)).at('base')
                maker.add_at(pin_xy, 
                             'face_corner', 'right', 1,
                             post=ad.ROTY_270 
                                * ad.translate(
                                    (-(nx + 0.5) * self.pitch, 
                                     (y - 0.5) * self.pitch, 
                                     0)))
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
