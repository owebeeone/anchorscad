'''
Created on 27 Jan 2024

@author: gianni

Extrusion shapes and Path tools for per layer flexible extrusions in a similar vein 
to LinearExtrude and RotateExtrude in extrude.py.

LinearFlexExtrude and RotateFlexExtrude allow for per layer parameters to define
the extrusion process.

'''

import anchorscad.core as core
from datatrees import datatree, dtfield
from anchorscad.extrude import ExtrudedShape, Path, PathBuilder, PolyhedronBuilder, \
    LinearExtrude, UnknownOperationException, MappedPolygon
import anchorscad_lib.linear as l

import numpy as np
from typing import List, Tuple, Callable
import manifold3d as m3d


@datatree(frozen=True)
class OffsetType:
    '''The type of offset to apply.'''
    offset_type: int
    

@datatree
class PathOffsetMaker:
    '''A MappedPolygon with an offset applied.'''
    
    OFFSET_ROUND=OffsetType(m3d.JoinType.Round)
    OFFSET_MITER=OffsetType(m3d.JoinType.Miter)
    OFFSET_SQUARE=OffsetType(m3d.JoinType.Square)
    
    mapped_poly: MappedPolygon = dtfield(doc='The mapped polygon to offset.')
    offset_type: OffsetType = dtfield(OFFSET_ROUND, doc='The type of offset to apply.')
    miter_limit: float=dtfield(2, doc='The miter limit for the offset.')
    circular_segments: int=dtfield(
        None, 
        doc='The number of circular segments to use for the offset. meta_data.fn is used if None.')
    
    m3d_cs: m3d.CrossSection=dtfield(None, init=False, doc='The manifold3d cross section.')
    order_reversed: bool=dtfield(None, doc='If true the order of the points is reversed.')
    
    def __post_init__(self):
        if self.circular_segments is None:
            self.circular_segments = self.mapped_poly.meta_data.fn

    def offset_polygon(self, size: float):
        '''Returns an offset of the polygon.'''

        if self.m3d_cs is None:
            poly = [self.mapped_poly.cleaned()]
            
            assert len(poly) > 0, \
                f'Only one polygon is supported. {poly}'
            cs = m3d.CrossSection(poly)
            
            if cs.is_empty():
                # AnchorSCAD Paths may be incorrectly ordered. Manifold3D requires a correct order
                # otherise it will return an empty cross section since it is deemed to be a hole.
                # TODO: Fix AnchorSCAD to handle multiple paths correctly.
                cs = m3d.CrossSection([poly[0][::-1]])
                self.order_reversed = True
                assert not cs.is_empty(), f'Empty cross section should not happen.'
            else:
                self.order_reversed = False
            
            self.m3d_cs = cs
        
        # If the size is less than the epsilon then we return the original polygon
        # with the order corrected.
        if np.abs(size) < self.mapped_poly.epsilon / 2:
            return self.m3d_cs.to_polygons()[0]
        
        # This is where we call the manifold/clipper2 offset function.
        offsed_cs = self.m3d_cs.offset(
            size, 
            self.offset_type.offset_type, 
            miter_limit=self.miter_limit, 
            circular_segments=self.circular_segments)
        
        polys = offsed_cs.to_polygons()
        
        return polys[0]


def make_offset_polygon2d(path: Path, size: float, offset_type: OffsetType, 
                          meta_data: core.ModelAttributes, offset_meta_data: core.ModelAttributes=None):
    '''This is just a test to see if we can use the manifold3d library to do the offsetting.'''
    if not offset_meta_data:
        offset_meta_data = meta_data
 
    mapped_poly = MappedPolygon(path, meta_data)
        
    points = mapped_poly.cleaned();
    cs = m3d.CrossSection([points])
    
    offsed_cs = cs.offset(size, offset_type.offset_type, miter_limit=0.1, circular_segments=offset_meta_data.fn)
    
    return offsed_cs.to_polygons()[0]


