'''
Created on 7 Jul 2022
@author: gianni
'''

import anchorscad as ad
from anchorscad.models.basic.sleeve import Sleeve

@ad.datatree
class HingeHolePath:
    sep: float=ad.dtfield(0.4, 'Separation between hinge sides')
    nib_r: float=ad.dtfield(1.3, 'Radius of inner hinge nib')
    nib_ang_len: float=ad.dtfield(3, 'Angle length of inner hinge nib')
    nib_angle: float=ad.dtfield(45, 'Angle degrees of hinge nib')
    edge_len: float=ad.dtfield(1.3, 'Length between nib and edge og hinge')
    
    def build(self):
        
        builder = ad.PathBuilder()
        
        builder.move((0, 0), direction=(0, 1))
        builder.stroke(self.sep, name='centre_line')
        builder.stroke(self.nib_r, degrees=-90, name='inner_nib')
        builder.stroke(self.nib_ang_len, degrees=self.nib_angle, name='i_nib_angle_surface')
        builder.arc_tangent_radius_sweep(radius=self.sep, 
                                         sweep_angle_degrees=-self.nib_angle, 
                                         name='inner_nib_arc')
        builder.stroke(self.edge_len, name='inner_face')
        builder.stroke(self.sep, degrees=-90, name='gap')
        builder.stroke(self.edge_len, degrees=-90, name='outer_face')
        builder.stroke(self.nib_ang_len, degrees=self.nib_angle, name='o_nib_angle_surface')
        builder.arc_tangent_radius_sweep(radius=self.sep, 
                                         sweep_angle_degrees=-self.nib_angle, 
                                         name='outer_nib_arc')
        
        return builder.build()



@ad.shape
@ad.datatree
class HingeHole(ad.CompositeShape):
    '''
    <description>
    '''
    path_node: ad.Node=ad.Node(HingeHolePath)
    rx_path: ad.Path=ad.dtfield(self_default=lambda s:s.path_node().build())
    extrude_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, prefix='rx_')
    
    cage_r: float=ad.dtfield(
            self_default=lambda s: s.rx_path.extents()[1][0],
            init=False)
    cage_h: float=ad.dtfield(
            self_default=lambda s: s.rx_path.extents()[1][1],
            init=False)
    cage_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cylinder, prefix='cage_'), init=False)
    cage_of_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=256, as_cage=False)
    EXAMPLE_ANCHORS=(ad.surface_args('base', scale_anchor=.4),)

    def build(self) -> ad.Maker:
        cage_shape = self.cage_node()
        maker = self.cage_of_node(cage_shape).at('base')
        shape = self.extrude_node()
        maker.add_at(shape.solid('hinge_hole').at(), 
                     'base', rh=1)
        return maker


@ad.shape
@ad.datatree
class HingeBar3X(ad.CompositeShape):
    '''
    <description>
    '''
    epsilon: float=ad.dtfield(0.001, doc='Fudge factor')
    hole_node: ad.Node=ad.ShapeNode(HingeHole)
    hole_shape: ad.Shape=ad.dtfield(
            doc='Shape object for field computation',
            self_default=lambda s: s.hole_node(),
            init=False)
    bar_r: float=ad.dtfield(
            doc='Radius of hinge bar',
            self_default=lambda s: s.hole_shape.cage_r - s.epsilon,
            init=False)
    bar_h: float=ad.dtfield(30, doc='Height of hinge bar')
    cyl_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='bar_'), init=False)
    joint_offset: float=ad.dtfield(7, 'Offset of hinge hole from end of bar')

    sleeve_r: float=ad.dtfield(
            doc='Radius of sleeve',
            self_default=lambda s: s.bar_r + s.sep,
            init=False)
    cyl_sleeve_node: ad.Node=ad.dtfield(ad.ShapeNode(
            ad.Cylinder, prefix='sleeve_', exclude=('h',)), init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=128)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        shape = self.cyl_node()
        maker = shape.solid('bar').at('centre')
        maker.add_at(self.hole_shape.hole('top_hole').at('base'), 
                     'top', post=ad.tranZ(-self.joint_offset))
        maker.add_at(self.hole_shape.hole('base_hole').at('base'), 
                     'base', post=ad.tranZ(-self.joint_offset))
        return maker
    
    def gen_sleeve(self, h):
        return self.cyl_sleeve_node(h=h)
    
    
