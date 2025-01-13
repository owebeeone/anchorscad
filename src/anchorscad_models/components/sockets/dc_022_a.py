'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad
import anchorscad_models.basic.stadium as stadium
import numpy as np

EXPANSION=0.1

@ad.datatree
class DC022ABodyShapeBuilder:
    
    body_r: float=ad.dtfield(11.8 / 2 + EXPANSION, doc='Body radius of the socket')
    body_flat_r: float=ad.dtfield(10.8 / 2 + EXPANSION, doc='Flat radius of the socket')
    
    def build(self) -> ad.Path:
        flat_l = np.sqrt(self.body_r ** 2 - self.body_flat_r ** 2)
        return (ad.PathBuilder()
                .move((0, -self.body_flat_r))
                .line((flat_l, -self.body_flat_r), 'base_rhs')
                .arc_points_radius((flat_l, self.body_flat_r), self.body_r, direction=True, name='rhs')
                .line((0, self.body_flat_r), 'top_rhs')
                .line((-flat_l, self.body_flat_r), 'top_lhs')
                .arc_points_radius((-flat_l, -self.body_flat_r), self.body_r, direction=True, name='lhs')
                .line((0, -self.body_flat_r), 'base_lhs')
                .build())

@ad.shape
@ad.datatree
class DC022A(ad.CompositeShape):
    '''An outline of a DC-022-2.5A-2.0 socket.'''
    
    top_r: float=ad.dtfield(13.8 / 2 + EXPANSION, doc='Top radius of the socket')
    top_h: float=ad.dtfield(2, doc='Height of top of the socket')
    top_cyl_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='top_')
    
    top_access_hole_r: float=ad.dtfield(13.8 / 2 + EXPANSION, 
            doc='Front access hole radius, only used for '
                'clearance for inserting the jack and plug.')
    top_access_hole_h: float=ad.dtfield(20, doc='Height of rear access hole')
    top_access_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='top_access_hole_')    
    
    body_path_node: ad.Node=ad.ShapeNode(DC022ABodyShapeBuilder) 
    body_path: ad.Path=ad.dtfield(self_default=lambda s: s.body_path_node().build())
    body_h: float=ad.dtfield(11.2, doc='Height of body of the socket')
    body_extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, prefix='body_')
    
    rear_access_hole_r: float=ad.dtfield(19.8 / 2 + EXPANSION, 
            doc='Rear access hole radius, must take mounting bolt')
    rear_access_hole_h: float=ad.dtfield(1 + 11.2, doc='Height of rear access hole')
    rear_access_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='rear_access_hole_')
    
    plug_r: float=ad.dtfield(6.3 / 2 + EXPANSION, doc='Plug radius of the socket')
    plug_h: float=ad.dtfield(10, doc='Height of plug hole of the socket')
    plug_hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='plug_')
    
    add_access_holes: bool=ad.dtfield(
        True, doc='Add access holes for inserting the plug and jack')
    
    thickness: float=ad.dtfield(5, doc='Thickness of the housing wall')
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64, add_access_holes=True)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        
        top_shape = self.top_cyl_node()
        maker = top_shape.solid('outer').at('top')
        
        body_shape = self.body_extrude_node()
        maker.add_at(body_shape.solid('body').at('centre_of', 'rhs', 0, normal_segment='base_rhs', angle=90), 'base', rh=1)
        
        top_access_hole_shape = self.top_access_hole_node()
        maker.add_at(top_access_hole_shape
                     .solid_cage('top_access_hole', not self.add_access_holes)
                     .colour('cyan').at('top'), 
                     'top', rh=1)
        
        rear_access_hole_shape = self.rear_access_hole_node()
        maker.add_at(rear_access_hole_shape
                     .solid_cage('rear_access_hole', not self.add_access_holes)
                     .colour('pink').at('base'), 
                    'body', 'centre_of', 'rhs', normal_segment='base_rhs', angle=90, post=ad.tranZ(-self.thickness))
        
        return maker

@ad.shape
@ad.datatree
class Dc022aHousing(ad.CompositeShape):
    '''A housing for a DC-022-2.5A-2.0 socket.'''

    socket_node: ad.Node=ad.ShapeNode(DC022A)
    socket_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.socket_node())
    
    shell_thickness: float=ad.dtfield(2, doc='Thickness of the housing shell')
    
    extension: float=ad.dtfield(15, doc='Extension of the housing beyond the socket')
    
    extender_h: float=ad.dtfield(
        self_default=lambda s: s.thickness + s.top_h + s.extension, doc='Height of the extender')
    extender_r: float=ad.dtfield(
        self_default=lambda s: s.socket_shape.top_access_hole_r + s.shell_thickness, doc='Radius of the extension')
    extender_w: float=ad.dtfield(0.1, init=False)
    extender_square_right: bool=ad.dtfield(True, init=False)
    extender_node: ad.Node=ad.ShapeNode(stadium.StadiumPrism, prefix='extender_')
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64, add_access_holes=True)
    
    
    def build(self) -> ad.Maker:
        extender = self.extender_node()
        
        maker = extender.solid('extender').colour('green').transparent(False).at('base', post=ad.ROTX_90 * ad.ROTY_90)
        
        maker.add_at(
            self.socket_shape.hole('housing').at('rear_access_hole', 'base'),
            'base', rh=1, post=ad.ROTZ_90)
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