@datatree
class ExtrudeLayerParams:
    '''Per layer extrusion parameters.'''
    a: tuple = dtfield(doc='The anchor specifier for this layer.')
    z: float = dtfield(doc='The z location of the layer.')
    twist: float = dtfield(doc='The twist of the layer in degrees.')
    scale: float = dtfield(doc='The scale of the layer in X and Y.')
    path: Path = dtfield(doc='The path of the layer. Note that there may be'
                         + 'a transformation applied to the path to get points.')
    polygon: List[List[float]] = dtfield(doc='The polygon of the layer.')

class ParamtericExtrusionIf:
    '''A supplier of Path and polygons for per layer extrusion.'''
    
    def get_layer_count(self) -> int:
        '''Returns the number of layers.'''
        raise NotImplementedError()
    
    def get_layer(self, i: int) -> Tuple[ExtrudeLayerParams, Path, List[List[float]]]:
        '''Returns the path for the given parameters.'''
        raise NotImplementedError()

class OffsetProfile:
    '''A Path builder for an offset profile.'''
    
    def build(self) -> Path:
        raise NotImplementedError("Override in subclass.")


@datatree
class BevelledProfile(OffsetProfile):
    '''Offset profile for bevelled extrusions.'''
    h: float = dtfield(1, doc='The overall height of extrusion.')
    r_base: float = dtfield(0, doc='The radius of the base bevel.')
    r_top: float = dtfield(0, doc='The radius of the top bevel.')
    slope_top: float = dtfield(0, doc='The slope of the top bevel in degrees.')
    slope_base: float = dtfield(30, doc='The base arc secant slope in degrees.')
    chamfer_top: float = dtfield(False, doc='The chamfer of the top bevel.')
    chamfer_base: float = dtfield(False, doc='The chamfer of the base bevel.')
    metadata: core.ModelAttributes = dtfield(None, doc='The metadata to use for the extrusions.')
    metadata_arcs: core.ModelAttributes = dtfield(None, doc='The metadata to use for the arcs.')
    
    def build(self) -> Path:
        if self.r_top < 0:
            raise ValueError(f'The top radius (r_top={self.r_top}) cannot be negative.')
        if self.r_base < 0:
            raise ValueError(f'The base radius (r_base={self.r_base}) cannot be negative.')
        straight_edge = self.h - self.r_base - self.r_top
        if straight_edge < 0:
            raise ValueError(f'The sum of the base and top (sum={self.r_top + self.r_base})'
                             + f'radius cannot be greater than the height (h={self.h}).')
        
        builder = PathBuilder()
        if self.r_base > 0:
            if self.chamfer_base:
                builder.move((-self.r_base, 0), name='base', direction=(-1, 1))
                builder.line((0, self.r_base), name='base_bevel', metadata=self.metadata)
            else:
                sinr = l.clean(np.sin(np.radians(self.slope_base)))
                cosr = l.clean(np.cos(np.radians(self.slope_base)))
                line_to = (-(1 - sinr) * self.r_base,
                           (1 - cosr) * self.r_base)
                if sinr == 0:
                    line_from = (-self.r_base, 0)
                    direction = (-1, 0)
                else:
                    line_from = (-(line_to[0] + line_to[1] * (cosr / sinr)), 0)
                    direction = (-(line_to[0] - line_from[0]), line_to[1] - line_from[1])
                direction = np.array(direction)
                builder.move(line_from, 'base', direction=direction)
                builder.line(line_to, 'base_bevel_line', metadata=self.metadata, 
                             direction_override=direction)
                builder.arc_tangent_point(
                    (0, self.r_base), name='base_bevel', direction=direction, metadata=self.metadata_arcs)
        
        builder.line((0, self.h - self.r_top), name='side', metadata=self.metadata)
        
        if self.r_top > 0:
            if self.chamfer_top:
                builder.line((-self.r_top, self.h), name='top_bevel', metadata=self.metadata)
            else:
                arc_to = (-(1 - np.sin(np.radians(self.slope_top))) * self.r_top,
                            self.h - (1 - np.cos(np.radians(self.slope_top))) * self.r_top)
                builder.arc_tangent_point(arc_to, name='top_bevel', metadata=self.metadata_arcs)
                builder.line((-self.r_top, self.h), 'top_bevel_line', metadata=self.metadata)
        
        return builder.build()
    
    
