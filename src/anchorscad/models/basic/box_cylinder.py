'''
Created on 29 Sep 2021

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class BoxCylinder(ad.CompositeShape):
    '''
    A Box with half a cylinder protruding from one side.
    
    Build as an LinearExtrude but has both Cylinder and Box cages for anchors. 
    The Box cage is the primary shape.
    '''
    size: tuple=(10, 20, 30)
    r: float=ad.dtfield(
        self_default=lambda s: s.size[0] / 2)
    h: float=ad.dtfield(
        self_default=lambda s: s.size[2])
    extrude_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.LinearExtrude, 'h'),
        init=False)
    cylinder_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 'r', 'h'),
        init=False)
    box_cage_of_node: ad.Node=ad.dtfield(
        ad.Node(ad.cageof, prefix='box_cage_'),
        init=False)
    cylinder_cage_of_node: ad.Node=ad.dtfield(
        ad.Node(ad.cageof, prefix='cylinder_cage_'),
        init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32,
                               box_cage_hide_cage=False,
                               cylinder_cage_hide_cage=False)
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'base'),
        ad.surface_args('face_centre', 'back'),
        ad.surface_args('cylinder', 'base'),
        ad.surface_args('round_centre', rh=1),
        ad.surface_args('round_centre', rh=0.5),)
    
    def build(self) -> ad.Maker:
        cage_size = (self.size[0], self.size[1] + self.r, self.size[2])
        maker = self.box_cage_of_node(ad.Box(cage_size)).at(
                'face_corner', 0, 0)
            
        path = (ad.PathBuilder()
            .move([0, 0])
            .line([-self.r, 0], 'edge1')
            .line([-self.r, self.size[1]], 'edge2')
            .arc_tangent_point([self.r, self.size[1]], name='arc')
            .line([self.r, 0], 'edge3')
            .line([0, 0], 'edge4')
            .build())
        
        shape = self.extrude_node(path)
        
        maker.add_at(shape.solid('box_cylinder')
                     # .colour([0, 0, 1, 0.4])
                     # .transparent(True)
                     .at('edge2', 0.5),
                     'face_edge', 'base', 1,
                     post=ad.ROTX_270 * ad.tranX(-self.r / 2))
        
        cylinder_cage = self.cylinder_cage_of_node(
            self.cylinder_node(fn=2 * self.fn if self.fn else None),
            properties=ad.CageOfProperties(name='cylinder', colour=(1, 0, 0, 0.4)))
        maker.add_at(cylinder_cage.at('surface'),
                     'box_cylinder', 'arc', 0.5, post=ad.ROTY_180)
        
        return maker

    @ad.anchor('Centre base. Deprecated: use "base" instead.', deprecated=True)
    def round_centre(self, h=0, rh=None):
        return self.maker.at('cylinder', 'base', h=h, rh=rh)
    
    @ad.anchor('Centre top. Deprecated: use "top" instead.', deprecated=True)
    def round_top(self, h=0, rh=None):
        return self.maker.at('cylinder', 'top', h=h, rh=rh)
    
    @ad.anchor('Base of cylindrical section.')
    def base(self, h=0, rh=None):
        return self.maker.at('cylinder', 'base', h=h, rh=rh)
    
    @ad.anchor('Top of cylindrical section.')
    def top(self, h=0, rh=None):
        return self.maker.at('cylinder', 'top', h=h, rh=rh)


MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)
if __name__ == '__main__':
    ad.anchorscad_main()
