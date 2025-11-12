import anchorscad as ad
from typing import Tuple # Use Tuple for field types as per datatree best practices (immutable)
import math # For math operations if needed, ad.rotate typically takes degrees

@ad.shape
@ad.datatree(frozen=True) # frozen=True is good practice for datatree objects
class KnifeBlock(ad.CompositeShape):
    """
    A parametric knife block that can be slanted and oriented.
    Slots are defined by a 2D array of knife girths (width of knife slot).
    The block is conceptually constructed flat (slots opening upwards along Z),
    then rotated as a whole to achieve the desired slant and final orientation.
    """
    # --- Configuration Parameters ---
    knife_slots_config: Tuple[Tuple[float, ...], ...] = ad.dtfield(
        default=((25.0, 20.0), (15.0, 15.0, 15.0)), # Default: 2 rows, various girths
        doc="Tuple of tuples. Each inner tuple contains knife girths (slot widths in mm) for a row."
    )
    slot_depth: float = ad.dtfield(
        default=150.0, 
        doc="Depth of the knife slots (mm)."
    )
    slot_blade_thickness: float = ad.dtfield(
        default=3.0, 
        doc="Thickness of the knife blade slot (Y-dimension of slot when block is flat, mm)."
    )
    row_spacing: float = ad.dtfield(
        default=20.0, 
        doc="Spacing between rows of slots (center-to-center spacing for slot_blade_thickness, mm)."
    )
    slot_spacing: float = ad.dtfield(
        default=20.0, 
        doc="Spacing between individual slots in a single row (edge-to-edge, mm)."
    )
    
    margin_sides: float = ad.dtfield(
        default=20.0, 
        doc="Margin on the left and right sides of the slot area (X-dimension, mm)."
    )
    margin_front_back: float = ad.dtfield(
        default=20.0, 
        doc="Margin on the 'front' and 'back' of the slot area (Y-dimension when block is flat, mm)."
    )
    base_thickness: float = ad.dtfield(
        default=20.0, 
        doc="Thickness of the block material below the bottom of the deepest slot (mm)."
    )
    
    block_angle_deg: float = ad.dtfield(
        default=75.0, 
        doc="Angle of the block's front face with the horizontal plane (e.g., 75 deg means slanted back by 15 deg from vertical)."
    )
    block_orientation_z_deg: float = ad.dtfield(
        default=0.0, 
        doc="Additional rotation around the Z-axis after slanting (degrees)."
    )
    
    epsilon: float = ad.dtfield(
        default=0.1, 
        doc="Small value for CSG operations to ensure holes cut through properly."
    )

    # --- Computed Internal Fields (not directly set by user) ---
    _slots_area_width: float = ad.dtfield(
        self_default=lambda s: max(
            (sum(girths) + (len(girths) - 1) * s.slot_spacing if girths else 0.0)
            for girths in s.knife_slots_config
        ) if s.knife_slots_config else 0.0,
        init=False, repr=False, doc="Calculated width of the area occupied by all slots and their spacing."
    )
    
    _slots_area_depth: float = ad.dtfield(
        self_default=lambda s: (
            len(s.knife_slots_config) * s.slot_blade_thickness +
            (max(0, len(s.knife_slots_config) - 1)) * s.row_spacing
        ) if s.knife_slots_config else 0.0,
        init=False, repr=False, doc="Calculated depth (Y-dim when flat) of the area occupied by all rows and their spacing."
    )

    _block_face_width: float = ad.dtfield(
        self_default=lambda s: s._slots_area_width + 2 * s.margin_sides,
        init=False, repr=False, doc="Total width of the block's face (X-dim when flat)."
    )
    
    _block_face_depth: float = ad.dtfield(
        self_default=lambda s: s._slots_area_depth + 2 * s.margin_front_back,
        init=False, repr=False, doc="Total depth of the block's face (Y-dim when flat)."
    )
    
    _block_thickness_total: float = ad.dtfield(
        self_default=lambda s: s.slot_depth + s.base_thickness,
        init=False, repr=False, doc="Total thickness of the block (Z-dim when flat, along slot depth)."
    )

    # --- Example Configuration for Testing ---
    EXAMPLE_SHAPE_ARGS = ad.args(
        knife_slots_config=((30.0, 25.0, 20.0), (18.0, 18.0, 18.0, 18.0), (10.0, 10.0)),
        slot_depth=160.0,
        slot_blade_thickness=3.5,
        row_spacing=22.0, # Note: This is spacing between slot_blade_thickness areas
        slot_spacing=22.0,
        margin_sides=25.0,
        margin_front_back=25.0,
        base_thickness=25.0,
        block_angle_deg=70.0, # Slanted back 20 deg from vertical
        block_orientation_z_deg=10.0,
        #fn=64 # OpenSCAD rendering quality (though this model is all boxes)
    )
    EXAMPLE_ANCHORS = () # No custom anchors defined on the KnifeBlock itself for now

    def build(self) -> ad.Maker:
        """
        Constructs the knife block model.
        The strategy is to build the block lying flat (slots pointing up in Z),
        and then rotate the entire assembly.
        """
        # This maker will hold all components of the block (solid part and holes)
        # before the final rotation. It's centered at its own origin.
        #flat_block_components_maker = ad.Maker()

        # 1. Define the main solid block shape (when lying flat)
        # Its dimensions are calculated based on slot configuration and margins.
        main_block_shape = ad.Box(size=(self._block_face_width, self._block_face_depth, self._block_thickness_total))
        
        flat_block_components_maker = main_block_shape.solid('base_block_solid').at('centre')
        
        # Add the solid block to the flat_block_components_maker.
        # It's defined .at('centre'), so its center will be at the origin of flat_block_components_maker.
        #base_block_solid_component = main_block_shape.solid('base_block_solid').at('centre')
        #flat_block_components_maker.add(base_block_solid_component)

        # 2. Create and add the knife slots (as holes)
        # Slots are positioned relative to the center of the block's top face.
        # When the block is flat and centered at origin, its top face is at Z = self._block_thickness_total / 2.
        
        # Y-coordinate for the center of the first row's slots on the block face
        # (relative to block face center, which is Y=0 for the centered block)
        # This is the Y-center of the *strip* of thickness slot_blade_thickness for the first row.
        current_y_center_of_row_strip = -self._slots_area_depth / 2 + self.slot_blade_thickness / 2
        
        for row_idx, row_girths in enumerate(self.knife_slots_config):
            if not row_girths: # Skip empty rows
                continue

            # Calculate the total width occupied by slots and spacing in the current row
            current_row_content_width = sum(row_girths) + (max(0, len(row_girths) - 1)) * self.slot_spacing
            
            # X-coordinate for the center of the first slot in this row
            # (relative to block face center, X=0)
            current_x_center_of_slot = -current_row_content_width / 2 + row_girths[0] / 2
            
            for slot_idx, girth in enumerate(row_girths):
                # Define the shape for a single slot hole
                slot_hole_shape = ad.Box(size=(girth, self.slot_blade_thickness, self.slot_depth + self.epsilon))
                
                # Determine the absolute X, Y, Z coordinates for the top-center of this hole
                # in the flat_block_components_maker's coordinate system.
                hole_top_center_x = current_x_center_of_slot
                hole_top_center_y = current_y_center_of_row_strip
                hole_top_center_z = self._block_thickness_total / 2 # Hole's top aligns with block's top

                # Define the hole component. Its local Z=0 is its top face, XY centered ('face_centre', 'top').
                # Then, this local frame is translated to the calculated absolute position.
                hole_as_component = slot_hole_shape.hole(
                    ('slot', row_idx, slot_idx) # Unique name for the hole
                ).colour('red').at(
                    'face_centre', 'top', # Local anchor: Z=0 at top face, XY centered
                    post=ad.rotX(180) * ad.translate((hole_top_center_x, hole_top_center_y, hole_top_center_z))
                     # Rotate 90 deg around X to align with block face
                )
                
                # Add this positioned hole to the flat block assembly
                flat_block_components_maker.add(hole_as_component)
                
                # Advance X-coordinate for the next slot in the current row
                if slot_idx < len(row_girths) - 1:
                    # Move from center of current slot to center of next slot
                    current_x_center_of_slot += (girth / 2) + self.slot_spacing + (row_girths[slot_idx+1] / 2)
            
            # Advance Y-coordinate for the center of the next row's strip
            # This moves from the center of current row's strip to center of next one
            if row_idx < len(self.knife_slots_config) - 1 :
                 current_y_center_of_row_strip += self.slot_blade_thickness / 2 + self.row_spacing + self.slot_blade_thickness / 2


        # 3. Apply final transformations (slant and orientation)
        # The flat_block_components_maker is now complete, with all parts centered around its origin.
        # We define a new Maker that is the flat_block_components_maker transformed.
        
        # Slant transformation: Rotate around X-axis.
        # block_angle_deg = 90 means vertical block face, 0 means flat on table.
        # To slant "back", if block_angle_deg = 75 (15 deg from vertical), rotate by 75-90 = -15 deg around X.
        slant_transform = ad.rotX(self.block_angle_deg - 90.0)
        
        # Orientation transformation: Rotate around Z-axis.
        orient_transform = ad.rotY(self.block_orientation_z_deg)
        
        # Combine transformations: AnchorSCAD applies matrix multiplication such that B then A is A * B.
        # We want to apply slant first, then orientation to the already slanted block.
        # So, the object is first slanted (transformed by slant_transform).
        # Then, this result is oriented (transformed by orient_transform).
        # This means the combined transformation is orient_transform * slant_transform.
        combined_final_transform = orient_transform * slant_transform
        
        # Create the final maker by taking the 'centre' anchor of the flat assembly
        # and applying the combined_final_transform to it.
        # The .at() method on a Maker with a 'post' transform effectively returns a new
        # Maker representing the transformed original.
        fully_transformed_block_maker = flat_block_components_maker.solid('final_block_solid').at('centre', post=combined_final_transform)
        
        return fully_transformed_block_maker

MAIN_DEFAULT=ad.ModuleDefault(all=True)

# Standard boilerplate for running AnchorSCAD scripts
if __name__ == "__main__":
    # This allows AnchorSCAD's command-line tools to discover and render shapes in this file.
    # For example, running `python your_script_name.py --write-scad`
    # or `python your_script_name.py --render KnifeBlock --args "fn=30" --output-stl`
    ad.anchorscad_main()

    # To manually render a specific configuration from within Python (e.g., for debugging):
    # block_instance = KnifeBlock(
    #     knife_slots_config=((50,50),(20,20,20)),
    #     block_angle_deg=65,
    #     fn=32
    # )
    # print(f"Attempting to render: {block_instance.name}")
    # ad.render_to_file(block_instance, f"{block_instance.name}.scad")
    # print(f"Generated {block_instance.name}.scad")

