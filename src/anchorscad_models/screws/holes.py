'''
Created on 9 Feb 2021

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.pipe import Pipe
from anchorscad_models.screws.dims import HoleDimensions, holeMetricDims


@ad.shape
@ad.datatree
class SelfTapHole(ad.CompositeShape):
    thru_len: float
    tap_len: float
    outer_dia: float=None
    dia: object=None
    dims: HoleDimensions=None
    outer_delta: float=6
    overlap_delta: float=0.01
    
    pipe_node: ad.Node=ad.ShapeNode(Pipe, {})
    cylinder_node: ad.Node=ad.ShapeNode(ad.Cylinder, {})
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(thru_len=16, tap_len=8, dia=2.6, fn=20)
    EXAMPLE_ANCHORS=(ad.surface_args('start'), ad.surface_args('bottom'))
    
    def build(self) -> ad.Maker:
        dims = self.dims
        if not dims:
            dims = holeMetricDims(self.dia)
        outer_dia = self.outer_dia
        if not outer_dia:
            outer_dia = dims.thru_dia + self.outer_delta
            self.outer_dia = outer_dia
        
        thru_hole = self.pipe_node(
            h=self.thru_len + self.overlap_delta * 2, 
            inside_r=dims.thru_dia / 2, 
            outside_r=outer_dia / 2)
        tap_hole = self.pipe_node(
            h=self.tap_len + self.overlap_delta * 2, 
            inside_r=dims.tap_dia / 2,
            outside_r=outer_dia / 2)
        cage_cyl = self.cylinder_node(h=self.thru_len + self.tap_len, r=outer_dia / 2)
        maker = cage_cyl.cage('pipe').at('top')
        maker.add_at(thru_hole.composite('thru').at('top'), 'top', pre=ad.tranZ(self.overlap_delta))
        maker.add_at(tap_hole.composite('tap').at('base'), 'base', pre=ad.tranZ(self.overlap_delta))
        
        return maker
        
    @ad.anchor('The entrance point for screws')
    def start(self):
        return self.maker.at('top')
    
    @ad.anchor('The bottom of the screw hole')
    def bottom(self):
        return self.maker.at('base')


@ad.shape
@ad.datatree
class CountersinkAccessHole(ad.CompositeShape):
    access_len: float
    access_dia: float
    counter_sink_overlap: float
    overlap_delta: float=0.01

    cylinder_node: ad.Node=ad.ShapeNode(ad.Cylinder, {})
    code_node: ad.Node=ad.ShapeNode(ad.Cone, {})
    
    EXAMPLE_SHAPE_ARGS=ad.args(access_len=10, access_dia=4.5, counter_sink_overlap=0.5, fn=20)
    
    def build(self) -> ad.Maker:
        access_r = self.access_dia / 2
        access_hole = self.cylinder_node(
            h=self.access_len + self.counter_sink_overlap,
            r=access_r)

        access_hole_cage = self.cylinder_node(
            h=self.access_len,
            r=access_r)
        maker = access_hole_cage.cage('access_hole_cage').at('top')
        maker.add_at(access_hole.hole('access_hole')
                     .at('surface', self.counter_sink_overlap, tangent=False),
                     'surface', 0, tangent=False)
        
        couter_sink_hole = self.code_node(h=access_r, r_base=0, r_top=access_r)
        
        maker.add_at(couter_sink_hole.hole('couter_sink_hole').colour([1,0,0]).at('surface', access_r, tangent=False),
                     'access_hole', 'surface', self.overlap_delta, tangent=False)
        
        return maker


@ad.shape
@ad.datatree
class CountersinkSelfTapHole(ad.CompositeShape):
    '''A self tapped screw hole (two internal diameters) with a extended access hole above
    the screw hole.
    '''
    thru_len: float
    tap_len: float
    access_len: float=1
    access_dia: float=None
    counter_sink_overlap: float=0.5
    outer_dia: float=None
    dia: object=None
    dims: HoleDimensions=None
    outer_delta: float=6
    overlap_delta: float=0.01
    countersink_acccess_hole_node: ad.Node=ad.ShapeNode(CountersinkAccessHole)
    self_tap_hole_node: ad.Node=ad.ShapeNode(SelfTapHole)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        thru_len=10, tap_len=5, access_len=10, 
        access_dia=5, outer_dia=8, dia=2.6, counter_sink_overlap=0.5, fn=180)
    
    def build(self) -> ad.Maker:
        
        self_tap_hole = self.self_tap_hole_node()
        if not self.access_dia:
            self.access_dia = self_tap_hole.outer_dia + self.overlap_delta
        countersink_acccess_hole = self.countersink_acccess_hole_node()
        maker = self_tap_hole.composite('screw_hole').at('top')

        maker.add_at(countersink_acccess_hole.composite('access_hole').at('base', post=ad.ROTX_180),
                     'top')
        return maker


if __name__ == "__main__":
    ad.anchorscad_main(False)
