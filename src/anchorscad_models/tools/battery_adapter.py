'''
Created on 23-Jul-2023

@author: gianni
'''

import anchorscad as ad

@ad.datatree
class BatteryAdapterProfile:
    '''Provides a Path for the battery adapter for linear extrusion.
    '''
    r_small: float=ad.dtfield(14.2 / 2, doc='Radius of the smaller battery')
    r_large: float=ad.dtfield(26.2 / 2, doc='Radius of the larger battery')
    compensation: float=ad.dtfield(0.2, doc='Compensation for FDM printer')
    gap_angle: float=ad.dtfield(110, doc='Gap of the enlosing cylinder in angle')

    def build(self) -> ad.Path:

        inner_r = self.r_small + self.compensation
        outer_r = self.r_large - self.compensation

        path = (ad.PathBuilder()
                .move((0, inner_r))
                .line((0, outer_r), 'start')
                .arc_tangent_radius_sweep(
                    radius=outer_r,
                    sweep_angle =self.gap_angle-360,
                    angle=-90,
                    name='outer')
                .stroke(outer_r - inner_r, angle=-90, name='end')
                .arc_tangent_radius_sweep(
                    radius=inner_r,
                    sweep_angle =360-self.gap_angle,
                    angle=90,
                    sweep_direction=True,
                    name='inner')
                .build())
        return path

@ad.shape
@ad.datatree
class BatteryAdapter(ad.CompositeShape):
    '''Battery adapter for cylindrical batteries. This assumes the batteries 
    are the same length but different diameters.
    '''

    count: int=ad.dtfield(2, doc='Number of batteries')
    l: float=ad.dtfield(50, doc='Length of battery')
    margin: float=ad.dtfield(5, doc='Margin at the ends of the batteries')
    profile_node: ad.Node=ad.Node(BatteryAdapterProfile)

    h: float=ad.dtfield(self_default=lambda s: s.l * s.count - s.margin * 2)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.profile_node().build())

    linear_extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)

    fn: int=ad.dtfield(64, doc='Number of facets for the linear extrusion')

    # Example for AA and C batteries.
    EXAMPLE_SHAPE_ARGS=ad.args(r_small=14.2 / 2, r_large=26.2 / 2, count=2)
    
    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.linear_extrude_node()
        maker = shape.solid('adapter').at()
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
