"""
Parametric Citrus Juicer Model

A functional hand-operated citrus juicer that 3D prints as one piece:
- Integrated shallow bowl to catch juice
- Textured central reamer with bulbous profile for juice extraction
- Properly integrated spout
- Single-piece design for 3D printing

Author: Created with AnchorSCAD API
"""

import anchorscad as ad
import math


@ad.datatree
class ReamerPath:
    """
    Path factory for creating reamer profiles using PathBuilder.
    """
    
    # Reamer profile dimensions
    h: float = ad.dtfield(
        default=40.0,
        doc="Height of the reamer in mm"
    )
    r: float = ad.dtfield(
        default=20.0,
        doc="Base radius of the reamer profile in mm (actual max may vary with spline)"
    )
    taper_slope: float = ad.dtfield(
        default=0,
        doc="Taper control at base in mm"
    )
    height_slope: float = ad.dtfield(
        default=0.2,
        doc="Height slope control at top in mm"
    )
    cv_len: tuple[float, float] = ad.dtfield(
        default=(20.0, 20.0),
        doc="Control vector lengths for spline (start, end)"
    )
    
    EXAMPLE_SHAPE_ARGS = ad.args()
    EXAMPLE_ANCHORS = ()

    def build(self):
        """Build the reamer profile path."""
        
        # Create path for bulbous reamer profile using our parameters
        path = (ad.PathBuilder()
                .move([0, 0])  # Start at origin
                .line([0, self.h], 'axis')  # Line up the axis
                .spline([
                    (1, self.h - self.height_slope),                        # Near top, small radius  
                    (self.r - self.taper_slope, 1),     # Near base, main bulge
                    (self.r, 0)  # Base point
                ], name='curve', cv_len=self.cv_len)
                .line([0, 0], 'base')  # Close the path
                .build())
        
        return path


@ad.shape
@ad.datatree
class ReamerOnly(ad.CompositeShape):
    """
    Just the reamer with bulbous profile and bumps for debugging purposes.
    """
    num_height_levels: int = ad.dtfield(
        default=15,
        doc="Number of height levels for bumps"
    )
    # Reamer texture (bumps for juice extraction)
    bumps_per_level: int = ad.dtfield(
        default=30,
        doc="Number of spherical bumps on the reamer"
    )
    bump_r: float = ad.dtfield(
        default=5,
        doc="Radius of texture bumps in mm"
    )
    
    # Shape quality parameters
    fn: int = ad.dtfield(default=64, doc="Number of facets for cylinders")
    fs: float = ad.dtfield(default=0.5, doc="Minimum facet size")
    fa: float = ad.dtfield(default=6.0, doc="Minimum facet angle")
    bump_fn: int = ad.dtfield(default=12, doc="Number of facets for bumps (lower for performance)")
    
    # Shape nodes for quality control
    path_node: ad.Node[ReamerPath] = ad.ShapeNode(ReamerPath)
    reamer_path: ad.Path = ad.dtfield(self_default=lambda s: s.path_node().build(), init=False)
    reamer_node: ad.Node[ad.RotateExtrude] = ad.ShapeNode(ad.RotateExtrude, prefix='reamer_')
    bump_node: ad.Node[ad.Sphere] = ad.ShapeNode(ad.Sphere, {'fn': 'bump_fn'})
    
    EXAMPLE_SHAPE_ARGS = ad.args(
    )
    
    EXAMPLE_ANCHORS = ()

    def build(self) -> ad.Maker:
        """Build the bulbous reamer with bumps."""
        # Create the reamer using RotateExtrude with the path
        reamer = self.reamer_node()
        maker = reamer.solid('reamer').at('base', 1)
        
        # Add texture bumps to the reamer using surface anchors
        self._add_reamer_texture(maker)
        
        return maker.solid('reamer_only').at('centre')
    
    def _add_reamer_texture(self, maker: ad.Maker):
        """Add spherical bumps to the reamer using surface anchors."""
        
        # Simple approach: same number of bumps per level
        num_height_levels = self.num_height_levels
        bumps_per_level = self.bumps_per_level
        
        bump_index = 0
        
        for level in range(num_height_levels):
                
            # Height fraction distribution
            height_fraction = (level + 1) / (num_height_levels + 1)
            
            rotation_offset = level * 30.0
            
            for bump_in_level in range(bumps_per_level):
                    
                angle = (bump_in_level * 360 / bumps_per_level) + rotation_offset
                
                # Create bump and position using surface anchor
                bump = self.bump_node()
                bump_maker = bump.solid(('bump', bump_index)).at('centre')
                
                # Use add_at with curve surface anchor
                maker.add_at(
                    bump_maker, 
                    'reamer', 'curve', t=height_fraction, angle=angle
                )
                
                bump_index += 1