@ad.shape
@ad.datatree
class HingeBar3XEndHoles(ad.CompositeShape):
    '''
    <description>
    '''
    hinge_bar_shape: HingeBar3X
    cage_of_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(HingeBar3X(fn=128), as_cage=False)
    EXAMPLE_ANCHORS=(ad.surface_args('base', scale_anchor=0.4),
                     ad.surface_args('base_hole', 'base', scale_anchor=0.4))
    
    def build(self) -> ad.Maker:
        maker = self.cage_of_node(self.hinge_bar_shape).at()
        
        maker.add_between(
            target_from=ad.at_spec('top'), 
            target_to=ad.at_spec('top_hole', 'base',
                                 post=ad.tranZ(-self.hinge_bar_shape.sep)),
            lazy_named_shape=
                ad.lazy_shape(self.hinge_bar_shape.gen_sleeve, 'h')
                .solid('top_sleeve'),
            shape_from=ad.at_spec('top'),
            shape_to=ad.at_spec('base'),
            align_axis=ad.Y_AXIS,
            align_plane=ad.X_AXIS)
        
        maker.add_between(
            target_from=ad.at_spec('base_hole', 'base',
                                   post=ad.tranZ(-self.hinge_bar_shape.sep)), 
            target_to=ad.at_spec('base'),
            lazy_named_shape=
                ad.lazy_shape(self.hinge_bar_shape.gen_sleeve, 'h')
                .solid('base_sleeve'),
            shape_from=ad.at_spec('top'),
            shape_to=ad.at_spec('base'),
            align_axis=ad.Y_AXIS,
            align_plane=ad.X_AXIS)
        return maker
    
    
@ad.shape
@ad.datatree
class HingeBar3XMiddleHole(ad.CompositeShape):
    '''
    <description>
    '''
    hinge_bar_shape: HingeBar3X
    cage_of_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(HingeBar3X(fn=128), as_cage=False)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        maker = self.cage_of_node(self.hinge_bar_shape).at()
        maker.add_between(
            target_from=ad.at_spec('top_hole', 'base'), 
            target_to=ad.at_spec('base_hole', 'base'),
            lazy_named_shape=
                ad.lazy_shape(self.hinge_bar_shape.gen_sleeve, 'h').solid('top_sleeve'),
            shape_from=ad.at_spec('top'),
            shape_to=ad.at_spec('base'),
            align_axis=ad.Y_AXIS,
            align_plane=ad.X_AXIS)
        return maker
    

@ad.shape
@ad.datatree
class Hinge3XTestPrint(ad.CompositeShape):
    '''
    <description>
    '''
    bar_node: ad.Node=ad.ShapeNode(HingeBar3X,  
                                           {'as_cage': 'bar_cage_as_cage'},
                                           expose_all=True)
    hinge_bar_shape: ad.Shape=ad.dtfield(
            self_default=lambda s: s.bar_node(), init=False)
    sleeves_node: ad.Node=ad.ShapeNode(HingeBar3XEndHoles, 
                                           {'as_cage': 'bar_ends_as_cage'},
                                           expose_all=True)
    sleeve_middle_node: ad.Node=ad.ShapeNode(HingeBar3XMiddleHole, 
                                           {'as_cage': 'bar_middle_as_cage'},
                                           expose_all=True)
    
    cage_size: tuple=ad.dtfield(
            self_default=lambda s: (s.bar_h,
                       s.bar_h * 2,
                       s.hinge_bar_shape.bar_r * 2,), 
            doc='Size of cage')
    cage_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    cage_of_node: ad.Node=ad.CageOfNode()
    
    plate_size: tuple=ad.dtfield(
            self_default=lambda s: (s.bar_h,
                       s.cage_size[1] / 2,
                       s.hinge_bar_shape.bar_r,), 
            doc='Size of plate')
    plate_node: ad.Node=ad.ShapeNode(ad.Box, prefix='plate_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(as_cage=True,
                               bar_middle_as_cage=True,
                               bar_ends_as_cage=True,
                               sep=0.1,
                               fn=128)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        cage_shape = self.cage_node()
        plate_shape = self.plate_node()
        maker = self.cage_of_node(cage_shape).at('face_centre', 'base')

        etched_plate_ends = plate_shape.solid('plate_1').colour((1,0,0)).at()
        sleeve_ends = self.sleeves_node()
        etched_plate_ends.add_at(
            sleeve_ends.hole('sleeve_ends')
            .at('centre', post=ad.ROTY_90), 
            'face_edge', 'top', 0)

        etched_plate_mid = plate_shape.solid('plate_2').colour((0,0,1)).at()
        sleeve_mid = self.sleeve_middle_node()
        etched_plate_mid.add_at(
            sleeve_mid.hole('sleeve_middle')
            .at('centre', post=ad.ROTY_90), 
            'face_edge', 'top', 0)
        
        maker.add_at(etched_plate_ends.solid('plate_1')
                     .at('face_edge', 'base', 0), 
                     'face_edge', 'base', 0)
        maker.add_at(etched_plate_mid.solid('plate_2')
                     .at('face_edge', 'base', 0), 
                     'face_edge', 'base', 2)
        
        maker.add_at(self.hinge_bar_shape.composite('bar').at('centre'), 
                     'plate_1', 'sleeve_ends', 'centre')
        return maker
    
    
