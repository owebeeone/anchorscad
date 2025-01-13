'''
Created on 2023-09-16

@author: gianni
'''

import anchorscad as ad
import anchorscad.models.name_plate.embedded_text as et

@ad.shape
@ad.datatree
class SimmyPlate(ad.CompositeShape):
    '''
    Named plate for Simmy
    '''

    plate_node: ad.Node=ad.dtfield(
        ad.ShapeNode(et.RoundedSquarePlateWithText))
    
    EXAMPLE_SHAPE_ARGS=ad.args(
        label_text='Simmy', 
        label_font='Britannic Bold', 
        label_anchor_point='front',
        label_material=ad.Material('blue_glow_PLA', priority=10), 
        plate_size=(150, 50, 4), 
        plate_bevel_radius=10,
        hide_cage=True,
        label_depth=0.4,
        label_plate_overlap=0.4 - 0.01,
        fn=64)


    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.plate_node()
        maker = shape.solid('plate').material(ad.Material('white_PLA')).at()
        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
