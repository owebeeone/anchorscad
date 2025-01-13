'''
Created on 15-Jul-2023

@author: gianni
'''

import anchorscad as ad


@ad.datatree
class PawnPath:
    '''Provides a profile path of a half pawn.
    '''
    h: float = ad.dtfield(46.7, doc='Overall height of pawn')
    r_dome: float = ad.dtfield(16.2 / 2, doc='Radius of top dome')
    a_dome: float = ad.dtfield(147, doc='Sweep angle of top dome in degrees')
    r_base: float = ad.dtfield(26 / 2, doc='Radius of base')
    r_base_inner: float = ad.dtfield(24.5 / 2, doc='Radius base inset')
    r_pedestal: float = ad.dtfield(14 / 2, doc='Radius of pedestal')
    r_base_stem: float = ad.dtfield(9.15 / 2, doc='Radius at base of stem')
    r_top_stem: float =  ad.dtfield(7.2 / 2, doc='Radius at top of stem')

    r_collar: float = ad.dtfield(15.34 / 2, doc='Radius of collar')
    h_collar_centre: float = ad.dtfield(29.3, doc='Height of collar centre')
    h_collar_base: float = ad.dtfield(27.75, doc='Height of collar base')
    h_adjust_collar_for_printability: float = ad.dtfield(
        2, doc='Adjust collar base for printability.'
               ' Makes the collar base sloped up as horizontal edges can\'t be printed.')

    h_stem_bottom: float = ad.dtfield(15.9, doc='Height of stem bottom')
    h_pedestal_rim: float = ad.dtfield(14.4, doc='Height of pedestal rim')
    h_pedestal_base: float = ad.dtfield(11.5, doc='Height of pedestal base')

    h_base_upper_edge: float = ad.dtfield(4.66, doc='Height of base edge upper edge')
    h_base_ridge: float = ad.dtfield(3.2, doc='Height of base ridge')
    
    def build(self) -> ad.Path:
        collar_base_h = self.h_collar_base - self.h_adjust_collar_for_printability

        path = (ad.PathBuilder()
                    .move((0, 0), 'start', (0, 1))
                    .line((0, self.h), 'axis')
                    .arc_tangent_radius_sweep(
                        radius=self.r_dome,
                        sweep_angle=-self.a_dome,
                        angle=90,
                        side=True,
                        name='dome'
                        )
                    .spline(
                        ((self.r_collar, self.h_collar_centre + 1),
                         (self.r_collar, self.h_collar_centre)),
                         angle=(self.a_dome, 0),
                         cv_len=(0.25, 1.0),
                        name='collar_top')
                    .spline(
                        ((self.r_top_stem + 1, collar_base_h + 1),
                         (self.r_top_stem, collar_base_h)),
                         cv_len=(1.5, 1.5),
                        name='collar_bottom')
                    .line((self.r_base_stem, self.h_stem_bottom), 'stem_edge')
                    .spline(
                        ((self.r_base_stem + 1, self.h_stem_bottom - 0.5),
                         (self.r_pedestal, self.h_pedestal_rim + 1),
                         (self.r_pedestal, self.h_pedestal_rim)),
                         cv_len=(0.5, 0.8),
                        name='pedestal_top')
                    .line((self.r_pedestal, self.h_pedestal_base), 'pedestal_edge')
                    .spline(
                        ((self.r_base, self.h_base_upper_edge + 1),
                         (self.r_base, self.h_base_upper_edge)),
                         cv_len=(2.5, 1.8),
                        name='base_top')
                    .spline(
                        ((self.r_base_inner + 1, self.h_base_ridge + 1),
                         (self.r_base_inner, self.h_base_ridge)),
                         cv_len=(0.5, 0.8),
                        name='base_upper_edge')
                    .spline(
                        ((self.r_base, 0 + 1),
                         (self.r_base, 0)),
                         angle=(90, 0),
                         cv_len=(1.5, 0.8),
                        name='base_lower_edge')
                    .line((0, 0), 'base')
                    .build())
        return path


@ad.shape
@ad.datatree
class Pawn(ad.CompositeShape):
    '''
    A pawn chess piece.
    '''
    path_node: ad.Node = ad.Node(PawnPath, expose_all=True)
    path: ad.Path = ad.dtfield(self_default=lambda s: s.path_node().build())
    
    rotate_extrude_node: ad.Node = ad.dtfield(
        ad.ShapeNode(ad.RotateExtrude, expose_all=True))
    
    fn: int = 128

    def build(self) -> ad.Maker:
        
        shape = self.rotate_extrude_node()
        maker = shape.solid('pawn').at('centre')
        return maker


# Uncomment the line below to default to writing all example output files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
