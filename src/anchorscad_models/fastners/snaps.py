'''
Created on 20 Sep 2021

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.box_side_bevels import BoxSideBevels


@ad.shape
@ad.datatree(frozen=True)
class Snap(ad.CompositeShape):
    '''
    A snap-on tab for fastening two shapes together.
    This is meant to be used as a hole on one side and a solid on the other.
    The 'snap' anchor is intended to be shared on both sides.
    '''
    size: tuple=(15, 10, 3)
    depth_factor: float=0.5
    max_x: float=0.55
    t_size: float=1.3
    tab_protrusion: float=1.5
    tab_height: float=4
    epsilon: float=1.e-2
    snap_offs_factor: float=0.17
    fn:int = 16
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
                ad.surface_args('snap', 0.5),)
    
    def build(self) -> ad.Maker:
        box = ad.Box(self.size)
        maker = box.cage(
            'cage').transparent(1).colour([1, 1, 0, 0.5]).at('centre')
            
        max_x = self.max_x
        t_size = self.t_size
        extentX = self.size[2] * self.depth_factor
        extentY = self.size[1]
        extentX_t = extentX + self.tab_protrusion
        
        start=[1, 0]
        
        path = (ad.PathBuilder()
            .move(start)
            .line([-max_x, t_size], 'edge1')
            .line([-max_x, 1.2 * t_size], 'edge3')
            .line([0, 1.5 * t_size], 'edge4')
            .line([0, extentY], name='draw')
            .line([extentX, extentY], name='top')
            .line([extentX_t, extentY - self.tab_protrusion], name='top_protrusion')
            .line(start, name='bottom')
            .build())

        shape = ad.LinearExtrude(path, h=self.size[0])
        
        maker.add_at(shape.solid('tooth').at('top', 0),
                     'face_edge', 0, 3, post=ad.ROTY_180)
        
        # Round the clip.
        clip_size = box.size.A[0:3] + 2 * self.epsilon
        clip_size[2] = clip_size[2] + self.tab_protrusion
        clip_cage = (ad.Box(clip_size).cage('clip_cage')
                .transparent(1).colour([0, 1, 0, 0.5])
                .at('centre'))
        
        
        th = self.tab_height
        cutter_size = clip_size + self.epsilon / 2
        cutter_size[1] = th
        clip = ad.Box(cutter_size)
        clip_cage.add_at(clip.solid('clip').at(
            'face_corner', 1, 1), 'face_corner', 1, 1)
           
        keep_size = clip_size + self.epsilon
        keep = BoxSideBevels(keep_size, th, fn=self.fn)
        clip_cage.add_at(keep.hole('keep').at('shell', 'face_corner', 1, 1),
                    'face_corner', 1, 1)
        
        
        
        maker.add_at(
            clip_cage.hole('clip').at('face_centre', 1), 
            'face_centre', 1, 
            post=ad.translate([-self.epsilon / 2, -self.epsilon, 0]))
        
        return maker
        
    @ad.anchor('Snap seam edge.')
    def snap(self, rpos=0.5):
        '''Anchors to the seam line..
        Args:
            rpos: 0.0-1.0, 0.5 is centre.
        '''
        return (self.at('centre') * ad.ROTZ_180 * ad.tranY(
            -self.snap_offs_factor * self.size[1]))


MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
