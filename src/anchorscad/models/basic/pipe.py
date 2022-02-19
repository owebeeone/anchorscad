'''
Created on 26 Jan 2021

@author: gianni
'''

from dataclasses import dataclass

from numpy.core.defchararray import center

import ParametricSolid.core as core
import ParametricSolid.linear as l


@core.shape('anchorscad/models/basic/pipe')
@dataclass
class Pipe(core.CompositeShape):
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
    
    EXAMPLE_SHAPE_ARGS=core.args(h=50, inside_r=6, outside_r=10)
    EXAMPLE_ANCHORS=(
        core.surface_args('top'),
        core.surface_args('base'),
        core.surface_args('surface', 50, 0),
        core.surface_args('inner_surface', 0, 45),
        )
    
    def __post_init__(self):
        assert self.outside_r > self.inside_r, (
            f'Inside radius ({self.inside_r}) must be smaller than outside ({self.outside_r}')
        params = core.non_defaults_dict(self, include=('fn', 'fa', 'fs'))
        maker = core.Cone(
            h=self.h, r_base=self.outside_r, r_top=self.outside_r, **params).solid(
            'outer').at('centre')
        
        self.maker = maker
        
        maker.add_at(core.Cone(
            h=self.h + self.hole_h_delta, r_base=self.inside_r, r_top=self.inside_r, **params).hole(
            'inner').at('centre'))

    @core.anchor('inner surface anchor corrected so Z points away from surface.')
    def inner_surface(self, *args, **kwds):
        return self.maker.at('inner', 'surface', *args, **kwds) * l.ROTX_180

if __name__ == '__main__':
    core.anchorscad_main(False)