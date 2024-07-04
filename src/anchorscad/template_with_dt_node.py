'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class ShapeName(ad.CompositeShape):
    '''
    <description>
    '''
    x: float=10
    y: float=20
    z: float=30
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.x, s.y, s.z))
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, 'size'))
    
    EXAMPLE_SHAPE_ARGS=ad.args(x=40, y=40, z=40)
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'top'),
        ad.surface_args('face_centre', 'base'),
        ad.surface_args('face_centre', 'front'),
        ad.surface_args('face_centre', 'back'),
        ad.surface_args('face_centre', 'left'),
        ad.surface_args('face_centre', 'right'),)

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
