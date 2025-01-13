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
    angle: float | ad.Angle=ad.dtfield(60,
        doc='Degrees of the first arc, the adjacent arcs are 180 - degrees')
    angle2: ad.Angle=ad.dtfield(
        self_default=lambda s: ad.angle(180) - ad.angle(s.angle), 
        doc='Degrees of the second arc')

    def build(self) -> ad.Path:
        '''Build the path.'''
        builder = (ad.PathBuilder()
                .move((0, 0), direction=(1, 0)))

        lx = (self.l1, self.l2)
        angles = (ad.angle(self.angle), self.angle2)    
        for n in range(4):
            builder.arc_tangent_radius_sweep(
                radius=self.r, 
                sweep_angle=-angles[n % 2], name=('arc', n))
            builder.stroke(lx[n % 2], name=('side', n))
        
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
    EXAMPLE_ANCHORS=(ad.surface_args('centre', rh=0),
                     ad.surface_args('centre', t=0.1, rh=1, ry=0.1),)

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('prism').at()
        return maker

    @ad.anchor('Centre of the model with relative adjustments.')
    def centre(self, t=0.5, rh=0.5, ry=0.5) -> ad.GMatrix:
        '''Anchor for the centre of the model.
        Args:
            t: The t (default 0.5) for the "side" of edge1, 0 is left, 1 is right.
            rh: The relative height (default 0.5) 0 is the top, 1 is the base.
            ry: The relative y position (default 0.5) 0 is the front, 1 is the back.
        '''
        s1 : ad.GMatrix = self.maker.at(('side', 1), t, rh=rh) * ad.ROTX_90
        v1 : ad.GVector = s1.get_translation()
        s3 : ad.GMatrix = self.maker.at(('side', 3), 1 - t, rh=rh) * ad.ROTX_270
        v3 : ad.GVector = s3.get_translation()
        # The centre of the top face is the average of the two vectors
        c : ad.GVector = v1 * (1 - ry) + v3 * ry
        mat = s1.A
        for i in range(4):
            mat[i, 3] = c[i]
        return ad.GMatrix(mat)

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
