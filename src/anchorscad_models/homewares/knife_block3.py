"""
Simple Parametric Knife Block - Clean Implementation

Creates a knife block with configurable slot arrangement defined by a 2D array.
Each sub-array represents a row of knife slots with specified girths.

Example: [[20, 20, 15], [10, 10, 10, 10]]
- First row: 3 slots of 20mm, 20mm, 15mm girth
- Second row: 4 slots of 10mm girth each
"""

import anchorscad as ad
from typing import Tuple


@ad.shape
@ad.datatree
class KnifeBlock(ad.CompositeShape):
    """
    A simple knife block with rows of slots for different knife sizes.
    """
    
    # Main knife slot configuration - 2D array as requested
    knife_girths: Tuple[Tuple[float, ...], ...] = ad.dtfield(
        default=((20.0, 20.0, 15.0), (10.0, 10.0, 10.0, 10.0)),
        doc="2D array: each inner tuple defines girths (widths) for a row of knife slots"
    )
    
    # Basic dimensions
    knife_length: float = ad.dtfield(
        default=200.0,
        doc="Overall length of knives (depth of slots)"
    )
    slot_width: float = ad.dtfield(
        default=4.0, 
        doc="Width of each slot (blade thickness)"
    )
    
    # Layout spacing
    margin: float = ad.dtfield(
        default=25.0,
        doc="Margin around all edges"
    )
    slot_gap: float = ad.dtfield(
        default=15.0,
        doc="Gap between adjacent slots"
    )
    row_gap: float = ad.dtfield(
        default=20.0,
        doc="Gap between rows"
    )
    
    # Block properties
    base_height: float = ad.dtfield(
        default=30.0,
        doc="Height of solid base below slots"
    )
    slant_angle: float = ad.dtfield(
        default=15.0,
        doc="Angle to slant block backward (degrees)"
    )
    orientation: float = ad.dtfield(
        default=0.0,
        doc="Rotation around vertical axis (degrees)"
    )
    
    # Base flattening
    base_cut: float = ad.dtfield(
        default=5.0,
        doc="Distance to cut from bottom for flat base"
    )
    
    # Calculated dimensions
    _block_width: float = ad.dtfield(
        self_default=lambda s: max(
            sum(row) + (len(row) - 1) * s.slot_gap 
            for row in s.knife_girths if row
        ) + 2 * s.margin,
        init=False
    )
    
    _block_depth: float = ad.dtfield(
        self_default=lambda s: (
            len(s.knife_girths) * s.slot_width + 
            (len(s.knife_girths) - 1) * s.row_gap + 
            2 * s.margin
        ),
        init=False
    )
    
    _block_height: float = ad.dtfield(
        self_default=lambda s: s.knife_length + s.base_height,
        init=False
    )
    
    # Example shape
    EXAMPLE_SHAPE_ARGS = ad.args(
        knife_girths=((25.0, 20.0, 15.0), (12.0, 12.0, 12.0, 12.0)),
        knife_length=180.0,
        slant_angle=20.0,
        orientation=10.0,
        margin=30.0
    )
    
    EXAMPLE_ANCHORS = ()

    def build(self) -> ad.Maker:
        """Build the knife block step by step."""
        
        # 1. Create main solid block
        block = ad.Box([self._block_width, self._block_depth, self._block_height])
        maker = block.solid('main').at('centre')
        
        # 2. Cut knife slots
        self._add_knife_slots(maker)
        
        # 3. Transform the whole assembly
        transformed = self._apply_transforms(maker)
        
        # 4. Cut flat bottom
        final = self._cut_flat_base(transformed)
        
        return final
    
    def _add_knife_slots(self, maker: ad.Maker):
        """Add all the knife slots as holes."""
        
        # Start position for first row
        y_start = -self._block_depth/2 + self.margin + self.slot_width/2
        
        for row_idx, girths in enumerate(self.knife_girths):
            if not girths:
                continue
                
            # Y position for this row
            y_pos = y_start + row_idx * (self.slot_width + self.row_gap)
            
            # Calculate row layout
            row_width = sum(girths) + (len(girths) - 1) * self.slot_gap
            x_start = -row_width/2
            x_pos = x_start
            
            # Create each slot in the row
            for slot_idx, girth in enumerate(girths):
                x_center = x_pos + girth/2
                
                # Make slot hole - extra long to ensure it cuts through
                slot = ad.Box([
                    girth + 1.0,  # Slightly wider
                    self.slot_width + 1.0,  # Slightly thicker  
                    self._block_height + 10.0  # Much taller
                ])
                
                slot_hole = slot.hole(f'slot_{row_idx}_{slot_idx}').at(
                    'centre',
                    post=ad.translate([x_center, y_pos, 0])
                )
                
                maker.add(slot_hole)
                
                # Move to next slot position
                x_pos += girth + self.slot_gap
    
    def _apply_transforms(self, maker: ad.Maker) -> ad.Maker:
        """Apply slant and orientation transforms."""
        
        # Combine transformations
        slant = ad.rotX(-self.slant_angle)
        orient = ad.rotZ(self.orientation)
        transform = orient * slant
        
        return maker.solid('transformed').at('centre', post=transform)
    
    def _cut_flat_base(self, maker: ad.Maker) -> ad.Maker:
        """Cut the bottom flat for stable placement."""
        
        # Large cutting box positioned below the base cut line
        size = max(self._block_width, self._block_depth, self._block_height) * 2
        cutter = ad.Box([size, size, size])
        
        cut_hole = cutter.hole('base_cut').at(
            'face_centre', 'top',
            post=ad.translate([0, 0, -self.base_cut])
        )
        
        maker.add(cut_hole)
        return maker.solid('knife_block').at('centre')


# Standard AnchorSCAD boilerplate
MAIN_DEFAULT = ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main() 