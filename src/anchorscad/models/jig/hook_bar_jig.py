'''
Created on 2023-10-28

@author: gianni
'''

import anchorscad as ad

EXPLAND_FOR_PRINTER_TOLERANCE=0.2

@ad.datatree
class BarProfile:
    '''
    The 2D cross section of the bar stock for the hook bar jig.
    '''
    t: float=2.86 + EXPLAND_FOR_PRINTER_TOLERANCE
    w: float=12.0 + EXPLAND_FOR_PRINTER_TOLERANCE
    r: float=0.05 
    
    metadata: ad.ModelAttributes=ad.ModelAttributes(fn=8)
    
    
    def build(self) -> ad.Path:

        # Allow for expansion of the when used as a hole to 
        # accommodate 3D printer over extrusion tolerance.       
        t = self.t
        w = self.w
        r = self.r
        
        builder = (ad.PathBuilder()
            .move((0, r))
            .line((0, w - r), 'lhs')
            .arc_tangent_radius_sweep(
                radius=r, 
                sweep_angle_degrees=-90, 
                name='arc_lhs_upper',
                metadata=self.metadata)
            .stroke(t - 2 * r, name='upper')
            .arc_tangent_radius_sweep(
                radius=r,
                sweep_angle_degrees=-90, 
                name='arc_rhs_upper',
                metadata=self.metadata)
            .stroke(w - 2 * r, name='rhs')
            .arc_tangent_radius_sweep(
                radius=r,
                sweep_angle_degrees=-90, 
                name='arc_rhs_lower',
                metadata=self.metadata)
            .stroke(t - 2 * r, name='lower')
            .arc_tangent_radius_sweep(
                radius=r,
                sweep_angle_degrees=-90, 
                name='arc_lhs_lower',
                metadata=self.metadata)
        )
        
        return builder.build()
    
@ad.datatree
class HookBarCutoutPath:
    w: float=9
    d: float=3
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
            .move((0, 0))
            .line((0, self.w), 'lhs')
            .line((self.d, self.w / 2), 'upper_rhs')
            .line((0, 0), 'lower_rhs')
        )
        
        return builder.build()
    
@ad.shape
@ad.datatree
class HookBarCutoutShape(ad.CompositeShape):
    '''
    When holes are drilled in the stock, the bar is unable to slide out. This
    cutout allows the bar to be removed..
    '''
    
    path_node: ad.Node=ad.dtfield(ad.ShapeNode(HookBarCutoutPath, prefix='co_'))
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_node().build())
    
    l: float=88
    cutout_cage_size: tuple=ad.dtfield(self_default=lambda s: (s.l, s.co_w, s.co_d))
    
    cutour_cage_shape_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='cutout_cage_'))
    extrude_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.LinearExtrude, {'h': 'l'}, 'path'))
    
    cutout_cage_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False)
    
    def build(self) -> ad.Maker:
        
        maker = self.cutout_cage_node(self.cutour_cage_shape_node()).at('centre')
        
        shape = self.extrude_node().solid('cutout').at('lhs', 0.5)
        
        maker.add_at(shape, 'face_edge', 'left', 2, post=ad.ROTX_270)
        
        return maker
    

@ad.shape
@ad.datatree
class HookBarStock(ad.CompositeShape):
    '''
    The stock for the hook bar jig.
    '''
    l: float=88
    path_node: ad.Node=ad.dtfield(ad.ShapeNode(BarProfile, expose_all=True))
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_node().build())
    cage_size: tuple=ad.dtfield(
        self_default=lambda s: (
            s.l, s.t, s.w))
    cage_shape_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='cage_'))
    extrude_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.LinearExtrude, {'h': 'l'}, 'path'))
    
    cage_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'front'),)
    
    def build(self) -> ad.Maker:

        maker = self.cage_node(self.cage_shape_node()).at('centre')
        
        shape = self.extrude_node()
        maker.add_at(
            shape.solid('stock').at('lhs', 0.5), 
            'face_edge', 'left', 3, post=ad.ROTX_270)
        
        return maker
    

    
