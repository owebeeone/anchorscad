'''
Created on 20-Dec-2023

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class MultiMaterialTest(ad.CompositeShape):
    '''
    A basic test of multi-material support. Basically a box with a sphere on top.
    The box and sphere are different materials.
    '''
    xy: float=30
    z: float=10
    
    # Builds a tuple from the x, y, z fields.
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.xy, s.xy, s.z))
    
    # A node that builds a box from the size tuple. See:
    # https://github.com/owebeeone/anchorscad/blob/master/docs/datatrees_docs.md
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, 'size'))
    
    sphere_r: float=ad.dtfield(self_default=lambda s: s.xy/2)
    
    shpere_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Sphere, prefix='sphere_'))
    
    EXAMPLE_SHAPE_ARGS=ad.args(xy=20, z=10)
    xEXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'top'),)

    def build(self) -> ad.Maker:
        
        box_shape = self.box_node()
        maker = box_shape.solid('box') \
                .material(ad.Material('box', priority=10)) \
                .at('face_centre', 'base', post=ad.ROTX_180)
        maker.add_at(
            self.shpere_node()
                    .solid('sphere')
                    .material(ad.Material('sphere', priority=9))
                    .at('top', rh=1.4),
            'face_centre', 'top')
        
        non_physical_mat = ad.Material('non_physical', priority=20, kind=ad.NON_PHYSICAL_MATERIAL_KIND)
        
        maker.add_at(
            self.shpere_node()
                    .solid('sphere_non_physical')
                    .material(non_physical_mat)
                    .at('top', rh=1.9),
            'face_centre', 'top')
        

        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=False)

if __name__ == "__main__":
    ad.anchorscad_main()
