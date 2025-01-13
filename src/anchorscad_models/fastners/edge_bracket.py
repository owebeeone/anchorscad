'''
Created on 2024-05-05

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.screws.holes import CountersinkSelfTapHole


@ad.datatree
class EdgeBracketPathBuilder:
    '''Edge bracket path builder.'''
    
    w: float=ad.dtfield(12, doc='Width of edge bracket')
    l: float=ad.dtfield(20, doc='Overall length of edge bracket')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((0, self.w / 2), direction=(1, 0))
                .arc_tangent_radius_sweep(self.w / 2, 180, name='base')
                .stroke(self.l - self.w, 0, name='right')
                .arc_tangent_radius_sweep(self.w / 2, 180, angle=180, name='top')
                .stroke(self.l - self.w, 0, name='left'))
 
                    
        return builder.build()


@ad.shape
@ad.datatree
class EdgeBracket(ad.CompositeShape):
    '''Bracket for holding a flat object at the edge. This specifically was designed
    to replace the plastic brackets that hold a mirror in place on a make-up table
    which had become brittle and needed replacement.
    '''
    path_builder: ad.Node = ad.ShapeNode(EdgeBracketPathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    tw: float=ad.dtfield(4, doc='Tab width')
    
    sr: float=ad.dtfield(self_default=lambda s: s.w / 2, doc='separator radius')
    sw: float=ad.dtfield(4, doc='separator width')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, 'path', {'h': 'tw'})
    
    cylinder_node: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'sr', 'h': 'sw'})
    
    screw_hole_len: float=ad.dtfield(
        self_default=lambda s: s.tw + s.sw - 0.01,
        doc='Overall screw length')
    screw_hole_thru_len: float=ad.dtfield(
        self_default=lambda s: s.tw + s.sw - 0.01)
    screw_hole_tap_len: float=ad.dtfield(
        self_default=lambda s: s.screw_hole_len - s.screw_hole_thru_len)
    
    screw_hole_outer_delta: float=1.9
    screw_hole_counter_sink_overlap: float=0.25
    screw_hole_dia: float=2.6
    screw_hole: ad.Node=ad.dtfield(ad.ShapeNode(CountersinkSelfTapHole, prefix='screw_hole_'))
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=(
        #ad.surface_args('base', 0),
    )

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('extrusion').at()
        
        separator = self.cylinder_node().solid('sepatator').at('base', rh=1)        
        maker.add_at(separator, 'centre_of', 'base')
        
        screw_hole = self.screw_hole().composite('screw_hole').at('top')
        maker.add_at(screw_hole, 'centre_of', 'base', rh=1, post=ad.ROTX_180)
        
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
