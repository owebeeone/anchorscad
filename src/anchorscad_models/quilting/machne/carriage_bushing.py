'''
Created on 2025-01-01

@author: gianni
'''

import anchorscad as ad

from anchorscad_models.basic.box_side_bevels import BoxSideBevels

@ad.datatree
class HoleWithBevels:
    '''A simple example of a path builder.'''
    
    r_inner: float=ad.dtfield(22 / 2, doc='Inner radius of the hole.')
    r_outer: float=ad.dtfield(25 / 2, doc='Outer radius of the hole with bevels.')
    b_depth: float=ad.dtfield(3, doc='Depth of the bevels.')
    h: float=ad.dtfield(40, doc='Height of the hole.')
    epsilon: float=ad.dtfield(0.01, doc='Epsilon for the size.')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((0, -self.epsilon / 2))
                .line((self.r_outer, -self.epsilon / 2), 'base')
                .line((self.r_inner, self.b_depth), 'base_bevel')
                .relative_line((0, self.h - self.b_depth * 2), 'surface')
                .line((self.r_outer, self.h + self.epsilon / 2), 'top_bevel')
                .relative_line((-self.r_outer, 0), 'top')
                .line((0, -self.epsilon / 2), 'centre'))

        return builder.build()



@ad.shape
@ad.datatree
class CarriageBushing(ad.CompositeShape):
    '''
    Carriage bushing for the Gammill quilting machine.
    '''
    w: float=ad.dtfield(34.2, doc='width of the bushing block.')
    h: float=ad.dtfield(30, doc='Length of the bushing block.')  # noqa: E741
    r: float=ad.dtfield(21.9 / 2, doc='Radius of the bushing hole.')
    bevel_radius: float=ad.dtfield(4, doc='Radius of the bevels on the bushing block.')
    
    
    # Builds a tuple from the x, y, z fields.
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of CarriageBushing machine block.',
        self_default=lambda s: (s.w, s.w, s.h))
    
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(BoxSideBevels))
    
    hole_path_node: ad.Node=ad.dtfield(ad.ShapeNode(HoleWithBevels))
    hole_path: ad.Path=ad.dtfield(self_default=lambda s: s.hole_path_node().build())
    hole_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.RotateExtrude, {'path': 'hole_path'}))
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=256)
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'top'),)
    
    EXAMPLES_EXTENDED={
        'test': ad.ExampleParams(
            shape_args=ad.args(h=10, fn=256))
    }

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.box_node()
        maker = shape.solid('block').transparent(False).at('face_centre', 'base', 0, post=ad.ROTX_180)
        
        hole_shape = self.hole_node()
        maker.add_at(hole_shape.hole('hole').at('top', 1, post=ad.tranZ(-self.epsilon / 2)), 'face_centre', 'top')
        
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
