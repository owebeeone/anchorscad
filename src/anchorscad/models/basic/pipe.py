'''
A circular pipe with a hole shape in the centre.

Created on 26 Jan 2021

@author: gianni
'''

import anchorscad as ad


@ad.shape('anchorscad/models/basic/pipe')
@ad.datatree
class Pipe(ad.CompositeShape):
    '''
    A pipe. Inner hollow part is a hole.
    '''
    h: float
    inside_r: float
    outside_r: float
    inside_cyl_node: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'inside_r'})
    outside_cyl_node: ad.Node=ad.ShapeNode(ad.Cylinder, 'h', {'r': 'outside_r'})
    hole_h_delta: float=0.01  # Prevents tearing in preview mode.
    
    EXAMPLE_SHAPE_ARGS=ad.args(h=50, inside_r=6, outside_r=10)
    EXAMPLE_ANCHORS=(
        ad.surface_args('top'),
        ad.surface_args('base'),
        ad.surface_args('surface', 50, 0),
        ad.surface_args('inner_surface', 0, 45),
        )
    
    def __post_init__(self):
        assert self.outside_r > self.inside_r, (
            f'Inside radius ({self.inside_r}) must be smaller than outside ({self.outside_r}')
        maker = self.outside_cyl_node().solid('outer').at('centre')
        
        maker.add(self.inside_cyl_node(
            h=self.h + self.hole_h_delta).hole('inner').at('centre'))
        
        self.set_maker(maker)

    @ad.anchor('inner surface anchor')
    def inner_surface(self, *args, **kwds):
        '''Inner surface anchor with corrected Z points away from surface.'''
        return self.maker.at('inner', 'surface', *args, **kwds) * ad.ROTX_180


if __name__ == '__main__':
    ad.anchorscad_main(False)