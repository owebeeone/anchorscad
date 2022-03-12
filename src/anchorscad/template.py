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
    
    size: tuple=ad.dtfield((1, 2, 3), 'The (x,y,z) size of ShapeName')
    
    EXAMPLE_SHAPE_ARGS=ad.args(size=(10, 20, 30))
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'top'),)

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
    ad.anchorscad_main()
