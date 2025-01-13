'''
Created on 2024-06-07

@author: gianni
'''

import anchorscad as ad
from anchorscad_models.basic.parallelogram_rounded import ParallelogramRounded


@ad.shape
@ad.datatree
class ZipperTag(ad.CompositeShape):
    '''
    A tag for a zipper.

    A 2 material model for a tag. The inner material being the boundary and the 'label' material
    being the outer part of the tag. The tag has a hole located in a corner of the model.

    The inner material can be made from a stronger material like carbon fibre (CF) PETG while the outer
    material can be made from white PETG. Since CF PETG is usually black, it would be unsuitable for
    printing text on it, hence the need for a label material.

    TODO: Future extension will be to add a model to print on the label and hence allow for custom
    icons or text on labels.
    '''

    tag_node: ad.Node=ad.dtfield(ad.ShapeNode(ParallelogramRounded))
    offset: float=ad.dtfield(0.5, doc='The inner radius')
    layer_size: float=ad.dtfield(0.6, doc='The thickness of label material')
    epsilon: float=ad.dtfield(0.01, doc='The gap between the inner and outer tags')

    substrate_material: ad.Material=ad.dtfield(ad.Material("substrate", priority=5))
    label_material: ad.Material=ad.dtfield(ad.Material("label", priority=6))

    hole_r: float=ad.dtfield(2.1, doc='The radius of the hole in the tag')
    hole_h: float=ad.dtfield(
        self_default=lambda s: s.h + 4 * s.epsilon, 
        doc='The height of the hole in the tag')

    hole_node: ad.Node=ad.ShapeNode(ad.Cylinder, prefix='hole_')
    
    EXAMPLE_SHAPE_ARGS=ad.args(h=2.5, r=3.5, fn=32)

    def build(self) -> ad.Maker:
        shape = self.tag_node()
        maker = shape.solid('tag') \
            .material(self.substrate_material) \
            .colour('grey').at()

        inner_shape = self.tag_node(r=self.r - self.offset, h=self.layer_size)
        inner_lower_maker = inner_shape.solid('lower_tag') \
            .material(self.label_material) \
            .at('centre_of', ('arc', 0))

        maker.add_at(
            inner_lower_maker,
            'centre_of', ('arc', 0), 
            post=ad.tranZ(self.epsilon))
        
        inner_upper_maker = inner_shape.solid('upper_tag') \
            .material(self.label_material) \
            .at('centre_of', ('arc', 0), rh=1)

        maker.add_at(
            inner_upper_maker,
            'centre_of', ('arc', 0), rh=1,
            post=ad.tranZ(-self.epsilon))
        
        hole_shape = self.hole_node()
        hole_maker = hole_shape.hole('hole').at('base')
        maker.add_at(
            hole_maker, 
            'centre_of', ('arc', 1), 
            post=ad.tranZ(self.epsilon * 2))

        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