class PathGeneratorIf:
    
    def init_processor(self, metadata: core.ModelAttributes) -> 'ParamtericExtrusionProcessorIf':
        '''Generates a processor for the given metadata.'''
        raise NotImplementedError()
    
@datatree
class LayerData:
    '''Data for a layer.'''
    h: float=dtfield(doc='The height of the layer.')
    polygon: List[List[float]]=dtfield(doc='The polygon of the layer.')


class ParamtericExtrusionProcessorIf:
    def get_polygon(self, k: int) -> LayerData:
        '''Returns the polygon for the given index.'''
        raise NotImplementedError()
    
    def get_count(self) -> int:
        '''Returns the number of paths.'''
        raise NotImplementedError()
    
    def get_z_extents(self) -> Tuple[float, float]:
        '''Returns the z extents of the paths.'''
        raise NotImplementedError()
    
    def get_x_extents(self) -> Tuple[float, float]:
        '''Returns the x extents of the paths.'''
        raise NotImplementedError()


@datatree
class ParamtericExtrusionProcessorBasic(ParamtericExtrusionProcessorIf):
    
    parametric_extrusion: ParamtericExtrusionIf = dtfield(doc='The parametric extrusion.')
    
    metadata: core.ModelAttributes = dtfield(None, doc='The metadata to use for the extrusions.')
    
    mapped_poly: MappedPolygon = dtfield(self_default=lambda s: MappedPolygon(s.path, s.metadata))
    
    offset_type: OffsetType = dtfield(PathOffsetMaker.OFFSET_ROUND, doc='The type of offset to apply.')
    path_gen: PathOffsetMaker = dtfield(
        self_default=lambda s: PathOffsetMaker(mapped_poly=s.mapped_poly, offset_type=s.offset_type))
    
    #path: Path = dtfield(doc='The path to extrude.')
    
    
    
    def get_polygon(self, k: int) -> LayerData:
        '''Returns the polygon for the given index.'''
        
        
        
        return LayerData()

            
    def get_count(self) -> int:
        return len(self.points)
    
    def get_z_extents(self) -> Tuple[float, float]:
        '''Returns the z extents of the paths.'''
        raise NotImplementedError()
    
    def get_x_extents(self) -> Tuple[float, float]:
        '''Returns the x extents of the paths.'''
        raise NotImplementedError()
    
@datatree
class ParamtericExtrusionOffsetPath(ParamtericExtrusionIf):
    '''A basic flex extrusion implementation.'''
    
    bevel_profile: BevelledProfile = dtfield(doc='The bevel profile.')
    path_gen: PathGeneratorIf = dtfield(doc='The path generator.')
    twist_gen: Callable[[float], float] = dtfield(doc='The twist generator.')
    scale_gen: Callable[[float], Tuple[float, float]] = dtfield(doc='The scale generator.')
    points_gen: Callable[[float, List[List[float]]], List[List[float]]] = dtfield(doc='The points generator.')
    
    def init_processor(self, metadata: core.ModelAttributes) -> ParamtericExtrusionProcessorIf:
        return ParamtericExtrusionProcessorBasic(self, metadata)
    
    def get_layer_count(self) -> int:
        '''Returns the number of layers.'''
        raise NotImplementedError()
    
    def get_layer(self, i: int) -> Tuple[ExtrudeLayerParams, Path, List[List[float]]]:
        '''Returns the path for the given parameters.'''
        raise NotImplementedError()


