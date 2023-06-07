'''
Created on 4-Jun-2023

@author: gianni
'''

import anchorscad as ad
import numpy as np

@ad.datatree
class RoofRackBarOutline:
    '''Provides the outline for the roof rack bar.
    This one is specific to bars shaped like and areofoil.
    '''
    
    thickness: float=24
    min_thickness: float=5
    width: float=85
    maximal_thickness_x: float=28
    minimum_thickness_x: float=3
    
    def build(self):
        
        p_max = (self.maximal_thickness_x, self.thickness / 2)
        p_max_dir = (p_max[0] - 1, p_max[1])
        
        p_min_dir = (self.width, 1)
        p_min = (self.width, 0)
        
        p_base_max = (self.maximal_thickness_x, - self.thickness / 2)
        p_base_max_dir = (p_base_max[0] + 1, p_base_max[1])
        
        path = (ad.PathBuilder()
            .move((0, 0), 'start', direction=(0, 1))
            .spline((p_max_dir, p_max), 'front_top', cv_len=(10, 15))
            .spline((p_min_dir, p_min), 'back_top', cv_len=(15, 7))
            .spline((p_base_max_dir, p_base_max), 'back_base', cv_len=(1, 25))
            .spline(((0, -1), (0, 0)), 'front_base', cv_len=(15, 10))
        ).build()

        return path

@ad.shape
@ad.datatree
class RoofRackBracketHole(ad.CompositeShape):
    '''
    Padding for a roof rack bracket. The bracket consists of a
    U bolt and a flat plate and this is the padding for the 
    flat plate and U bolt to snugly fit around the roof rack
    bar.
    '''
    
    width: float=3
    
    outline: ad.Node=ad.Node(RoofRackBarOutline, prefix='outline_')
    
    path: ad.Path=ad.dtfield(
        self_default=lambda s: s.outline().build())
    
    extrude_node : ad.Node=ad.ShapeNode(
        ad.LinearExtrude, 'path', {'h': "width"})
    
    fn: int=64
    
        
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        
        maker = shape.solid('outline').at()
        return maker
    
    @ad.anchor('The centre of the outline')
    def centre(self):
        return ad.translate((self.outline_width / 2, 0, self.width / 2))
    

@ad.shape
@ad.datatree
class RoofRackBracket(ad.CompositeShape):
    '''
    Padding for a roof rack bracket. The bracket consists of a
    U bolt and a flat plate and this is the padding for the 
    flat plate and U bolt to snugly fit around the roof rack
    bar.
    '''
    
    width: float=4
    padding: float=15
    
    bracket_hole: ad.Node=ad.Node(RoofRackBracketHole)
    
    cage_size: tuple=ad.dtfield(self_default=lambda s: 
        (s.outline_width + s.padding, s.outline_thickness + s.padding, s.width))
    
    cage_node : ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    
    block_size: tuple=ad.dtfield(self_default=lambda s: 
        (s.cage_size[0], s.cage_size[1] / 2, s.cage_size[2]))
    
    block_node : ad.Node=ad.ShapeNode(ad.Box, prefix='block_')

    fn: int=64
    epsilon: float=0.01
    
    upper_half: bool=True
    
        
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'front'),
    )
    EXAMPLES_EXTENDED={'upper': ad.ExampleParams(
                            ad.args(upper_half=True)),
                       'lower': ad.ExampleParams(
                            ad.args(upper_half=False)),
                       }
        

    def build(self) -> ad.Maker:
        
        cage_shape = self.cage_node()
        maker = cage_shape.cage('cage').at('centre')
        
        face = 'back' if self.upper_half else 'front'
        
        block_shape = self.block_node()
        maker = maker.add_at(block_shape.solid('block').at('face_centre', face),
                             'face_centre', face)
        
        shape = self.bracket_hole(width=self.width + self.epsilon)
        
        # Align cage and hole centres.
        maker.add_at(shape.hole('rack_outline').at('centre'), 'centre')
        return maker
    



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(write_files=True, write_path_files=True)

if __name__ == "__main__":
    ad.anchorscad_main()
