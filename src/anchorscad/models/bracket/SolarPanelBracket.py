'''
Created on 4-Jun-2023

@author: gianni
'''

import anchorscad as ad
import anchorscad.models.screws.tnut_washer as tnut_washer
import numpy as np

@ad.datatree
class SolarPanelEdgeOutline:
    '''Provides the outline of a profile of a solar panel alumminium edge.
    '''
    
    h: float=34.3
    w: float=29.9
    thickness: float=1.05
    inner_w: float=24
    inner_h: float=28.3 - 1.05
    inner_r: float=4
    
    ROOT2 = np.sqrt(2.0)
    
    def build(self):
        
        top_right_h = self.h - self.inner_h - self.thickness
        
        path = (ad.PathBuilder()
            .move((0, 0), 'start', direction=(0, 1))
            .line((0, self.h), 'left')
            .stroke(self.w, -90, name='top')
            .stroke(top_right_h, -90, name='right')
            .stroke(self.inner_w - self.inner_r, -90, name='inner_top')
            
            .stroke(self.inner_r * self.ROOT2, 45, name='inner_top_right')
            .stroke(self.inner_h - 2 * self.inner_r, 45, name='inner_right')
            .arc_tangent_radius_sweep(self.inner_r, 90, degrees=-180, name='inner_bottom_right')
            .stroke(self.inner_w - self.inner_r, 0, name='inner_bottom')
            .stroke(self.thickness, -90, name='lower_right')
        ).build()

        return path

@ad.shape
@ad.datatree
class SolarPanelEdgeProfile(ad.CompositeShape):
    '''A profile of a solar panel alumminium edge.
    '''
    
    width: float=20
    
    outline: ad.Node=ad.Node(SolarPanelEdgeOutline, prefix='outline_')
    
    path: ad.Path=ad.dtfield(
        self_default=lambda s: s.outline().build())
    
    extrude_node : ad.Node=ad.ShapeNode(
        ad.LinearExtrude, 'path', {'h': "width"})
    
    fn: int=64
    
        
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        ad.surface_args('inner_screw_locator'),
        ad.surface_args('outer_screw_locator'),
    )

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        
        maker = shape.solid('outline').at()
        return maker
        
    @ad.anchor('The locator for the screw hole on the inside of the edge')
    def inner_screw_locator(self):
        return self.maker.at('inner_right', 0.5, rh=0.5) * ad.ROTX_180
    
    @ad.anchor('The locator for the screw hole on the outside of the edge')
    def outer_screw_locator(self):
        return self.maker.at('inner_right', 0.5, rh=0.5) * ad.tranZ(
            self.outline_w - self.outline_inner_w)
    
    
@ad.shape
@ad.datatree
class SolarPanelInnerWasher(ad.CompositeShape):
    '''A inner washer for using the tnut washer model.
    '''
    
    tnut_inner_node: ad.Node=ad.dtfield(ad.ShapeNode(
        tnut_washer.TnutWasherInner, prefix='tnut_inner_'))
    profile_node: ad.Node=ad.dtfield(ad.ShapeNode(
        SolarPanelEdgeProfile, prefix='profile_'))
    
    epsilon: float=0.01
    
    as_cage: bool=True
    cage_node: ad.Node=ad.CageOfNode()


    EXAMPLE_ANCHORS=(
        #ad.surface_args('outer_screw_locator'),
    )

    def build(self) -> ad.Maker:
        washer = self.tnut_inner_node()
        outline_w = washer.base_size[1] + self.epsilon
        shape = self.profile_node(width=outline_w)
        
        maker = self.cage_node(shape, cage_name='profile').at()
        
        maker.add_at(
            washer.solid('washer').at('face_centre', 'top'), 
            'profile', 'inner_screw_locator', post=ad.ROTX_180)
        
        maker.add_at(shape.hole('hole').at('inner_screw_locator'),
                     'profile', 'inner_screw_locator')
        
        return maker
    
    @ad.anchor('The locator for the screw hole on the outside of the edge')
    def outer_screw_locator(self):
        return self.maker.at('inner_screw_locator') * ad.tranZ(
            -(self.profile_outline_w - self.profile_outline_inner_w)) * ad.ROTX_180
        

@ad.shape
@ad.datatree
class SolarPanelOuterWasher(ad.CompositeShape):
    '''A outer washer for using the tnut washer model.
    '''
    
    inner_washer_node: ad.Node=ad.dtfield(ad.ShapeNode(SolarPanelInnerWasher))
    tnut_outer_offset: float=2.5
    tnut_outer_node: ad.Node=ad.dtfield(ad.ShapeNode(
        tnut_washer.TnutWasherOuter, prefix='tnut_outer_'))
    
    as_cage: bool=True
    cage_node: ad.Node=ad.CageOfNode()
    
    def build(self) -> ad.Maker:
        
        shape = self.inner_washer_node()
        maker = self.cage_node(shape, cage_name='inner_washer').at('inner_screw_locator')
        
        washer = self.tnut_outer_node()
        
        maker.add_at(washer.solid('outer_washer').at('outer_cyl', 'base', rh=1),
                     'outer_screw_locator', post=ad.ROTX_180)
        
        return maker
 
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(write_files=True, write_path_files=True)

if __name__ == "__main__":
    ad.anchorscad_main()

    
