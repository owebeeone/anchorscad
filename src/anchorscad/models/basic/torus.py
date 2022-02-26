'''
Torus shape.

Created on 23 Feb 2022

@author: gianni
'''
from dataclasses import field
import anchorscad as ad


@ad.shape('anchorscad/models/basic/torus.Torus')
@ad.datatree
class Torus(ad.CompositeShape):
    '''
    A torus.
    '''

    r_hole: float=30
    r_section: float=10
    path: ad.Path=field(init=False)
    section_start_angle_degrees: float=0
    section_sweep_angle_degrees: float=360
    rotate_extrude_node: ad.Node=ad.ShapeNode(
        ad.RotateExtrude, expose_all=True)

    EXAMPLE_SHAPE_ARGS=ad.args(
        degrees=90, 
        section_start_angle_degrees=20,
        section_sweep_angle_degrees=120,
        path_fn=32,
        fn=64)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('surface', section_degrees=10, degrees=10),
        ad.surface_args('surface', section_degrees=110, degrees=80),
        ad.surface_args('centre_start', rr=0.5, degrees=20),
        ad.surface_args('centre_end', rr=0.5, degrees=70),
        ad.surface_args('centre'),
        )
    
    EXAMPLES_EXTENDED={
        'example2': ad.ExampleParams(
            shape_args=ad.args(r_hole=20, 
                               r_section=5, 
                               path_fn=16, 
                               fn=64,
                               use_polyhedrons=0),
            anchors=(
                ad.surface_args('surface', section_degrees=90),)
            )
        }

    def build(self) -> ad.Maker:
        centre = (self.r_hole + self.r_section, 0)
        rotz = ad.rotZ(-self.section_start_angle_degrees)
        start_pos = (
            ad.tranX(centre[0]) * rotz
            * ad.GVector((-self.r_section, 0, 0))).A[:2]
        centre_direction = rotz.A[0][:2]
        self.path = (ad.PathBuilder()
                .move(centre, 'section_centre', direction=centre_direction)
                .line(start_pos, 'section_centre_to_surface')
                .arc_tangent_radius_sweep(
                    radius=self.r_section,
                    sweep_angle_degrees=-self.section_sweep_angle_degrees,
                    degrees=90,
                    side=True,
                    name='surface'
                    )
                .line(centre, 'surface_to_section_centre')
                .build())
        shape = self.rotate_extrude_node()
        
        maker = shape.solid('torus').at()
        return maker

    @ad.anchor('Surface anchor')
    def surface(self, degrees=0, radians=None, section_degrees=0, t=0):
        t += section_degrees / self.section_sweep_angle_degrees        
        return self.maker.at(
            'surface',
            degrees=degrees,
            radians=radians,
            t=t) * ad.ROTX_180
            
    @ad.anchor('Section centre to start of torus arc.')
    def centre_start(self, degrees=0, radians=None, r=0, rr=0):
        t = rr + r / self.r_section
        return self.maker.at(
            'section_centre_to_surface',
            degrees=degrees,
            radians=radians,
            t=t) * ad.ROTX_180

    @ad.anchor('Section centre to end of torus arc.')
    def centre_end(self, degrees=0, radians=None, r=0, rr=0):
        t = rr + r / self.r_section
        return self.maker.at(
            'surface_to_section_centre',
            degrees=degrees,
            radians=radians,
            t=t) * ad.ROTX_180


@ad.shape
@ad.datatree
class TorusChain(ad.CompositeShape):
    '''
    A chain of tori.
    '''
    count: int=10
    torus_node: ad.Node=ad.ShapeNode(Torus)

    EXAMPLE_SHAPE_ARGS=ad.args(
        path_fn=32,
        fn=64)
    
    EXAMPLE_ANCHORS=(ad.surface_args(
            'surface', section_degrees=10, degrees=10),)

    def build(self) -> ad.Maker:
        shape = self.torus_node()
        maker = shape.solid(('torus', 0)).at()
        
        for i in range(1, self.count):
            maker.add_at(
                shape.solid(('torus', i)).at('surface'),
                ('torus', i-1), 'surface', degrees=180, 
                post=ad.ROTX_180 * ad.ROTZ_90)
        
        return maker


if __name__ == "__main__":
    ad.anchorscad_main(False)
