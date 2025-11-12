'''
Created on 15-May-2025

@author: gianni
'''

import anchorscad as ad


@ad.datatree
class ExtensionPath:
    w: float=5.8
    d: float=2.2

    def build(self) -> ad.Path:
        
        path = (ad.PathBuilder()
                .move((0, 0))
                .line((-self.w / 2, 0), "lbase")
                .spline(((-self.w / 2, 1), (self.w / 2, 1), (self.w / 2, 0)),
                        cv_len=(3, 3))
                .line((0, 0), "rbase")
                .build())
        return path

@ad.shape
@ad.datatree
class CE156F18Punchdown(ad.CompositeShape):
    '''
    A punchdown tool for a CE156F18 connector.
    '''
    w: float=5.95
    d: float=2.2
    h: float=7
    
    lex_h: float=100
    
    size: tuple=ad.dtfield(
        self_default=lambda s: (s.w, s.d, s.d + s.lex_h))
    main_node: ad.ShapeNode[ad.Box]
    
    extension_path_node: ad.ShapeNode[ExtensionPath]
    lex_path: ad.Path=ad.dtfield(self_default=lambda s: s.extension_path_node().build())
    lex_scale: tuple[float, float]=(15 / 5.8, 15 / 2.2)
    lex_node: ad.ShapeNode[ad.LinearExtrude] = ad.ShapeNode(ad.LinearExtrude, prefix="lex_")
    
    slit_w: float=0.6
    slit_h: float=2.33
    
    slit_size: tuple=ad.dtfield(self_default=lambda s: (s.slit_w, s.d, s.slit_h))
    slit_node: ad.ShapeNode[ad.Box] = ad.ShapeNode(prefix='slit_')
    
    slit_pos: tuple[float, ...] = (1.85, 3.90)
    
    notch_size: tuple[float, ...] = ad.dtfield(self_default=lambda s : 
        (s.slit_pos[1] - s.slit_pos[0], 0.5, s.h))
    
    notch_node: ad.ShapeNode[ad.Box] = ad.ShapeNode(prefix='notch_')
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.main_node()
        maker = shape.solid('box').at('centre')
        
        ext_shape = self.lex_node()
        ext_maker = ext_shape.solid("handle").at("lbase")
        maker.add_at(ext_maker, "face_edge", "front", 0, post=ad.ROTY_180 * ad.tranY(self.h))
        
        slit_shape = self.slit_node()
        
        for i, pos in enumerate(self.slit_pos):
            slit_maker = slit_shape.hole(('slit', i)).colour("red", 0.3 * (i + 1)).at('face_corner', 'front', 0)
            maker.add_at(slit_maker, 'face_corner', 'front', 0, post=ad.tranX(pos))
            
        notch_shape = self.notch_node()
        
        maker.add_at(
            notch_shape.hole('notch').at('face_corner', 'front', 0),
            ('slit', 0), 'face_corner', 'back', 0
        )
        
        return maker

    @ad.anchor('An example anchor')
    def example_anchor(self):
        return self.maker.at()


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
