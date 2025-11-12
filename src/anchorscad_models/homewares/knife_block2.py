"""
A parametric knife block model using AnchorSCAD.

This model creates a slanted knife block with configurable slots arranged in rows.
Each row can contain multiple knife slots with different girths (widths).

Author: Created with AnchorSCAD API
"""

import anchorscad as ad
from typing import Tuple


@ad.shape
@ad.datatree
class KnifeBlock(ad.CompositeShape):
    """
    A parametric knife block that can be slanted and oriented.
    
    The block is defined by a 2D array where each inner array represents
    a row of knife slots, and each value represents the girth (width) of
    a knife slot in that row.
    
    Example:
        knife_slots = [[20, 20, 15], [10, 10, 10, 10]]
        This creates:
        - Row 1: 3 slots of 20mm, 20mm, and 15mm width
        - Row 2: 4 slots of 10mm width each
    """
    
    # Main configuration parameters
    knife_slots: Tuple[Tuple[float, ...], ...] = ad.dtfield(
        default=((20.0, 20.0, 15.0), (10.0, 10.0, 10.0, 10.0)),
        doc="2D array defining knife slot girths. Each inner tuple is a row of slots."
    )
    
    # Slot dimensions
    slot_depth: float = ad.dtfield(
        default=150.0,
        doc="Depth of knife slots in mm."
    )
    slot_thickness: float = ad.dtfield(
        default=3.0,
        doc="Thickness of each slot (blade thickness) in mm."
    )
    
    # Spacing parameters
    row_spacing: float = ad.dtfield(
        default=25.0,
        doc="Spacing between rows of slots in mm."
    )
    slot_spacing: float = ad.dtfield(
        default=20.0,
        doc="Spacing between individual slots within a row in mm."
    )
    
    # Margin parameters
    margin_x: float = ad.dtfield(
        default=20.0,
        doc="Margin on left and right sides in mm."
    )
    margin_y: float = ad.dtfield(
        default=20.0,
        doc="Margin on front and back in mm."
    )
    base_thickness: float = ad.dtfield(
        default=20.0,
        doc="Thickness of material below slots in mm."
    )
    
    # Angle and orientation parameters
    slant_angle: float = ad.dtfield(
        default=15.0,
        doc="Angle to slant the block backwards from vertical in degrees."
    )
    orientation_angle: float = ad.dtfield(
        default=0.0,
        doc="Additional rotation around Z-axis in degrees."
    )
    
    # Base flattening parameters
    base_cut_offset: float = ad.dtfield(
        default=2.0,
        doc="Offset from bottom for base cut to ensure flat bottom in mm."
    )
    
    # Small epsilon for CSG operations
    epsilon: float = ad.dtfield(
        default=1.0,
        doc="Small value for ensuring proper CSG operations."
    )
    
    # Computed dimensions
    _total_width: float = ad.dtfield(
        self_default=lambda s: max(
            sum(row) + (len(row) - 1) * s.slot_spacing if row else 0.0
            for row in s.knife_slots
        ) + 2 * s.margin_x,
        init=False,
        doc="Total width of the block."
    )
    
    _total_depth: float = ad.dtfield(
        self_default=lambda s: (
            len(s.knife_slots) * s.slot_thickness + 
            (len(s.knife_slots) - 1) * s.row_spacing +
            2 * s.margin_y
        ),
        init=False,
        doc="Total depth of the block."
    )
    
    _total_height: float = ad.dtfield(
        self_default=lambda s: s.slot_depth + s.base_thickness,
        init=False,
        doc="Total height of the block."
    )
    
    # Example configuration
    EXAMPLE_SHAPE_ARGS = ad.args(
        knife_slots=((30.0, 25.0, 20.0), (18.0, 18.0, 18.0), (15.0, 15.0)),
        slot_depth=160.0,
        slot_thickness=3.5,
        row_spacing=22.0,
        slot_spacing=25.0,
        margin_x=25.0,
        margin_y=25.0,
        base_thickness=25.0,
        slant_angle=20.0,
        orientation_angle=15.0,
        base_cut_offset=3.0,
    )
    
    EXAMPLE_ANCHORS = ()

    def build(self) -> ad.Maker:
        """
        Build the knife block model.
        
        Strategy:
        1. Create the main block as a solid
        2. Create slots as holes that extend through the entire height
        3. Apply slant and orientation transformations
        4. Cut the base flat so it sits properly on a surface
        """
        
        # Create the main solid block
        main_block = ad.Box([self._total_width, self._total_depth, self._total_height])
        maker = main_block.solid('main_block').at('centre')
        
        # Calculate starting positions for slots
        start_y = -self._total_depth / 2 + self.margin_y + self.slot_thickness / 2
        
        # Create slots for each row - holes extend through entire height
        for row_idx, row in enumerate(self.knife_slots):
            if not row:  # Skip empty rows
                continue
                
            # Calculate row width and starting X position
            row_width = sum(row) + (len(row) - 1) * self.slot_spacing
            start_x = -row_width / 2
            current_x = start_x
            
            # Calculate Y position for this row
            current_y = start_y + row_idx * (self.slot_thickness + self.row_spacing)
            
            # Create slots for this row
            for slot_idx, girth in enumerate(row):
                # Position for this slot
                slot_x = current_x + girth / 2
                
                # Create slot as a hole that extends through the entire height
                # Make it slightly larger in all dimensions to ensure complete penetration
                slot_height = self._total_height + 2 * self.epsilon
                slot_width = girth + 2 * self.epsilon  # Add epsilon to width
                slot_thickness = self.slot_thickness + 2 * self.epsilon  # Add epsilon to thickness
                slot = ad.Box([slot_width, slot_thickness, slot_height])
                
                slot_maker = slot.hole(('slot', row_idx, slot_idx)).at(
                    'centre',
                    post=ad.translate([slot_x, current_y, 0])
                )
                
                # Add slot to the main maker
                maker.add(slot_maker)
                
                # Move to next slot position
                current_x += girth + self.slot_spacing
        
        # Apply slant transformation first
        slant_transform = ad.rotX(-self.slant_angle)
        
        # Apply orientation transformation
        orientation_transform = ad.rotZ(self.orientation_angle)
        
        # Combine transformations (orientation after slant)
        combined_transform = orientation_transform * slant_transform
        
        # Create slanted block
        slanted_maker = maker.solid('slanted_block').at('centre', post=combined_transform)
        
        # Create a cutting box to flatten the base
        # The cutting box should be large enough and positioned to cut the bottom flat
        cut_size = max(self._total_width, self._total_depth, self._total_height) * 3
        cutting_box = ad.Box([cut_size, cut_size, cut_size])
        
        # Position the cutting box to cut below the base_cut_offset
        cut_maker = cutting_box.hole('base_cut').at(
            'face_centre', 'top',
            post=ad.translate([0, 0, -self.base_cut_offset])
        )
        
        # Apply the base cut to flatten the bottom
        slanted_maker.add(cut_maker)
        
        # Create final maker
        final_maker = slanted_maker.solid('knife_block').at('centre')
        
        return final_maker


# Main execution
MAIN_DEFAULT = ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
