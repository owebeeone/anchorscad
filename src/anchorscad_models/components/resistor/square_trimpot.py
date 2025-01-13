'''
Created on 25-Sep-2024

@author: gianni
'''

import anchorscad as ad

@ad.datatree
class Bourns3296Sytle:
    adj_anchor: tuple
    base_anchor: tuple
    base_offset: callable

TRIMPOT_STYLE: dict[Bourns3296Sytle]={
    'W': Bourns3296Sytle(
        adj_anchor=ad.args(
            'front', 
            1, 
            post=ad.translate((-1.27, 1.27, 0))),
        base_anchor=ad.args('foot-left', 0),
        base_offset=lambda s: (s.w / 2, s.h / 2, 0)
        ),
    # TODO: Add the other styles
    # 'P': Bourns3296Sytle(None, None, None),
    # 'X': Bourns3296Sytle(None, None, None)
}


@ad.datatree
class Bourns3296Path:
    '''A Bourns 3296 square trimpot cross section path.'''

    w: float=9.53
    d: float=10.03
    tw: float=0.5
    
    def build(self) -> ad.Path:
        
        return (
            ad.PathBuilder()
            .move((0, 0))
            .line((self.w, 0), 'front')
            .line((self.w, self.d), 'left')
            .line((self.w - self.tw, self.d), 'foot-left')
            .line((self.w - self.tw, self.d - self.tw), 'foot-side-left')
            .line((self.tw, self.d - self.tw), 'base')
            .line((self.tw, self.d), 'foot-side-right')
            .line((0, self.d), 'foot-right')
            .line((0, 0), 'right')
        ).build()


@ad.shape
@ad.datatree(frozen=True)
class Bourns3296(ad.CompositeShape):
    '''A Bourns 3296 square trimpot.'''

    variant: str='W'
    
    path_builder_node: ad.Node=ad.ShapeNode(Bourns3296Path)
    path: ad.Path=ad.dtfield(
        self_default=lambda s: s.path_builder_node().build(),
        doc='The path of the trimpot cross section')
    
    h: float=4.83
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    adj_h: float=1.52
    adj_r: float=2.19 / 2
    adj_cyl_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='adj_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=(ad.surface_args('mount_base', scale_anchor=0.5),)

    def build(self) -> ad.Maker:
        style_data: Bourns3296Sytle = TRIMPOT_STYLE[self.variant]
        
        shape = self.extrude_node()
        maker = shape.solid('trimpot').at(args=style_data.base_anchor, post=ad.ROTX_180)
        
        adj_shape = self.adj_cyl_node()
        maker.add_at(adj_shape.solid('adj').at('base', post=ad.ROTX_180), 
                     args=style_data.adj_anchor)
        return maker

    @ad.anchor('mount base of the trimpot')
    def mount_base(self):
        style_data: Bourns3296Sytle = TRIMPOT_STYLE[self.variant]
        return self.maker.at(
            *style_data.base_anchor[0], 
            **style_data.base_anchor[1]) * ad.translate(style_data.base_offset(self))

    @ad.anchor('mount corner of the trimpot')
    def mount_corner(self):
        style_data: Bourns3296Sytle = TRIMPOT_STYLE[self.variant]
        return self.maker.at(
            *style_data.base_anchor[0], 
            **style_data.base_anchor[1])


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
