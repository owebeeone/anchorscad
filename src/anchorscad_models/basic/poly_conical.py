'''
Created on 7 Aug 2022

@author: gianni
'''

from numpy import kaiser
import anchorscad as ad


@ad.datatree(frozen=True)
class Segment:
    '''Defines a segment of the PolyConical shape.'''
    r: float=ad.dtfield(doc='Radius of segment')
    h: float=ad.dtfield(0, doc='Height of segment')
    name: object=ad.dtfield(None, doc='optional name of segment')
    
    def nameof(self, i):
        if self.name is None:
            return ('segment', i)
        else:
            return self.name

def segmentsToPolyConicalPath(segments: tuple):
    builder = ad.PathBuilder().move((0, 0), direction=(1, 0))
    last_h = 0
    last_name = 'base_segment'
    for i, s in enumerate(segments):
        builder.line((s.r, last_h), last_name)
        last_h -= s.h
        last_name = s.nameof(i)
    
    builder.line((0, last_h), 'top_segment')
    
    return builder.build()


@ad.shape
@ad.datatree(frozen=True)
class PolyConical(ad.CompositeShape):
    '''A circular polycone shape. The segments are defined by
    a tuple of Segment objects.
    '''
    segments: tuple=ad.dtfield(doc='Tuple of Segments defining shape')
    path: ad.Path=ad.dtfield(
        self_default=lambda s:
            segmentsToPolyConicalPath(s.segments),
        doc='Path of shape')
    
    extrude_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.RotateExtrude),
        init=False)

    EXAMPLE_SHAPE_ARGS=ad.args(segments=(Segment(10, 10), Segment(20, 10), Segment(10, 10), Segment(20)))
    EXAMPLE_ANCHORS=(ad.surface_args('base'),
                     ad.surface_args('top'),
                     ad.surface_args('surface', 2, 0.5),)

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.extrude_node()
        maker = shape.solid('poly_cone').at('base_segment', 0)
        return maker

    @ad.anchor('Base of the shape')
    def base(self):
        return self.maker.at('base_segment', 0) * ad.ROTY_180
    
    @ad.anchor('Top of the shape')
    def top(self):
        return self.maker.at('top_segment', 1) * ad.ROTY_180
    
    @ad.anchor('Surface of the shape')
    def surface(self, index, t=0, **kwargs):
        segment = self.segments[index]
        name = segment.nameof(index)
        return self.maker.at(name, t, **kwargs) * ad.ROTY_180

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
