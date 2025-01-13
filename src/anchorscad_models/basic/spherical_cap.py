'''
Created on ${date}

@author: ${user}
'''

import anchorscad as ad
import numpy as np


@ad.shape
@ad.datatree
class SphericalCap(ad.CompositeShape):
    '''
    A cap of a sphere.
    '''
    degrees: float=ad.dtfield(90, doc='The angle of the cap in degrees')
    radians: float=ad.dtfield(None, 
            'The angle of the cap in radians. '
            'If provided, degrees is ignored.')
    sinr_cosr: tuple=ad.dtfield(None, 
            'The sin and cos of the angle. '
            'If provided, degrees and radians are ignored.')
    cage_of_node: ad.Node=ad.CageOfNode()

    sphere_node: ad.Node=ad.ShapeNode(ad.Sphere)
    
    rotate_node: ad.Node=ad.ShapeNode(ad.RotateExtrude, 
            {'path': None}, prefix='rotate_', expose_all=True)
    
    EXAMPLE_SHAPE_ARGS=ad.args(r=30, degrees=95, hide_cage=False, fn=16)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        cage_shape = self.sphere_node()
        maker = self.cage_of_node(cage_shape).at('centre')
        
        if not self.sinr_cosr:
            radians = self.radians
            if radians is None:
                radians = ad.to_radians(self.degrees)
            sinr_cosr = (ad.clean(np.sin(radians)), ad.clean(np.cos(radians)))
        else:
            sinr_cosr = self.sinr_cosr
            
        assert sinr_cosr[0] >= 0, 'Rotation angle must be between 0 and 180'
        
        y_last_point = sinr_cosr[1] * self.r
        path = (ad.PathBuilder()
                .move([0, self.r])
                .arc_tangent_point(
                    (sinr_cosr[0] * self.r, y_last_point),
                    direction=(1, 0),
                    name='arc')
                .line((0, y_last_point), 'cut')
                .line((0, self.r), 'axis')
                ).build()
        
        cap_shape = self.rotate_node(path)
        
        maker.add_at(cap_shape.solid('cap').at('arc', 0), 
                     'centre', rh=1, post=ad.ROTY_180)
        
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
