'''
Created on 26 Jan 2021

@author: gianni
'''

from dataclasses import dataclass

import anchorscad as ad


@ad.shape('anchorscad/models/basic/pipe')
@ad.datatree
class Pipe(ad.CompositeShape):
    '''
    A pipe.
    '''
    h: float
    inside_r: float
    outside_r: float
    hole_h_delta: float=0.01  # Prevents tearing in preview mode.
    fn: int=None
    fa: float=None
    fs: float=None
    
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
        params = ad.non_defaults_dict(self, include=('fn', 'fa', 'fs'))
        maker = ad.Cone(
            h=self.h, r_base=self.outside_r, r_top=self.outside_r, **params).solid(
            'outer').at('centre')
        
        self.set_maker(maker)
        
        maker.add_at(ad.Cone(
            h=self.h + self.hole_h_delta, r_base=self.inside_r, r_top=self.inside_r, **params).hole(
            'inner').at('centre'))

    @ad.anchor('inner surface anchor corrected so Z points away from surface.')
    def inner_surface(self, *args, **kwds):
        return self.maker.at('inner', 'surface', *args, **kwds) * ad.ROTX_180

if __name__ == '__main__':
    ad.anchorscad_main(False)