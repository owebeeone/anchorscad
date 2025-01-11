'''
Created on 27 Sep 2021

@author: gianni
'''

import anchorscad as ad
import numpy as np


def radians(degs):
    return degs * np.pi / 180 

@ad.shape
@ad.datatree
class CurlySpokes(ad.CompositeShape):
    '''
    Axial fan grille with bent spokes.
    '''
    h: float
    as_cutout: bool=True
    r_outer: float=29.0 / 2
    r_inner: float=12.0 / 2
    r_mid_ratio: float=0.5
    curl_mid_angle: float=-10
    curl_inner_angle: float=0
    min_solid_size: float=1.4
    min_hole_size: float=1.4
    epsilon: float=1.e-2
    
    cylinder_node: ad.Node=ad.ShapeNode(ad.Cylinder, {})
    linear_extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, {})
    
    fn: int=None
    
    EXAMPLE_SHAPE_ARGS=ad.args(h=2)
    EXAMPLE_ANCHORS=()
    
    EXAMPLES_EXTENDED={
        'as_cutout': ad.ExampleParams(
            shape_args=ad.args(h=2, as_cutout=False),
            anchors=(ad.surface_args('centre'),)),
        'as_solid': ad.ExampleParams(
            shape_args=ad.args(h=2, as_cutout=False),
            anchors=(ad.surface_args('centre'),))}

    
    def build(self) -> ad.Maker:
            
        count = self.min_count()
        r_diff = self.r_outer - self.r_inner
        r_mid = r_diff * self.r_mid_ratio + self.r_inner
        min_sum = self.min_solid_size + self.min_hole_size
        phi_outer_solid = 360 * (self.min_solid_size / min_sum ) / (2 * count)
        phi_outer_hole = 360 * (self.min_hole_size / min_sum ) / (2 * count)
        phi_inner_solid = 360 * (self.min_solid_size / min_sum ) / (count)
        phi_inner_hole = 360 * (self.min_hole_size / min_sum ) / (count)
        
        outer_points = self.points(self.r_outer + self.epsilon, 0,
            phi_outer_solid, phi_outer_hole, phi_outer_solid)
        mid_points = self.points(r_mid, self.curl_mid_angle,
            phi_outer_solid, phi_outer_solid)
        inner_points = self.points(self.r_inner - self.epsilon, 
            self.curl_inner_angle, phi_inner_solid)
        
        if not self.fn:
            fn = count * 4
        else:
            fn = self.fn
        
        maker = self.cylinder_node(r=self.r_outer, h=self.h).cage(
            'cage').transparent(1).colour([1, 1, 0, 0.5]).at('centre')
            
        if self.as_cutout:
            maker.add_at(self.cylinder_node(r=self.r_outer, h=self.h)
                         .solid('core').at('centre'))
        
        path = (ad.PathBuilder()
                       .move(inner_points[0])
                       .line(mid_points[0], ('inner', 'mid', 0))
                       .line(outer_points[0], ('mid', 'outer', 0))
                       .line(outer_points[1], ('outer', 'outer', 0))
                       .line(mid_points[1], ('outer', 'mid', 1))
                       .line(outer_points[2], ('mid', 'outer', 1))
                       .line(outer_points[3], ('outer', 'outer', 1))
                       .line(mid_points[2], ('outer', 'mid', 2))
                       .line(inner_points[1], ('mid', 'inner', 0))
                       .line(inner_points[0], ('inner', 'inner', 0))
                       .build())
        
        shape = self.linear_extrude_node(path, h=self.h + self.epsilon)
        
        spokes_mode = (ad.ModeShapeFrame.HOLE 
                if self.as_cutout 
                else ad.ModeShapeFrame.SOLID)
        for i in range(count):
            maker.add_at(shape
                         .named_shape(('spoke', i), spokes_mode)
                         .at(post=ad.rotZ(i * 360 / count)),
                         'base', post=ad.tranZ(-self.h - self.epsilon / 2)
                         )
            
        
        maker.add_at(ad.Cylinder(r=self.r_inner, h=self.h + self.epsilon, fn=fn)
                     .named_shape('inner_core', spokes_mode).at('centre'))
        
        return maker
        
    def points(self, r, start_angle, *phis):
        sum_phis = start_angle
        angles = [radians(sum_phis)]
        for phi in phis:
            sum_phis += phi
            angles.append(radians(sum_phis))
        return tuple( (r * np.sin(a), r * np.cos(a)) for a in angles)
        
    def min_count(self):
        count_inner = int(self.r_inner * 2 * np.pi 
                          / (self.min_solid_size + self.min_hole_size))
        count_outer = int(self.r_outer * 2 * np.pi 
                          / (2 * self.min_solid_size + 2 * self.min_hole_size))
        count = count_inner if count_inner > count_outer else count_outer
        return count

    @ad.anchor('An example anchor specifier.')
    def side(self, *args, **kwds):
        return self.maker.at('face_edge', *args, **kwds)


MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)
if __name__ == '__main__':
    ad.anchorscad_main(False)
