'''
Created on 21 June 2022

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class HullExample(ad.CompositeShape):
    '''
    An example using OpenSCAD hull. 
    
    Note that no anchors are provided for the surface resulting from
    the generated hull surface.
    '''
    x: float=10
    y: float=20
    z: float=30
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.x, s.y, s.z))
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, 'size'), init=False)
    
    r: float=10
    sphere_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Sphere, 'r'), init=False)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args()
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
        hull_collection = shape.solid('box').at('centre')
        sphere = self.sphere_node()
        hull_collection.add_at(sphere.solid('sphere').at('centre'),
                     'face_centre', 'front')
        maker = hull_collection.hull('hull').at()
        return maker

    @ad.anchor('An example anchor')
    def example_anchor(self):
        return self.maker.at()


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
