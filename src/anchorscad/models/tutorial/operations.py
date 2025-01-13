'''
Created on 31 July 2022

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class SquareSphereOperation(ad.CompositeShape):
    '''Example of a box and sphere with various compositions.
    '''
    size: tuple=ad.dtfield(
        default=(30, 30, 20),
        doc='The (x,y,z) size of the box')
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box), init=False)
    
    sphere_mode: ad.ModeShapeFrame=ad.dtfield(
        default=ad.ModeShapeFrame.SOLID,
        doc='Mode applied to sphere.'
        )
    
    r: tuple=ad.dtfield(
        default=15,
        doc='Sphere radius')
    sphere_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Sphere), init=False)
    
    overall_mode: ad.ModeShapeFrame=ad.dtfield(
        default=ad.ModeShapeFrame.SOLID,
        doc='Mode applied to whole.'
        )
    
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    EXAMPLES_EXTENDED={
        'intersection': ad.ExampleParams(
            shape_args=ad.args(
                sphere_mode=ad.ModeShapeFrame.SOLID,
                overall_mode=ad.ModeShapeFrame.INTERSECT),
            anchors=()),
        'hull': ad.ExampleParams(
            shape_args=ad.args(
                sphere_mode=ad.ModeShapeFrame.SOLID,
                overall_mode=ad.ModeShapeFrame.HULL),
            anchors=()),
        'hole': ad.ExampleParams(
            shape_args=ad.args(
                sphere_mode=ad.ModeShapeFrame.HOLE,
                overall_mode=ad.ModeShapeFrame.SOLID),
            anchors=()),
        'minkowski': ad.ExampleParams(
            shape_args=ad.args(
                sphere_mode=ad.ModeShapeFrame.SOLID,
                overall_mode=ad.ModeShapeFrame.MINKOWSKI,
                fn=32),
            anchors=())
        }

    def build(self) -> ad.Maker:
        box_shape = self.box_node()
        maker = box_shape.solid('box')\
            .colour((0.9, 0.1, 0.1, 1))\
            .at('centre')
        
        sphere_shape = self.sphere_node()
        
        # note named_shape(name, SOLID) is the same as .solid(name)
        sphere_maker = sphere_shape\
            .named_shape('sphere', self.sphere_mode)\
            .colour((0.1, 0.1, .8, 1))\
            .at('centre')
        
        maker.add_at(sphere_maker, 'face_corner', 'right', 2)
        
        return maker.named_shape('overall', self.overall_mode).at()


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
