'''
Created on 26 Jan 2021

@author: gianni
'''

from dataclasses import dataclass

import ParametricSolid.core as core
import ParametricSolid.linear as l
import anchorscad.models.basic.pipe as pipe
import numpy as np


@core.shape('anchorscad/models/screws/hole_tester')
@dataclass
class HoleTester(core.CompositeShape):
    '''A test model for screws. This creates a model with multiple holes with
    different sizes to allow for testing of screw interference with actual printed models.'''
    
    dia: float  # Screw hole diameter
    size_range: tuple=(0.05 / 2, 0.4 / 2)
    count: int=15
    block_size: tuple=(1, 1, 1.5)
    outer_dia_delta: float=4
    outer_stem_height: float=5
    text_size: float=8
    fn: int=None
    fa: float=None
    fs: float=None
    
    
    EXAMPLE_SHAPE_ARGS=core.args(2.00, 
                                 count=10, 
                                 outer_dia_delta=6, 
                                 size_range=(-0.0 / 2, 0.3 / 2),
                                 fn=64)
        
    def __post_init__(self):
        
        pipe_outer_r = self.dia / 2 + self.outer_dia_delta
        
        block_size = np.array(self.block_size) + np.array(
            [pipe_outer_r * 2 + self.text_size * 2, pipe_outer_r * 2, 0])
        
        swatch_size = block_size * np.array([1, self.count, 1])
        
        maker = core.Box(size=swatch_size).solid('substrate').at('centre')
        
        self.maker = maker
        params = core.non_defaults_dict(self, include=('fn', 'fa', 'fs'))
        fnparams = core.non_defaults_dict(self, include=('fn',))
        
        size_incr = (self.size_range[1] - self.size_range[0]) / (self.count - 1)
        for i in range(self.count):
            hole_size = self.dia / 2 + self.size_range[0] + i * size_incr
            pre = l.translate(block_size * np.array([0, i + 0.5, 0]))
            maker.add_at(
                pipe.Pipe(self.outer_stem_height, hole_size, pipe_outer_r / 2, **params)
                    .composite(('hole', i)).colour([0, 1, 0]).at('base'),
                'face_corner', 1, 2, pre=pre
                )
            maker.add_at(
                core.Text(f'{hole_size * 2:3.2f}', size=self.text_size, 
                          font='Ubuntu Mono:style=Bold', **fnparams
                          ).hole(('label', i)).colour([1, 0, 0]).at('default', 'front'),
                'face_corner', 4, 0, pre=pre * l.translate([0, -self.text_size /2, 0.01]))
        
    
    def render(self, renderer):
        return self.maker.render(renderer)


if __name__ == "__main__":
    core.anchorscad_main(False)
