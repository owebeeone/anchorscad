'''
Created on 27 Jan 2022

@author: adrian
'''

from numpy import pi

import anchorscad as ad
from anchorscad import datatree, Node, PathBuilder, Path, RotateExtrude

import numpy as np


PRINT_ERROR_OFFSET = .25

COVER_CAVITY_R = 50.5 / 2 + PRINT_ERROR_OFFSET
OUTER_CYL_R1 = 60 / 2
OUTER_CYL_R2 = 56 / 2

TOTAL_H = 19.1
FLANGE_H = 4.65
COVER_H = TOTAL_H - FLANGE_H

COVER_DEPTH = 11.96
TOTAL_DEPTH = COVER_DEPTH + FLANGE_H

FLANGE_THICKNESS = FLANGE_H - 1.94
FLANGE_CAVITY_R = 55.1 / 2 + PRINT_ERROR_OFFSET


@datatree
class SharedDimensions:
    inner_h: float=COVER_DEPTH
    inner_r: float=COVER_CAVITY_R
    
    flange_h: float=FLANGE_H
    flange_r: float=FLANGE_CAVITY_R
    
    stock_r_top: float=OUTER_CYL_R1
    stock_r_base: float=OUTER_CYL_R2
    
    epsilon: float=.003
    

@ad.shape
@datatree
class BasicCavityOutline(ad.CompositeShape, SharedDimensions):
    inner_cavity_node: Node=ad.ShapeNode(ad.Cylinder, prefix='inner_')
    flange_cavity_node: Node=ad.ShapeNode(ad.Cylinder, prefix='flange_')
    
    fn: int=128
    
    def __post_init__(self):
        maker = self.inner_cavity_node().solid('inner_cavity').at('centre')
        
        maker.add_at(self.flange_cavity_node().solid('flange_cavity').
                     at('base'), 
                     'base', rh=1, post=ad.tranZ(self.epsilon))
        
        self.maker = maker
        
        
@ad.shape
@datatree
class TaperedFlange(ad.CompositeShape, SharedDimensions):
    
    flange_shape_h: float=FLANGE_THICKNESS
    flange_shape_r: float=OUTER_CYL_R2
    flange_shape_inner_r: float=OUTER_CYL_R2 - (3.98 - 2.3)
    flange_shape_node: Node=ad.ShapeNode(ad.Cylinder, prefix='flange_shape_')
    
    flange_extrude_path: Path=None
    flange_extrude_angle: float=55
    flange_extrude_node: Node=ad.ShapeNode(RotateExtrude, prefix='flange_extrude_')
    
    fn: float=128
   
    def __post_init__(self):
        path = (PathBuilder()
                .move([self.flange_shape_inner_r, 0], name='origin')
                .line([self.flange_shape_inner_r, self.flange_shape_h], name='inner')
                .line([self.flange_shape_r, self.flange_shape_h], name='top')
                .line([self.flange_shape_r, 0], name='outer')
                .line([self.flange_shape_inner_r, 0], name='base')
                .build())
        
        extrusion = self.flange_extrude_node(path)
        
        flange = extrusion.solid('extrusion')\
                    .at('base', angle=self.flange_extrude_angle / 2)
                    
        intersector_size = [self.flange_r,
                            self.flange_r,
                            self.flange_shape_h * 2]
        intersector = ad.Box(intersector_size)
        
        raised_taper = .3
        taper_angle = 181.5
        flange.add_at(intersector.solid('intersector')
                      .at('face_centre', 1, 
                          post=ad.rotY(taper_angle) * ad.tranZ(-raised_taper)), 
                      post=ad.IDENTITY)
        
        extents = path.extents()
        
        self.maker = flange.intersect('tapered_flange').at()
        
        size_yz = extents[1] - extents[0]
        size_stopper = (2, size_yz[0], size_yz[1] + 1)
        
        stopper = ad.Box(size_stopper).solid('stopper')
        
        self.maker.add_at(stopper.at('face_corner', 0, 0, 
                                     post=ad.ROTZ_180 * ad.ROTX_90), 
                          'top', 1)
        

