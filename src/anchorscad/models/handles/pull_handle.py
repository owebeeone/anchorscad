'''
Created on 25-Nov-2023

@author: gianni
'''

import anchorscad as ad

import anchorscad.models.basic.stadium as stadium
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew

@ad.shape
@ad.datatree
class PullHandleScaffold(ad.CompositeShape):
    '''The main shape of the handle.'''
    d: float=11
    base_w: float=45
    depth: float=120
    depth_outer: float=40
    overlap: float=20
    riser_l: float=25
    
    scaffold_r: float=ad.dtfield(self_default=lambda s: s.d / 2)
    scaffold_inner_r: float=10
    scaffold_r: float=7
    scaffold_w: float=10
    scaffold_t: float=8
    scaffold_bend_angle: float=80
    scaffold_sequence: tuple=ad.dtfield(self_default=lambda s:
        (('P', ad.args(h=s.depth_outer, square_right=True)),
         ('R', ad.args(sweep_angle=s.scaffold_bend_angle, transform=ad.tranZ(s.overlap))),
         ('P', ad.args(h=s.riser_l)),
         ('R', ad.args(sweep_angle=-s.scaffold_bend_angle)),
         ('P', ad.args(h=s.depth)),
         ('R', ad.args(sweep_angle=s.scaffold_bend_angle)),
         ('P', ad.args(h=s.riser_l)),
         ('R', ad.args(sweep_angle=-s.scaffold_bend_angle)),
         ('P', ad.args(h=s.depth_outer, square_right=True, transform=ad.tranZ(s.overlap))),
         ))
    
    scaffold_node: ad.Node=ad.ShapeNode(stadium.StadiumSequence, prefix='scaffold_')
    
    fn: int=ad.dtfield(128)
    
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('handle', 'element-0', 'stadium', 'right', 0.5),
 #       ad.surface_args('ubolt', 'element-4', 'stadium', 'right', 0.5, rh=1),
    )
    
    def build(self) -> ad.Maker:
        # Creates a stadium shape sequence of 5 elements.
        scaffold_shape = self.scaffold_node()
        
        maker = scaffold_shape.solid('handle').at('base')
        
        # extension_len = self.scaffold_inner_r * 2 + self.scaffold_w
        # extension = scaffold_shape.prism_node(h=extension_len)
        
        # maker.add_at(extension.solid('extension1').at('top'), 
        #              'element-0', 'top', post=ad.ROTX_180)
        
        # maker.add_at(extension.solid('extension2').at('top'), 
        #              'ubolt', 'element-4', 'base', post=ad.ROTX_180)
        
        # flat_extension_len = self.base_w + self.scaffold_inner_r
        # flat_extension = scaffold_shape.prism_node(h=flat_extension_len, square_right=True)
        
        # maker.add_at(flat_extension.solid('flat_base').at('stadium', 'top', 0, rh=0.5), 
        #              'ubolt', 'element-2', 'stadium', 'top', 0, rh=0.5)
        
        return maker
    
    def overall_width(self):
        p1 = self.maker.at('ubolt', 'element-0', 'stadium', 'right', 0.5)
        p2 = self.maker.at('ubolt', 'element-4', 'stadium', 'right', 0.5, rh=1)
        return ad.distance_between(p1, p2)

@ad.shape
@ad.datatree
class PullHandle(ad.CompositeShape):
    '''
    A basic pull handle.
    '''
    w: float=ad.dtfield(20, doc='The width of the handle.')
    l_hole: float=ad.dtfield(150, doc='The length of the handle hole.')
    h_hole: float=ad.dtfield(50, doc='The height of the handle hole.')
    d: float=ad.dtfield(10, doc='The depth of the handle.')
    
    scaffold_r: float=ad.dtfield(20, doc='The radius of the bevels.')
    scaffold_d: float=ad.dtfield(50, doc='The depth of the scaffold.')
    
    scaffold_node: ad.Node=ad.ShapeNode(PullHandleScaffold, prefix='scaffold_')
    scaffold_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.scaffold_node())
    
    screw_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: s.d + 2 * s.scaffold_r, doc='The overall length of the screw_shaft.')
    screw_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.screw_shaft_overall_length, doc='The length of the screw_shaft.')
    screw_size_name: str=ad.dtfield('BUGLE_14g-10', doc='The size of the screw.')
    
    screw_node: ad.Node=ad.ShapeNode(CountersunkScrew, prefix='screw_')
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        ad.surface_args('scaffold', 'handle', 'element-0', 'stadium', 'left', 0.5),
    )

    def build(self) -> ad.Maker:
        maker = self.scaffold_shape.solid('scaffold').at()
        
        screw_hole_shape = self.screw_node()
        maker.add_at(screw_hole_shape.composite(('screw_hole', 0)).at('top'),
                     *self.anchor_for_screw(False), rh=0.5, post=ad.ROTX_180)
        maker.add_at(screw_hole_shape.composite(('screw_hole', 1)).at('top'),
                     *self.anchor_for_screw(True), rh=0.5, post=ad.ROTX_180)
        
        return maker
    
    def anchor_for_screw(self, for_last):
        index = len(self.scaffold_shape.scaffold_sequence) - 1 if for_last else 0
        element = f'element-{index}'
        return ('scaffold', 'handle', element, 'stadium', 'left', 0.5)


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
