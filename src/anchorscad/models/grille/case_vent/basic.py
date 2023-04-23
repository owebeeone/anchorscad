'''
Created on 12 Sep 2021

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class RectangularGrille(ad.CompositeShape):
    '''
    A grille of vent holes.
    '''
    size: ad.GVector=(50, 2, 10)
    h: float=10
    w: float=3
    chamfer_size_ratio = 0.25
    sep: float=3
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.size).cage(
            'cage').at('centre')
        
        requested_size = self.w + self.sep
        
        count = int(self.size[0] // requested_size)
        
        actual_size = self.size[0] / count
        
        actual_sep = actual_size - self.w
        
        full_path, half_path = self._paths(self.size[1], actual_sep) 
        
        full_shape = ad.LinearExtrude(full_path, h=self.size[2])
        half_shape = ad.LinearExtrude(half_path, h=self.size[2])
        
        post_transform = ad.ROTY_90 * ad.translate([self.size[1] / 2, 0, 0])
        
        maker.add_at(half_shape.solid(('vane', 'left'))
                     .at('inner', 0),
                     'face_edge', 0, 0, 0, post=post_transform)
        for i in range(count - 1):
            
            maker.add_at(full_shape.solid(('vane', i)).at('inner', 0),
                         'face_edge', 0, 0, (i + 1) / count, 
                         post=post_transform)
        
        
        maker.add_at(half_shape.solid(('vane', 'right')).at('inner', 0),
                     'face_edge', 0, 0, 1, post=post_transform * ad.ROTY_180)
        
        return maker
        
    def complete(self, maker):
        return maker
        
    def as_holes(self, maker):
        
        maker1 = maker.hole('grille').at('centre')
        maker1.add_at(ad.Box(self.size).solid('etch').at('centre'))
    
        return maker1.solid('holes')
        
    def _paths(self, vane_w, sep):
        
        assert(self.chamfer_size_ratio < 0.5) and (self.chamfer_size_ratio >= 0
                ), 'chamfer_size_ratio is out of range - [0 - 0.5]'
        top = sep / 2
        base = -top
        ch_size = vane_w * self.chamfer_size_ratio
        ch_right = vane_w / 2 - ch_size
        ch_left = -ch_right
        ch_top = top - ch_right
        right = vane_w / 2
        left = -right
        
        path_builder = (ad.PathBuilder()
            .move([0, 0])
            .line([left, 0], 'inner')
            .line([left, ch_top], ('left', 'upper'))
            .line([ch_left, top], ('left_champher', 'upper'))
            .line([0, top], ('left', 'top'))
            .line([ch_right, top], ('right', 'top'))
            .line([right, ch_top], ('right_champher', 'upper'))
            .line([right, 0], ('right', 'upper')))
        
        half_path = path_builder.build()
        
        full_path = (path_builder
            .line([right, -ch_top], ('right', 'lower'))
            .line([ch_right, -top], ('right_champher', 'lower'))
            .line([0, -top], ('right', 'base'))
            .line([ch_left, -top], ('left', 'base'))
            .line([left, -ch_top], ('left_champher', 'lower'))
            .line([left, 0], ('left', 'lower'))
            .build())

        return full_path, half_path
    

@ad.shape
@ad.datatree(chain_post_init=True)
class RectangularGrilleAsHoles(RectangularGrille):
    
    def complete(self, maker):
        return self.as_holes(maker).at('centre')
    

@ad.shape
@ad.datatree
class RectangularGrilleHoles(ad.CompositeShape):
    '''
    A grille of as holes.
    '''
    size: ad.GVector=(50, 2, 10)
    w: float=3
    sep: float=0.01
    chamfer_size_ratio = 0.25
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.size).cage(
            'cage').transparent(True).colour([0.3, 1, 0.3, 0.3]).at('centre')
        
        k = self.sep / self.w
        
        count = int((self.size[0] - self.sep)// (self.sep + self.w))
        
        actual_w = self.size[0] / ( 2 * count - k)
        actual_sep = k * actual_w
        
        full_path = self._paths(self.size[1], actual_w, actual_sep) 
        
        full_shape = ad.LinearExtrude(full_path, h=self.size[2])
        
        post_transform = ad.translate([actual_w, 0, -self.size[1]])
        
        for i in range(count):
            maker.add_at(full_shape.solid(('vane', i)).at(('left', 'upper'), 0),
                         'face_edge', 0, 0, i / count, 
                         post=post_transform)
        
        return maker
        
    def complete(self, maker):
        return maker
        
    def as_holes(self, maker):
        
        maker1 = maker.hole('grille').at('centre')
        maker1.add_at(ad.Box(self.size).solid('etch').at('centre'))
    
        return maker1.solid('holes')
        
    def _paths(self, vane_w, actual_w, sep):
        
        assert(self.chamfer_size_ratio < 0.5) and (self.chamfer_size_ratio >= 0
                ), 'chamfer_size_ratio is out of range - [0 - 0.5]'
        top = actual_w / 2
        base = -top
        ch_size = vane_w * self.chamfer_size_ratio
        ch_right = vane_w / 2 - ch_size
        ch_left = -ch_right
        ch_top = top + ch_right
        right = vane_w / 2
        left = -right
        
        path_builder = (ad.PathBuilder()
            .move([0, 0])
            .line([left, 0], 'inner')
            .line([left, ch_top], ('left', 'upper'))
            .line([ch_left, top], ('left_champher', 'upper'))
            .line([0, top], ('left', 'top'))
            .line([ch_right, top], ('right', 'top'))
            .line([right, ch_top], ('right_champher', 'upper'))
            .line([right, 0], ('right', 'upper')))
        
        full_path = (path_builder
            .line([right, -ch_top], ('right', 'lower'))
            .line([ch_right, -top], ('right_champher', 'lower'))
            .line([0, -top], ('right', 'base'))
            .line([ch_left, -top], ('left', 'base'))
            .line([left, -ch_top], ('left_champher', 'lower'))
            .line([left, 0], ('left', 'lower'))
            .build())

        return full_path
    

MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
