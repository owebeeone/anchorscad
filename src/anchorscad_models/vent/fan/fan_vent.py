'''
Created on 28 Sep 2021

@author: gianni
'''

from anchorscad import datatree, Node, tranZ, ROTY_180, shape, CompositeShape, \
                       cageof, ShapeNode, args, Maker, Box, ModeShapeFrame, \
                       anchor, anchorscad_main

from anchorscad_models.basic.pipe import Pipe
from anchorscad_models.screws.dims import holeMetricDims 
from anchorscad_models.grille.round.CurlySpokes import CurlySpokes


@datatree(frozen=True)
class FanVentScrewHoleParams:
    '''Fan vent screw hole parameters.'''
    size: tuple=(30, 30, 7.4),
    screw_support_dia: float=4.7,
    screw_support_depth: float=2.3,
    screw_centres: float=(27.3 + 20.6) / 2,
    curl_inner_angle: float=0
    r_outer: float=29.0 / 2
    r_inner: float=12.0 / 2


FAN_30x7_TYPE1=FanVentScrewHoleParams(
    size=(30, 30, 7.4),
    screw_support_dia=4.7,
    screw_support_depth=2.3,
    screw_centres=(27.3 + 20.6) / 2,
    curl_inner_angle=0)

FAN_30x7_TYPE2=FanVentScrewHoleParams(
    size=(30, 30, 7.7),
    screw_support_dia=4.3,
    screw_support_depth=3.1,
    screw_centres=(28.52 + 19.41) / 2,
    curl_inner_angle=-30)

FAN_30x7_TYPE3=FanVentScrewHoleParams(
    size=(30, 30, 7.8),
    screw_support_dia=4.6,
    screw_support_depth=2.75,
    screw_centres=(28.6 + 19.37) / 2,
    curl_inner_angle=-30)


@shape
@datatree
class FanVent(CompositeShape):
    '''
    A fan screw mount and vent using CurlySpokes.
    Different fan dimensions are supported using a FanVentScrewHoleParams
    data class.
    '''
    vent_thickness: float=2
    screw_hole_size: float=2.6
    screw_hole_tap_dia_scale: float=0.95 # Needs more to tap onto.
    screw_hole_extension: float=1.5
    screw_params: FanVentScrewHoleParams=FAN_30x7_TYPE2
    fan_cage_hide_cage: bool=True
    fan_cage: Node=Node(cageof, prefix='fan_cage_')
    r_outer: float=None
    r_inner: float=None
    curl_inner_angle: float=None
    grille_type: Node=ShapeNode(
        CurlySpokes, {'h': 'vent_thickness'}, expose_all=True)
    as_cutout: bool=False
    fn: int=36
    
    EXAMPLE_SHAPE_ARGS=args(fan_cage_hide_cage=False)
    EXAMPLE_ANCHORS=()
    
    def build(self) -> Maker:
        self.fan_cage_shape = Box(self.screw_params.size)
        maker = self.fan_cage(cage_name='fan').at('face_centre', 1)
        
        inside_r = (self.screw_hole_tap_dia_scale
            * holeMetricDims(self.screw_hole_size).tap_dia / 2)
            
        screw_mount = Pipe(h=self.screw_params.screw_support_depth 
                               + self.screw_hole_extension,
                           inside_r=inside_r,
                           outside_r=self.screw_params.screw_support_dia / 2,
                           fn=self.fn)
        screw_cage = Box(
            [self.screw_params.screw_centres, 
             self.screw_params.screw_centres, 
             self.screw_params.size[2]])
        maker.add_at(screw_cage.cage('screw_cage').at('centre'),
                     'fan', 'centre')
        for i in range(4):
            maker.add_at(screw_mount.composite(('mount', i)).at('base'),
                                    'screw_cage', 'face_corner', 1, i,
                                    pre=tranZ(self.screw_hole_extension))
        if self.curl_inner_angle is None:
            self.curl_inner_angle = self.screw_params.curl_inner_angle
        if self.r_outer is None:
            self.r_outer = self.screw_params.r_outer
        if self.r_inner is None:
            self.r_inner = self.screw_params.r_inner
        grille = self.grille_type()
        
        mode = (ModeShapeFrame.HOLE 
                if self.as_cutout 
                else ModeShapeFrame.SOLID)
        
        maker.add_at(grille.named_shape('grille', mode).at('base'),
                     'face_centre', 1, post=ROTY_180)
        
        return maker

    @anchor('Centre of grille.')
    def grille_centre(self, *args, **kwds):
        return self.maker.at('grille', 'centre', *args, **kwds)
    
    @anchor('Centre of grille_base.')
    def grille_base(self, *args, **kwds):
        return self.maker.at('grille', 'base', *args, **kwds)

if __name__ == '__main__':
    anchorscad_main(False)