@ad.shape
@ad.datatree
class HingeBar(ad.CompositeShape):
    '''
    <description>
    '''
    epsilon: float=ad.dtfield(0.001, doc='Fudge factor')
    hole_node: ad.Node=ad.ShapeNode(HingeHole)
    hole_shape: ad.Shape=ad.dtfield(
            doc='Shape object for field computation',
            self_default=lambda s: s.hole_node(),
            init=False)
    bar_r: float=ad.dtfield(
            doc='Radius of hinge bar',
            self_default=lambda s: s.hole_shape.cage_r - s.epsilon,
            init=False)
    bar_h: float=ad.dtfield(30, doc='Height of hinge bar')
    cyl_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='bar_'), init=False)
    seg_count: int=ad.dtfield(7, 'Number of segments in hinge bar')

    sleeve_r: float=ad.dtfield(
            doc='Radius of sleeve',
            self_default=lambda s: s.bar_r + s.sep,
            init=False)
    cyl_sleeve_node: ad.Node=ad.dtfield(ad.ShapeNode(
            Sleeve, prefix='sleeve_', exclude=('h',)), init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        shape = self.cyl_node()
        maker = shape.solid('bar').at('centre')
        
        segment_size = self.bar_h / (self.seg_count + 1)
        for i in range(self.seg_count):
            joint_offset = (1 + i) * segment_size
            maker.add_at(self.hole_shape.hole(('hole', i)).at('base'), 
                         'top', post=ad.tranZ(-joint_offset))
        return maker
    
    def gen_sleeve(self, h, ir=None):
        inside_r = self.bar_r if ir is None else ir
        return self.cyl_sleeve_node(h=h, 
                                    inside_r=inside_r,
                                    outside_r=self.sleeve_r,
                                    start_degrees=0, 
                                    end_degrees=180)
    
    def gen_end(self, h):
        return self.gen_sleeve(h, 0)


@ad.shape
@ad.datatree
class HingeBarSleeveHoles(ad.CompositeShape):
    '''
    <description>
    '''
    hinge_bar_shape: HingeBar
    cage_of_node: ad.Node=ad.CageOfNode()
    side: int=ad.dtfield(
            0, '0 or 1 for left or right sides of hinge bar')
    
    EXAMPLE_SHAPE_ARGS=ad.args(HingeBar(fn=8, seg_count=7, bar_h=50), 
                               side=1, 
                               as_cage=False)
    EXAMPLE_ANCHORS=(ad.surface_args('base', scale_anchor=0.4),
                     ad.surface_args(('hole', 0), 'base', scale_anchor=0.4))
    
    def build(self) -> ad.Maker:
        maker = self.cage_of_node(self.hinge_bar_shape).at()
        sep = self.hinge_bar_shape.sep
        seg_count = self.hinge_bar_shape.seg_count
        
        for i in range(self.side, 
                       seg_count + 1, 
                       2):
            
            target_from=self.anchor_for(i - 1)
            length = self.length_between(
                maker,
                target_from=target_from, 
                target_to=self.anchor_for(i,
                        post=ad.tranZ(-sep)))
            
            sleeve = self.hinge_bar_shape.gen_sleeve(length)
            
            maker.add_at(sleeve.solid(('sleeve', i))
                         .at('base'),
                         anchor=target_from)
            
        if not self.side:
            end = self.hinge_bar_shape.gen_end(sep)
            target_from = self.anchor_for(-1)
            maker.add_at(end.solid('sleeve_base').at('base'),
                         anchor=target_from,
                         post=ad.tranZ(sep))
            
        if self.side == seg_count % 2:
            end = self.hinge_bar_shape.gen_end(sep)
            target_from = self.anchor_for(seg_count)
            maker.add_at(end.solid('sleeve_top').at('base'),
                         anchor=target_from)        
        
        return maker
    
    def length_between(self, source_maker, target_from, target_to):
        '''Returns the length between the two anchors'''
    
        # Get start and end points.
        from_vec = target_from.apply(source_maker).get_translation()
        to_vec = target_to.apply(source_maker).get_translation()
        
        # Need the diff vector to align to.
        diff_vector = from_vec - to_vec
        
        # The length allows us to build the shape now.
        length = diff_vector.length()
        return length
    
    def anchor_for(self, i, *args, **kwds):
        if i == -1:
            return ad.surface_args('top')
        elif i == self.hinge_bar_shape.seg_count:
            return ad.surface_args('top', rh=1)
        return ad.surface_args(('hole', i), 'base', *args, **kwds)
    

@ad.shape
@ad.datatree
class Hinge(ad.CompositeShape):
    '''
    <description>
    '''
    bar_node: ad.Node=ad.ShapeNode(HingeBar,  
                                           {'as_cage': 'bar_cage_as_cage'},
                                           expose_all=True)
    hinge_bar_shape: ad.Shape=ad.dtfield(
            self_default=lambda s: s.bar_node(), init=False)
    sleeves_node: ad.Node=ad.ShapeNode(
        HingeBarSleeveHoles, 
        {'as_cage': 'bar_ends_as_cage'},
        exclude=('side',),
        expose_all=True)    
    
    EXAMPLE_SHAPE_ARGS=ad.args(sep=0.5,
                               seg_count=14,
                               bar_h=80,
                               fn=32)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        maker = self.hinge_bar_shape.composite('bar').at('centre')
        
        sleeve_evens = self.sleeves_node(side=0)
        maker.add_at(
            sleeve_evens.hole('sleeve_evens')
            .at('centre'), 
            'centre')        
        sleeve_odds = self.sleeves_node(side=1)
        maker.add_at(
            sleeve_odds.hole('sleeve_odds')
            .at('centre', post=ad.ROTZ_180), 
            'centre')
        return maker
    

@ad.shape
@ad.datatree
class HingeTestPrint(ad.CompositeShape):
    '''
    <description>
    '''
    bar_node: ad.Node=ad.ShapeNode(HingeBar,  
                                           {'as_cage': 'bar_cage_as_cage'},
                                           expose_all=True)
    hinge_bar_shape: ad.Shape=ad.dtfield(
            self_default=lambda s: s.bar_node(), init=False)
    sleeves_node: ad.Node=ad.ShapeNode(
        HingeBarSleeveHoles, 
        {'as_cage': 'bar_ends_as_cage'},
        exclude=('side',),
        expose_all=True)
    
    cage_size: tuple=ad.dtfield(
            self_default=lambda s: (s.bar_h,
                       s.bar_h * 2,
                       s.hinge_bar_shape.bar_r * 2,), 
            doc='Size of cage')
    cage_node: ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    cage_of_node: ad.Node=ad.CageOfNode()
    
    plate_size: tuple=ad.dtfield(
            self_default=lambda s: (s.bar_h + 3,
                       s.cage_size[1] / 2,
                       s.hinge_bar_shape.bar_r,), 
            doc='Size of plate')
    plate_node: ad.Node=ad.ShapeNode(ad.Box, prefix='plate_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(as_cage=True,
                               sep=0.5,
                               seg_count=7,
                               fn=8)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> ad.Maker:
        cage_shape = self.cage_node()
        plate_shape = self.plate_node()
        maker = self.cage_of_node(cage_shape).at('face_centre', 'base')

        etched_plate_evens = plate_shape.solid('plate_evens').colour((1,0,0)).at()
        sleeve_evens = self.sleeves_node(side=0)
        etched_plate_evens.add_at(
            sleeve_evens.hole('sleeve_evens')
            .at('centre', post=ad.ROTY_90), 
            'face_edge', 'top', 0)

        etched_plate_odds = plate_shape.solid('plate_odds').colour((0,0,1)).at()
        sleeve_odds = self.sleeves_node(side=1)
        etched_plate_odds.add_at(
            sleeve_odds.hole('sleeve_odds')
            .at('centre', post=ad.ROTY_270), 
            'face_edge', 'top', 0)
        
        maker.add_at(etched_plate_evens.solid('plate_evens')
                     .at('face_edge', 'base', 0), 
                     'face_edge', 'base', 0)
        maker.add_at(etched_plate_odds.solid('plate_odds')
                     .at('face_edge', 'base', 0), 
                     'face_edge', 'base', 2)
        
        maker.add_at(self.hinge_bar_shape.composite('bar').at('centre'), 
                     'plate_evens', 'sleeve_evens', 'centre')
        return maker
    
    
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()