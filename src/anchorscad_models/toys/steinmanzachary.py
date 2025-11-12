'''
Created on 2025-07-09

@author: gianni

A reddit/openSCAD challenge.
'''

import anchorscad as ad

@ad.datatree
class Sqaure(ad.CompositeShape):
    '''
    A box.
    '''
    w: float=5
    h: float=20
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                   .move((0, 0))
                   .line((0, self.h), 'left')
                   .line((self.w, self.h), 'top')
                   .line((self.w, 0), 'right')
                   .line((0, 0), 'bottom')
                   .build())
        return builder

@ad.shape
@ad.datatree
class ShapeName(ad.CompositeShape):
    '''
    <description>
    '''
    r: float=30

    square_node: ad.ShapeNode[Sqaure]
    square_path: ad.Path=ad.dtfield(self_default=lambda s: s.square_node())
    
    lin_ext_node: ad.ShapeNode[ad.LinearExtrude] = ad.dtfield(
        ad.ShapeNode(ad.LinearExtrude, prefix='lin_ext_'))
    

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.box_node()
        maker = shape.solid('box').at('centre')
        return maker

    @ad.anchor('An example anchor')
    def example_anchor(self):
        return self.maker.at()


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
