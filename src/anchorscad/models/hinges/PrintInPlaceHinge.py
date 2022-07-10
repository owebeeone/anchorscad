'''
Created on 6 Jul 2022
@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class PrintInPlaceHingeShaft(ad.CompositeShape):
    '''
    Rotatable hinge shaft component
    '''
    
    outer_r: float=ad.dtfield(8, 'outer radius of shaft')
    outer_hinge_r: float=ad.dtfield(7, 'larger radius of hinge cone')
    inner_hinge_r: float=ad.dtfield(2, 'inner radius of shaft cone')

    shaft_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, {'r': 'outer_r', 'h': 'inner_w'}))
    outer_w: float=ad.dtfield(22, 'width of outer hinge part')
    inner_w: float=ad.dtfield(10, 'width of inner hinge part')
    
    hinge_w: float=ad.dtfield(5.5, 'width of hinge cone')
    hinge_cone_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cone, {'h': 'hinge_w',
                               'r_base': 'outer_hinge_r',
                               'r_top': 'inner_hinge_r'}))
    epsilon: float=ad.dtfield(.01, 'anti-aliasing shift')
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        ad.surface_args('base'),)

    def build(self) -> ad.Maker:
        shaft_shape = self.shaft_node()
        maker = shaft_shape.solid('shaft').at('base')
        
        hinge_cone = self.hinge_cone_node()
        maker.add_at(hinge_cone.hole('top_hole').at('base'), 
                     'shaft', 'top', post=ad.tranZ(self.epsilon))
        maker.add_at(hinge_cone.hole('base_hole').at('base'), 
                     'shaft', 'base', post=ad.tranZ(self.epsilon))
        
        return maker

 
@ad.shape
@ad.datatree
class PrintInPlaceHinge(ad.CompositeShape):
    '''
    Hinge assembly
    '''
    separation: float=ad.dtfield(.5, 'separation between hinge surfaces')
    hinge_shaft_node: ad.Node=ad.dtfield(
        ad.ShapeNode(PrintInPlaceHingeShaft))

    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=(
        ad.surface_args('base'),)

    def build(self) -> ad.Maker:
        shaft_shape = self.hinge_shaft_node()
        maker = shaft_shape.solid('shaft').at('base')
        
        hinge_cone = self.hinge_cone_node()
        maker.add_at(hinge_cone.solid('top_cone').at('base'), 
                     'shaft', 'top', post=ad.tranZ(self.separation))
        maker.add_at(hinge_cone.solid('base_cone').at('base'), 
                     'shaft', 'base', post=ad.tranZ(self.separation))
        
        return maker


@ad.shape
@ad.datatree
class PrintInPlaceHingeWithJoiners(ad.CompositeShape):
    '''
    Hinge assembly
    '''
    hinge_node: ad.Node=ad.dtfield(
        ad.ShapeNode(PrintInPlaceHinge))

    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    EXAMPLE_ANCHORS=(
        ad.surface_args('base'),)

    def build(self) -> ad.Maker:
        hinge_shape = self.hinge_node()
        maker = hinge_shape.solid('hinge').at('centre')
        

        return maker

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()