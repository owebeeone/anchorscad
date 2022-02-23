'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad


@ad.shape('${file}/ShapeName')
@ad.datatree
class ShapeName(ad.CompositeShape):
    '''
    <description>
    '''
    
    size: tuple=(1, 2, 3)
    
    EXAMPLE_SHAPE_ARGS=ad.args()

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = ad.Box(self.size)
        maker = shape.solid('box').at('face_corner', 'front', 0)
        return maker

    @ad.anchor('An example anchor')
    def example_anchor(self):
        return self.maker.at()


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
#MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main(False)
