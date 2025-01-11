'''

Provides a box shape with bevels on 4 sides. The top and bottom edges
are not beveled.

Created on 25 Jan 2021
@author: gianni

'''

from dataclasses import dataclass, field

import anchorscad as ad
import anchorscad.extrude as e
import numpy as np

EPSILON = 1.e-10


@ad.shape
@ad.datatree
class BoxSideBevels(ad.CompositeShape):
    '''
    Creates a box with bevels on 4 size (flat top and bottom) using extrusion.
    '''
    size: tuple=(30., 20., 10.)
    bevel_radius: float=2.0
    cageof_node: ad.Node=field(
        default=ad.Node(ad.cageof, prefix='cage_'), init=False)
    fn: int=None
    fa: float=None
    fs: float=None

    EXAMPLE_SHAPE_ARGS=ad.args([100., 80., 40.], bevel_radius=8, fn=20)
    EXAMPLE_ANCHORS=tuple(
        (ad.surface_args('face_corner', f, c)) for f in (0, 3) for c in range(4)
        ) + tuple(ad.surface_args('face_edge', f, c) for f in (1, 3) for c in range(4)
        ) + tuple(ad.surface_args('face_centre', f) for f in (0, 3)
        ) + (
            ad.surface_args('face_edge', 2, 2, 0.1),
            ad.surface_args('face_edge', 2, 2, -0.5),
             ad.inner_args('centre'),)
        
    EXAMPLES_EXTENDED={
        'show_cage': ad.ExampleParams(
            shape_args=ad.args([50., 30., 20.], 8,
                                cage_hide_cage=False,
                                fn=64),
            anchors=(ad.surface_args('face_edge', 0, 0),))
        }
    
    EDGE=('edge_0_5', 'edge_5_3', 'edge_3_2', 'edge_3_0')
    

    def build(self) -> ad.Maker:
        shape = ad.Box(self.size)
        maker = self.cageof_node(shape, cage_name='shell').at('centre')
        
        
        r = self.bevel_radius
        if r <= EPSILON:
            maker.add_at(shape.solid('hull').at('centre'), 'centre')
        else: 
            sx = self.size[0]
            sy = self.size[1]
            sz = self.size[2]
            metadata = ad.ModelAttributes(fn=self.fn, fa=self.fa, fs=self.fs)
            path = (ad.PathBuilder()
                    .move([r, 0])
                    .line([sx - r, 0], 'face_0')
                    .arc_tangent_point([sx, r], name=self.EDGE[0], metadata=metadata)
                    .line([sx, sy - r], 'face_5')
                    .arc_tangent_point([sx - r, sy], name=self.EDGE[1], metadata=metadata)
                    .line([r, sy], 'face_3')
                    .arc_tangent_point([0, sy - r], name=self.EDGE[2], metadata=metadata)
                    .line([0, r], 'face_2')
                    .arc_tangent_point([r, 0], name=self.EDGE[3], metadata=metadata)
                    .build())
            
            maker.add_at(
                e.LinearExtrude(path, h=sz).solid('hull').at('face_0', 0.5, 0),
                'face_edge', 0, 0)
        return maker


@ad.shape
@dataclass
class BoxShell(ad.CompositeShape):
    '''
    Creates a box with the same box type hollowed out.
    '''
    size: tuple=(30., 20., 10.)
    bevel_radius: float=2.0
    shell_size: float=1.0
    box_class: type=BoxSideBevels
    fn: int=None
    fa: float=None
    fs: float=None
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        [100., 80., 40.], bevel_radius=8, shell_size=1.5, fn=20)
    
    EXAMPLE_ANCHORS=BoxSideBevels.EXAMPLE_ANCHORS
    
    def build(self) -> ad.Maker:
        size = np.array(self.size)
        centre_size = size - self.shell_size
        inner_size = size - 2 * self.shell_size
        if self.bevel_radius > self.shell_size:
            inner_bevel = self.bevel_radius - self.shell_size
        else:
            inner_bevel= 0
        
        if self.bevel_radius > self.shell_size / 2:
            centre_bevel = self.bevel_radius - self.shell_size
        else:
            centre_bevel= 0
            
        
        params = ad.non_defaults_dict(self, include=('fn', 'fa', 'fs'))
        
        outer_box = self.box_class(size=self.size, bevel_radius=self.bevel_radius, **params)
        centre_cage_box = self.box_class(size=centre_size, bevel_radius=centre_bevel, **params)
        inner_box = self.box_class(size=inner_size, bevel_radius=inner_bevel, **params)
        
        maker = outer_box.solid('outer').at('centre')
        maker.add(centre_cage_box.cage('shell_centre').at('centre'))
        maker.add(inner_box.hole('inner').at('centre'))
        
        return maker


@ad.shape
@dataclass
class BoxOpenShell(ad.CompositeShape):
    '''
    Creates a box with the same box type but open at the top.
    '''
    size: tuple=(30., 20., 10.)
    bevel_radius: float=2.0
    shell_size: float=1.0
    box_class: type=BoxSideBevels
    z_adjust: float=0.0
    fn: int=None
    fa: float=None
    fs: float=None
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        [100., 80., 40.], bevel_radius=8, shell_size=3, z_adjust=-.01, fn=20)
    
    EXAMPLE_ANCHORS=BoxSideBevels.EXAMPLE_ANCHORS
    
    def build(self) -> ad.Maker:
        size = np.array(self.size)
        inner_size = size - np.array([2, 2, 1]) * self.shell_size
        if self.bevel_radius > self.shell_size:
            inner_bevel = self.bevel_radius - self.shell_size
        else:
            inner_bevel= 0
        
        params = ad.non_defaults_dict(self, include=('fn', 'fa', 'fs'))
        
        outer_box = self.box_class(size=self.size, bevel_radius=self.bevel_radius, **params)
        inner_box = self.box_class(size=inner_size, bevel_radius=inner_bevel, **params)
        
        maker = outer_box.solid('outer').at('centre')
        maker.add_at(inner_box.hole('inner').at(
            'face_centre', 4, pre=ad.translate([0, 0, self.z_adjust])), 'face_centre', 4)
        
        return maker
        


@ad.shape
@dataclass
class BoxCutter(ad.CompositeShape):
    ''''''
    model: ad.Shape   # The model to be cut
    cut_size: tuple=(200, 200, 200)
    cut_face: int=1
    post: ad.GVector=ad.IDENTITY
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        BoxShell([100., 80., 40.], bevel_radius=8, shell_size=1.5, fn=40), 
        post=ad.translate([0, 0, 10]) * ad.ROTY_180)
    
    EXAMPLE_ANCHORS=BoxSideBevels.EXAMPLE_ANCHORS
    
    def build(self):
        maker = self.model.composite('main').at()
        maker.add(ad.Box(self.cut_size).hole('cut_box').at(
            'face_centre', self.cut_face, post=self.post))
        
        return maker

MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
