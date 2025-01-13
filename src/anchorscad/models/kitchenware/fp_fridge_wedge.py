'''
Created on 2024-05-05

@author: gianni

The Fisher Paykel RF605QDVX2 refridgerator has a short shelf that has a lip 
at the rear. When placing containers that are longer than the shelf, they 
can't easily be pushed all the way to the rear unless they are lifted over
rear lip. This model makes a wedge that clips to the rear of the shelf to
allow the sliding of containers that are longer than the shelf all the way
to the rear. The container also has a foot that causes it to catch on the
rear lip. The wedge has a chamfered rear edge to allow the container to slide
over the rear lip as well.
'''

import anchorscad as ad
import numpy as np


@ad.datatree
class FisherPaykelWedgePathBuilder:
    '''Path builder for the Fisher Paykel wedge.'''
    
    d: float=ad.dtfield(80, doc='Depth of the wedge.')
    h1: float=ad.dtfield(2, doc='Height of first lip')
    d1: float=ad.dtfield(20, doc='Depth of first lip')
    h2: float=ad.dtfield(10, doc='Height of second lip')
    r2: float=ad.dtfield(2, doc='Radius of second lip')
    d2: float=ad.dtfield(5.5, doc='Depth of second lip')
    he: float=ad.dtfield(2, doc='Height of outer edge')
    de: float=ad.dtfield(1.25, doc='Height of outer edge')
    lh: float=ad.dtfield(2, doc='Lip height')
    lw: float=ad.dtfield(3.25, doc='Lip width')
    rh: float=ad.dtfield(14, doc='Rear height')
    c1: float=ad.dtfield(6, doc='Chamfer of the rear edge')
    
    def build(self) -> ad.Path:
        
        chamfer = np.array((self.c1, self.c1/2))
        normalized_chamfer = chamfer / np.linalg.norm(chamfer)
        builder = (ad.PathBuilder()
                .move((0, 0), direction=(0, -1))
                .line(-chamfer, name='rear_chamfer')
                .stroke(self.rh - self.c1, angle=ad.angle(sinr_cosr=normalized_chamfer), name='rear')
                .stroke(self.lw, 90, name='rear_lip')
                .stroke(self.lh, 90, name='rear_inner_lip')
                .stroke(self.de, 90, name='rear_inner_upper_lip')
                .stroke(self.he, -90, name='rear_inner')
                .stroke(self.d2, -90, name='inner_upper_lip')
                .stroke(self.h2 - self.r2, -90, name='inner_front_lip')
                .arc_tangent_radius_sweep(self.r2, 90, side=1, name='inner_front_corner')
                .stroke(self.d1 - self.r2, 0, name='upper_lip')
                .stroke(self.h1, -90, name='outer_edge')
                .stroke(self.d, 90, name='wedge_base')
                .line((0, 0), name='wedge_top'))
                    
        return builder.build()


@ad.shape
@ad.datatree
class FisherPaykelWedge(ad.CompositeShape):
    '''The Fisher Paykel RF605QDVX2 refridgerator has a short shelf. This model
    makes a wedge that clips to the rear of the shelf to allow the sliding of
    containers that are longer than the shelf to allow them slide above the 
    lip.'''
    
    path_builder: ad.Node = ad.ShapeNode(FisherPaykelWedgePathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    w: float=ad.dtfield(35, doc='Wedge width')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, 'path', {'h': 'w'})

    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=(
        ad.surface_args('inner_front_corner', 0.5),
    )

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('extrusion').at()        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
