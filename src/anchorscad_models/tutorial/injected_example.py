'''
Created on 31 July 2022

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class ClockFace(ad.CompositeShape):
    '''Simple clock face with different sized spheres at the points.'''
    count_points: int=ad.dtfield(12, 'The number of points on the clock face')
    r_mod_map: tuple=ad.dtfield(((12, 6), (3, 4), (1, 3)), 'Radius at each point')
    x_pos: float=ad.dtfield(40, 'Radius of the clock face centres')
    sphere_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Sphere), init=False)

    def build(self) -> ad.Maker:
        maker = ad.Cylinder(r=self.x_pos).cage('cage').at('centre')
        for i in range(self.count_points):
            for div, r in self.r_mod_map:
                if i % div == 0:
                    maker.add_at(self.sphere_node(r=r + self.r)
                                 .solid(('point', i)).at('centre'),
                        'surface', angle=i * 360 / self.count_points)
                    break
        return maker


MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
