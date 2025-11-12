'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad

from anchorscad_models.basic.box_side_bevels import BoxSideBevels


@ad.shape
@ad.datatree
class BasicToyBox(ad.CompositeShape):
    '''
    <description>
    '''
    x: float=30
    y: float=30
    z: float=30.3
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.x, s.y, s.z))
    
    txt_text: str = "Elaina"
    txt_size: float = 8.0
    txt_halign: str = "center"
    txt_valign: str = "center"
    txt_depth: float = 0.5
    text_node: ad.ShapeNode[ad.Text] = ad.dtfield(ad.ShapeNode(ad.Text, prefix="txt_"))
    
    bevel_radius: float=2.0
    box_node: ad.ShapeNode[BoxSideBevels]
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.box_node()
        maker = shape.solid('box').at('centre')
        
        text_shape = self.text_node()
        text_maker = text_shape.hole('text').colour("green") \
            .at('default', post=ad.rotZ(45) * ad.tranZ(self.txt_depth/2 - 0.01))
        
        maker.add_at(text_maker, "face_centre", "top")
        
        return maker

    @ad.anchor('An example anchor')
    def example_anchor(self):
        return self.maker.at()


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
