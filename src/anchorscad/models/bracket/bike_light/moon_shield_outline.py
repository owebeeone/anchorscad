'''
The brackets on the Moon Shield bike light often fail. These are held
on by a 2.2M screw. This is a replacement bracket for mounting on the
back of a bike bag.
    
Created on 30-Apr-2023

@author: gianni
'''

import anchorscad as ad
from anchorscad.core import Maker
from anchorscad.models.basic.spherical_cap import SphericalCap
from anchorscad.models.screws.CountersunkScrew import CountersunkScrew


@ad.shape
@ad.datatree
class MoonShieldOutline(ad.CompositeShape):
    '''
    This outlines the mounting holes for the Moon Shield bike light.
    '''

    cage_size: tuple=ad.dtfield(
        default=(56, 37, 24),
        doc='cage represents the moon shield light primary body.')
    cage_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='cage_'))
    cage_of_node: ad.Node=ad.CageOfNode()
    
    mount_boss_x_offset: float=ad.dtfield(
        default=25.6,
        doc='The offset of the centre of the boss from the edge of the cage.')
    
    mount_boss_r: float=ad.dtfield(
        default=5.15 / 2,
        doc='The radius of the boss.')
    
    mount_boss_h: float=ad.dtfield(
        default=2.35,
        doc='The height of the boss.')
    
    mount_boss_cyl_node: ad.Node=ad.dtfield(
        default=ad.ShapeNode(ad.Cylinder, prefix='mount_boss_'))
    
    mount_boss_chamfer_size: tuple=ad.dtfield(
        self_default=lambda s: (
            4.5, s.mount_boss_r * 2, s.mount_boss_h + s.epsilon),
        doc='The size of the chamfer on the boss.')
    
    mount_boss_chamfer_node: ad.Node=ad.dtfield(
        default=ad.ShapeNode(ad.Box, prefix='mount_boss_chamfer_'))
    
    rib_size: tuple=ad.dtfield(
        default=(5.1, 1.1, 1.5),
        doc='The size of the rib.')
    
    rib_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='rib_'))
    
    rib_separation: float=ad.dtfield(
        default=6.43,
        doc='The separation of the ribs centres.')
    
    rib_cage_size: tuple=ad.dtfield(
        self_default=lambda s: (
            s.rib_size[0], s.rib_separation, s.rib_size[2]),
        doc='Size of the rib separation cage.')
    
    rib_cage_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='rib_cage_'))
    
    rib_boss_offset: float=ad.dtfield(
        default=5.9,
        doc='The offset between the ribs and boss.')
    
    epsilon: float=ad.dtfield(0.01, doc='An epsilon value for tearing suppression.')
    
    EXAMPLE_SHAPE_ARGS=ad.args(as_cage=False, fn=32)
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_edge', 'top', 3),
        ad.surface_args('boss', 'surface', 0, -90),
        ad.surface_args('boss', 'chamfer', 'face_edge', 'right', 0),
    )

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        cage_shape = self.cage_node()
        maker = self.cage_of_node(cage_shape).at('face_centre', 'top')
        
        boss_shape = self.mount_boss_cyl_node()
        boss = boss_shape.solid('boss_cylinder').at('top', rh=1)
        
        boss.add_at(
            self.mount_boss_chamfer_node().solid('chamfer')
                #.colour((1, 0, 0, 0.2)).transparent(True)
                .at('face_edge', 'left', 0),
            'surface', 0, -90
        )
        
        maker.add_at(
            boss.intersect('boss').at(),
            'face_edge', 'top', 3, post=ad.tranY(self.mount_boss_x_offset))
        
        rib_shape = self.rib_node()
        
        rib_cage_shape = self.rib_cage_node()
        rib_cage = self.cage_of_node(
                rib_cage_shape, 
                properties=ad.CageOfProperties(colour=(1.0, 0.0, 0.35, 0.5))
            ).at('face_edge', 'left', 0,
                 post=ad.tranY(rib_cage_shape.size[2]) * ad.ROTX_180)
            
        rib_cage.add_at(
            rib_shape.solid('rib_right').at('face_centre', 'front'),
            'face_centre', 'front', post=ad.ROTX_180)
        rib_cage.add_at(
            rib_shape.solid('rib_left').at('face_centre', 'back'),
            'face_centre', 'back', post=ad.ROTX_180)
        
        maker.add_at(
            rib_cage.solid('rib_cage').at(),
            'boss', 'chamfer', 'face_edge', 'right', 0,
            pre=ad.tranX(self.rib_boss_offset))
        
        return maker