@ad.shape
@ad.datatree
class CitrusJuicer(ad.CompositeShape):
    """
    A functional citrus juicer designed for 3D printing as one piece.
    """
    
    # Main bowl dimensions
    bowl_r: float = ad.dtfield(
        default=80.0,
        doc="Radius of the main juice bowl in mm"
    )
    bowl_h: float = ad.dtfield(
        default=23.0,  # bowl_depth + wall_thickness
        doc="Total height of bowl walls in mm"
    )
    bowl_depth: float = ad.dtfield(
        default=20.0,
        doc="Depth of the juice bowl in mm"
    )
    wall_thickness: float = ad.dtfield(
        default=3.0,
        doc="Thickness of bowl walls in mm"
    )
    
    # # Reamer (central cone) dimensions - sized for actual citrus
    # reamer_h: float = ad.dtfield(
    #     default=30.0,
    #     doc="Height of the central reamer cone in mm"
    # )
    # reamer_r_base: float = ad.dtfield(
    #     default=32.5,
    #     doc="Base radius of the reamer cone in mm (sized for citrus)"
    # )
    # reamer_r_top: float = ad.dtfield(
    #     default=3.0,
    #     doc="Top radius of the reamer cone in mm"
    # )
    
    # # Reamer texture (bumps for juice extraction)
    # bump_count: int = ad.dtfield(
    #     default=300,
    #     doc="Number of spherical bumps on the reamer"
    # )
    # bump_r: float = ad.dtfield(
    #     default=1.5,
    #     doc="Radius of texture bumps in mm"
    # )
    
    # Base dimensions
    base_r: float = ad.dtfield(
        default=90.0,
        doc="Radius of the base for stability in mm"
    )
    base_h: float = ad.dtfield(
        default=10.0,
        doc="Height of the base in mm"
    )
    
    # Bowl cavity dimensions
    cavity_r: float = ad.dtfield(
        default=80.0,  # bowl_diameter / 2
        doc="Radius of the bowl cavity in mm"
    )
    cavity_h: float = ad.dtfield(
        default=21.0,  # bowl_depth + 1.0
        doc="Height of the bowl cavity in mm"
    )
    
    # Spout dimensions
    spout_size: tuple = ad.dtfield(
        default=(20.0, 25.0, 6.0),  # length, width, height
        doc="Size of the pouring spout (length, width, height) in mm"
    )
    
    # Spout channel dimensions
    channel_size: tuple = ad.dtfield(
        default=(35.0, 21.0, 3.5),  # length, width, height
        doc="Size of the spout channel (length, width, height) in mm"
    )
    
    # Shape quality parameters
    fn: int = ad.dtfield(default=64, doc="Number of facets for cylinders")
    fs: float = ad.dtfield(default=0.5, doc="Minimum facet size")
    fa: float = ad.dtfield(default=6.0, doc="Minimum facet angle")
    bump_fn: int = ad.dtfield(default=12, doc="Number of facets for bumps (lower for performance)")
    
    # Shape nodes for quality control
    base_node: ad.Node[ad.Cylinder] = ad.ShapeNode(ad.Cylinder, prefix='base_')
    bowl_node: ad.Node[ad.Cylinder] = ad.ShapeNode(ad.Cylinder, prefix='bowl_')
    reamer_only_node: ad.Node[ReamerOnly] = ad.ShapeNode(ReamerOnly)
    cavity_node: ad.Node[ad.Cylinder] = ad.ShapeNode(ad.Cylinder, prefix='cavity_')
    spout_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='spout_')
    channel_node: ad.Node[ad.Box] = ad.ShapeNode(ad.Box, prefix='channel_')
    
    # Computed dimensions
    _total_height: float = ad.dtfield(
        self_default=lambda s: s.base_h + s.wall_thickness + s.bowl_depth + s.reamer_h,
        init=False,
        doc="Total height of the juicer"
    )
    
    # Example configuration
    EXAMPLE_SHAPE_ARGS = ad.args(
        # reamer_h=25.0,
        # reamer_r=30.0,
        # bump_count=250,
        # bump_r=1.5
    )
    
    EXAMPLE_ANCHORS = ()

    def build(self) -> ad.Maker:
        """Build the integrated citrus juicer as one piece."""
        
        # Create the main structure as one integrated piece
        maker = self._create_integrated_structure()
        
        return maker.solid('citrus_juicer').at('centre')
    
    def _create_integrated_structure(self) -> ad.Maker:
        """Create the main structure as one connected piece."""
        
        # Start with the base using shape node
        base = self.base_node()
        maker = base.solid('base').at('centre')
        
        # Add bowl walls (connected to base)
        bowl_outer_radius = self.bowl_r + self.wall_thickness
        
        # Outer bowl structure using shape node
        outer_bowl = self.bowl_node()
        
        bowl_maker = outer_bowl.solid('bowl_walls').at(
            'base',
            post=ad.translate([0, 0, self.base_h])
        )
        maker.add(bowl_maker)
        
        # Add reamer using ReamerOnly shape node
        reamer = self.reamer_only_node()
        reamer_maker = reamer.solid('reamer').at('base', 1)
        
        # Position reamer at cavity centre using proper anchoring
        maker.add_at(reamer_maker, 'bowl_cavity', 'centre')
        
        # Add integrated spout (connected to bowl rim)
        self._add_integrated_spout(maker, bowl_outer_radius)
        
        # Cut out bowl cavity (after all solid parts are added)
        self._cut_bowl_cavity(maker)
        
        return maker
    
    def _add_integrated_spout(self, maker: ad.Maker, bowl_outer_radius: float):
        """Add spout that's properly integrated with the bowl."""
        
        # Spout positioned at bowl rim level
        spout_z = self.base_h + self.wall_thickness + self.bowl_depth
        
        # Main spout body using shape node
        spout = self.spout_node()
        
        spout_maker = spout.solid('spout').at(
            'face_centre', 'left',
            post=ad.translate([bowl_outer_radius, 0, spout_z - self.wall_thickness])
        )
        maker.add(spout_maker)
    
    def _cut_bowl_cavity(self, maker: ad.Maker):
        """Cut the bowl cavity after all solid parts are integrated."""
        
        # Bowl cavity - positioned to leave walls intact using shape node
        cavity = self.cavity_node()
        
        cavity_maker = cavity.hole('bowl_cavity').at(
            'base',
            post=ad.translate([0, 0, self.base_h + self.wall_thickness])
        )
        maker.add(cavity_maker)
        
        # Cut spout channel using shape node
        spout_z = self.base_h + self.wall_thickness + self.bowl_depth
        bowl_outer_radius = self.bowl_r + self.wall_thickness
        
        # Channel from bowl edge to spout end
        channel = self.channel_node()
        
        channel_maker = channel.hole('spout_channel').at(
            'face_centre', 'left',
            post=ad.translate([bowl_outer_radius - 5, 0, spout_z - 0.5])
        )
        maker.add(channel_maker)
    

# Standard AnchorSCAD boilerplate
MAIN_DEFAULT = ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main() 