@core.shape
@datatree
class BevelProfileShapeTest(core.CompositeShape):
    path_builder_node: core.Node = dtfield(
        core.ShapeNode(BevelledProfile),
        doc='The path builder for the extrusion profile.')
    path: Path = dtfield(self_default=lambda s: s.path_builder_node().build(), 
                         doc='The path to extrude.')
    extrude_node: core.Node = dtfield(
        core.ShapeNode(LinearExtrude))
    
    EXAMPLE_SHAPE_ARGS=core.args(
        h=100,
        r_top=10,
        r_base=20,
        slope_base=25,
        chamfer_top=False,
        chamfer_base=True,
        use_polyhedrons=False
        )
    
    def build(self) -> core.Maker:
        shape = self.extrude_node()
        maker = shape.solid('test').at()
        return maker

@datatree
class BevelProfilePolyhedronBuilderContext:
    builder: 'BevelProfilePolyhedronBuilder'
    metadata: core.ModelAttributes
    points: List[List[float]]

@datatree
class BevelProfilePolyhedronBuilder:
    '''A builds a polyhedron using a profile.'''
    
    bevel_path_builder_node: core.Node = dtfield(
        core.ShapeNode(BevelledProfile),
        doc='The path builder for the extrusion profile.')
    bevel_path: Path = dtfield(self_default=lambda s: s.path_builder_node().build(), 
                         doc='The path to extrude.')
    
    pbuilder: PolyhedronBuilder = dtfield(
        default_factory=PolyhedronBuilder, init=False, doc='The polyhedron builder.')
    
    def __post_init__(self):
        self.bevel_path = self.bevel_path_builder_node().build()

    def _get_polygon_for_layer(self, layer: int) -> List[List[float]]:
        pass
        

    def get_points_and_faces(self) -> Tuple[List[List[float]], List[List[int]]]:
        '''Returns the points and faces of the polyhedron.'''
        raise NotImplementedError()