@ad.datatree
class BasicClipPath:
    h: float=ad.dtfield(40, doc='The height of the path.')
    d: float=ad.dtfield(15, doc='The depth of the clip.')
    base_w: float=ad.dtfield(4, doc='The width of the clip at the base.')
    outer_w: float=ad.dtfield(2.5, doc='The width at the outer part.')
    curvature: float=ad.dtfield(0.95, doc="Relative spline curvature.")
    outer_lower_w: float=ad.dtfield(2, doc='The width at the lower part.')
    lower_h: float=ad.dtfield(10, doc='The height of the lower curve')
    lower_curvature: float=ad.dtfield(0.6, doc="Relative spline curvature.")
    separation: float=ad.dtfield(0.15, doc='The separation between upper and lower.')
    
    end_d: float=ad.dtfield(4, doc='The depth of the end.')
    end_h: float=ad.dtfield(2, doc='The height of the end.')
    end_w: float=ad.dtfield(2, doc='The width of the end.')
    
    def build(self):
        base_h = self.h - self.d / 2
        inner_curve_size = self.curvature * self.d / 2
        inner_x_pos = self.base_w
        outer_upper_x_pos = self.d - self.outer_w
        
        upper_outer_curve_size = self.curvature * (self.d / 2 + self.base_w)
        base_outer_curve_size = self.curvature * (self.d / 2 + self.base_w)
        
        lower_outer_curve_size = self.lower_curvature * (self.d / 2 + self.outer_lower_w)
        lower_outer_curve_size = self.lower_curvature * (self.d / 2 + self.outer_lower_w)
        
        
        inner_x_pos_sep = inner_x_pos + self.separation
        
        inner_end_x_pos = inner_x_pos_sep + self.end_d
        inner_end_y_pos = self.end_h
        
        path = (ad.PathBuilder()
                .move((0, 0), direction=(1, 0))
                .spline((
                    (inner_x_pos, 0),
                    (inner_x_pos, inner_x_pos)),
                    cv_len=(inner_x_pos / 2, inner_x_pos / 2),
                    name='base_curve'
                    )
                .line((inner_x_pos, base_h), 'inner_base')
                .spline(
                    ((inner_x_pos, base_h + inner_curve_size),
                    (outer_upper_x_pos, base_h + inner_curve_size),
                    (outer_upper_x_pos, base_h)),
                    name='upper_inner_curve'
                )
                
                .spline(
                    ((inner_x_pos_sep, base_h),
                     (inner_x_pos_sep, self.lower_h)),
                    cv_len=(lower_outer_curve_size, lower_outer_curve_size),
                    name='lower_inner_curve'
                )
                
                .spline(
                    ((inner_end_x_pos - 0.3, inner_end_y_pos + 0.3),
                    (inner_end_x_pos, inner_end_y_pos)),
                    cv_len=(lower_outer_curve_size / 2, lower_outer_curve_size / 2),
                    name='end_inner_curve')
                
                .spline(
                    ((inner_x_pos_sep + self.outer_lower_w, self.lower_h -1),
                     (inner_x_pos_sep + self.outer_lower_w, self.lower_h)), 
                    cv_len=(lower_outer_curve_size, lower_outer_curve_size / 2),
                    name='end_outer_curve')

                
                .spline(((self.d, self.lower_h),
                         (self.d, base_h)), 
                        degrees=(0, 0),
                        cv_len=(lower_outer_curve_size, lower_outer_curve_size),
                        name='lower_outer_curve')
                
                .spline(
                    ((self.d, base_h + upper_outer_curve_size ),
                     (0, base_h + base_outer_curve_size ),
                     (0, base_h)),
                    name='upper_outer_curve')
                .line((0, 0), 'outer_base')
                ).build()
        
        return path

