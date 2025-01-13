'''
Torus shape.

Created on 23 Feb 2022

@author: gianni
'''

import anchorscad as ad

def torus_path(
    r_hole: float, 
    r_section: float, 
    section_start_angle: float | ad.Angle,
    section_sweep_angle: float | ad.Angle,
    metadata: ad.ModelAttributes) -> ad.Path:
    '''Provides a semi-circle path for for circular extrusion into a torus.
    Args:
      r_hole: Inner radius of torus hole.
      r_section: Radius of torus section.
      section_start_angle: Start angle of torus section.
      section_sweep_angle: Sweep angle of torus section.
    '''
    centre = (r_hole + r_section, 0)
    rotz = ad.rotZ(-section_start_angle)
    start_pos = (
        ad.tranX(centre[0]) * rotz
        * ad.GVector((-r_section, 0, 0))).A[:2]
    centre_direction = rotz.A[0][:2]
    path = (ad.PathBuilder()
                .move(centre, 'section_centre', direction=centre_direction)
                .line(start_pos, 'section_centre_to_surface')
                .arc_tangent_radius_sweep(
                    radius=r_section,
                    sweep_angle=-section_sweep_angle,
                    angle=90,
                    side=True,
                    name='surface',
                    metadata=metadata
                    )
                .line(centre, 'surface_to_section_centre')
                .build())
    return path


@ad.shape
@ad.datatree
class Torus(ad.CompositeShape):
    '''
    A torus, also provides ability to speficy a sector of the cross section.
    
    This includes a cage that is always the full torus in which the torus is 
    a complete circular extrusion. The anchors cage_centre_start, cage_centre_end 
    and cage_surface are on the cage and are stable despite the sector chosen.
    '''

    r_hole: float=30
    r_section: float=10
    section_start_angle: float=0
    section_sweep_angle: float=360
    metadata_fn: int=64
    metadata_node: ad.Node=ad.Node(
        ad.ModelAttributes, prefix='metadata_', expose_all=True)
    metadata: ad.ModelAttributes=ad.dtfield(self_default=lambda s: s.metadata_node())
    path_node: ad.Node=ad.dtfield(ad.Node(torus_path))
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_node(), init=False)
    
    rotate_extrude_node: ad.Node=ad.ShapeNode(
        ad.RotateExtrude, expose_all=True)
    
    cage_of_node: ad.Node=ad.CageOfNode()

    EXAMPLE_SHAPE_ARGS=ad.args(
        angle=90, 
        section_start_angle=20,
        section_sweep_angle=120,
        path_fn=32,
        fn=64,
        hide_cage=False)
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('surface', section_angle=10, angle=10),
        ad.surface_args('surface', section_angle=110, angle=80),
        ad.surface_args('centre_start', rr=0.5, angle=20),
        ad.surface_args('centre_end', rr=0.5, angle=70),
        ad.surface_args('centre'),
        ad.surface_args('cage_surface', angle=45, section_angle=90),
        )
    
    EXAMPLES_EXTENDED={
        'example2': ad.ExampleParams(
            shape_args=ad.args(r_hole=20, 
                               r_section=5, 
                               path_fn=16, 
                               fn=64,
                               use_polyhedrons=0),
            anchors=(
                ad.surface_args('surface', section_angle=90),)
            )
        }

    def build(self) -> ad.Maker:
        
        shape = self.rotate_extrude_node()
        maker = shape.solid('torus').at()
        
        cage_path = self.path_node(
            section_start_angle=0,
            section_sweep_angle=360)
        
        cage_shape = self.rotate_extrude_node(cage_path)
        
        maker.add_at(self.cage_of_node(cage_shape).at())
        
        return maker

    @ad.anchor('Surface anchor')
    def surface(self, angle: float | ad.Angle=0, section_angle: float | ad.Angle=0, t: float =0):
        t += ad.angle(section_angle).degrees() / ad.angle(self.section_sweep_angle).degrees()
        return self.maker.at(
            'surface',
            angle=angle,
            t=t) * ad.ROTX_180
        
    @ad.anchor('Surface anchor on cage')
    def cage_surface(self, angle: float | ad.Angle =0, section_angle: float | ad.Angle =0, t: float =0):
        t += ad.angle(section_angle).degrees() / ad.angle(self.section_sweep_angle).degrees()
        return self.maker.at(
            'cage', 'surface',
            angle=angle,
            t=t) * ad.ROTX_180
            
    @ad.anchor('Section centre to start of torus arc.')
    def centre_start(self, angle: float | ad.Angle =0, r: float =0, rr: float =0):
        t = rr + r / self.r_section
        return self.maker.at(
            'section_centre_to_surface',
            angle=angle,
            t=t) * ad.ROTX_180
                    
    @ad.anchor('Section centre to start of cage torus arc.')
    def cage_centre_start(self, angle: float | ad.Angle =0, r: float =0, rr: float =0):
        t = rr + r / self.r_section
        return self.maker.at(
            'cage', 'section_centre_to_surface',
            angle=angle,
            t=t) * ad.ROTX_180

    @ad.anchor('Section centre to end of torus arc.')
    def centre_end(self, angle: float | ad.Angle =0, r: float =0, rr: float =0):
        t = rr + r / self.r_section
        return self.maker.at(
            'surface_to_section_centre',
            angle=angle,
            t=t) * ad.ROTX_180
        
    @ad.anchor('Section centre to end of cage torus arc.')
    def cage_centre_end(self, angle: float | ad.Angle =0, r: float =0, rr: float =0):
        t = rr + r / self.r_section
        return self.maker.at(
            'cage', 'surface_to_section_centre',
            angle=angle,
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
        r_hole=10,
        r_section=4,
        path_fn=32,
        metadata_fn=32,
        fn=128)
    
    EXAMPLE_ANCHORS=(ad.surface_args(
            'surface', section_angle=10, angle=10),)

    def build(self) -> ad.Maker:
        shape = self.torus_node()
        maker = shape.solid(('torus', 0)).at(post=ad.rotX(-60))
        
        for i in range(1, self.count):
            angle = 60 * (-1 if i % 2 else 1)
            maker.add_at(
                shape.solid(('torus', i)).at('surface'),
                ('torus', i-1), 'surface', angle=180, 
                post=ad.ROTX_180 * ad.rotZ(angle) * ad.tranZ(-self.r_section / 3))
        
        return maker


MAIN_DEFAULT=ad.ModuleDefault(all=True)
if __name__ == "__main__":
    ad.anchorscad_main(False)
