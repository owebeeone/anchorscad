'''
Created on 2022-03-16

@author: gianni
'''

import anchorscad as ad
from anchorscad.models.basic.box_side_bevels import BoxSideBevels


EPSILON = 0.002

@ad.shape
@ad.datatree
class RoundedSquarePlateWithText(ad.CompositeShape):
    '''
    A rounded square plate with extruded text in the center.
    '''
    plate_size: float = ad.dtfield((70, 40, 6), doc='The size of the plate')
    label_depth: float = ad.dtfield(3, doc='The depth of the label')
    label_plate_overlap: float = ad.dtfield(2.8, doc='The depth of overlap with plate')    

    size: tuple = ad.dtfield(
        doc='The (x,y,z) size of RoundedSquarePlateWithText',
        self_default=lambda s: (s.plate_size, s.plate_size, 5))
    plate_node: ad.Node = ad.dtfield(ad.ShapeNode(BoxSideBevels, prefix="plate_"))
    
    label_text: str = ad.dtfield("34", doc='The text to extrude')
    label_size: float = ad.dtfield(30, doc='The size of the text')
    label_valign: str = ad.dtfield("center", doc='The vertical alignment of the text')
    label_halign: str = ad.dtfield("center", doc='The horizontal alignment of the text')
    label_node: ad.Node = ad.dtfield(ad.ShapeNode(ad.Text, prefix="label_"))
    label_font: str = ad.dtfield("Ariel", doc='The font of the label')
    label_anchor_point: str = ad.dtfield("front", doc='The anchor point of the label')
    label_horiz_fixer_size: float = ad.dtfield((0.1, 0.1, 0.1), doc='The size of the horizontal fixer')
    
    cage_size: tuple = ad.dtfield(self_default=lambda s: (
        s.plate_size[0], 
        s.plate_size[1], 
        s.plate_size[2] + s.label_depth - s.label_plate_overlap))
    
    cage_node: ad.Node = ad.dtfield(ad.ShapeNode(ad.Box, prefix="cage_"))
    
    cage_of_node: ad.Node = ad.CageOfNode()
    
    
    label_render: bool=ad.dtfield(True, doc='Show the label')
    plate_render: bool=ad.dtfield(True, doc='Show the plate')
    

    EXAMPLE_SHAPE_ARGS = ad.args(plate_size=(50, 40, 1),
                                 hide_cage=True, 
                                 label_anchor_point='front', 
                                 label_font='Britannic Bold',
                                 fn=64)
    EXAMPLE_ANCHORS=(
        #ad.surface_args('label', 'default', 'front'),
        ad.surface_args('plate', 'face_centre', 'top'),
    )
    
    DEFAULT_ARGS = ad.args(
                    label_text="13",
                    label_horiz_fixer_size=None,
                    plate_size=(50, 40, 3),
                    label_depth=0.4,
                    label_plate_overlap=0.4 - EPSILON,
                    hide_cage=True, 
                    label_font='Britannic Bold',
                    fn=64)
        
    EXAMPLES_EXTENDED={
        'combined': ad.ExampleParams(
            shape_args=DEFAULT_ARGS
            ),
        'label': ad.ExampleParams(
            shape_args=ad.apply_args(
                    DEFAULT_ARGS,
                    plate_render=False
                    )
            ),
        'plate': ad.ExampleParams(
            shape_args=ad.apply_args(
                    DEFAULT_ARGS,
                    label_render=False
                    )
            )
        }

    def build(self) -> ad.Maker:

        maker = self.cage_of_node(self.cage_node()).at('face_centre', 'top', post=ad.ROTY_180)

        plate_shape = self.plate_node()
        
        maker.add_at(plate_shape.solid_cage('plate', not self.plate_render).at('face_centre', 'base'), 
                     'face_centre', 'base')

        # Create the extruded text and center it on the plate
        label_shape = self.label_node()
        
        maker.add_at(label_shape.solid_hole('label', not self.label_render)
                     .colour([1, 0, 0])
                     .at('default', self.label_anchor_point), 
                        'plate', 'face_centre', 'top',
                        post=ad.tranZ(self.label_depth - self.label_plate_overlap))

        # If we're rendering just the label, then add a box to anchor to Z=0
        if self.label_render and not self.plate_render and not self.label_horiz_fixer_size is None:
            maker.add_at(ad.Box(size=self.label_horiz_fixer_size)
                                .solid('label-z-fixer').at('face_centre', 'base'), 
                         'cage', 'face_edge', 'base', 0, post=ad.tranY(-10))

        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()