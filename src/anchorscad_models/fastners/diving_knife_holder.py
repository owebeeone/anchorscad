'''
Created on 21-Dec-2023

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.pipe import Pipe
import anchorscad_models.basic.stadium as stadium

from typing import Tuple


@ad.datatree
class DivingKnifeHolderPathBuilder(ad.CompositeShape):
    '''OBSOLETE - superceeded by SpringHandleHolder.
    The path builder for the diving knife holder. This outline is the base and ring.
    '''
    
    base_w: float = 18
    base_t: float = 4.4
    stem_w: float = 5
    stem_l: float = 25
    base_bevel_r: float = 3

    def build(self):
        
        base_len = (self.base_w - self.stem_w) / 2 - self.base_bevel_r
        
        pathBuilder = (ad.PathBuilder()
            .move((0, 0))
            .line((self.base_w / 2, 0), name='base_bottom_right')
            .stroke(self.base_t, 90, name='base_right')
            .stroke(base_len, 90, name='base_top_right')
            .arc_tangent_radius_sweep(self.base_bevel_r, -90, name='base_top_right_bevel')
            .stroke(self.stem_l - self.base_bevel_r, 0, name='stem_right')
            .stroke(self.stem_w / 2, 90, name='stem_top_right')
            .stroke(self.stem_w / 2, 0, name='stem_top_left')
            .stroke(self.stem_l - self.base_bevel_r, 90, name='stem_left')
            .arc_tangent_radius_sweep(self.base_bevel_r, -90, name='base_top_left_bevel')
            .stroke(base_len, 0, name='base_top_left')
            .stroke(self.base_t, 90, name='base_left')
            .stroke(self.base_w / 2, 90, name='base_bottom_left')
                       )
        
        return pathBuilder.build()

@ad.shape
@ad.datatree
class DivingKnifeHolder(ad.CompositeShape):
    '''
    OBSOLETE - superceeded by SpringHandleHolder.
    Replacement for elastic dive knife holder. This inserts into the scabbard
    and holds the knife handle in place.
    '''
    
    path_builder_node: ad.Node=ad.dtfield(
        ad.ShapeNode(DivingKnifeHolderPathBuilder))
    
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder_node().build())
    
    h: float = 12
    inside_r: float = 26 / 2
    outside_r: float = 26 / 2 + 2
    linear_extrude_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.LinearExtrude))
    
    ring_node: ad.Node=ad.dtfield(ad.ShapeNode(Pipe))
    
    fn: int=64
    
    xEXAMPLE_SHAPE_ARGS=ad.args()
    xEXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'top'),)

    def build(self) -> ad.Maker:
        
        shape = self.linear_extrude_node()
        
        maker = shape.solid('holder').at()
        
        ring_shape = self.ring_node()
        
        maker.add_at(
            ring_shape.solid('ring').at('inner_surface', 0, rh=0.5),
            'stem_top_left', rh=0.5)
        return maker
    

@ad.datatree
class ScabbardMountHoleInnerPath:
    '''The scabbard's mounting hole for the knife holder.
    This is basically a rectangle with arcs at 2 opposing sides. This path is the
    same the the actual hole as well as the recess where the original rubber holder used to sit.
    '''
    
    base_w: float = 8.4
    centre_w: float = 11.8
    base_h: float = 14.4
    
    def build(self):
        
        builder = (ad.PathBuilder()
                   .move((0, 0))
                   .line((self.base_w / 2, 0), name='base_right')
                   .arc_points(
                       (self.centre_w / 2, self.base_h / 2), 
                       (self.base_w / 2, self.base_h), 
                       name='right')
                   .line((0, self.base_h), name='top_right')
                   .stroke(self.base_w / 2, name='top_left')
                   .arc_points(
                       (-self.centre_w / 2, self.base_h / 2), 
                       (-self.base_w / 2, 0), 
                       name='left',
                       direction=True)
                )

        return builder.build()

@ad.datatree
class ScabbardMountHoleRecessPath(ScabbardMountHoleInnerPath):
    '''The scabbard's mounting hole recess for the knife holder.'''
    
    base_w: float = 17.9
    centre_w: float = 22.1
    base_h: float = 21.1


@ad.shape
@ad.datatree
class ScabbardMountHole(ad.CompositeShape):
    '''The scabbard's mounting hole for the knife holder. Use this as a hole
    to make the base shape.
    '''
    
    inner_path_node: ad.Node=ad.dtfield(ad.ShapeNode(ScabbardMountHoleInnerPath, prefix='inner_'))
    inner_path: ad.Path=ad.dtfield(self_default=lambda s: s.inner_path_node().build())
    inner_h: float = 2.8
    inner_extrude_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.LinearExtrude, prefix='inner_'))
    
    top_scale: Tuple[float, float]=ad.dtfield((1.2, 1), "Scale factor (x, y) to create a wedge to hold the base.")
    
    recess_path_node: ad.Node=ad.dtfield(ad.ShapeNode(ScabbardMountHoleRecessPath, prefix='recess_'))
    recess_path: ad.Path=ad.dtfield(self_default=lambda s: s.recess_path_node().build())
    recess_h: float = 4.45
    recess_extrude_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.LinearExtrude, prefix='recess_'))
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=(
        ad.surface_args('inner_hole', 'base_right', 0),
    )
    
    def build(self) -> ad.Maker:
        shape = self.inner_extrude_node()
        top_shape = self.inner_extrude_node(scale=self.top_scale)
        
        maker = shape.solid('inner_hole').at()
        maker.add_at(top_shape.solid('inner_top').at('base_right', rh=1), 'base_right', rh=1, post=ad.ROTZ_180)
        
        recess_shape = self.recess_extrude_node()
        
        # Make a box that when intersected, will cut the outer shape so that it is flush with one side
        # of the inner shape. This is so we can print it flat on the print bed.
        recess_extents = self.recess_path.extents()
        cut_box_size = (recess_extents[1][0] - recess_extents[0][0], 
                        recess_extents[1][1] - recess_extents[0][1] - (self.recess_base_h - self.inner_base_h) / 2, 
                        self.recess_h)
        cut_box_shape = ad.Box(cut_box_size)
        
        recess_maker = recess_shape.solid('recess_hole').at()
        recess_maker.add_at(
            cut_box_shape.solid('cut_box').colour('pink').at('face_edge', 'front', 0), 'base_right')
        
        
        maker.add_at(recess_maker.intersect('cut_recess_hole').at(), 
                     post=ad.ROTY_180 * ad.tranY((self.inner_base_h - self.recess_base_h) / 2))
        
        return maker


