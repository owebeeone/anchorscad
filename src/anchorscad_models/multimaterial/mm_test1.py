'''
Created on 2023-10-19

@author: gianni
'''

import anchorscad as ad
from typing import Tuple


@ad.shape
@ad.datatree
class MultiMaterialTest(ad.CompositeShape):
    '''
    A basic multi-material test shape.
    '''
    h: float=50
    r_top: float=20
    r_base: float=30
    
    extensions: Tuple[float, ...]=(10, 20, 30, 40)
    overlap: float=2

    cone_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cone))
    
    EXAMPLE_SHAPE_ARGS=ad.args(60, 10, 40, fn=64)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.cone_node()
        maker = shape.hole('master').at('base', post=ad.IDENTITY)
        
        for i in range(len(self.extensions) - 1):
            ext = self.extensions[i]
            next_ext = self.extensions[i+1]
            h = next_ext - ext
            m = (self.r_top - self.r_base) / self.h
            r_base = ext * m + self.r_base
            r_top = next_ext * m + self.r_base + self.overlap
            shape = self.cone_node(h=h, r_top=r_top, r_base=r_base)
            g = (1 + i) / len(self.extensions)
            maker2 = shape.solid(('ext', i))\
                .part(ad.Part(f"part{i // 2}", i))\
                .material(ad.Material(f"mat{i}"))\
                .colour((1, g, 0.2, 0.7))\
                .at('base', post=ad.ROTX_180)
            maker.add_at(maker2, 'base', post=ad.ROTX_180*ad.tranZ(ext))
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
