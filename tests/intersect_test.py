'''
Created on 12 Jul 2022
@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class SomeTestShape(ad.CompositeShape):
    '''
    <description>
    '''
    
    sphere_node: ad.Node=ad.ShapeNode(ad.Sphere)
    
    EXAMPLE_SHAPE_ARGS=ad.args(r=50)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.sphere_node()
        maker = shape.solid('sphere').at('centre')
        
        return maker

    
@ad.shape
@ad.datatree
class IntersectShape(ad.CompositeShape):
    '''
    <description>
    '''
    
    size: tuple=(10, 10, 10)
    box_node: ad.Node=ad.ShapeNode(ad.Box)
    test_node: ad.Node=ad.ShapeNode(SomeTestShape)
    as_hole: bool=True
    
    _GEN_TEST_ARGS = lambda as_hole: \
        ad.args(size=(30, 30, 30), r=20, as_hole=as_hole)

    EXAMPLE_SHAPE_ARGS=_GEN_TEST_ARGS(False)
    EXAMPLE_ANCHORS=()
    EXAMPLES_EXTENDED={
        'example2': ad.ExampleParams(
            shape_args=_GEN_TEST_ARGS(True))}


    def build(self) -> ad.Maker:
        return ad.make_intersection_or_hole( 
            self.as_hole,
            self.test_node(),
            ad.surface_args('centre'),
            self.box_node(),
            ad.surface_args('face_corner', 'front', 0),
            name='foo')


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=False)

if __name__ == "__main__":
    ad.anchorscad_main()