'''
Created on 16 Nov 2021

@author: gianni
'''

from dataclasses import dataclass
import ParametricSolid.core as core
import ParametricSolid.extrude as e
import ParametricSolid.linear as l
import numpy as np

MAX_SCALED = np.array((135 * 2, 123.665, 1.45))
MAX_ACTUAL = np.array((22.75, 10.42, 1.45))

@core.shape('anchorscad/models/clips/lace_clip/LaceClip')
@dataclass
class LaceClip(core.CompositeShape):
    '''A clip for holding shoe laces when using magnetic shoe lace ties. 
    '''
    
    size: np.ndarray=MAX_ACTUAL
    scaled_size: np.ndarray=MAX_SCALED
    dia: float=2.75
    fn: int=32
    
    EXAMPLE_SHAPE_ARGS=core.args()
    
    
    def __post_init__(self):
        shape = core.Box(self.size)
        self.maker = (shape.cage('cage')
                      .transparent(True)
                      .colour([0, 1, 0, 0.4])
                      .at('face_corner', 0, 0))
        maker = self.maker
        
        y = self.scaled_size[1] / 2
        x = self.scaled_size[0] / 2
        path = (e.PathBuilder()
                .move((0, 0))
                .line((0, 44), 'centre_upper')
                .line((8, 44), 'upper_1')
                .line((32, y), 'upper_2')
                .line((100, y - 4.5), 'upper_3')
                .spline(
                    ((x, 1 + y - 30), (x, y - 30)),
                     cv_len=(20, 10), name='upper_5')
                .spline(
                    ((129, y - 48), (116, y - 60)),
                     cv_len=(10, 10), name='side_1')
                .line((53, y - 42.3), 'side_2')
                .arc_points_radius((68, y - 59.2), 
                                   36.7 / 2, 
                                   is_left=False, 
                                   name='hole')
                
                .line((109, y - 71), 'side_3')
                .spline(
                    ((119.6, y - 72.6), (130, y - 91)),
                     cv_len=(10, 10), name='side_4')
                .spline(
                    ((x, 1 + y - 105), (x, y - 105)),
                     cv_len=(5, 5), name='side_5')
                .spline(
                    ((108, -y), (107, -y)),
                     cv_len=(20, 5), name='side_6')
                .line((37, -y), 'lower_1')
                .line((8, -44), 'lower_2')
                .line((0, -44), 'lower_3')
                .line((0, 0), 'centre_lower')
                .build())
        
        scale = self.size / self.scaled_size
        path = path.transform(l.scale((scale[0], scale[0], 1)))
        
        shape = e.LinearExtrude(path, self.size[2], fn=self.fn)
        
        maker.add_at(shape.solid('rhs').at('centre_upper', rh=0.5),
                     'centre', post=l.ROTZ_90 * l.ROTX_90)
        maker.add_at(shape.solid('lhs').at('centre_upper', rh=0.5),
                     'centre', post=l.ROTY_180 * l.ROTZ_90 * l.ROTX_90)


    
if __name__ == "__main__":
    core.anchorscad_main(False)
