'''
Created on 30-Jan-2024

@author: gianni

A generic screwed lidded case.
'''

import anchorscad as ad
from anchorscad_models.basic.box_side_bevels import BoxShell, BoxSideBevels
from anchorscad_models.cases.esp32_generic.exp32_assembly import Exp32Assembly
from anchorscad_models.components.sockets.dc_022_a import Dc022aHousing
from anchorscad_models.screws.CountersunkScrew import FlatHeadScrew
from anchorscad_models.screws.holes import CountersinkSelfTapHole

import numpy as np

EPSILON = 1e-2

def expand(v, expansion=EPSILON):
    return np.array(v) + expansion

@ad.shape
@ad.datatree
class CaseShellCutter(ad.CompositeShape):
    '''
    <description>
    '''
    
    size: tuple=ad.dtfield((150, 60, 60), doc='The (x,y,z) size of overall case size')
    cut_depth: float=20
    top_case: bool=True
    cut_z_size: float=ad.dtfield(
        self_default=lambda s: s.cut_depth if s.top_case else (s.size[2] - s.cut_depth))
    cut_size: tuple=ad.dtfield(
        self_default=lambda s: expand((s.size[0], s.size[1], s.cut_z_size)))
    
    
    box_cage_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box))
    box_cut_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='cut_'))

    def build(self) -> ad.Maker:
        shape = self.box_cage_node()
        maker = shape.cage('cage').at('centre')
        #maker = shape.solid('cage').transparent(True).colour('cyan', 0.4).at('centre')
        cut_shape = self.box_cut_node()
        side = 'top' if self.top_case else 'base'
        maker.add_at(
            cut_shape.solid('cutter').at('face_centre', side), 
                     'face_centre', side)
        return maker

@ad.shape
@ad.datatree
class PcbMountingHole(ad.CompositeShape):
    '''
    A mounting hole for a PCB.
    '''

    pcb_screw_hole_shaft_overall_length: float=14
    pcb_screw_hole_shaft_thru_length: float=0
    pcb_screw_hole_tap_len: float=15
    pcb_screw_hole_size_name=ad.dtfield('M2')
    
    pcb_screw_hole_node: ad.Node=ad.dtfield(ad.ShapeNode(FlatHeadScrew, prefix='pcb_screw_hole_'))
    
    def build(self) -> ad.Maker:
        shape = self.pcb_screw_hole_node()
        maker = shape.composite('pcb_screw_hole').at('top')
        return maker


@ad.shape
@ad.datatree
class WiringAccessHole(ad.CompositeShape):
    '''
    A hole for accessing connections on the PCB.
    '''
    
    shell_size: tuple=ad.dtfield(3, doc='The thickness of the shell')
    access_hole_w: float=ad.dtfield(8.5, doc='The width of the access hole')
    access_hole_h: float=ad.dtfield(12, doc='The height of the access hole')
    
    access_hole_size: tuple=ad.dtfield(
        self_default=lambda s: (s.access_hole_w, s.access_hole_h, 10+ s.shell_size + 2 * EPSILON), 
        doc='The (x,y,z) size of the hole')
    
    access_hole_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='access_hole_'))
    
    def build(self) -> ad.Maker:
        shape = self.access_hole_node()
        maker = shape.solid('access_hole').at('centre')
        return maker

