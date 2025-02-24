"""
Created on 24-Feb-2025

@author: gianni

This is a base for a water dispenser that would normally be placed on a 
20L water bottle. The base is designed to be 3D printed and is intended to 
be held by a tolerance fit.
"""

import anchorscad as ad

from anchorscad_models.screws.CountersunkScrew import CountersunkScrew

@ad.datatree
class BasePathBuilder:
    """A simple example of a path builder."""

    rol: float = ad.dtfield(58.78 / 2, doc="Lower outer radius")  # type: ignore
    rou: float = ad.dtfield(58.35 / 2, doc="Upper outer radius")  # type: ignore
    ril: float = ad.dtfield(18.13 / 2, doc="Lower inner radius")  # type: ignore
    riu: float = ad.dtfield(18.60 / 2, doc="Upper inner radius")  # type: ignore
    offset: float = ad.dtfield(0.1, doc="Adjustment for 3D printer tolerances")  # type: ignore
    h: float = ad.dtfield(15, doc="Height")  # type: ignore
    chamfer: float = ad.dtfield(1, doc="Chamfer size")  # type: ignore

    def build(self) -> ad.Path:
        builder = (
            ad.PathBuilder()
            .move((self.ril + self.offset + self.chamfer, 0))
            .line((self.riu + self.offset, self.chamfer), "inner-lower-chamfer")
            .line((self.riu + self.offset, self.h - self.chamfer), "inner")
            .line((self.riu + self.offset + self.chamfer, self.h), "inner-upper-chamfer")
            .line((self.rou - self.offset - self.chamfer, self.h), "top")
            .line((self.rou - self.offset, self.h - self.chamfer), "outer-upper-chamfer")
            .line((self.rol - self.offset, self.chamfer), "outer")
            .line((self.rol - self.offset - self.chamfer, 0), "outer-lower-chamfer")
            .line((self.ril + self.offset + self.chamfer, 0), "base")
        )

        with builder.construction() as c:
            c.move((0, 0))
            c.line((0, self.h), "centre-line")

        return builder.build()


@ad.shape
@ad.datatree
class WaterFountainBase(ad.CompositeShape):
    """
    A base for a water dispenser that would normally be placed on a 
    20L water bottle.
    """

    base_path_node: ad.Node[BasePathBuilder]
    base_path: ad.Path = ad.dtfield(self_default=lambda s: s.base_path_node().build())

    extrude_node: ad.Node[ad.RotateExtrude] = ad.ShapeNode(ad.RotateExtrude, prefix="base_")

    screw_shaft_overall_length: float = ad.dtfield(self_default=lambda s: s.h * 2)
    screw_shaft_thru_length: float = ad.dtfield(self_default=lambda s: s.h * 2)
    screw_tap_shaft_dia_delta: float = 0
    screw_size_name: str = "M6"
    screw_head_depth_factor: float = 1.1
    screw_include_thru_shaft: bool = False
    screw_as_solid: bool = False
    screw_hole_node: ad.Node = ad.ShapeNode(CountersunkScrew, prefix='screw_')

    screw_cage_r: float = ad.dtfield(0.4 + (41.35 + 21.3) / 4, doc="Screw cage radius")
    screw_cage_h: float = ad.dtfield(8, doc="Screw cage height")
    screw_cage_node: ad.Node = ad.ShapeNode(ad.Cylinder, prefix='screw_cage_')

    rib_w: float = ad.dtfield(1.25, doc="Rib width")
    rib_h: float = ad.dtfield(1.1, doc="Rib height")
    rib_size: tuple[float, float, float] = ad.dtfield(
        self_default=lambda s: (s.rib_w, s.rib_h, s.h),
        doc='The (x,y,z) size of the rib',
    )
    rib_node: ad.Node = ad.ShapeNode(ad.Box, prefix='rib_')


    EXAMPLE_SHAPE_ARGS = ad.args(fn=128)
    EXAMPLE_ANCHORS = (
        ad.surface_args("screw_cage", "top"),
        ad.surface_args("screw_cage", "surface", rh=1),
        ad.surface_args("screw_cage", "surface", rh=1, angle=180),
    )

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid("fountain_base").at("centre-line", 0, post=ad.ROTX_270)

        screw_cage_shape: ad.Shape = self.screw_cage_node()

        screw_cage = screw_cage_shape.solid("screw_cage").colour('red', 0.5).transparent(True).at("top", rh=1)

        maker.add_at(screw_cage, "centre-line", 0, post=ad.ROTX_270)

        screw_shape = self.screw_hole_node()

        for i in range(2):
            maker.add_at(
                screw_shape.composite(("screw", i)).at("top"),
                "screw_cage", 
                "surface",
                rh=1,
                angle=180 * i,
                post=ad.ROTX_270,
            )

        rib_shape = self.rib_node()
        rib_count = 5
        for i in range(rib_count):
            maker.add_at(
                rib_shape.hole(("rib", i)).at("face_centre", "front"),
                "fountain_base",
                "outer",
                t=0.5,
                angle=90 +360 * i / rib_count,
                post=ad.ROTY_180,
            )
        return maker
    


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT = ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