@ad.shape
@ad.datatree
class BasicClipShape(ad.CompositeShape):
    '''
    This is the bracket for the bike bag.
    '''
    h: float=ad.dtfield(17, doc='The depth of the clip.')
    n: int=ad.dtfield(3, doc='The number of caps.')
    cap_r: int=ad.dtfield(
        self_default=lambda s: s.path_base_w / 2, doc='The radius of the caps.')
    path_node: ad.Node=ad.dtfield(ad.ShapeNode(BasicClipPath, prefix='path_'))
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_node().build(), init=False)
    extrude_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.LinearExtrude))
    spherical_cap_node: ad.Node=ad.ShapeNode(SphericalCap, {'r': 'cap_r'})
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)

    def build(self) -> ad.Maker:
        
        clip_shape = self.extrude_node()
        
        maker = clip_shape.solid('clip').at('outer_base', 0.5)
        
        cap_hole_shape = self.spherical_cap_node(r=self.path_base_w / 2, degrees=65)
        
        for i in range(self.n):
            rh = 1 / (1 + self.n) * (i + 1)
            maker.add_at(cap_hole_shape.hole(('cap_hole', i)).at('centre'), 
                         'clip', 'end_inner_curve', rh=rh, post=ad.tranZ(-0.75))

        maker = maker.solid('clip_with_hole').at()
                
        cap_solid_shape = self.spherical_cap_node(r=self.path_base_w / 2 - 0.5, degrees=100)
        
        for i in range(self.n):
            maker.add_at(cap_solid_shape.solid(('cap_solid', i)).at('centre'),
                        ('cap_hole', i), 'centre')
        return maker

@ad.shape
@ad.datatree
class MoonShieldClip(ad.CompositeShape):
    '''
    A moon shield clip.
    '''

    clip_shape_node: ad.Node=ad.ShapeNode(BasicClipShape, prefix='clip_')
    outline_node: ad.Node=ad.ShapeNode(MoonShieldOutline, prefix='outline_')
    epsilon: float=ad.dtfield(0.1, doc='The epsilon for the clip.')
    
    screw_shaft_overall_length: float=ad.dtfield(
        self_default=lambda s: s.clip_path_base_w)
    screw_shaft_thru_length: float=ad.dtfield(
        self_default=lambda s: s.clip_path_base_w - s.outline_mount_boss_h)
    screw_size_name: str='M2.6'
    screw_include_thru_shaft: bool=True
    screw_include_tap_shaft: bool=True
    screw_access_hole_depth:float=ad.dtfield(
        self_default=lambda s: s.clip_path_d + 1)
    screw_as_solid: bool=False
    screw_node: ad.Node=ad.dtfield(ad.ShapeNode(CountersunkScrew, prefix='screw_'))
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    
    def build(self) -> Maker:
        
        maker = self.outline_node().hole('outline').at()
        
        clip_shape = self.clip_shape_node()
        
        maker.add_at(clip_shape.solid('clip').at('outer_base', 0.4, rh=0.5),
                     'boss', 'base', post=ad.ROTZ_270 * ad.tranZ(-self.epsilon))
        
        screw_shape = self.screw_node()
        
        maker.add_at(screw_shape.composite('screw').at('thru_shaft', 'base'),
            'outline', 'boss', 'base', rh=1)
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True, write_path_files=True)

if __name__ == "__main__":
    ad.anchorscad_main()
