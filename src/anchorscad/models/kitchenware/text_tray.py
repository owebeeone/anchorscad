'''
Created on 2024-11-17

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class TextTray(ad.CompositeShape):
    '''
    Creates a tray with the outline of the given text.
    '''

    text: str=ad.dtfield('Y', 'Text string to render.')
    size: float=ad.dtfield(170.0, 'Height of text')
    depth: float=ad.dtfield(20.0, 'Depth of text')
    
    font: str=ad.dtfield('Comic Sans MS', 'Font name for rendering.')
    
    text_node: ad.Node=ad.ShapeNode(ad.Text)
    
    inner_delta: float=ad.dtfield(11, 'inner offset (can be negative).')
    base_thickness: float=ad.dtfield(3, 'Thickness of the base.')
    outer_delta: float=ad.dtfield(15, 'outer offset')
    
    fn: int=ad.dtfield(64, 'Number of facets for the text.')
    
    epsilon: float=ad.dtfield(0.1, 'Epsilon to avoid tearing.')
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(text='LILY')

    def build(self) -> ad.Maker:
        
        base_shape = self.text_node(offset_delta=self.outer_delta)
        
        maker = base_shape.solid('base').at('default', 'front')
        
        inner_shape = self.text_node(
            offset_delta=self.inner_delta,
            depth=self.depth - self.base_thickness)
        
        inner_maker = inner_shape.hole('inner').at('default', 'front')
        
        maker.add_at(inner_maker, post=ad.tranZ(self.epsilon))
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