@ad.shape
@ad.datatree
class HookBarStockWithHoles(ad.CompositeShape):
    '''
    The stock for the hook bar with holes.
    '''
    
    hook_bar_stock_node: ad.Node=ad.dtfield(ad.ShapeNode(HookBarStock))
    hook_size: float=ad.dtfield(25, doc='The size of the bar devoted to the hook')
    hole_locations: tuple=(0.2, 0.5)
    hole_r: float=ad.dtfield(2.5)
    hole_h: float=ad.dtfield(self_default=
                             lambda s: s.t + s.epsilon)
    hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='hole_'))
    epsilon: float=ad.dtfield(0.01)
    
    fn: int=ad.dtfield(32)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args(('hole', 0), 'centre'),
        ad.surface_args('face_centre', 'left'),)
    
    def build(self) -> ad.Maker:
        maker = self.hook_bar_stock_node().solid('stock').at()
        
        hole = self.hole_node()
        
        l_size = self.l - self.hook_size
        
        for i, loc in enumerate(self.hole_locations):
            maker.add_at(
                hole.solid(('hole', i))
                    .colour('red')
                    .at('centre', post=ad.ROTY_90),
                'face_centre', 'left',
                    post=ad.tranZ(-loc * l_size))
        
        return maker

    
@ad.shape
@ad.datatree
class HookBarHoleJig(ad.CompositeShape):
    '''
    The hole jig for the hook bar. The hook bar stock is inserted into the jig
    including a template for guiding hole drilling (the plastic is too soft to
    guide the drill bit directly). Drilling lubricant holes are provided that
    direct lubricant flow into the drilling hole.
    
    The jig hole is set to only provide the pilot hole. The final drilling can
    be done without a jig.
    '''
    
    hook_bar_stock_node: ad.Node=ad.dtfield(
        ad.ShapeNode(HookBarStockWithHoles))
    
    hook_bar_stock: HookBarStockWithHoles=ad.dtfield(
        self_default=lambda s: s.hook_bar_stock_node(),
        doc='The hook bar stock to be inserted into the jig')
    
    jig_buffer: float=ad.dtfield(17, doc='The buffer around the hook bar stock')
    jig_lenth_shortening: float=ad.dtfield(6,
        doc='The jig is made is much shorter than the hook bar stock to allow '
            'for the hook bar to be removed')
    jig_size: tuple=ad.dtfield(
        self_default=lambda s: 
            (s.hook_bar_stock.l - s.jig_lenth_shortening,
             s.hook_bar_stock.t + s.jig_buffer,
             s.hook_bar_stock.w + s.jig_buffer),
        doc='The size of the jig main block')
    jig_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Box, prefix='jig_'))
    
    jig_hole_r: float=ad.dtfield(1.5, doc='The radius of the jig guide/pilot hole')
    jig_hole_h: float=ad.dtfield(self_default=
        lambda s: s.jig_size[1] + s.epsilon,
        doc='The length of the jig guide/pilot hole')
    
    jig_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='jig_hole_'))
    
    lube_hole_r: float=ad.dtfield(2.5, doc='The radius of the jig lubricant hole')
    lube_hole_h: float=ad.dtfield(self_default=lambda s: s.jig_size[2] + s.epsilon,
        doc='The length of the jig lubricant hole')
    lube_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, prefix='lube_hole_'))
    
    lube_hole_yoffset: float=ad.dtfield(4.5, doc='The y offset of the lubricant hole')
    lube_hole_zoffset: float=ad.dtfield(14, doc='The z offset of the lubricant hole')
    lube_hole_slant_angle_degrees: float=ad.dtfield(25, 
        doc='The slant angle of the lubricant hole')
    
    cutout_node: ad.Node=ad.dtfield(
        ad.ShapeNode(HookBarCutoutShape))
    
    def build(self) -> ad.Maker:
        #maker = self.jig_node().solid('jig').colour('blue', 0.3).transparent(True).at()
        maker = self.jig_node().solid('jig').at()
        
        hook_bar_stock_centre_maker = self.hook_bar_stock\
            .hole('stock_centres').transparent(False).colour('cyan', 0.3)\
                .at('face_centre', 'right')
        
        maker.add_at(hook_bar_stock_centre_maker, 'face_centre', 'left')
        
        hook_bar_stock_hole_maker = self.hook_bar_stock\
            .hole('stock_holes').transparent(False).colour('pink', 0.3)\
                .at('face_centre', 'right')
                
        maker.add_at(hook_bar_stock_hole_maker, 'face_centre', 'left', post=ad.tranX(5))
        
        cutout_shape = self.cutout_node()
        maker.add_at(
            cutout_shape.hole('cutout').colour('purple', 0.3).at('face_edge', 'left', 2),
            'stock_holes', 'face_edge', 'left', 3, post=ad.ROTZ_180 * ad.tranY(-self.epsilon))
        
        jig_hole_shape = self.jig_hole_node()
        
        lube_hole_shape = self.lube_hole_node()
        
        for i in range(len(self.hook_bar_stock.hole_locations)):
            maker.add_at(
                jig_hole_shape
                    .hole(('jig_hole', i))
                    .at('centre'),
                'stock_centres', ('hole', i), 'centre')
            
            maker.add_at(
                lube_hole_shape
                    .hole(('lube_hole', i))
                    .at('centre'),
                'stock_centres', ('hole', i), 'centre',
                post=ad.rotX(90 - self.lube_hole_slant_angle_degrees) 
                    * ad.tranY(-self.lube_hole_yoffset) 
                    * ad.tranZ(-self.lube_hole_zoffset))
                
        
        return maker


