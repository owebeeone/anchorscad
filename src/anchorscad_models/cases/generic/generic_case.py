'''
Created on 30-Jan-2024

@author: gianni

A generic screwed lidded case.
'''

import anchorscad as ad
from anchorscad_models.basic.box_side_bevels import BoxShell, BoxSideBevels
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
class CaseShell(ad.CompositeShape):
    '''
    <description>
    '''

    size: tuple=ad.dtfield((210, 76, 30), doc='The (x,y,z) size of Case')
    bevel_radius: float=6.0
    shell_size: float=2.5
    top_case: bool=True
    
    cut_depth: float=20
    
    case_holes: tuple=ad.dtfield(
        ((ad.surface_args('base_cutter', 'cutter', 'face_edge', 'left', 0, 0.25), 5.5),
         (ad.surface_args('base_cutter', 'cutter', 'face_edge', 'left', 0, 0.75), 3.5),
         (ad.surface_args('base_cutter', 'cutter', 'face_edge', 'right', 0, 0.25), 3.5),
         (ad.surface_args('base_cutter', 'cutter', 'face_edge', 'right', 0, 0.75), 3.5),
        ),
        doc='List of (anchor, hole_radius) pairs for case holes')
    
    fn: int=64
    
    box_shell_node: ad.Node=ad.dtfield(ad.ShapeNode(BoxShell))
    box_cutter_node: ad.Node=ad.dtfield(ad.ShapeNode(CaseShellCutter))
    
    case_hole_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, {}))
    
    screw_mount_r: float=5
    screw_mount_h: float=ad.dtfield(self_default=lambda s: s.size[2])
    
    screw_mount: ad.Node=ad.dtfield(ad.ShapeNode(ad.Cylinder, prefix='screw_mount_'))
        
    screw_mounts: tuple=ad.dtfield(
        (
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[0]),),
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[1]),),
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[2]),),
            (ad.surface_args('hull', 'centre_of', BoxSideBevels.EDGE[3]),),
        ),
        doc='List of (anchor, hole_radius) pairs for case holes')
    
    screw_hole_len: float=ad.dtfield(25, doc='Overall screw length')
    screw_hole_thru_len: float=ad.dtfield(
        self_default=lambda s: s.size[2] - s.cut_depth)
    screw_hole_tap_len: float=ad.dtfield(
        self_default=lambda s: s.screw_hole_len - s.screw_hole_thru_len)
    screw_hole_dia: float=2.6
    
    screw_hole: ad.Node=ad.dtfield(ad.ShapeNode(CountersinkSelfTapHole, prefix='screw_hole_'))
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=16)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('hull', 'centre_of', 'edge_0_5', rh=1, post=ad.translate((-3, -3, 0))),
        ad.surface_args('cut', 'left', 0),
        ad.surface_args('top_cutter', 'cutter', 'face_edge', 'right', 0),
        ad.surface_args('top_cutter', 'cutter', 'face_edge', 'right', 0, 0.2),
        ad.surface_args('top_cutter', 'cutter', 'face_edge', 'right', 0, 0.8),
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
        
        for i, (anchor, hole_radius) in enumerate(self.case_holes):
            case_hole_shape = self.case_hole_node(
                r=hole_radius, h=self.shell_size + 2 * EPSILON)
            maker.add_at(
                case_hole_shape.hole(('case_hole', i)).at('top', post=ad.tranZ(-EPSILON)),
                anchor=anchor)
            
        screw_mount_shape = self.screw_mount()
        tap_screw_hole = self.screw_hole()
        for i, (anchor,) in enumerate(self.screw_mounts):
            maker.add_at(
                screw_mount_shape.solid(('mount', i)).at('top'),
                anchor=anchor, post=ad.translate((0, 0, 0)))
            maker.add_at(
                tap_screw_hole.composite(('screw_hole', i)).at('top'),
                ('mount', i), 'top')
            
        maker = maker.solid('assembled').at()
        
        cutter_shape = self.box_cutter_node()
        maker.add_at(cutter_shape.solid('cutter').at('centre'), 'centre')
            
        #return maker
        return maker.intersect('cut_case').at('centre')
    
    @ad.anchor('Anchor from base cut box.')
    def cut(self, *args, **kwds) -> ad.GMatrix:
        return self.at('base_cutter', 'cutter', 'face_edge', *args, **kwds)



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
