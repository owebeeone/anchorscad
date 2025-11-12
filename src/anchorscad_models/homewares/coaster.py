import anchorscad as ad
import math
from typing import Tuple

# Set default behavior to write output files when script is run
MAIN_DEFAULT = ad.ModuleDefault(True, False, False) # Write .scad, not graph, not deps

@ad.shape
@ad.datatree(frozen=True)
class Coaster(ad.CompositeShape):
    '''A cup coaster with a hexagonal cutout pattern.'''

    # --- Parameters ---
    diameter: float = ad.dtfield(90.0, 'Outer diameter of the coaster (mm)')
    height: float = ad.dtfield(5.0, 'Total height of the coaster (mm)')
    rim_width: float = ad.dtfield(4.0, 'Width of the solid outer rim (mm)')
    hex_radius: float = ad.dtfield(5.0, 'Radius of the hexagonal cutouts (mm)')
    hex_center_dist: float = ad.dtfield(10.0, 'Distance between centers of adjacent hexagons (mm)')
    epsilon: float = ad.dtfield(0.01, 'Small value for ensuring clean cuts')
    fn: int = ad.dtfield(64, 'OpenSCAD $fn subdivision parameter for curves')

    # --- Calculated Fields ---
    inner_radius: float = ad.dtfield(doc='Radius inside the rim',
                                     self_default=lambda s: s.diameter / 2 - s.rim_width)

    # --- Nodes for Shapes ---
    # Using ShapeNode automatically passes self.fn, self.fa, self.fs if they exist
    base_cylinder_node: ad.Node = ad.dtfield(
        ad.ShapeNode(ad.Cylinder, exclude=('r',)), # Exclude r as it's calculated below
        init=False, repr=False
    )
    inner_hole_node: ad.Node = ad.dtfield(
        ad.ShapeNode(ad.Cylinder, exclude=('r', 'h')),
        init=False, repr=False
    )
    hex_hole_node: ad.Node = ad.dtfield(
        ad.ShapeNode(ad.Cylinder, exclude=('r', 'h')), # Exclude r, h as they are set below
        init=False, repr=False
    )

    # --- Example Arguments for anchorscad_main ---
    EXAMPLE_SHAPE_ARGS = ad.args(diameter=95, height=5, rim_width=5, hex_radius=6, hex_center_dist=12)

    def build(self) -> ad.Maker:
        '''Builds the coaster Maker object.'''

        # 1. Create the main base cylinder
        maker = self.base_cylinder_node(
            r=self.diameter / 2,
            h=self.height
        ).solid('base').at('base') # Position relative to its base

        # 2. Create the inner cutout for the rim (if rim_width > 0)
        if self.inner_radius > 0 and self.rim_width > 0:
            inner_hole_maker = self.inner_hole_node(
                r=self.inner_radius,
                h=self.height + 2 * self.epsilon # Make slightly taller for clean cut
            ).hole('inner_cut').at('base')

            # Add the inner hole, offsetting slightly down
            maker.add_at(inner_hole_maker, 'base', post=ad.tranZ(-self.epsilon))
            maker = maker.solid('main').at()
        else:
            # If no rim, the pattern goes to the edge boundary check below handles it
            pass

        # 3. Create the hexagonal hole pattern
        hole_hex_shape = self.hex_hole_node(
            r=self.hex_radius,
            h=self.height+ 2 * self.epsilon, # Ensure cut goes through
            fn=6 # Make the cylinder a hexagon
        )
        

        # Hex grid calculations
        step_y = self.hex_center_dist * math.sqrt(3) / 2 # Vertical distance between rows
        step_x = self.hex_center_dist                 # Horizontal distance in a row
        num_y = int(self.diameter / step_y) + 2
        num_x = int(self.diameter / step_x) + 2

        pattern_radius_limit_sq = (self.inner_radius - self.hex_radius / 2)**2 # Check center position

        for j in range(-num_y // 2, num_y // 2 + 1):
            y_pos = j * step_y
            x_offset = (j % 2) * step_x / 2 # Offset alternate rows

            for i in range(-num_x // 2, num_x // 2 + 1):
                x_pos = i * step_x + x_offset

                # Check if the center of the hex is within the inner radius boundary
                if x_pos**2 + y_pos**2 < pattern_radius_limit_sq:
                    # Add the hex hole relative to the main base's origin
                    hole_maker = hole_hex_shape.solid(('hex_hole', i, j)).colour('red').at('base', post=ad.rotZ(30)) # Name the hole type
                    maker.add_at(
                        hole_maker, # The hole maker defined above
                        'base',     # Align with the base plate's 'base' anchor (origin)
                        # Apply a translation to move the hole to the correct (x, y)
                        # and slightly down (-epsilon)
                        post=ad.translate((x_pos, y_pos, -self.epsilon))
                    )

        return maker


# This standard block allows running the script directly
if __name__ == "__main__":
    ad.anchorscad_main()