@ad.shape
@ad.datatree
class HookBarBendLineJig(ad.CompositeShape):
    '''
    The bend line jig for the hook bar. The hook bar stock is inserted into the jig
    flush with the front. The drilled part is dropped into a vice with this jig
    above the vice jaws. Once the vice is clamped, a bending tool provides the
    bend location. Removing the jig allows the bar to be bent at the precise position. 
    '''
    
    hook_bar_stock_node: ad.Node=ad.dtfield(
        ad.ShapeNode(HookBarStockWithHoles))
    
    hook_bar_stock: HookBarStockWithHoles=ad.dtfield(
        self_default=lambda s: s.hook_bar_stock_node())
    
    jig_buffer: float=ad.dtfield(15, doc='The buffer around the hook bar stock')
    jig_size: tuple=ad.dtfield(self_default=
        lambda s: (s.hook_size,
                   s.hook_bar_stock.t + s.jig_buffer,
                   s.hook_bar_stock.w + s.jig_buffer))
    jig_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Box, prefix='jig_'))
    
    def build(self) -> ad.Maker:
        shape = self.jig_node()
        
        maker = shape.solid('jig').at()
        
        hook_bar_stock_hole_maker = self.hook_bar_stock\
            .hole('stock_holes').transparent(False).colour('pink', 0.3)\
                .at('face_centre', 'right')
                
        maker.add_at(hook_bar_stock_hole_maker, 'face_centre', 'left')
        
        return maker
    
@ad.shape
@ad.datatree
class HookBarBendLineJigMultiple(ad.CompositeShape):
    '''Multiple bend line jigs assembled side by side.'''
    
    single_jig_node: ad.Node=ad.dtfield(ad.ShapeNode(HookBarBendLineJig))
    
    count: int=ad.dtfield(4, doc='The number of side by side bend line jigs')
    
    def build(self) -> ad.Maker:
        shape = self.single_jig_node()
        maker = shape.solid(('jig', 0)).at('face_centre', 'top')
        for i in range(self.count - 1):
            maker.add_at(
                shape.solid(('jig', i + 1)).at('face_centre', 'top'),
                ('jig', i), 'face_centre', 'base', post=ad.ROTY_180)
        
        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