@ad.shape
@ad.datatree
class Esp32Shell(ad.CompositeShape):
    '''
    <description>
    '''

    size: tuple=ad.dtfield((115, 90, 29), doc='The (x,y,z) size of Case')
    bevel_radius: float=6.0
    shell_size: float=2.5
    top_case: bool=True
    
    cut_depth: float=25
    
    # case_holes: tuple=ad.dtfield(
    #     ((ad.surface_args('base_cutter', 'cutter', 'face_edge', 'left', 0, 0.25), 5.5),
    #      (ad.surface_args('base_cutter', 'cutter', 'face_edge', 'left', 0, 0.75), 3.5),
    #      (ad.surface_args('base_cutter', 'cutter', 'face_edge', 'right', 0, 0.25), 3.5),
    #      (ad.surface_args('base_cutter', 'cutter', 'face_edge', 'right', 0, 0.75), 3.5),
    #     ),
    #     doc='List of (anchor, hole_radius) pairs for case holes')
    
    fn: int=64
    
    box_shell_node: ad.Node[BoxShell] = ad.dtfield(ad.ShapeNode(BoxShell))
    box_cutter_node: ad.Node[CaseShellCutter] = ad.dtfield(ad.ShapeNode(CaseShellCutter))
    
    case_hole_node: ad.Node[ad.Cylinder]=ad.dtfield(ad.ShapeNode(ad.Cylinder, {}))
    
    screw_mount_r: float=5
    screw_mount_h: float=ad.dtfield(self_default=lambda s: s.size[2])
    
    screw_mount: ad.Node[ad.Cylinder] = \
        ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='screw_mount_'))
        
    screw_mounts: tuple=ad.dtfield(
        (
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[0]),),
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[1]),),
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[2]),),
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[3]),),
        ),
        doc='List of (anchor, hole_radius) pairs for case holes')
    
    pcb_screw_hole_hide_cage: bool=False
    pcb_mounting_hole_node: ad.Node[PcbMountingHole]
    
    exp32_assembly_node: ad.ShapeNode[Exp32Assembly]
    
    screw_hole_len: float=ad.dtfield(25, doc='Overall screw length')
    screw_hole_thru_len: float=ad.dtfield(
        self_default=lambda s: s.size[2] - s.cut_depth)
    screw_hole_tap_len: float=ad.dtfield(
        self_default=lambda s: s.screw_hole_len - s.screw_hole_thru_len)
    screw_hole_dia: float=2.6
    
    screw_hole: ad.Node[CountersinkSelfTapHole]= \
        ad.ShapeNode(CountersinkSelfTapHole, prefix='screw_hole_')
        
    pcb_front_support_size: tuple=ad.dtfield((8, 10), doc='The size of the pcb support')
    
    button_hole_r: float=ad.dtfield(2, doc='The radius of the button hole')
    button_hole_h: float=ad.dtfield(self_default=lambda s: s.shell_size + 2 * EPSILON)
    button_hole_node: ad.Node[ad.Cylinder]=ad.ShapeNode(ad.Cylinder, prefix='button_hole_')
    
    jack_extension: float=ad.dtfield(0)
    jack_extender_hide_cage: bool=ad.dtfield(True)
    jack_shell_thickness: float=ad.dtfield(3)
    jack_housing_node: ad.Node[Dc022aHousing] = ad.ShapeNode(Dc022aHousing, prefix='jack_')
    
    wiring_access_hole_node: ad.ShapeNode[WiringAccessHole]
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    
    EXAMPLE_ANCHORS=(
        # ad.surface_args('face_centre', 'base'),
        # ad.surface_args('inner', 'face_centre', 'right'),
        # ad.surface_args('exp32_assembly', 'mount_hole', 0, 'base'),
        # ad.surface_args('hull', 'centre_of', 'edge_0_5', rh=1, post=ad.translate((-3, -3, 0))),
        
        # ad.surface_args('cut', 'left', 0),
        # ad.surface_args('top_cutter', 'cutter', 'face_edge', 'right', 0),
        # ad.surface_args('top_cutter', 'cutter', 'face_edge', 'right', 0, 0.2),
        # ad.surface_args('top_cutter', 'cutter', 'face_edge', 'right', 0, 0.8),
    )
    
    EXAMPLES_EXTENDED={
        'top': ad.ExampleParams(
            shape_args=ad.args(top_case=True),),
        'bottom': ad.ExampleParams(
            shape_args=ad.args(top_case=False),)
        }


    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.box_shell_node()
        maker = shape.solid('shell').at('centre')
        
        # Add cages for cutters.
        cutter_top_shape = self.box_cutter_node(top_case=True)
        cutter_base_shape = self.box_cutter_node(top_case=True)
        maker.add_at(cutter_top_shape.cage('top_cutter').at('centre'), 'centre')
        maker.add_at(cutter_base_shape.cage('base_cutter').at('centre'), 'centre')
        
        # for i, (anchor, hole_radius) in enumerate(self.case_holes):
        #     case_hole_shape = self.case_hole_node(
        #         r=hole_radius, h=self.shell_size + 2 * EPSILON)
        #     maker.add_at(
        #         case_hole_shape.hole(('case_hole', i)).at('top', post=ad.tranZ(-EPSILON)),
        #         anchor=anchor)
            
        screw_mount_shape = self.screw_mount()
        tap_screw_hole = self.screw_hole()
        for i, (anchor,) in enumerate(self.screw_mounts):
            maker.add_at(
                screw_mount_shape.solid(('mount', i)).at('top'),
                anchor=anchor, post=ad.translate((0, 0, 0)))
            maker.add_at(
                tap_screw_hole.composite(('screw_hole', i)).at('top'),
                ('mount', i), 'top')
            
        fastener_hole_shape = self.pcb_mounting_hole_node(pcb_screw_hole_size_name='M2.6')
        for i in range(4):
            trans = (10, 10, 0) if i != 2 else (15, 5, 0)
            maker.add_at(
                fastener_hole_shape.composite(('fastener_hole', i)).colour('cyan').at('top'),
                'inner', 'face_corner', 'top', i, 
                post=ad.translate(trans) * ad.ROTX_180)
            
        jack_housing_shape = self.jack_housing_node()
        
        maker.add_at(
            jack_housing_shape.composite('jack_housing').colour('blue') \
                .at('base'), 
            'face_edge', 'back', 3, post=ad.translate((1.9, 25, 0)) * ad.ROTZ_180)
        
        wiring_access_hole_shape = self.wiring_access_hole_node()
        maker.add_at(
            wiring_access_hole_shape.hole('wiring_access_hole').colour('magenta') \
                .at('face_centre', 'front'),
            'face_edge', 'right', 3, post=ad.ROTX_90 * ad.ROTY_90 * ad.translate((16, EPSILON, 0.5)))
            
        maker = maker.solid('assembled').at()
        
        cutter_shape = self.box_cutter_node()
        maker.add_at(cutter_shape.solid('cutter').at('centre'), 'centre')
        
        final_maker = maker.intersect('cut_case').at('centre')
        
        exp32_assembly: Exp32Assembly = self.exp32_assembly_node()
        final_maker.add_at(
            exp32_assembly.hole('exp32_assembly').colour("teal").at('mount_hole', 0, 'top'),
            'face_corner', 'top', 1,
            post=ad.ROTX_180 * ad.translate((27, -8, 23)))
        
        # Add pcb support. Note that 0 and 2 are the right most mount holes and we can
        # use the side wall of the case to reinforce it.
        support_width, support_height = \
            self._find_distance_from_mount_hole_to_right_and_top_edge(final_maker)
            
        support_size = (  
                        self.pcb_front_support_size[0],
                        support_width + self.pcb_front_support_size[1] / 2,
                        support_height )
        support_box = ad.Box(support_size)
        for i in (0, 2):
            support_maker = support_box.solid_hole(
                (('pcb_support', i), not self.top_case), not self.top_case) \
                .at('face_edge', 'top', 0)
            final_maker.add_at(support_maker, 
                               'exp32_assembly', 'mount_hole', i, 'base',
                               post=ad.ROTY_180 * ad.ROTZ_180 \
                                   * ad.tranY(-self.pcb_front_support_size[1] / 2))
            
        support_size_other = (  
                self.pcb_front_support_size[0] - 1,
                self.pcb_front_support_size[1],
                support_height )
        support_box_other = ad.Box(support_size_other)
        for i in (1, 3):
            support_maker = support_box_other.solid_hole(
                (('pcb_support', i), not self.top_case), not self.top_case) \
                .at('face_centre', 'top')
            final_maker.add_at(support_maker, 
                               'exp32_assembly', 'mount_hole', i, 'base',
                               post=ad.ROTY_180 * ad.ROTZ_90 * ad.tranX(2.2))
        
        button_hole_shape = self.button_hole_node()
        for i in range(3):
            pos = self._find_button_hole_position(final_maker, i)
            
            final_maker.add_at(
                button_hole_shape.hole(('button_hole', i)).colour('red').at('top'),
                post=pos * ad.ROTX_180 * ad.tranZ(EPSILON))
        
        if self.top_case:
            pcb_mounting_hole_shape = self.pcb_mounting_hole_node()
            for i in range(4):
                final_maker.add_at(
                    pcb_mounting_hole_shape.composite(('pcb_mounting_hole', i)).at('top'),
                    'exp32_assembly', 'mount_hole', i, 'top')
        
        return final_maker
    
    def _find_button_hole_position(self, final_maker: ad.Maker, button: float) -> float:
        mount_hole_frame = final_maker.at(
            'exp32_assembly', ('tactile_switch', button), 'shaft', 'base')
        base_frame = final_maker.at('face_centre', 'base')
        
        return ad.plane_line_intersect(base_frame, mount_hole_frame)
        
    
    def _find_distance_from_mount_hole_to_right_and_top_edge(self, final_maker: ad.Maker) -> float:
        mount_hole_frame = final_maker.at(
            'exp32_assembly', 'mount_hole', 0, 'base')
        rhs_frame = final_maker.at('inner', 'face_centre', 'right')
        top_frame = final_maker.at('face_centre', 'top')
        
        return np.abs(ad.distance_between_point_plane(mount_hole_frame, rhs_frame)), \
            np.abs(ad.distance_between_point_plane(mount_hole_frame, top_frame))

    
    @ad.anchor('Anchor from base cut box.')
    def cut(self, *args, **kwds) -> ad.GMatrix:
        return self.at('base_cutter', 'cutter', 'face_edge', *args, **kwds)



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=2, write_stl_mesh_files=None)

if __name__ == "__main__":
    ad.anchorscad_main()
