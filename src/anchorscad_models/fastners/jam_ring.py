'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad


@ad.datatree
class JamRingPathBuilder:
    '''A simple example of a path builder.'''
    
    rs: float=ad.dtfield(7.8 / 2, doc='Radius of the small end (base)')
    rl: float=ad.dtfield(8.2 / 2, doc='Radius of the large end (top)')
    ro: float=ad.dtfield(14 / 2, doc='Radius of the outer surface')
    h: float=ad.dtfield(7, doc='Height of the jam ring')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((self.rs, 0))
                .line((self.rl, self.h), 'inner')
                .line((self.ro, self.h), 'top')
                .line((self.ro, 0), 'outer')
                .line((self.rs, 0), 'base')
                )
        
        return builder.build()


@ad.shape
@ad.datatree
class JamRing(ad.CompositeShape):
    '''
    <description>
    '''
    path_builder: ad.Node = ad.ShapeNode(JamRingPathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('extrusion').at()
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
