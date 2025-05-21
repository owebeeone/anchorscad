'''
Created on 2025-05-04

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.box_side_bevels import BoxSideBevels

SHRINK_FACTOR = 0.1

@ad.shape
@ad.datatree
class CylinderStack(ad.CompositeShape):
    '''
    A stack of cylinders.
    '''
    r: float=25.4/2 + SHRINK_FACTOR
    h: float=114.5
    n: int=6
    separation: float=1

    cylinder_node: ad.ShapeNode[ad.Cylinder]
    
    EXAMPLE_SHAPE_ARGS=ad.args()

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.cylinder_node()
        
        maker = shape.solid(('cylinder', 0)).at('base')
        
        for i in range(self.n - 1):
            maker_n = shape.solid(('cylinder', i + 1)).at('base')
            maker.add_at(maker_n, 'base', post=ad.tranX((self.separation + self.r * 2) * (i + 1)))
            
        box_cage = ad.Box(self.size()).solid('bbox').transparent(True).colour('red', 0.5) \
            .at('face_edge', 'left', 1)
        maker.add_at(box_cage, 'surface', angle=180)

        return maker
    
    def size(self) -> tuple:
        return (self.r * 2 * self.n + self.separation * (self.n - 1), self.h, self.r * 2)

@ad.shape
@ad.datatree
class BobbinTray(ad.CompositeShape):
    '''
    A Tray for bobbins.
    '''
    
    margin: float=1.45
    thickness: float=10
    base_min_thickness: float=2
    
    stack_node: ad.ShapeNode[CylinderStack]
    stack_shape: CylinderStack = ad.dtfield(self_default=lambda s: s.stack_node())
    stack_size: tuple = ad.dtfield(self_default=lambda s: s.stack_shape.size())
    
    box_size: tuple = ad.dtfield(self_default=lambda s: (
        s.stack_size[0] + 2 * s.margin, 
        s.stack_size[1] + 2 * s.margin, 
        s.thickness))

    box_bevel_radius: float=4
    box_node: ad.ShapeNode[BoxSideBevels] = ad.ShapeNode(
        BoxSideBevels, prefix='box_')
    
    fn: int=64

    def build(self) -> ad.Maker:
        box_shape = self.box_node()
        
        maker = box_shape.solid('box').at('face_centre', 'base')
        
        stack_maker = self.stack_shape.hole('stack').at('bbox', 'face_centre', 'base')
        maker.add_at(stack_maker, 'face_centre', 'base', post=ad.tranZ(-self.base_min_thickness))
        
        #print(self.box_size)
        return maker
    
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