@ad.shape
@datatree
class FlangeOutline(ad.CompositeShape, SharedDimensions):
#     cavity_node: Node=ad.ShapeNode(BasicCavityOutline)
    
    taper_node: Node=ad.ShapeNode(TaperedFlange)

    taper_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.taper_node())
    
    flange_cage_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.taper_shape.flange_shape_node())
    
    flange_cage_node: Node=ad.Node(ad.cageof, prefix='flange_cage_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(flange_cage_hide_cage=False)
    
    def build(self) -> ad.Maker:
        
        self.flange_cage_shape = self.flange_cage_shape
        
        flange_cage = self.flange_cage_node()
        
        maker = flange_cage.at()
        
        extrusion = self.taper_node()
        
        for i in range(3):
            maker.add_at(extrusion.solid(('flange', i))
                              .at('outer', 1, post=ad.ROTX_180),
                              'surface', 0, angle=(360 / 3) * i)
            
        return maker


# @ad.shape
# @datatree
# class GripOutline(ad.CompositeShape, SharedDimensions):
#     diameter: float=2 * SharedDimensions.stock_r_top
#     circumference: float=diameter * np.pi
    
#     grip_width: float=2
#     grip_count: int=360 / grip_width
#     grip_angle: float=circumference / grip_count
       
        
@ad.shape
@datatree
class ShellAssembly(ad.CompositeShape):
    cavity_node: Node=ad.ShapeNode(BasicCavityOutline)
    
    flange_outline_node: Node=ad.ShapeNode(FlangeOutline) 
    
    stock_h: float=TOTAL_H
    stock_cyl_node: Node=ad.ShapeNode(ad.Cone, prefix='stock_')   
    
    EXAMPLE_SHAPE_ARGS=ad.args(flange_cage_hide_cage=True)     
    
    def build(self) -> ad.Maker:
        outline = self.stock_cyl_node().solid('stock').at()
        
        outline.add_at(self.cavity_node().hole('cavity')
                     .at('flange_cavity', 'top', post=ad.tranZ(-self.epsilon)), 
                     'top')        
        
        maker = outline.solid('outline').at()
        
        flanges = self.flange_outline_node()
        
        maker.add_at(flanges.solid('flanges').at('top'), 'top')
        
        return maker


@datatree
class GripRibPath:

    grip_h: float=13
    grip_d: float=1.3

    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
            .move((0, 0))
            .line((self.grip_h, 0), 'base')
            .arc_points(
                middle=(self.grip_h / 2, self.grip_d),
                last=(0, 0),
                name='top'))
        
        return builder.build()


@ad.shape
@datatree
class GripRib(ad.CompositeShape):

    path_node: Node=ad.ShapeNode(GripRibPath)
    grip_path: ad.Path=ad.dtfield(self_default=lambda s: s.path_node().build())
    grip_w: float=3.0

    extrude_node: Node=ad.ShapeNode(ad.LinearExtrude, {'h': 'grip_w', 'path': 'grip_path'})

    def build(self) -> ad.Maker:
        
        return self.extrude_node().solid('grip_rib').at()
        
@ad.shape
@datatree
class LensCap(ad.CompositeShape):
    assembly_node: Node=ad.ShapeNode(ShellAssembly)

    grip_rib_node: Node=ad.ShapeNode(GripRib)
    grip_rib_count: int=32
    grip_rib_zoffs: float=0.3
    grip_rib_as_recess: bool=True

    EXAMPLE_SHAPE_ARGS=ad.args(fn=256, grip_rib_as_recess=False)

    EXAMPLES_EXTENDED={
        'recessed_rib': ad.ExampleParams(
            shape_args=ad.args(fn=256, grip_rib_as_recess=True),
            anchors=()
            )
        }

    def build(self) -> ad.Maker:
        maker = self.assembly_node().composite('assembly').at()

        for i in range(self.grip_rib_count):

            angle = (360 / self.grip_rib_count) * i
            
            if self.grip_rib_as_recess:
                orientation = ad.IDENTITY
                zoffs = self.grip_rib_zoffs
                msf = ad.ModeShapeFrame.HOLE
            else:
                orientation = ad.ROTX_180
                zoffs = -self.grip_rib_zoffs
                msf = ad.ModeShapeFrame.SOLID 

            rib_maker = self.grip_rib_node().named_shape(('grip_rib', i), msf) \
                .at('base', 0.5, rh=0.5, post=ad.ROTZ_90 * orientation)
            maker.add_at(
                rib_maker,
                'outline', 'stock', 'surface', angle=angle, rh=0.5, 
                post=ad.tranZ(zoffs))

        return maker
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == '__main__':
    ad.anchorscad_main(False)