@ad.shape
@ad.datatree
class SpringBase(ad.CompositeShape):
    '''The main shape of the handle attachment with adjustable number of spring loops.'''
    d: float=10
    base_w: float=45
    depth: float=0.1
    depth_outer: float=1
    riser_l: float=2
    
    scaffold_r: float=1
    scaffold_inner_r: float=0.5
    scaffold_r: float=1
    scaffold_w: float=2
    scaffold_t: float=8
    scaffold_bend_degrees: float=90
    num_springs: int=1
    knife_handle_r: float=24 / 2
    tab_angle: float=26.5
    tab_bevel_r: float=3
    tab_l: float=19
    tab_w: float=3
    scaffold_sequence: tuple=ad.dtfield(self_default=lambda s:
        (('P', ad.args(h=s.depth_outer, square_right=True)),
         ('R', ad.args(sweep_angle=s.scaffold_bend_degrees)),
         ('P', ad.args(h=s.depth)),
        )
        +
        (
         ('R', ad.args(sweep_angle=s.scaffold_bend_degrees)),
         ('P', ad.args(h=s.riser_l)),
         ('R', ad.args(sweep_angle=-s.scaffold_bend_degrees)),
         ('P', ad.args(h=s.depth)),
        ) * s.num_springs
        +
        (
         ('R', ad.args(sweep_angle=s.scaffold_bend_degrees)),
         ('P', ad.args(h=s.depth_outer, square_right=True)),
         ('R', ad.args(sweep_angle=-180 + s.tab_angle, inner_r=s.knife_handle_r)),
         ('R', ad.args(sweep_angle=-90 + s.tab_angle, inner_r=s.tab_bevel_r)),
         ('P', ad.args(h=s.tab_l)),
         ('R', ad.args(sweep_angle=-180, inner_r=s.tab_w/2)),
         ('P', ad.args(h=s.tab_l)),
         ('R', ad.args(sweep_angle=-90 + s.tab_angle, inner_r=s.tab_bevel_r)),
         ('R', ad.args(sweep_angle=-180 + s.tab_angle, inner_r=s.knife_handle_r)),
         ))
    
    scaffold_node: ad.Node=ad.ShapeNode(stadium.StadiumSequence, prefix='scaffold_')
    
    fn: int=ad.dtfield(128)
    
    
    xEXAMPLE_ANCHORS=(
        ad.surface_args('handle', 'element-8', 'base'),
        ad.surface_args('handle', 'element-7', 'base'),
        ad.surface_args('handle', 'element-6', 'base'),
        ad.surface_args('handle', 'element-8', 'top'),
        ad.surface_args('handle', 'element-7', 'top'),
        ad.surface_args('handle', 'element-6', 'top'),
 #       ad.surface_args('ubolt', 'element-4', 'stadium', 'right', 0.5, rh=1),
    )
    
    def build(self) -> ad.Maker:
        # Creates a stadium shape sequence of 5 elements.
        scaffold_shape = self.scaffold_node()
        
        maker = scaffold_shape.solid('handle').at('base')
        

        return maker
    
    def overall_width(self):
        p1 = self.maker.at('ubolt', 'element-0', 'stadium', 'right', 0.5)
        p2 = self.maker.at('ubolt', 'element-4', 'stadium', 'right', 0.5, rh=1)
        return ad.distance_between(p1, p2)


@ad.shape
@ad.datatree
class SpringHandleHolder(ad.CompositeShape):
    '''The whole knife holder assembly.
    This is intended to be printed in an elastic material like a flexible TPU/TPE 
    '''
    
    spring_base_node: ad.Node=ad.ShapeNode(SpringBase)
    spring_base: SpringBase=ad.dtfield(self_default=lambda s: s.spring_base_node())

    
    mount_node: ad.Node=ad.ShapeNode(ScabbardMountHole, prefix='mount_')

    def build(self) -> ad.Maker:
        
        maker = self.spring_base.solid('spring_base').at(post=ad.ROTZ_180)
        
        mount_shape = self.mount_node()
        
        mount_maker = mount_shape.solid('mount').at('inner_top', 'top_right', 0.5, post=ad.ROTX_90)
        
        maker.add_at(
            mount_maker,
            'element-0', 'stadium', 'top', 0, post=ad.ROTX_270 * ad.ROTY_270)
        
        
        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
