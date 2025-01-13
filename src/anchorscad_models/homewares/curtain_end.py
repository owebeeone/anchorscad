'''
Created on 19-Nov-2023

@author: gianni

A simple curtain end cap with parameterized interference fit.
'''

import anchorscad as ad

@ad.datatree
class CurtainEndCapPath:
    '''The 2D Path for the curtain end cap for rotate_extrude.'''
    r: float=ad.dtfield(25.6 / 2, doc='The radius of the curtain rod.')
    w: float=ad.dtfield(30, doc='The width of the end cap.')
    br: float=ad.dtfield(1.5, doc='The radius of the bevel.')
    t: float=ad.dtfield(4, doc='The thickness of the end cap.')
    tb: float=ad.dtfield(8, doc='The thickness of the base of the end cap.')
    ih: float=ad.dtfield(0.4, doc='Interference ridge height.')
    iw: float=ad.dtfield(10, doc='Interference ridge width.')
    io: float=ad.dtfield(10, doc='Interference offset from top of cap path.')
    irel_len: float=ad.dtfield(0.4, doc='Interference ridge spline relative length.')
    
    def build(self) -> ad.Path:
        builder = ad.PathBuilder()
        
        end_ridge = self.w - (self.iw + self.io)
        assert end_ridge >= self.tb, f"Interference ridge too wide by {self.tb - end_ridge}."
        
        mid_ridge = end_ridge + self.iw / 2
        
        
        (builder.move((0, 0))
         .line((-(self.r + self.t - self.br), 0), 'base')
         .arc_tangent_radius_sweep(self.br, -90, name='base_bevel')
         .stroke(self.w - 2 * self.br, name='outer_side')
         .arc_tangent_radius_sweep(self.br, -90, name='outer_top_bevel')
         .stroke(self.t - 2 * self.br, name='outer_top')
         .arc_tangent_radius_sweep(self.br, -90, name='inner_top_bevel')
         .stroke(self.io - self.br, name='upper_inner_side')
         .spline(
             ((-self.r + self.ih, mid_ridge + 1), (-self.r + self.ih, mid_ridge)), 
             cv_len=(1, 1), 
             rel_len=self.irel_len,
             name='upper_ridge')
         
         .spline(
             ((-self.r, end_ridge + 1), (-self.r, end_ridge)), 
             cv_len=(1, 1), 
             rel_len=self.irel_len,
             name='lower_ridge')
         .line((-self.r, self.tb), 'lower_inner_side')
         .line((0, self.t), 'inner_base')
         .line((0, 0), 'centre_axis')
         )
        
        return builder.build()

@ad.shape
@ad.datatree
class CurtainEndCap(ad.CompositeShape):
    '''
    A simple curtain end cap.
    '''
    
    # All parameters are injected from CurtainEndCapPath.
    path_node: ad.Node=ad.dtfield(ad.ShapeNode(CurtainEndCapPath))
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_node().build())
    
    # Injected parameter "path" from RotateExtrude will pick up the self_default path. 
    rotate_extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude)
    
    # Try a stupidly high number of facets to get a smoother curve.
    fn: int=ad.dtfield(256, doc='The number of facets for the rotate_extrude.')

    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        # Not much to do here, just build the rotate_extrude shape and name it.
        shape = self.rotate_extrude_node()
        maker = shape.solid('end_cap').at()
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