#@core.shape
@datatree
class LinearFlexExtrude(ExtrudedShape):
    '''Generates a linear extrusion of a given Path.'''
    path: Path=dtfield(doc='The path to extrude.')
    h: float=dtfield(100, doc='The height of the extrusion.')
    twist: float=dtfield(0.0, doc='The twist of the extrusion in degrees.')
    slices: int=dtfield(4, doc='The number of slices to use for the extrusion if twist is applied.')
    scale: float=dtfield((1.0, 1.0), doc='The scale of the extrusion in X and Y.')
    fn: int=dtfield(None, doc='The number of facets to use for the extrusion.')
    use_polyhedrons: bool=dtfield(None, doc='If true will use polyhedrons to generate the extrusion.')
    
    _SCALE=2
    
    EXAMPLE_SHAPE_ARGS=core.args(
        PathBuilder()
            .move([0, 0])
            .line([100 * _SCALE, 0], 'linear')
            .spline([[150 * _SCALE, 100 * _SCALE], [20 * _SCALE, 100 * _SCALE]],
                     name='curve', cv_len=(0.5,0.4), angle=(90,), rel_len=0.8)
            .line([0, 100 * _SCALE], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
        h=80,
        fn=30,
        twist=45,
        slices=10,
        scale=(1, 0.3),
        use_polyhedrons=True
        )

    EXAMPLE_ANCHORS=(
                core.surface_args('edge', 'linear', 0.5),
                core.surface_args('linear2', 0.5, 10),
                core.surface_args('linear2', 0, 40),
                core.surface_args('linear2', 1, 40),
                core.surface_args('linear3', 0.5, 20, None, True, True),
                core.surface_args('curve', 0, 40),
                core.surface_args('curve', 0.1, rh=0.9),
                core.surface_args('curve', 0.2, 40),
                core.surface_args('curve', 0.3, 40),
                core.surface_args('curve', 0.4, 40),
                core.surface_args('curve', 0.5, 40, None, True, True),
                core.surface_args('curve', 0.6, 40, None, True, True),
                core.surface_args('curve', 0.7, 40, None, True, True),
                core.surface_args('curve', 0.8, 40, None, True, True),
                core.surface_args('curve', 0.9, 40, None, True, True),
                core.surface_args('curve', 1, 40, None, True, True),
                core.surface_args('linear2', 0.1, rh=0.9),
                core.surface_args('linear2', 0.5, 0.9, True, True),
                core.surface_args('linear2', 1.0, rh=0.9),
                )
        
    EXAMPLES_EXTENDED={
        'example2': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([0, 0])
                    .line([50 * _SCALE, 0], 'linear1')
                    .line([50 * _SCALE, 50 * _SCALE], 'linear2')
                    .line([0, 50 * _SCALE], 'linear3')
                    .line([0, 0], 'linear4')
                    .build(),
                h=50,
                ),
            anchors=(
                core.surface_args('linear1', 0, 0),
                core.surface_args('linear1', 0.5, 25 * _SCALE),
                core.surface_args('linear2', 0, 0),
                core.surface_args('linear2', 1, 0),
                )),
        'example3': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([0, 0])
                    .line([50 * _SCALE, 0], 'linear1')
                    .arc_tangent_point([0, 50 * _SCALE], name='curve', angle=90)
                    .line([0, 0], 'linear4')
                    .build(),
                h=50,
                fn=80,
                #slices=20,
                #twist=90,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0, 0),
                core.surface_args('linear1', 0.5, 25 * _SCALE),
                core.surface_args('curve', 0, 0),
                core.surface_args('curve', 0.6, 0),
                core.surface_args('curve', 1, 0),
                core.surface_args('curve', 0, 50),
                core.surface_args('curve', 0.6, 50),
                core.surface_args('curve', 1, 50),
                core.surface_args('linear4', 0, 0),
                core.surface_args('linear4', 1, 0),
                ))
        }

    def render(self, renderer):
        renderer.add_path(self.path)
        if self.use_polyhedrons or (self.use_polyhedrons is None and
            renderer.get_current_attributes().use_polyhedrons):
            return self.render_as_polyhedron(renderer)
        else:
            return self.render_as_linear_extrude(renderer)
        
    def get_path_attributes(self, renderer):
        metadata = renderer.get_current_attributes()
        if self.fn:
            metadata = metadata.with_fn(self.fn)
            
        if self.twist or self.scale != (1, 1):
            metadata = metadata.with_segment_lines(True)
        return metadata

    def render_as_linear_extrude(self, renderer):
        polygon = renderer.model.Polygon(*self.path.cleaned_polygons(
            self.get_path_attributes(renderer)))
        params = core.fill_params(
            self, 
            renderer, 
            ('fn',), 
            exclude=('path', 'use_polyhedrons'), 
            xlation_table={'h': 'height'})
        return renderer.add(renderer.model.linear_extrude(**params)(polygon))
    
    def generate_transforms(self):
        '''Generates a list of transforms for the given set of parameters.'''
        slices = self.slices if self.twist != 0 else 1
        sx = (self.scale[0] - 1) / slices
        sy = (self.scale[1] - 1) / slices
        rot = self.twist / slices
        return (l.IDENTITY,) + tuple(
            l.tranZ(self.h * i / slices) 
              * l.scale([1 + sx * i, 1 + sy * i, 1])
                * l.rotZ(-rot * i)
            for i in range(1, slices + 1))

    def render_as_polyhedron(self, renderer):
        points_paths = self.path.cleaned_polygons(
            self.get_path_attributes(renderer))
        builders = PolyhedronBuilder.create_builders_from_paths(points_paths)
        
        transforms = self.generate_transforms()
        for builder in builders:
            builder.make_two_ended(transforms)
            renderer.add(
                renderer.model.polyhedron(
                    points=builder.get_points_3d(),
                    faces=builder.faces))
        return renderer
    
    def _z_radians_scale_align(self, rel_h, twist_vector):
        xelipse_max = self.scale[0] * rel_h + (1 - rel_h)
        yelipse_max = self.scale[1] * rel_h + (1 - rel_h)
        eliplse_angle = np.arctan2(xelipse_max * twist_vector.y, yelipse_max * twist_vector.x)
        circle_angle = np.arctan2(twist_vector.y, twist_vector.x)
        return eliplse_angle - circle_angle
        
    
    @core.anchor('Anchor to the path edge and surface.')
    def edge(self, path_node_name, t=0, h=0, rh=None, align_twist=False, align_scale=False):
        '''Anchors to the edge and surface of the linear extrusion.
        Args:
            path_node_name: The path node name to attach to.
            t: 0 to 1 being the beginning and end of the segment. Numbers out of 0-1
               range will depart the path linearly.
            h: The absolute height of the anchor location.
            rh: The relative height (0-1).
            align_twist: Align the anchor for the twist factor.
        '''
        if not rh is None:
            h = h + rh * self.h
        op = self.path.name_map.get(path_node_name)
        if not op:
            raise UnknownOperationException(f'Could not find {path_node_name}')
        pos = self.to_3d_from_2d(op.position(t), h)
        normal_t = 0 if t < 0 else 1 if t > 1 else t 
        twist_vector = self.to_3d_from_2d(op.position(normal_t), 0)
        twist_radius = twist_vector.length()
        plane_dir = op.direction_normalized(normal_t)
        x_direction = self.to_3d_from_2d([plane_dir[0], -plane_dir[1]])
        z_direction = self.eval_z_vector(1)
        y_direction = z_direction.cross3D(x_direction)
        orientation = l.GMatrix.from_zyx_axis(x_direction, y_direction, z_direction) * l.rotX(90)
        
        # The twist angle is simply a rotation about Z depending on height.
        rel_h = h / self.h
        twist_angle = self.twist * rel_h
        twist_rot = l.rotZ(-twist_angle)
        
        twist_align = l.IDENTITY
        z_to_centre = l.IDENTITY
        if align_twist:
            # Aligning to the twist requires rotation about a axis perpendicular to the
            # axis of the twist (which is at (0, 0, h).
            z_to_centre = l.rot_to_V(twist_vector, [0, 0, 1])
            twist_align = l.rotZ(
                radians=np.arctan2(self.twist * np.pi / 180 * twist_radius , self.h))

        # The scale factors are for the x and y axii.
        scale = l.scale(
            tuple(self.scale[i] * rel_h + (1 - rel_h) for i in range(2)) + (1,))
        
        scale_zalign = l.IDENTITY
        scale_xalign = l.IDENTITY
        if align_scale:
            # Scaling adjustment along the Z plane is equivalent to a z rotation 
            # of the difference of the angle of a circle and the scaleg cirle.
            scale_zalign = l.rotY(radians=self._z_radians_scale_align(rel_h, twist_vector)) 
            
            scaled_vector = scale * twist_vector
            scale_xalign = l.rotZ(radians=-np.arctan2(
                twist_vector.length() - scaled_vector.length(), rel_h * self.h)) 
                      

        twisted = (twist_rot * l.translate(pos) * z_to_centre.I 
                   * twist_align * z_to_centre * orientation * scale_zalign * scale_xalign)
        
        
        result = scale * twisted 

        # Descaling the matrix so the co-ordinates don't skew.
        result = result.descale()
        return result
    
    @core.anchor('Centre of segment.')
    def centre_of(self, segment_name, rh=0) -> l.GMatrix:
        '''Returns a transformation to the centre of the given segment (arc) with the
        direction aligned to the coordinate system. The rh parameter is the 
        relative height (0-1) of the arc centre.'''

        centre_2d = self.path.get_centre_of(segment_name)
        if centre_2d is None:
            raise ValueError(f'Segment has no "centre" property: {segment_name}')
        
        return l.translate((centre_2d[0], centre_2d[1], rh * self.h)) * l.ROTY_180

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=core.ModuleDefault(all=True)

if __name__ == "__main__":
    core.anchorscad_main(False)
    
