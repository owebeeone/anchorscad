'''
Created on 2024-06-06

@author: gianni
'''

import anchorscad as ad


@ad.datatree
class ParallelogramRoundedPath:
    '''Path for a parallelogram with rounded corners.
    
    Anchor names are:
     (arc, n) for the n-th arc
     (side, n) for the n-th side
     For n=(0, 1, 2, 3)
    '''

    l1: float=ad.dtfield(10, doc='Length 1 of the parallelogram')
    l2: float=ad.dtfield(20, doc='Length 2 of the parallelogram')

    r: float=ad.dtfield(4, doc='Radius of the rounded corners')
    degrees1: float=ad.dtfield(60, doc='Degrees of the first arc')
    degrees2: float=ad.dtfield(
        self_default=lambda s: 180 - s.degrees1, 
        doc='Degrees of the second arc')

    def build(self) -> ad.Path:
        '''Build the path.'''
        builder = (ad.PathBuilder()
                .move((0, 0), direction=(1, 0)))

        l = (self.l1, self.l2)
        degrees = (self.degrees1, self.degrees2)    
        for n in range(5):
            builder.arc_tangent_radius_sweep(
                radius=self.r, 
                sweep_angle_degrees=-degrees[n % 2], name=('arc', n))
            builder.stroke(l[n % 2], name=('side', n))
        
        return builder.build()


@ad.shape
@ad.datatree
class ParallelogramRounded(ad.CompositeShape):
    '''
    A parallelogram prism with rounded corners.
    '''
    path_builder: ad.Node = ad.ShapeNode(ParallelogramRoundedPath)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    h: float=ad.dtfield(5, doc='Height (thickness) of the parallelogram prism')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('prism').at()
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
