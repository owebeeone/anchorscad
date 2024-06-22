'''
Created on 2021-07-02

@author: gianni
'''

import anchorscad as ad
import numpy as np

@ad.datatree
class CircularSection:
    '''
    A circular section with a angle range.
    '''
    degrees: float=10
    depth: float=50
    r: float=100
    fn: int=4
    
    def build(self) -> ad.Path:

        radians = np.radians(self.degrees / 2)
        widthd2 = np.sin(radians) * self.r
        height = np.cos(radians) * self.r
        assert self.depth <= height, "Depth must be less than height"

        path = (ad.PathBuilder()
                .move((self.depth, 0))
                .line((self.depth, widthd2), 'base_left')
                .line((height, widthd2), 'left')
                .arc_points_radius(
                    (height, -widthd2), 
                    self.r, 
                    is_left=False, 
                    direction=False, 
                    name='arc',
                    metadata=ad.ModelAttributes(fn=self.fn))
                .line((self.depth, -widthd2), 'right')
                .line((self.depth, 0), 'base_right')
                .build())

        return path


@ad.shape
@ad.datatree
class SphereSection(ad.CompositeShape):
    '''
    A spherical section with a angle range for the lat and long.
    '''
    lat_degrees: float=30
    lng_degrees: float=45
    depth: float=250
    r: float=300
    path_node: ad.Node=ad.Node(CircularSection, {'degrees': 'lat_degrees'}, expose_all=True)

    path: ad.Path=ad.dtfield(self_default=lambda self: self.path_node().build())

    rot_extrude_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.RotateExtrude, {'degrees': 'lng_degrees'}, expose_all=True))

    fn: int=128
    
    def build(self) -> ad.Maker:

        shape = self.rot_extrude_node(fn=self.fn * int(1 + 360 / self.lat_degrees) )

        maker = shape.solid('section').at()

        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(write_files=True, write_path_files=True)

if __name__ == "__main__":
    ad.anchorscad_main()
