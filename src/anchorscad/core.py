"""
Created on 5 Jan 2021

@author: gianni
"""

import argparse
import copy
from dataclasses import replace
import fnmatch
import inspect
import os
import pathlib
import re
import sys
import textwrap
import traceback

from frozendict import frozendict
from abc import abstractmethod

import anchorscad_lib.linear as l
from datatrees import Node, BoundNode, datatree, dtfield, METADATA_DOCS_NAME, get_injected_fields
from anchorscad_lib.utils.colours import Colour
from anchorscad.svg_renderer import HtmlRenderer
import numpy as np
import pythonopenscad as posc
from typing import Any, Hashable, Dict, List, Tuple, Union
import builtins


def _field_assign(obj, name, value):
    """Field assignment that works on frozen objects."""
    builtins.object.__setattr__(obj, name, value)


class CoreEception(Exception):
    """Base exception functionality"""

    def __init__(self, message):
        self.message = message


class DuplicateNameException(CoreEception):
    """Attempting to add a shape with a name that is already used."""


class UnimplementedRenderException(CoreEception):
    """Attempting to render from a class that has nor implemented render()."""


class IllegalParameterException(CoreEception):
    """Received an unexpected parameter."""


class AnchorSpecifierNotFoundException(CoreEception):
    """Requested anchor is not found."""


class IncorrectAnchorArgs(CoreEception):
    """Attempted to call an anchor and it failed."""


class InvalidNumberOfParametersException(CoreEception):
    """Number of parameters provided is incorrect."""


class InvalidParametersException(CoreEception):
    """Parameters provided were not recognised.."""


class IllegalStateException(CoreEception):
    """An operation was attempted where not permitted."""


class MustImplementBuild(CoreEception):
    """Must implement build() function returning a Maker."""


class ShapeNode(Node):
    """A datatree Node that by default preserves the names of the
    standard metadata variables (fn, fs and fa) and exposes them if available."""

    DEFAULT_PRESERVE_SET = {"fn", "fs", "fa"}
    DEFAULT_EXPOSE_IF_AVAIL = {"fn", "fs", "fa"}

    def __init__(self, *args, expose_if_avail=None, preserve=None, **kwds):
        expose_if_avail = (
            self.DEFAULT_EXPOSE_IF_AVAIL
            if expose_if_avail is None
            else self.DEFAULT_EXPOSE_IF_AVAIL.union(expose_if_avail)
        )

        preserve = (
            self.DEFAULT_PRESERVE_SET
            if preserve is None
            else self.DEFAULT_PRESERVE_SET.union(preserve)
        )

        super().__init__(*args, expose_if_avail=expose_if_avail, preserve=preserve, **kwds)


def args(*args, **kwds) -> Tuple[List[Any], Dict[str, Any]]:
    """Returns a tuple or args and kwds passed to this function."""
    return (args, frozendict(kwds))


def args_add(args_tuple: Tuple[List[Any], Dict[str, Any]], **kwds):
    """Returns a new args tuple with the kwds added."""
    return (args_tuple[0], frozendict({**args_tuple[1], **kwds}))


def apply_args(other_args, *args, **kwds):
    """Returns a tuple of args and kwds that is the combination of the
    args and kwds passed to this function and the args and kwds provided
    in other_args."""
    return (other_args[0] + args, {**kwds, **(other_args[1])})


def kwargs_chain_pre_post(kwargs, pre=None, post=None):
    """Returns a new kwargs with pre and post applied to the pre and post
    values in kwargs."""
    new_kwargs = None
    params = {"pre": pre, "post": post}
    for k, v in params.items():
        if v:
            new_kwargs = dict(kwargs) if new_kwargs is None else new_kwargs
            oldpost = kwargs.get(k, l.IDENTITY)
            kwargs[k] = oldpost * v
    return new_kwargs if new_kwargs else kwargs


def args_to_str(args):
    """Returns a string that represents the arguments passed into args()."""
    positional_bits = ", ".join(repr(v) for v in args[0])
    kwds_bits = ", ".join(f"{k}={v!r}" for k, v in args[1].items())
    return ", ".join((positional_bits, kwds_bits))


def surface_anchor_renderer(maker, anchor_args):
    """Helper to crate example anchor coordinates on surface of objects."""
    label = anchor_args.label
    xform = anchor_args.apply(maker)
    args_for_anchor = anchor_args.args_anchor
    if args_for_anchor:
        ac_args = args_for_anchor[0]
        ac_kwds = args_for_anchor[1]
    else:
        ac_args = ()
        ac_kwds = {}

    if label is not None:
        if not ac_kwds:
            ac_kwds = {"label": label}
        else:
            # If we have a label, but no label kwds, add it.
            if "label" not in ac_kwds:
                ac_kwds = dict(ac_kwds)
                ac_kwds["label"] = label
    maker.add_at(
        AnnotatedCoordinates(*ac_args, **ac_kwds)
        .solid(label)
        .material(COORDINATES_MATERIAL)
        .at("origin"),
        post=xform,
    )


def inner_anchor_renderer(maker, anchor_args):
    """Helper to crate example anchor coordinates inside an object."""
    xform = anchor_args.apply(maker)
    maker.add_at(
        AnnotatedCoordinates()
        .solid(args_to_str(anchor_args.args))
        .material(COORDINATES_MATERIAL)
        .at("origin"),
        post=xform,
    )


@datatree(frozen=True)
class AnchorArgs:
    args_: tuple = args()
    scale_anchor: object = None
    label_anchor: object = None
    args_anchor: object = None

    def apply(self, maker):
        result = apply_at_args(maker, *self.args_[1][0], **self.args_[1][1])
        if self.scale_anchor is not None:
            result = result * l.scale(self.scale_anchor)
        return result

    def rebase(self, *args):
        """Returns a new AnchorArgs with the provided args prefixing self's args."""
        newargs = (self.args_[0], (args + self.args_[1][0], self.args_[1][1]))
        return AnchorArgs(newargs, scale_anchor=self.scale_anchor)

    @property
    def name(self):
        return self.args_[1][0][0]

    @property
    def label(self):
        return self.label_anchor if self.label_anchor else args_to_str(self.args)

    @property
    def args(self):
        return self.args_[1]

    @property
    def pargs(self):
        return self.args_[1][0]

    @property
    def kwds(self):
        return self.args_[1][1]

    @property
    def func(self):
        return self.args_[0]


def surface_args(*args_, scale_anchor=None, label_anchor=None, args_anchor=args(), **kwds):
    """Defines an instance of an anchor example."""
    return AnchorArgs(
        (surface_anchor_renderer, (args_, kwds)),
        scale_anchor=scale_anchor,
        label_anchor=label_anchor,
        args_anchor=args_anchor,
    )


def inner_args(*args, scale_anchor=None, **kwds):
    """Defines an instance of an anchor example for anchors inside an object."""
    return AnchorArgs((inner_anchor_renderer, (args, kwds)), scale_anchor=scale_anchor)


def fn_field(fn=None):
    return dtfield(fn, "fixed number of segments. Overrides fa and fs")


def fa_field(fa=None):
    return dtfield(fa, "minimum angle (in degrees) of each segment")


def fs_field(fs=None):
    return dtfield(fs, "minimum length of each segment")


FN_FIELD = fn_field()
FS_FIELD = fs_field()
FA_FIELD = fa_field()

DEFAULT_PART_PRIORITY = 5.0
DEFAULT_MATERIAL_PRIORITY = 5.0


@datatree(frozen=True)
class MaterialKind:
    """The type of material. This is used to determine how to render the material.
    If the material is not for physical rendering but is used for support or region
    selection, then it is not physical."""

    physical: bool = dtfield(True, doc="Whether this intended to be a physical part of the model.")


PHYSICAL_MATERIAL_KIND = MaterialKind(physical=True)
NON_PHYSICAL_MATERIAL_KIND = MaterialKind(physical=False)


@datatree(frozen=True)
class Part:
    """A part of a model. Shapes of the same Part are rendered together as separate
    shapes and allows shapes of the same Part to be rendered as different files.
    """

    name: str = dtfield(doc="The name of the part")
    # A Part of higher priority is removed from Parts of lower priority.
    # Materials of the same priority will overlap if they are not mutually exclusive.
    priority: float = dtfield(
        DEFAULT_PART_PRIORITY,
        doc="The priority of the part. Higher priority parts are rendered first.",
    )

    def use_priority(self, other_part: "Part", priority_increment: float = 0.0) -> "Part":
        """Returns a new Part with the priority of this part and the name of other_part."""
        return Part(name=other_part.name, priority=self.priority + priority_increment)


DEFAULT_PART = Part("default", priority=DEFAULT_PART_PRIORITY)


@datatree(frozen=True)
class Material:
    """Applying a material will cause the coalesing on shapes that share the
    same material. This is useful for rendering the material specific component
    shapes of a with different models to allow them to be handled differently,
    like using a different material to render them."""

    name: str = dtfield(doc="The name of the material")
    # A material of higher priority is removed from materials of lower priority.
    # Materials of the same priority will overlap if they are not mutually exclusive.
    priority: float = dtfield(
        DEFAULT_MATERIAL_PRIORITY,
        doc="The priority of the material. Higher priority materials are rendered first.",
    )

    # The kind of material. This is used to determine how to render the material.
    kind: MaterialKind = dtfield(
        PHYSICAL_MATERIAL_KIND, hash=False, compare=False, doc="The type of material."
    )

    def priority_sort_key(self):
        return (self.kind.physical, self.priority)

    @classmethod
    def default_priority_sort_key(cls):
        return (PHYSICAL_MATERIAL_KIND.physical, DEFAULT_MATERIAL_PRIORITY)


def compare_material_priority(materials):
    """Returns a tuple of materials sorted by priority."""
    return tuple(sorted(materials, key=lambda m: m.priority, reverse=True))


# Matrial applied to example renders.
DEFAULT_EXAMPLE_MATERIAL = Material("default")

# Material applied to coordinates in example renders.
COORDINATES_MATERIAL = Material("anchor", kind=NON_PHYSICAL_MATERIAL_KIND)


# MaterialMap is used to map materials to other materials in order to provide
# a mechanism to reuse models with different materials and have materials mapped
# for different purposes.


class MaterialMap:
    """A map for materials to other materials.
    This can be used to map materials to other materials when rendering.
    """

    def map(self, material: Material, attributes: "ModelAttributes") -> Material:
        """(Deprecated, use map_material)
        Returns the mapped material for the given material."""
        return self._map_material(material, attributes)

    def _map_material(self, material: Material, attributes: "ModelAttributes") -> Material:
        """Returns the mapped material for the given material."""
        return material  # Default is no mapping.

    def _map_part(self, part: Part, attributes: "ModelAttributes") -> Part:
        """Returns the mapped part for the given part."""
        return part  # Default is no mapping.

    def _map_colour(self, colour: Colour, attributes: "ModelAttributes") -> Colour:
        """Returns the mapped colour for the given colour."""
        return colour  # Default is no mapping

    def map_attributes(self, attributes: "ModelAttributes") -> "ModelAttributes":
        """Returns a new ModelAttributes with various properties mapped.

        This method can be overridden to provide a single method to map any values in
        an interrelated way.

        For example, mapping colours to materials or parts to colours.
        """
        mapped_colour = self._map_colour(attributes.colour, attributes)
        mapped_material = self._map_material(attributes.material, attributes)
        map_part = self._map_part(attributes.part, attributes)
        return replace(attributes, colour=mapped_colour, material=mapped_material, part=map_part)


@datatree(frozen=True, provide_override_field=False)
class MaterialMapDefault(MaterialMap):
    """Sets the default material if unset."""

    material: Material

    def _map_material(self, material: Material, attributes: "ModelAttributes") -> Material:
        return material if material else self.material


@datatree(frozen=True, provide_override_field=False)
class MaterialMapDefaultPart(MaterialMap):
    """Sets the default material if unset."""

    part: Part

    def _map_part(self, part: Part, attributes: "ModelAttributes") -> Material:
        return part if part else self.part


@datatree(frozen=True, provide_override_field=False)
class MaterialMapBasic(MaterialMap):
    """Provides a set of basic mappings for materials."""

    map_dict: Dict[Material, Material]

    def _map_material(self, material: Material, attributes: "ModelAttributes") -> Material:
        return self.map_dict.get(material, material)


def create_material_map(*args):
    """Creates a material map from the arguments provided."""
    if not args:
        raise ValueError("No arguments provided.")

    if len(args) % 2 != 0:
        raise ValueError("Arguments must be in pairs.")
    # Combine pairs of args into tuples.
    entries = tuple(zip(args[0::2], args[1::2]))
    return MaterialMapBasic(frozendict(entries))


@datatree(frozen=True)
class MaterialMapStack(MaterialMap):
    """Combines a collection of material mappings."""

    map_stack: Tuple[MaterialMap]

    def map(self, material: Material, attributes: "ModelAttributes") -> Material:
        raise NotImplementedError("Use map_attributes")

    def _map_material(self, material: Material, attributes: "ModelAttributes") -> Material:
        raise NotImplementedError("Use map_attributes")

    def _map_part(self, part: Part, attributes: "ModelAttributes") -> Part:
        raise NotImplementedError("Use map_attributes")

    def _map_colour(self, colour: Colour, attributes: "ModelAttributes") -> Colour:
        raise NotImplementedError("Use map_attributes")

    def map_attributes(self, attributes: "ModelAttributes") -> "ModelAttributes":
        """Returns the mapped part, material and colour for the given part, material and colour.

        Applies the mappings in the order they are provided in the map_stack.
        """

        for mmap in self.map_stack:
            attributes = mmap.map_attributes(attributes)

        return attributes


@datatree(frozen=True)
class ModelAttributes(object):
    colour: Colour = dtfield(None, doc="Colour to be applied to this shape.")
    fa: float = dtfield(None, doc="$fa parameter for openscad - only for openscad rendered shapes.")
    fs: float = dtfield(None, doc="$fs parameter for openscad - only for openscad rendered shapes.")
    fn: int = dtfield(None, doc="Number of segements for arcs and splines for openscad shapes.")
    segment_lines: bool = dtfield(None, doc="Use fn, fs, fa to segment lines in extruded paths.")
    disable: bool = dtfield(None, doc="Flag to disable the shape.")
    show_only: bool = dtfield(None, doc="Flag to show only the shape.")
    debug: bool = dtfield(None, doc="Flag to enable debug mode.")
    transparent: bool = dtfield(None, doc="Flag to make the shape transparent.")
    use_polyhedrons: bool = dtfield(None, doc="Flag to use polyhedrons for the shape.")
    material: Material = dtfield(None, doc="Material to be applied to this shape.")
    material_map: MaterialMap = dtfield(None, doc="Material map for the shape.")
    part: Part = dtfield(None, doc="Part to be applied to this shape.")

    def _merge_of(self, attr, other) -> object:
        return getattr(other, attr) or getattr(self, attr)

    def _diff_of(self, attr: str, other: "ModelAttributes") -> object:
        self_value = getattr(self, attr)
        other_value = getattr(other, attr)
        if self_value == other_value:
            return None
        return other_value

    def merge(self, other: "ModelAttributes") -> "ModelAttributes":
        """Returns a copy of self with entries from other replacing self's."""
        if not other:
            return self

        return ModelAttributes(
            **dict((k, self._merge_of(k, other)) for k in self.__annotations__.keys())
        )

    def diff(self, other: "ModelAttributes") -> "ModelAttributes":
        """Returns a new ModelAttributes with the diff of self and other."""
        if not other:
            return self
        return ModelAttributes(
            **dict((k, self._diff_of(k, other)) for k in self.__annotations__.keys())
        )

    def is_empty(self) -> bool:
        """Returns True if all attributes are None."""
        return all(getattr(self, k) is None for k in self.__annotations__.keys())

    def _as_non_defaults_dict(self) -> Dict[str, object]:
        return dict(
            (k, getattr(self, k))
            for k in self.__annotations__.keys()
            if getattr(self, k) is not None
        )

    def _with(self, **kwds):
        return replace(self, **kwds)  # datatree replace

    def with_colour(self, *colour_args, **colour_kwds) -> "ModelAttributes":
        if len(colour_args) == 1 and len(colour_kwds) == 0:
            if isinstance(colour_args[0], Colour):
                return self._with(colour=colour_args[0])
        return self._with(
            colour=Colour(*colour_args, **colour_kwds) if colour_args or colour_kwds else None
        )

    def with_fa(self, fa: float) -> "ModelAttributes":
        return self._with(fa=fa)

    def with_fs(self, fs: float) -> "ModelAttributes":
        return self._with(fs=fs)

    def with_fn(self, fn: int) -> "ModelAttributes":
        return self._with(fn=fn)

    def with_segment_lines(self, segment_lines: bool) -> "ModelAttributes":
        return self._with(segment_lines=segment_lines)

    def with_disable(self, disable: bool) -> "ModelAttributes":
        return self._with(disable=disable)

    def with_show_only(self, show_only: bool) -> "ModelAttributes":
        return self._with(show_only=show_only)

    def with_debug(self, debug: bool) -> "ModelAttributes":
        return self._with(debug=debug)

    def with_transparent(self, transparent: bool) -> "ModelAttributes":
        return self._with(transparent=transparent)

    def with_use_polyhedrons(self, as_polyhedrons: bool) -> "ModelAttributes":
        return self._with(use_polyhedrons=as_polyhedrons)

    def with_material(self, material: Material) -> "ModelAttributes":
        return self._with(material=material)

    def with_material_map(self, material_map: MaterialMap) -> "ModelAttributes":
        if self.material_map:
            material_map = MaterialMapStack((self.material_map, material_map))
        return self._with(material_map=material_map)

    def with_part(self, part: Part) -> "ModelAttributes":
        return self._with(part=part)

    def fill_dict(self, out_dict, field_names=("fn", "fs", "fa")) -> Dict[str, object]:
        for field_name in field_names:
            if field_name in out_dict:
                continue
            value = getattr(self, field_name)
            if value is None:
                continue
            out_dict[field_name] = value
        return out_dict

    def to_str(self) -> str:
        """Generates a repr with just the non default values."""
        return (
            self.__class__.__name__
            + "("
            + ", ".join(f"{k}={v!r}" for k, v in self._as_non_defaults_dict().items())
            + ")"
        )

    def get_mapped_attributes(self):
        """Returns the material to use for this model level."""
        if self.material_map:
            return self.material_map.map_attributes(self)
        return self.material

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return self.to_str()


EMPTY_ATTRS = ModelAttributes()


@datatree(frozen=True)
class ShapeDescriptor:
    anchors: tuple


@datatree(frozen=True)
class ShapeFrame(object):
    name: Hashable
    shape: Hashable
    reference_frame: l.GMatrix
    attributes: ModelAttributes = None

    def inverted(self):
        return ShapeFrame(self.name, self.shape, self.reference_frame.I, self.attributes)

    def pre_mul(self, reference_frame):
        return ShapeFrame(
            self.name, self.shape, reference_frame * self.reference_frame, self.attributes
        )

    def post_mul(self, reference_frame):
        return ShapeFrame(
            self.name, self.shape, self.reference_frame * reference_frame, self.attributes
        )


def apply_post_pre(reference_frame, post: l.GMatrix = None, pre: l.GMatrix = None):
    """Optionally applies a pre and post matrix to the given reference_frame."""
    if pre:
        reference_frame = pre * reference_frame
    if post:
        reference_frame = reference_frame * post
    return reference_frame


def apply_at_args(
    shape, *pargs, pre=None, post=None, alter_pre=None, alter_post=None, descale=None, **kwds
):
    local_frame = shape.at(*pargs, **kwds) if pargs or kwds else l.IDENTITY
    if descale:
        local_frame = local_frame.descale()
    local_frame = apply_post_pre(local_frame, pre=pre, post=post)
    if alter_pre or alter_post:
        local_frame = apply_post_pre(local_frame, pre=alter_pre, post=alter_post)
    return local_frame


def apply_anchor_args(shape, anchor_args):
    return apply_at_args(shape, *anchor_args[1][0], **anchor_args[1][1])


def find_intersection(maker, plane_anchor, line_anchor):
    """Finds intersection of anchors on a maker.
    Args:
      maker: The Shape where anchors are found.
      plane_anchor: The anchor plane in surface_args() format.
      line_anchor: The anchor line in surface_args() format.
    Returns:
      A GMatrix representing the point of intersection or None if
      the line and plane don't intersect.
    """
    plane = plane_anchor.apply(maker)
    line = line_anchor.apply(maker)
    return l.plane_line_intersect(plane, line)


def find_all_intersect(maker, plane_anchor, *line_anchors):
    """Returns a tuple of GMatrix "points" marking the intersection of
    line_anchors and the plane_anchor.
    Args:
      maker: The Shape where anchors are found.
      plane_anchor: The anchor plane in surface_args() format.
      line_anchors: The args list of anchor line in surface_args() format.
    Returns:
      A tuple of results of intersections of the plane_anchor and the
      given line_anchots.
    """
    return tuple(find_intersection(maker, plane_anchor, la) for la in line_anchors)


@datatree(frozen=True)
class NamedShapeBase(object):
    shape: object  # Shape or Maker or LazyShape
    shape_type: Hashable
    name: Hashable
    attributes: ModelAttributes = None

    def _as_non_defaults_dict(self):
        return dict(
            (k, getattr(self, k))
            for k in self.__annotations__.keys()
            if getattr(self, k) is not None
        )

    def _with(self, **kwds):
        return replace(self, **kwds)  # datatree replace

    def with_attributes(self, attributes: ModelAttributes):
        return self.__class__(**self._with("attributes", attributes))

    def get_attributes_or_default(self):
        attributes = self.attributes
        if not attributes:
            attributes = EMPTY_ATTRS
        return attributes

    def colour(self, *colour_args, **colour_kwds):
        return self._with(
            attributes=self.get_attributes_or_default().with_colour(*colour_args, **colour_kwds)
        )

    def fa(self, fa: float):
        return self._with(attributes=self.get_attributes_or_default().with_fa(fa))

    def fs(self, fs: float):
        return self._with(attributes=self.get_attributes_or_default().with_fs(fs))

    def fn(self, fn: int):
        return self._with(attributes=self.get_attributes_or_default().with_fn(fn))

    def segment_lines(self, segment_lines: bool):
        return self._with(
            attributes=self.get_attributes_or_default().with_segment_lines(segment_lines)
        )

    def disable(self, disable: bool):
        return self._with(attributes=self.get_attributes_or_default().with_disable(disable))

    def show_only(self, show_only: bool):
        return self._with("attributes", self.get_attributes_or_default().with_show_only(show_only))

    def debug(self, debug: bool):
        return self._with(attributes=self.get_attributes_or_default().with_debug(debug))

    def transparent(self, transparent: bool):
        return self._with(attributes=self.get_attributes_or_default().with_transparent(transparent))

    def use_polyhedrons(self, as_polyhedrons: bool):
        return self._with(
            attributes=self.get_attributes_or_default().with_use_polyhedrons(as_polyhedrons)
        )

    def material(self, material: Material):
        return self._with(attributes=self.get_attributes_or_default().with_material(material))

    def material_map(self, material_map: MaterialMap):
        return self._with(
            attributes=self.get_attributes_or_default().with_material_map(material_map)
        )

    def part(self, part: Part):
        return self._with(attributes=self.get_attributes_or_default().with_part(part))


class NamedShape(NamedShapeBase):
    def at(
        self,
        *pargs,
        post: l.GMatrix = None,
        pre: l.GMatrix = None,
        args=None,
        anchor=None,
        descale=None,
        **kwds,
    ) -> l.GMatrix:
        """Creates a shape containing the nominated shape at the reference frame given.
        *args, **kwds: Parameters for the shape given. If none is provided then IDENTITY is used.
        pre: The pre multiplied transform.
        post: The post multiplied transform,
        """

        if (pargs or kwds) and (args or anchor) or (args and anchor):
            raise IllegalParameterException("Only one form of anchor parameters allowed.")

        alter_pre = None
        alter_post = None
        if anchor:
            args = anchor.args
        if args:
            pargs = args[0]
            kwds = dict(args[1])  # Copy the kwds since we're not allowed to mutate them.
            alter_pre = kwds.pop("pre", None)
            alter_post = kwds.pop("post", None)

        if not pargs and not kwds:
            reference_frame = l.IDENTITY
        else:
            reference_frame = self.shape.at(*pargs, **kwds)

        if descale:
            reference_frame = reference_frame.descale()

        reference_frame = apply_post_pre(reference_frame, pre=pre, post=post)
        if alter_pre or alter_post:
            reference_frame = apply_post_pre(reference_frame, pre=alter_pre, post=alter_post)

        return self.projection(reference_frame)

    def projection(self, reference_frame: l.GMatrix):
        return Maker(
            self.shape_type,
            ShapeFrame(self.name, self.shape, reference_frame),
            attributes=self.attributes,
        )


class ShapeNamer:
    @abstractmethod
    def named_shape(self, name, mode_shape_frame):
        assert False, "This method needs to be overridden in child classes."

    # Shape like functions.
    def solid(self, name) -> NamedShape:
        return self.named_shape(name, ModeShapeFrame.SOLID)

    def hole(self, name) -> NamedShape:
        return self.named_shape(name, ModeShapeFrame.HOLE)

    def cage(self, name) -> NamedShape:
        return self.named_shape(name, ModeShapeFrame.CAGE)

    def composite(self, name) -> NamedShape:
        return self.named_shape(name, ModeShapeFrame.COMPOSITE)

    def intersect(self, name) -> NamedShape:
        return self.named_shape(name, ModeShapeFrame.INTERSECT)

    def hull(self, name) -> NamedShape:
        return self.named_shape(name, ModeShapeFrame.HULL)

    def minkowski(self, name) -> NamedShape:
        return self.named_shape(name, ModeShapeFrame.MINKOWSKI)

    def by_index(self, name, index, *modes) -> NamedShape:
        """Select the shape mode by the index given over the provided modes."""
        if not index:
            index = 0
        return self.named_shape(name, modes[index])

    def solid_hole(self, name, is_hole) -> NamedShape:
        """Choose the mode as solid or hole determined by the is_hole parameter."""
        return self.by_index(name, is_hole, ModeShapeFrame.SOLID, ModeShapeFrame.HOLE)

    def solid_cage(self, name, is_cage) -> NamedShape:
        """Choose the mode as solid or cage determined by the is_cage parameter."""
        return self.by_index(name, is_cage, ModeShapeFrame.SOLID, ModeShapeFrame.CAGE)


class ShapeMaker:
    def as_maker(self, name, mode_shape_frame, reference_frame):
        assert False, "This method needs to be overridden in child classes."

    def as_solid(self, name, reference_frame):
        return self.as_maker(name, ModeShapeFrame.SOLID, reference_frame)

    def as_hole(self, name, reference_frame):
        return self.as_maker(name, ModeShapeFrame.HOLE, reference_frame)

    def as_cage(self, name, reference_frame):
        return self.as_maker(name, ModeShapeFrame.CAGE, reference_frame)

    def as_composite(self, name, reference_frame):
        return self.as_maker(name, ModeShapeFrame.COMPOSITE, reference_frame)

    def as_intersect(self, name, reference_frame):
        return self.as_maker(name, ModeShapeFrame.INTERSECT, reference_frame)

    def as_hull(self, name, reference_frame):
        return self.as_maker(name, ModeShapeFrame.HULL, reference_frame)

    def as_minkowski(self, name, reference_frame):
        return self.as_maker(name, ModeShapeFrame.MINKOWSKI, reference_frame)

    def by_index(self, name, index, *modes):
        """Select the shape mode by the index given over the provided modes."""
        if not index:
            index = 0
        return self.as_maker(name, modes[index])

    def as_solid_hole(self, name, is_hole):
        """Choose the mode as solid or hole determined by the is_hole parameter."""
        return self.by_index(name, is_hole, ModeShapeFrame.SOLID, ModeShapeFrame.HOLE)

    def as_solid_cage(self, name, is_cage):
        """Choose the mode as solid or cage determined by the is_cage parameter."""
        return self.by_index(name, is_cage, ModeShapeFrame.SOLID, ModeShapeFrame.CAGE)


class LazyNamedShape(NamedShapeBase):
    """Provides attributes but no transformation to a maker."""

    def to_named_shape(self, shape) -> NamedShape:
        values = self._as_non_defaults_dict()
        values["shape"] = shape
        return NamedShape(**values)


def mutable_copy(args):
    """Returns a copy of args that is mutable. In particular, instances of frozendict
    are converted to dict."""
    result = list(args)
    for i in range(len(result)):
        if isinstance(result[i], dict):
            t = {}
            for k, v in result[i].items():
                t[k] = copy.deepcopy(v)
            result[i] = t
        else:
            result[i] = copy.deepcopy(result[i])

    return result


@datatree(frozen=True)
class LazyShape(ShapeNamer):
    shape_type: type
    field_specifiers: tuple
    other_args: tuple

    def build(self, *params):
        if len(params) != len(self.field_specifiers):
            raise InvalidNumberOfParametersException(
                f"Received {len(params)} but expected {len(self.field_specifiers)}"
            )

        args = mutable_copy(self.other_args)
        for field_specifier, value in zip(self.field_specifiers, params):
            if isinstance(field_specifier, str):
                args[1][field_specifier] = value
            else:
                field_specifier(value, args)

        return self.shape_type(*args[0], **args[1])

    def named_shape(self, name, mode_shape_frame) -> LazyNamedShape:
        return LazyNamedShape(self, mode_shape_frame, name)


@datatree(frozen=True)
class AtSpecifier:
    """An 'at' specifier contains the args to call an Shape at() function. This allows
    lazy evaluation of a Shape a() call."""

    args_positional: tuple
    args_named: frozendict

    def apply(self, shape_obj):
        return apply_at_args(shape_obj, *self.args_positional, **self.args_named)


def at_spec(*args, **kwds):
    """Returns an AtSpecifier with the parameters sent to this function."""
    return AtSpecifier(args, kwds)


def add_between(
    source_maker,
    target_from,
    target_to,
    lazy_named_shape,
    shape_from,
    shape_to,
    shape_add_at=None,
    align_axis=None,
    align_plane=None,
    target_maker=None,
):
    """Creates a shape with the provided lazy_named_shape and the first parameter being
    the length of the vector between the frames resulting in evaluating the target_from and
    target_to. The shape's shape_from and shape_to AtSpecifiers are used as the align axis
    of the the created shape. If specified, shape_add_at will be used to provide the 'shape_from'
    actual location. Alignment of the axes perpendicular to the from-to axis can be done by
    providing the align_axis and align_plane parameters.
    Args:
        source_maker: The Shape (Maker) that provides the target frames.
        target_from: target_to: AtSpecifier for the from and to target frames.
        lazy_named_shape: The factory of a named shape given a distance.
        shape_from, shape_to: The frame (point only) that aligns with target frames.
        shape_add_at: The frame actually used to add the object (with the alignment
            computed from shape_from, shape_to alignment with target_from: target. if
            not provided shape_from is used (essentially IDENITY).
        align_axis, align_plane: The axis on the generated shape object that will be made
            co-planar with the target object's align_plane axis. i.e. The plane defined by
            the target object's align_plane normal vector.
    """

    # Get start and end points.
    from_frame = target_from.apply(source_maker)
    from_vec = from_frame.get_translation()
    to_vec = target_to.apply(source_maker).get_translation()

    # Need the diff vector to align to.
    diff_vector = from_vec - to_vec

    # The length allows us to build the shape now.
    length = diff_vector.length()
    shape_obj = lazy_named_shape.shape.build(length)

    # Get the new shape's alignment vector.
    shape_from_frame = shape_from.apply(shape_obj)
    shape_to_frame = shape_to.apply(shape_obj)

    # Get the frame of reference of the target point.
    shape_add_at_frame = shape_add_at.apply(shape_obj) if shape_add_at else shape_from_frame
    shape_add_at_frame_inv = shape_add_at_frame.I

    world_shape_to = shape_to_frame * shape_add_at_frame_inv
    world_shape_from = shape_from_frame * shape_add_at_frame_inv

    align_vec = world_shape_from.get_translation() - world_shape_to.get_translation()
    align_frame = l.rot_to_V(align_vec, diff_vector)

    # Axis alignment may be requested. The diff_vector will be the axis of rotation and the
    # alignment is made from the given model axis to the axis plane on the target anchor.
    if align_axis and align_plane:
        align_axis_vec = align_frame * align_axis
        align_plane_vec = from_frame.get_rotation() * align_plane
        axis_alignment = l.rotAlign(diff_vector, align_axis_vec, align_plane_vec)
        align_frame = axis_alignment * align_frame

    add_at_frame = l.translate(to_vec) * align_frame

    target_maker = target_maker if target_maker else source_maker

    named_shape = lazy_named_shape.to_named_shape(shape_obj)

    target_maker.add_at(named_shape.projection(shape_from_frame), pre=add_at_frame)

    return target_maker


def lazy_shape(shape_type, *field_specifiers, other_args=args()):
    """Returns a 'LazyShape', a factory for a shape. The parameters provided
    to the factory will be applied with 'other_args' to generate the final set
    of parameters to the Shape constructor.
    Args:
        shape_type: A Shape class or a factory function.
        field_specifiers: The field names what will be associated will be associated
        in the LazyShape.build() function.
        other_args: Other args passed to the shape_type constructor.
    """
    return LazyShape(shape_type, field_specifiers, other_args)


@datatree()
class ExampleParams:
    shape_args: tuple = args()
    anchors: tuple = ()
    base_anchor: AnchorArgs = surface_args()
    description: str = None

    def args_str(self):
        return f"(*{self.shape_args[0]!r}, **{self.shape_args[1]!r})"


class Shape(ShapeNamer, ShapeMaker):
    """The base "shape" class for Anchorscad."""

    EXAMPLE_VERSION = None
    EXAMPLE_ANCHORS = ()
    EXAMPLE_SHAPE_ARGS = args()
    EXAMPLES_EXTENDED = frozendict()

    def __init__(self):
        pass

    def copy_if_mutable(self):
        return self

    def named_shape(self, name, mode_shape_frame):
        "Overrides ShapeNamer.named_shape"
        return NamedShape(self.copy_if_mutable(), mode_shape_frame, name)

    def as_maker(self, name, mode_shape_frame, reference_frame):
        "Overrides ShapeNamer.as_maker"
        return Maker(mode_shape_frame, ShapeFrame(name, self.copy_if_mutable(), reference_frame))

    def has_anchor(self, name):
        return name in self.anchorscad.anchors

    def anchor_names(self):
        return tuple(self.anchorscad.anchors.keys())

    def at(self, *args, anchor=None, **kwds) -> l.GMatrix:
        if anchor and (args or kwds):
            raise IncorrectAnchorArgs(
                "Must not provide any other args when anchor parameter specified"
            )
        if anchor:
            return anchor.apply(self)

        anchor_name = args[0]
        args = args[1:]
        spec = self.anchorscad.get(anchor_name)
        if not spec:
            raise IncorrectAnchorArgs(
                f"Could not find {anchor_name!r} on {self.__class__.__name__}\n"
                f"Available names are {self.anchor_names()!r}"
            )

        func = spec[0]
        try:
            return func(self, *args, **kwds)
        except TypeError as e:
            raise IncorrectAnchorArgs(
                f"Attempted to call {anchor_name!r} on {self.__class__.__name__}"
                f" with args={args!r} kwds={kwds!r}"
            ) from e

    def name(self):
        return self.anchorscad.name

    def render(self, renderer):
        raise UnimplementedRenderException(f"Unimplemented render in {self.name()!r}.")

    @classmethod
    def examples(cls):
        """Returns a list of available examples."""
        non_str_keys = tuple(
            repr(s) for s in cls.get_extended_example_keys() if not isinstance(s, str)
        )
        assert not non_str_keys, (
            f'Shpae examples in "{cls.__name__}" contains non string keys: '
            f"{non_str_keys}. Recast these to strings."
        )
        assert "default" not in cls.get_extended_example_keys(), (
            f'Shpae examples in "{cls.__name__}" must not contain key "default".'
        )
        return ("default",) + tuple(cls.get_extended_example_keys())

    @classmethod
    def get_default_example_params(cls):
        return ExampleParams(cls.EXAMPLE_SHAPE_ARGS, cls.EXAMPLE_ANCHORS)

    def get_example_version(self):
        return self.EXAMPLE_VERSION

    @classmethod
    def get_extended_example_keys(cls):
        return cls.EXAMPLES_EXTENDED.keys()

    @classmethod
    def get_extended_example_params(cls, name):
        return cls.EXAMPLES_EXTENDED[name]

    @classmethod
    def example(cls, name="default"):
        if name == "default":
            example_params = cls.get_default_example_params()
        else:
            example_params = cls.get_extended_example_params(name)

        try:
            entryname = f"{cls.__name__}{example_params.args_str()}"  # noqa: F841
            shape = cls(*example_params.shape_args[0], **example_params.shape_args[1])
            projection = example_params.base_anchor.apply(shape)
            maker = shape.solid(name).material(DEFAULT_EXAMPLE_MATERIAL).projection(projection)

            for entry in example_params.anchors:
                entry.func(maker, entry)
        except BaseException:
            traceback.print_exception(*sys.exc_info(), limit=20)
            sys.stderr.write(f"Error while rendering example for {cls.__name__}:{name!r}, see:\n")
            sys.stderr.write(f'  File "{inspect.getsourcefile(cls)}", {cls.__name__}:{name!r}\n')
            raise

        return maker, shape

    def add_between(
        self,
        target_from,
        target_to,
        lazy_named_shape,
        shape_from,
        shape_to,
        shape_add_at=None,
        align_axis=l.X_AXIS,
        align_plane=l.X_AXIS,
        target_maker=None,
    ):
        """Builds a shape of type cls between two nominated anchors.
        Returns an AddBetween that allows the specification of the first and second
        anchors. The the length of the difference between he 2 anchors is optionally
        passed to the shape class constructor as a named parameter.
        Args:
            target_from: at_spec() of the from anchor parameters.
            target_to: at_spec() of the to anchor parameters.
            lazy_named_shape: a lazy_shape() with the parameters to create the shape.
            shape_from: at_spec() of the anchor to connect to target_from
            shape_to: at_spec() of the anchor to connect to target_to
            shape_add_at: at_spec() of an anchor point to offset the shape_from and shape_to
            align_axis: the shape axis to align to the align_plane in the shape frame of reference,
            align_plane: The plane to use for alignment of the align_axis in the target
                frame of reference.
        """
        return add_between(
            self,
            target_from,
            target_to,
            lazy_named_shape,
            shape_from,
            shape_to,
            shape_add_at=shape_add_at,
            align_axis=align_axis,
            align_plane=align_plane,
            target_maker=target_maker,
        )


@datatree(frozen=True)
class _Mode:
    mode: str
    has_operator_container: bool = False

    def make_container(self, model):
        return model.Union()


@datatree(frozen=True)
class SolidMode(_Mode):
    def __init__(self):
        super().__init__("solid")

    def pick_rendererx(self, renderer):
        return renderer.solid()


@datatree(frozen=True)
class HoleMode(_Mode):
    def __init__(self):
        super().__init__("hole")

    def pick_rendererx(self, renderer):
        return renderer.hole()


@datatree(frozen=True)
class CompositeMode(_Mode):
    def __init__(self):
        super().__init__("composite")

    def pick_rendererx(self, renderer):
        return renderer.hole()


@datatree(frozen=True)
class CageMode(_Mode):
    def __init__(self):
        super().__init__("cage")

    def pick_rendererx(self, renderer):
        return renderer.null()


@datatree(frozen=True)
class IntersectMode(_Mode):
    def __init__(self):
        super().__init__("intersect", True)

    def pick_rendererx(self, renderer):
        return renderer.intersect()

    def make_container(self, model):
        return model.Intersection()


@datatree(frozen=True)
class HullMode(_Mode):
    def __init__(self):
        super().__init__("hull", True)

    def pick_rendererx(self, renderer):
        return renderer.hull()

    def make_container(self, model):
        return model.Hull()


@datatree(frozen=True)
class MinkowskiMode(_Mode):
    def __init__(self):
        super().__init__("minkowski", True)

    def pick_rendererx(self, renderer):
        return renderer.minkowski()

    def make_container(self, model):
        return model.Minkowski()


class Renderer:
    POSC = posc

    def solid(self):
        pass

    def hole(self):
        pass

    def composite(self):
        pass

    def null(self):
        pass

    def intersect(self):
        pass

    def hull(self):
        pass

    def minkowski(self):
        pass


@datatree(frozen=True)
class ModeShapeFrame:
    SOLID = SolidMode()
    HOLE = HoleMode()
    CAGE = CageMode()
    COMPOSITE = CompositeMode()
    INTERSECT = IntersectMode()
    HULL = HullMode()
    MINKOWSKI = MinkowskiMode()

    mode: _Mode
    shapeframe: ShapeFrame
    attributes: ModelAttributes = None

    def inverted(self):
        return ModeShapeFrame(self.mode, self.shapeframe.inverted(), attributes=self.attributes)

    def pre_mul(self, reference_frame):
        return ModeShapeFrame(
            self.mode, self.shapeframe.pre_mul(reference_frame), attributes=self.attributes
        )

    def post_mul(self, reference_frame):
        return ModeShapeFrame(
            self.mode, self.shapeframe.post_mul(reference_frame), attributes=self.attributes
        )

    def reference_frame(self):
        return self.shapeframe.reference_frame

    def name(self):
        return self.shapeframe.name

    def shape(self):
        return self.shapeframe.shape

    def colour(self):
        return None if self.attributes is None else self.attributes.colour

    def to_str(self):
        parts = (repr(self.shape()), ".", self.mode.mode, "(", repr(self.name()))

        attr_parts = ()
        if self.attributes:
            attr_parts = (").attributes(", repr(self.attributes))
        projectopm_parts = (").projection(", repr(self.reference_frame()), ")")
        return "".join(parts + attr_parts + projectopm_parts)


@datatree(frozen=True)
class CageOfProperties:
    """Properties used by
    shape: Shape to be made a cage.
    name: The name to be applied to the shape.
    colour: The colour applied to the shape.
    """

    name: str = "cage"
    colour: object = (0.0, 1.0, 0.35, 0.4)

    def apply(self, shape, hide_cage, name=None):
        """Apply this object's properties to shape.
        Args:
              shape: Shape to be made a cage.
              hide_cage: If true, the shape will be treated as a cage and not rendered
                       If false, it will be rendered transparent with the given colour.
        """
        if isinstance(shape, BoundNode):
            shape = shape()
        if name is None:
            name = self.name
        if hide_cage:
            return shape.cage(name)
        return shape.solid(name).colour(self.colour).transparent(True)


def cageof(
    shape: Shape = None,
    hide_cage: bool = True,
    cage_name: object = None,
    properties: CageOfProperties = CageOfProperties(),
):
    """Conditionally returns either a cage mode or solid (but transparent)
    Maker. This can be used in a datatree Node and parameters will become
    encapsulated class fields. The default name is 'cage' from the
    properties parameter but can be overridden by a cage_name parameter.
    Args:
      shape: Shape to be made a cage.
      hide_cage: If true, the shape will be treated as a cage and not rendered
               If false, it will be rendered transparent with the given colour.
      cage_name: The name of the resulting Maker.
      properties: to be applied.
    """
    return properties.apply(shape, hide_cage, name=cage_name)


class CageOfNode(Node):
    def __init__(self, *args_, **kwds_):
        super().__init__(cageof, "hide_cage", *args_, **kwds_)


class AbsoluteReference:
    pass


ABSOLUTE = AbsoluteReference()


@datatree
class Maker(Shape):
    """The builder of composite shapes. Provides the ability to anchor shapes at various other
    frames (anchors) associated with Shapes already added.
    """

    reference_shape: ModeShapeFrame
    entries: Dict[Hashable, ModeShapeFrame]

    def __init__(self, mode=None, shape_frame=None, *, copy_of=None, attributes=None):
        if copy_of is None:
            self.reference_shape = ModeShapeFrame(mode, shape_frame, attributes=attributes)
            self.entries = {shape_frame.name: self.reference_shape.inverted()}
        else:
            if mode is None and shape_frame is None and attributes is None:
                self.reference_shape = copy_of.reference_shape
                self.entries = copy.copy(copy_of.entries)
            else:
                raise IllegalParameterException(
                    f"'copy_of' named parameter is provided and 'attributes', 'mode' or "
                    f"'shape_frame' parameters must not be provided but "
                    f"attributes={attributes!r}, mode={mode!r} and shape_frame={shape_frame!r}"
                )

    def copy_if_mutable(self) -> "Maker":
        return Maker(copy_of=self)

    def _add_mode_shape_frame(self, mode_shape_frame: ModeShapeFrame) -> "Maker":
        # Check for name collision.
        name = mode_shape_frame.shapeframe.name
        previous = self.entries.get(name, None)
        if previous:
            raise DuplicateNameException(
                "Attempted to add %r when it already exists in with mode %r"
                % (name, previous.mode.mode)
            )
        self.entries[name] = mode_shape_frame
        return self

    def add(self, maker: "Maker") -> "Maker":
        if not isinstance(maker, Maker):
            raise IllegalParameterException(
                f"Expected a parameter of type {self.__class__.__name__!r} but received an "
                f"object of type {maker.__class__.__name__!r}."
            )

        for entry in maker.entries.values():
            self._add_mode_shape_frame(entry)

        return self

    def add_at(
        self,
        maker: "Maker",
        *pargs,
        pre=None,
        post=None,
        args=None,
        anchor: AnchorArgs = None,
        **kwds,
    ) -> "Maker":
        """Adds another maker at the anchor of the provided parameters.
        If args is provided, this is a packed set of args from core.args.
        """
        if not isinstance(maker, Maker):
            raise IllegalParameterException(
                f"Expected a parameter of type {self.__class__.__name__!r} but received an "
                f"object of type {maker.__class__.__name__!r}."
            )

        if (pargs or kwds) and (args or anchor):
            raise IllegalParameterException(
                'Recieved positional args and kwds when parameter "args" or anchor is alsoprovided.'
            )
        if anchor:
            pargs = anchor.pargs
            kwds = anchor.kwds

        alter_pre = None
        alter_post = None
        if args:
            pargs = args[0]
            kwds = dict(args[1])
            alter_pre = kwds.pop("pre", None)
            alter_post = kwds.pop("post", None)

        local_frame = self.at(*pargs, **kwds) if pargs or kwds else l.IDENTITY
        local_frame = apply_post_pre(local_frame, pre=pre, post=post)
        if alter_pre or alter_post:
            local_frame = apply_post_pre(local_frame, pre=alter_pre, post=alter_post)

        for entry in maker.entries.values():
            self._add_mode_shape_frame(entry.pre_mul(local_frame))

        return self

    def add_shape(self, mode, shape_frame, attributes=None):
        return self._add_mode_shape_frame(ModeShapeFrame(mode, shape_frame.inverted(), attributes))

    def add_solid(self, shape_frame, attributes=None):
        return self.add_shape(ModeShapeFrame.SOLID, shape_frame, attributes)

    def add_hole(self, shape_frame, attributes=None):
        return self.add_shape(ModeShapeFrame.HOLE, shape_frame, attributes)

    def add_cage(self, shape_frame, attributes=None):
        return self.add_shape(ModeShapeFrame.CAGE, shape_frame, attributes)

    def add_intersect(self, shape_frame, attributes=None):
        return self.add_shape(ModeShapeFrame.INTERSECT, shape_frame, attributes)

    def add_hull(self, shape_frame, attributes=None):
        return self.add_shape(ModeShapeFrame.HULL, shape_frame, attributes)

    def add_minkowski(self, shape_frame, attributes=None):
        return self.add_shape(ModeShapeFrame.MINKOWSKI, shape_frame, attributes)

    def add_composite(self, shape_frame, attributes=None):
        return self.add_shape(ModeShapeFrame.COMPOSITE, shape_frame, attributes)

    def composite(self, name):
        return NamedShape(self.copy_if_mutable(), ModeShapeFrame.COMPOSITE, name)

    def as_composite(self, name, reference_frame, attributes):
        return Maker(
            ModeShapeFrame.COMPOSITE,
            ShapeFrame(name, self.copy_if_mutable(), reference_frame),
            attributes=attributes,
        )

    def has_anchor(self, name):
        ref_shape = self.reference_shape.shapeframe.shape
        if ref_shape.has_anchor(name):
            return True
        return name in self.entries

    def anchor_names(self):
        return self.reference_shape.shape().anchor_names() + tuple(self.entries.keys())

    def at(self, *args, anchor=None, **kwds) -> l.GMatrix:
        if anchor and (args or kwds):
            raise IncorrectAnchorArgs(
                "Must not provide any other args when anchor parameter specified"
            )
        if anchor:
            return anchor.apply(self)

        name = args[0]
        args = args[1:]
        shapeframe = self.reference_shape.shapeframe
        ref_shape = shapeframe.shape
        if isinstance(name, AbsoluteReference):
            # ABSOLUTE name is a path search modifier. It stops searching the
            # reference shape. Here we skip the ABSOLUTE name and continue with the
            # rest of the args.
            name = args[0]
            args = args[1:]
        elif ref_shape.has_anchor(name):
            entry = self.entries.get(self.reference_shape.name())
            return entry.reference_frame() * ref_shape.at(name, *args, **kwds)

        entry = self.entries.get(name)

        if entry is None:
            raise AnchorSpecifierNotFoundException(
                f"name={name!r} is not an anchor of the reference shape or a named shape. "
                f"Available names are {self.anchor_names()}."
            )

        return entry.reference_frame() * entry.shape().at(*args, **kwds)

    def name(self):
        return "Maker({name!r})".format(name=self.reference_shape.name())

    def to_str(self):
        parts = [self.reference_shape.to_str()]
        for entry in self.entries.values():
            if entry.name() == self.reference_shape.name():
                continue
            parts.append(f".add(\n    {entry.inverted().to_str()})")
        return "".join(parts)

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.to_str()

    def render(self, renderer):
        for v in self.entries.values():
            renderer.push(
                v.mode,
                v.reference_frame(),
                v.attributes,
                v.shapeframe.name,
                v.shapeframe.shape.__class__.__name__,
            )
            try:
                v.shape().render(renderer)
            finally:
                renderer.pop()


@datatree(frozen=True)
class AnchorSpec:
    """Associated with @anchor functions."""

    description: str


@datatree
class DeprecatedAnchorAnnouncer:
    """Announces deprecated anchor functions. This is used to provide a warning when
    deprecated anchors are used. The announcer can be silenced using the anchorscad_main()
    '--no_warn_deprecated_anchors_use' flag.

    Warnings are only issued once per anchor function called (per run).
    """

    announce_warning: bool = dtfield(
        False, doc="If true, a warning is issued when the anchor is used."
    )
    announcements: dict = dtfield(
        default_factory=dict, doc="A dictionary of anchor functions that have been announced."
    )

    def announce(self, fself, func):
        """Announces the deprecated anchor function. Only called when the anchor function is used and
        is deprecated."""
        if func in self.announcements:
            self.announcements[func] += 1
            return
        self.announcements[func] = 1
        if self.announce_warning:
            spec: AnchorSpec = func.__anchor_spec__
            print(
                f"WARNING: Deprecated anchor: {func.__qualname__}, class: {fself.__class__}, "
                f"package: {func.__module__}, "
                f"source: {func.__code__.co_filename}, "
                f"description: '{spec.description}",
                file=sys.stderr,
            )

    def warn_deprecated_anchors_use(self, announce_warning: bool):
        """Silences or enables the warning for deprecated anchor use."""
        self.announce_warning = announce_warning


DEPRECATED_ANCHOR_ANNOUNCER: DeprecatedAnchorAnnouncer = DeprecatedAnchorAnnouncer()


def anchor(description, deprecated=False):
    """Decorator for anchor functions."""

    def decorator(func):
        func.__anchor_spec__ = AnchorSpec(description)
        if deprecated:
            # Return a function that announces the deprecation.
            def anchor_func(fself, *args, **kwds):
                DEPRECATED_ANCHOR_ANNOUNCER.announce(fself, func)
                return func(fself, *args, **kwds)

            anchor_func.__anchor_spec__ = func.__anchor_spec__
            return anchor_func
        return func

    return decorator


# Converter for a list or iterable to a vector that defaults missing values to 1.
VECTOR3_FLOAT_DEFAULT_1 = l.list_of(np.float64, len_min_max=(3, 3), fill_to_min=np.float64(1))


@datatree(frozen=True)
class Anchors:
    name: str
    level: int
    anchors: frozendict

    def get(self, name):
        return self.anchors.get(name)


@datatree()
class AnchorsBuilder:
    """\
    name: is the shape class name to use
    """

    name: str
    level: int
    anchors: dict

    def __init__(self, name, level=10, anchors={}):
        self.name = name
        self.level = level
        self.anchors = dict(anchors)

    def add(self, name, func, anchor_spec):
        self.anchors[name] = (func, anchor_spec)

    def get(self, name):
        return self.anchors.get(name)

    def build(self):
        return Anchors(name=self.name, level=self.level, anchors=frozendict(self.anchors))


def _build_args_doc(clz, init_only=True):
    fields = getattr(clz, "__dataclass_fields__", None)
    if fields is None:
        return None, None
    with_docs = "\n".join(
        f"    {n}: {f.metadata[METADATA_DOCS_NAME].get_doc()}"
        for n, f in fields.items()
        if f.metadata and METADATA_DOCS_NAME in f.metadata and (not init_only or f.init)
    )

    wo_docs = ", ".join(
        f"{n}"
        for n, f in fields.items()
        if not (f.metadata and METADATA_DOCS_NAME in f.metadata) and (not init_only or f.init)
    )
    return with_docs, wo_docs


def shape(clazz_or_name=None, /, *, name=None, level=10):
    """Decorator for shape classes.
    This finds and registers all @anchor functions in the class.
    If level is provided, it is used as the selector for which shapes examples are
    built when runnin anchorscad_runner."""

    if isinstance(clazz_or_name, str):
        name = clazz_or_name
        clazz_or_name = None

    def decorator(clazz):
        """Actual decorator function for @shape."""
        builder = AnchorsBuilder(name, level)
        for func_name in dir(clazz):
            if func_name.startswith("__"):
                continue
            func = getattr(clazz, func_name)
            if not callable(func):
                continue
            if not hasattr(func, "__anchor_spec__"):
                continue
            builder.add(func_name, func, func.__anchor_spec__)
        clazz.anchorscad = builder.build()

        # Add field documentation.
        args_doc, args_no_doc = _build_args_doc(clazz)
        if args_doc:
            curr_doc = clazz.__doc__
            curr_doc = (curr_doc + "\n") if curr_doc else ""
            clazz.__doc__ = curr_doc + "Args:\n" + args_doc

        if args_no_doc:
            curr_doc = clazz.__doc__
            curr_doc = (curr_doc + "\n") if curr_doc else ""
            clazz.__doc__ = curr_doc + "Other args:\n    " + args_no_doc

        return clazz

    if clazz_or_name is None:
        return decorator

    return decorator(clazz_or_name)


@datatree
class FabricatorParams:
    level: float


def fabricator(clazz=None, /, *, level=10):
    """Decorator for fabricator classes.
    Fabricator classes are used to generate shapes that can be used as buildable
    shapes. They can be ready to slice projects and can be used to invoke
    OpenSCAD and slicers."""

    def wrap(clazz):
        clazz.anchorscad_fabricator = FabricatorParams(level)
        return clazz

    # See if we're being called as @datatree or @datatree().
    if clazz is None:
        # We're called with parens.
        return wrap

    # We're called as @datatree without parens.
    return wrap(clazz)


@shape
@datatree(frozen=True)
class Box(Shape):
    """Generates rectangular prisms (cubes where x=y=z).
    Anchor functions have a 'face' parameter which are 'front', 'back',
    'left', 'right', 'base' and 'top'. The 'front' face's plane is
    perpendicular with the y axis.
    """

    size: l.GVector = dtfield(doc="(x,y,z) size of Box")

    # Orientation of the 6 faces.
    ORIENTATION = (
        l.rotX(90),
        l.rotX(90) * l.rotX(90),
        l.rotX(90) * l.rotY(-90),
        l.rotX(90) * l.rotX(180),
        l.rotX(90) * l.rotX(-90),
        l.rotX(90) * l.rotY(90),
    )

    COORDINATES_CORNERS = (
        ((), (0,), (0, 2), (2,)),
        ((1,), (0, 1), (0,), ()),
        ((1,), (), (2,), (1, 2)),
        ((1, 2), (0, 1, 2), (0, 1), (1,)),
        ((2,), (0, 2), (0, 1, 2), (1, 2)),
        ((0,), (0, 1), (0, 1, 2), (0, 2)),
    )

    COORDINATES_EDGE_HALVES = tuple(
        tuple(
            [
                tuple([tuple(set(face[i]) ^ set(face[(i + 1) % 4])) for i in range(4)])
                for face in COORDINATES_CORNERS
            ]
        )
    )

    COORDINATES_CORNERS_ZEROS = tuple(
        tuple(
            [
                tuple([tuple(set((0, 1, 2)) - set(coords)) for coords in face])
                for face in COORDINATES_CORNERS
            ]
        )
    )

    COORDINATES_CENTRES_AXIS = tuple(
        tuple(set((0, 1, 2)) - set(face[0]) - set(face[2])) for face in COORDINATES_CORNERS[0:3]
    )

    EXAMPLE_ANCHORS = (
        tuple((surface_args("face_corner", f, c)) for f in ("front", "back") for c in range(4))
        + tuple(surface_args("face_edge", f, c) for f in (1, 3) for c in range(4))
        + tuple(
            surface_args("face_centre", f)
            for f in ("front", "back", "left", "right", "base", "top")
        )
        + (
            surface_args("face_edge", 2, 2, 0.1),
            surface_args("face_edge", "left", 2, -0.5),
            inner_args("centre"),
        )
    )
    EXAMPLE_SHAPE_ARGS = args([100, 120, 140])
    EXAMPLES_EXTENDED = {
        "one_face": ExampleParams(
            shape_args=args((100, 100, 100)),
            anchors=(
                surface_args("face_centre", "front"),
                surface_args("face_centre", "front", rh=-1),
                surface_args("face_corner", "front", 0),
                surface_args("face_corner", "front", 0, rh=-0.5),
                surface_args("face_edge", "front", 2),
                surface_args("face_edge", "front", 1, 0.15),
                surface_args("face_centre", "top"),
                surface_args("face_corner", "top", 0),
                surface_args("face_edge", "top", 2),
                surface_args("face_edge", "top", 2, rh=0.5),
                surface_args("face_edge", "top", 1, 0.15),
            ),
        )
    }

    FACE_MAP = frozendict(
        {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            "front": 0,
            "back": 3,
            "base": 1,
            "top": 4,
            "left": 2,
            "right": 5,
        }
    )

    def __init__(self, size=[1, 1, 1]):
        _field_assign(self, "size", l.GVector(VECTOR3_FLOAT_DEFAULT_1(size)))

    def render(self, renderer):
        renderer.add(renderer.model.Cube(self.size.A3))
        return renderer

    @anchor("Centre of box oriented same as face 0")
    def centre(self):
        return l.translate(l.GVector(self.size) / 2)

    @anchor("Corner of box given face (0-5) and corner (0-3)")
    def face_corner(self, face, corner, t=0, d=0, h: float = 0.0, rh: float = 0.0):
        return self.face_edge(face, corner, t=t, d=d, h=h, rh=rh)

    @anchor("Edge centre of box given face (0-5) and edge (0-3)")
    def face_edge(self, face, edge, t=0.5, d=0, h: float = 0.0, rh: float = 0.0):
        face = self.FACE_MAP[face]
        orientation = self.ORIENTATION[face] * l.rotZ(90 * edge)
        loc = l.GVector(self.size)  # make a copy.
        half_of = self.COORDINATES_EDGE_HALVES[face][edge]
        zero_of = self.COORDINATES_CORNERS_ZEROS[face][edge]
        keep_value = self.COORDINATES_CENTRES_AXIS[face % 3][0]
        for i in range(3):
            if i == keep_value:
                if face < 3:
                    loc[i] = 0.0
                h += self.size[i] * rh
            if i in half_of:
                if i in zero_of:
                    loc[i] = t * loc[i] + d
                else:
                    loc[i] = (1 - t) * loc[i] - d
            elif i in zero_of:
                loc[i] = 0.0
        return l.translate(loc) * orientation * l.tranZ(-h)

    @anchor("Centre of face given face (0-5)")
    def face_centre(self, face, h: float = 0.0, rh: float = 0.0):
        face = self.FACE_MAP[face]
        orientation = self.ORIENTATION[face]
        loc = l.GVector(self.size)  # make a copy.
        keep_value = self.COORDINATES_CENTRES_AXIS[face % 3][0]
        h: float = 0.0
        for i in range(3):
            if i == keep_value:
                if face < 3:
                    loc[i] = 0.0
                h += self.size[i] * rh
            else:
                loc[i] = loc[i] * 0.5
        return l.translate(loc) * orientation * l.tranZ(-h)


TEXT_DEPTH_MAP = {"centre": 0.5, "center": 0.5, "rear": 0.0, "front": 1.0}


def non_defaults_dict(dataclas_obj, include=None, exclude=()):
    if not (include is None or isinstance(include, tuple) or isinstance(include, dict)):
        raise IllegalParameterException(
            f"Expected parameter 'include' to be a tuple but is a {include.__class__.__name__}"
        )
    if not (exclude is None or isinstance(exclude, tuple) or isinstance(exclude, dict)):
        raise IllegalParameterException(
            f"Expected parameter 'exclude' to be a tuple but is a {exclude.__class__.__name__}"
        )
    return dict(
        (k, getattr(dataclas_obj, k))
        for k in dataclas_obj.__annotations__.keys()
        if (k not in exclude)
        and (include is None or k in include)
        and getattr(dataclas_obj, k) is not None
    )


def non_defaults_dict_include(dataclas_obj, include, exclude=()):
    if not (include is None or isinstance(include, tuple) or isinstance(include, dict)):
        raise IllegalParameterException(
            f"Expected parameter 'include' to be a tuple but is a {include.__class__.__name__}"
        )
    if not (exclude is None or isinstance(exclude, tuple) or isinstance(exclude, dict)):
        raise IllegalParameterException(
            f"Expected parameter 'exclude' to be a tuple but is a {exclude.__class__.__name__}"
        )
    return dict(
        (k, getattr(dataclas_obj, k))
        for k in include
        if (k not in exclude) and getattr(dataclas_obj, k) is not None
    )


ARGS_XLATION_TABLE = {"fn": "_fn", "fa": "_fa", "fs": "_fs"}
ARGS_REV_XLATION_TABLE = {"_fn": "fn", "_fa": "fa", "_fs": "fs"}


def translate_names(out_dict, xlation_table=ARGS_XLATION_TABLE):
    for old_name, new_name in xlation_table.items():
        if old_name in out_dict:
            out_dict[new_name] = out_dict[old_name]
            del out_dict[old_name]
    return out_dict


def fill_params(
    shape,
    renderer,
    attr_names,
    include=None,
    exclude=(),
    xlation_table=None,
    xlation_table2=ARGS_XLATION_TABLE,
):
    cur_attrs = renderer.get_current_attributes()
    params = cur_attrs.fill_dict(
        non_defaults_dict(shape, include=include, exclude=exclude), attr_names
    )
    if xlation_table:
        params = translate_names(params, xlation_table=xlation_table)
    if xlation_table2:
        params = translate_names(params, xlation_table=xlation_table2)
    return params


@shape
@datatree(frozen=True)
class Text(Shape):
    """Generates 3D text."""

    text: posc.str_strict = dtfield(None, "Text string to render.")
    size: float = dtfield(10.0, "Height of text")
    depth: float = dtfield(1.0, "Depth of text")
    font: posc.str_strict = dtfield(None, "Font name for rendering.")
    halign: posc.of_set("left", "center", "centre", "right") = dtfield(
        "left", "Horizontal alignment, left, center, centre or right"
    )
    valign: posc.of_set("top", "center", "centre", "baselinebottom") = dtfield(
        "bottom", "Vertical alignment. top, center, centre, baseline or bottom"
    )
    spacing: float = dtfield(1.0, "Character spacing.")
    direction: posc.of_set("ltr", "rtl", "ttb", "btt") = dtfield(
        "ltr", "Direction of rendering, ltr, rtl, ttb or btt"
    )
    language: posc.str_strict = dtfield(None, "Language being rendered.")
    script: posc.str_strict = dtfield(None, "Script being rendered.")
    fn: int = FN_FIELD
    fs: float = FS_FIELD
    fa: float = FA_FIELD
    text_node: Node = dtfield(
        default=Node(posc.Text, ARGS_REV_XLATION_TABLE, expose_all=True), init=False
    )
    offset_node: Node = dtfield(default=ShapeNode(posc.Offset, prefix="offset_"))

    EXAMPLE_ANCHORS = (surface_args("default", "rear"),)
    EXAMPLE_SHAPE_ARGS = args("Text Example", depth=5)
    EXAMPLES_EXTENDED = {
        "offset": ExampleParams(
            shape_args=args("Offset", depth=5, offset_delta=-0.3, font="Showcard Gothic", fn=64),
            anchors=(inner_args("default"),),
        )
    }

    def render(self, renderer):
        # Allow for proper spelling of centre.
        halign = "center" if self.halign == "centre" else self.halign
        valign = "center" if self.valign == "centre" else self.valign
        xlation: posc.Translate = renderer.model.Translate([0, 0, self.depth * -0.5])
        text_obj = self.text_node.call_with_alt_defaults(
            renderer.model.Text,
            halign=halign,
            valign=valign,
            alt_defaults=renderer.get_current_attributes(),
        )
        if self.offset_delta:
            offset = self.offset_node.call_with_alt_defaults(
                renderer.model.Offset,
                delta=self.offset_delta,
                alt_defaults=renderer.get_current_attributes(),
            )
            text_obj = offset(text_obj)
        extruded_text_obj = renderer.model.Linear_Extrude(self.depth)(xlation(text_obj))
        return renderer.add(extruded_text_obj)

    @anchor("The default position for this text. depth=(rear, centre, front)")
    def default(self, depth="centre", rd=None):
        if rd is None:
            rd = TEXT_DEPTH_MAP[depth]
        return l.translate([0, 0, self.depth * rd])


ANGLES_TYPE = l.list_of(l.angle, len_min_max=(3, 3), fill_to_min=0.0)


@shape
@datatree(frozen=True)
class Sphere(Shape):
    """Generates a Sphere."""

    r: float = dtfield(1.0, "Radius of sphere")
    fn: int = FN_FIELD
    fa: float = FA_FIELD
    fs: float = FS_FIELD

    EXAMPLE_ANCHORS = (
        surface_args("top"),
        surface_args("base"),
        inner_args("centre"),
        surface_args("surface", [90, 30, 45]),
        surface_args("surface", [-45, 0, 0]),
        surface_args("surface", [0, 0, 0]),
    )
    EXAMPLE_SHAPE_ARGS = args(20)

    def render(self, renderer):
        params = fill_params(self, renderer, ("fn", "fa", "fs"))
        params = translate_names(params)
        renderer.add(renderer.model.Sphere(**params))
        return renderer

    @anchor("The base of the shpere")
    def base(self, h=0, rh=None):
        if rh:
            h = h + rh * self.r
        return l.ROTX_180 * l.translate([0, 0, h + self.r])

    @anchor("The top of the shpere")
    def top(self, h=0, rh=None):
        if rh:
            h = h + rh * self.r
        return l.translate([0, 0, self.r - h])

    @anchor("The centre of the shpere")
    def centre(self, h=0, rh=None):
        if rh:
            h = h + rh * self.r
        return l.ROTX_180 * l.translate([0, 0, h])

    @anchor("A location on the sphere.")
    def surface(self, angles: tuple[l.Angle | float] = ANGLES_TYPE([0, 0, 0])):
        angles: tuple[l.Angle] = ANGLES_TYPE(angles)

        return (
            angles[2].rotY
            * angles[1].rotX
            * angles[0].rotZ
            * l.translate([self.r, 0, 0])
            * l.ROTV111_120
        )


CONE_ARGS_XLATION_TABLE = {"r_base": "r1", "r_top": "r2"}


@shape
@datatree(frozen=True)
class Cone(Shape):
    """Generates cones or horizontal conical slices and cylinders."""

    h: float = dtfield(1.0, "Height of cone")
    r_base: float = dtfield(1.0, "Base radius")
    r_top: float = dtfield(0.0, "Top radius")
    fn: int = FN_FIELD
    fa: float = FA_FIELD
    fs: float = FS_FIELD

    EXAMPLE_ANCHORS = (
        surface_args("base"),
        surface_args("top"),
        surface_args("surface", 20, 0),
        surface_args("surface", 10, l.angle(degrees=45)),
        surface_args("surface", 3, 90, tangent=False),
        inner_args("centre"),
    )
    EXAMPLE_SHAPE_ARGS = args(h=50, r_base=30, r_top=5, fn=30)

    def __post_init__(self):
        if self.h < 0:
            raise IllegalParameterException(f"Parameter h({self.h}) is less than 0.")
        if self.r_base < 0:
            raise IllegalParameterException(f"Parameter r_base({self.r_base}) is less than 0.")
        if self.r_top < 0:
            raise IllegalParameterException(f"Parameter r_top({self.r_top}) is less than 0.")

    def render(self, renderer):
        params = fill_params(self, renderer, ("fn", "fa", "fs"))
        params = translate_names(params, CONE_ARGS_XLATION_TABLE)
        params.pop("r", None)  # If self is a Cylinder, we don't want r.
        renderer.add(renderer.model.Cylinder(r=None, **params))
        return renderer

    @anchor("The base of the cone/cylinder.")
    def base(self, h=0, rh=None):
        if rh:
            h = h + rh * self.h
        transform = l.ROTX_180
        if not h:
            return transform
        return l.tranZ(h) * transform

    @anchor("The top of the cone/cylinder")
    def top(self, h=0, rh=None):
        if rh:
            h = h + rh * self.h
        return l.translate([0, 0, self.h - h])

    @anchor("The centre of the cone/cylinder")
    def centre(self):
        return l.translate([0, 0, self.h / 2]) * l.ROTX_180

    @anchor("A location on the curved surface.")
    def surface(
        self,
        h: float = 0,
        angle: l.Angle | float = 0.0,
        tangent: bool = True,
        rh=None,
        radius_delta=0.0,
    ):
        aangle = l.angle(angle)
        if h is None:
            h = 0.0
        if rh is not None:
            h = h + self.h * rh
        r = (h / self.h) if self.h else 0
        x = r * self.r_top + (1 - r) * self.r_base + radius_delta
        if tangent:
            m = l.rot_to_V([-1, 0, 0], [self.r_top - self.r_base, 0, self.h]) * l.ROTZ_90
        else:
            m = l.ROTV111_120
        return aangle.rotZ * l.translate([x, 0, h]) * m


@shape
@datatree(frozen=True)
class Cylinder(Cone):
    """Creates a Cone that has the same top and base radius.
    (i.e. a cylinder)."""

    h: float = dtfield(1.0, "Length of cylinder.")
    r: float = dtfield(1.0, "Radius of cylinder.")
    r_base: float = dtfield(self_default=lambda s: s.r, init=False)  # Hide this in the constructor.
    r_top: float = dtfield(self_default=lambda s: s.r, init=False)  # Hide this in the constructor.
    # The fields below should be marked kw only (Python 3.10 feature).
    fn: int = FN_FIELD
    fa: float = FA_FIELD
    fs: float = FS_FIELD

    EXAMPLE_SHAPE_ARGS = args(h=50, r=30, fn=30)


class CompositeShape(Shape):
    """Provides functionality for composite shapes. Subclasses must set 'maker' in
    the initialization of the class."""

    def render(self, renderer):
        return self.maker.render(renderer)

    def copy_if_mutable(self):
        result = copy.copy(self)
        result._set_maker(Maker(copy_of=self.maker))
        return result

    @anchor("Access to inner elements of this composite shape.")
    def within(self, *args, **kwds):
        return self.maker.at(*args, **kwds)

    def has_anchor(self, name):
        return name in self.anchorscad.anchors or self.maker.has_anchor(name)

    def anchor_names(self):
        return tuple(self.anchorscad.anchors.keys()) + self.maker.anchor_names()

    def at(self, anchor_name, *args, **kwds) -> l.GMatrix:
        spec = self.anchorscad.get(anchor_name)
        if spec:
            func = spec[0]
            try:
                return func(self, *args, **kwds)
            except TypeError as e:
                raise IncorrectAnchorArgs(
                    f"Attempted to call {anchor_name!r} on {self.__class__.__name__}"
                    f" with args={args!r} kwds={kwds!r}"
                ) from e
        if self.maker.has_anchor(anchor_name):
            return self.maker.at(anchor_name, *args, **kwds)
        else:
            raise IncorrectAnchorArgs(
                f"Could not find {anchor_name!r} on {self.__class__.__name__}\n"
                f"Available names are {self.anchor_names()!r}"
            )

    def _set_maker(self, maker):
        _field_assign(self, "maker", maker)

    def set_maker(self, maker):
        if hasattr(self, "maker"):
            raise IllegalStateException("Cannot set maker more than once.")
        self._set_maker(maker)

    def __post_init__(self):
        maker = self.build()
        assert maker is not None, "Function build() must return a Maker."
        self._set_maker(maker)

    def build(self) -> Maker:
        """build() must be overridden in derived classes."""
        raise MustImplementBuild(
            f"{self.__class__.__module__}.{self.__class__.__name__} "
            "must implement function build()."
        )


@shape
@datatree(frozen=True)
class Arrow(CompositeShape):
    """'arrow' shape with two end to end cones."""

    r_stem_top: float = 1.0
    r_stem_base: float = dtfield(self_default=lambda s: s.r_stem_top, init=True)
    l_stem: float = 6.0
    l_head: float = 3
    r_head_base: float = 2
    r_head_top: float = 0.0

    head_cone: Node = dtfield(
        default=ShapeNode(Cone, {"h": "l_head", "r_base": "r_head_base", "r_top": "r_head_top"})
    )
    stem_cone: Node = dtfield(
        default=ShapeNode(Cone, {"h": "l_stem", "r_base": "r_stem_base", "r_top": "r_stem_top"})
    )

    EXAMPLE_ANCHORS = (surface_args("base"), surface_args("top"), surface_args("stem", "top"))
    EXAMPLE_SHAPE_ARGS = args(
        r_stem_top=4, r_stem_base=6, l_stem=35, l_head=20, r_head_base=10, fn=30
    )

    def build(self) -> Maker:
        head = self.head_cone()
        stem = self.stem_cone()
        maker = stem.solid("stem").at("base")
        maker.add_at(head.solid("head").at("base", post=l.rotX(180)), "top")
        return maker

    @anchor("The base of the stem of the object")
    def base(self, *args, **kwds):
        return self.maker.at("stem", "base", *args, **kwds)

    @anchor("The top of the head")
    def top(self, *args, **kwds):
        return self.maker.at("head", "top", *args, **kwds)

    @anchor("Access to inner elements of this shape.")
    def within(self, *args, **kwds):
        return self.maker.at(*args, **kwds)


@shape
@datatree
class CoordinatesCage(Shape):
    """Provides anchor functions as a cage for the Coordinates shape."""

    base_frame: l.GMatrix = l.IDENTITY

    def render(self, renderer):
        return renderer

    @anchor("The untransformed origin.")
    def origin(self):
        return l.IDENTITY

    @anchor("x axis orientation")
    def x(self):
        return self.base_frame

    @anchor("y axis orientation")
    def y(self):
        return l.ROTV111_120 * self.base_frame

    @anchor("z axis orientation")
    def z(self):
        return l.ROTV111_240 * self.base_frame


@shape
@datatree(frozen=True)
class Coordinates(CompositeShape):
    overlap: float = 3.0
    colour_x: Colour = Colour("red")
    colour_y: Colour = Colour("green")
    colour_z: Colour = Colour("blue")
    hide_x: bool = False
    hide_y: bool = False
    hide_z: bool = True
    r_stem_top: float = 0.75
    r_stem_base: float = None  # Defaults to r_stem_top
    l_stem: float = 10.0
    l_head: float = 3
    r_head_base: float = 1.5
    r_head_top: float = 0.0
    arrow_node: Node = dtfield(init=False, default=ShapeNode(Arrow))

    def build(self) -> Maker:
        if self.r_stem_base is None:
            _field_assign(self, "r_stem_base", self.r_stem_top)
        arrow = self.arrow_node()
        maker = CoordinatesCage().cage("origin").at("origin")

        t = l.translate([0, 0, -self.overlap])

        maker.add_at(
            arrow.solid_cage("x_arrow", self.hide_x)
            .colour(self.colour_x)
            .at("base", pre=t * l.rotZ(180)),
            "x",
            pre=l.rotY(-90),
        )
        maker.add_at(
            arrow.solid_cage("y_arrow", self.hide_y)
            .colour(self.colour_y)
            .at("base", pre=t * l.rotZ(180)),
            "y",
            pre=l.rotZ(-90),
        )
        maker.add_at(
            arrow.solid_cage("z_arrow", self.hide_z)
            .colour(self.colour_z)
            .at("base", pre=t * l.rotZ(180)),
            "z",
            pre=l.rotX(-90),
        )
        return maker

    @anchor("The base of the stem of the object")
    def origin(self):
        return l.IDENTITY

    @anchor("Access to inner elements of this shape.")
    def within(self, *args, **kwds):
        return self.maker.at(*args, **kwds)


DEFAULT_ANNOTATED_LABELS = frozendict({"x": "x", "y": "y", "z": "z"})


@shape
@datatree(frozen=True)
class AnnotatedCoordinates(CompositeShape):
    coord_labels: frozendict = dtfield(default_factory=lambda: DEFAULT_ANNOTATED_LABELS)
    text_stem_size_ratio: float = 0.3
    coord_label_at: tuple = args(post=l.translate([0, 0, 1]) * l.rotY(-90))
    label: str = None
    label_pos_ratio: l.GVector = l.GVector([0.5, 0.5, 0.5])
    hide_x: bool = dtfield(self_default=lambda s: "x" not in s.coord_labels)
    hide_y: bool = dtfield(self_default=lambda s: "y" not in s.coord_labels)
    hide_z: bool = dtfield(self_default=lambda s: "z" not in s.coord_labels)
    coordinates_node: Coordinates = dtfield(init=False, default=ShapeNode(Coordinates))
    coordinates: Coordinates = dtfield(init=True, self_default=lambda s: s.coordinates_node())

    EXAMPLE_SHAPE_ARGS = args(label="This is label")

    EXAMPLES_EXTENDED = {
        "x_y_only": ExampleParams(
            shape_args=args(coord_labels=frozendict({"x": "x", "y": "y"})), anchors=()
        )
    }

    def build(self) -> Maker:
        coordinates = self.coordinates_node()
        maker = coordinates.solid("coords").at("origin")
        if self.coord_labels:
            for k, s in self.coord_labels.items():
                txt = Text(s, size=self.text_stem_size_ratio * coordinates.l_stem)
                maker.add_at(
                    txt.solid(k).at("default", "centre"),
                    "within",
                    f"{k}_arrow",
                    "top",
                    *self.coord_label_at[0],
                    **self.coord_label_at[1],
                )
        if self.label:
            txt = Text(
                self.label, halign="left", size=self.text_stem_size_ratio * coordinates.l_stem
            )
            xform = l.translate(
                [-10 * self.text_stem_size_ratio, -5 * -self.text_stem_size_ratio, 0]
            ) * l.rotZ(-45)
            maker.add(txt.solid("label").colour([0, 1, 0.5]).at("default", "centre", post=xform))

        return maker

    @anchor("The base of the stem of the object")
    def origin(self):
        return l.IDENTITY


def make_intersection_or_hole(
    as_hole,
    base_shape,
    base_anchor,
    other_shape,
    other_anchor,
    other_anchor_intersect=None,
    name="result",
):
    """Returns either an intersection or difference between two given shapes.
    Args:
        as_hole: returns a difference if True, intersection if False
        base_shape: the solid shape
        base_anchor: the reference anchor for base_shape
        base_shape: the shape being differenced or intersected
        base_anchor: the reference anchor for other_shape
        other_anchor_intersect: anchor to use for intersection
        name: the name applied to the resulting shape
    """

    maker = base_shape.solid("base").at(anchor=base_anchor)
    mode = ModeShapeFrame.HOLE if as_hole else ModeShapeFrame.SOLID
    other_anchor_in_use = other_anchor
    if other_anchor_intersect is not None and not as_hole:
        other_anchor_in_use = other_anchor_intersect
    maker.add_at(other_shape.named_shape("other", mode).at(anchor=other_anchor_in_use))
    final_mode = ModeShapeFrame.SOLID if as_hole else ModeShapeFrame.INTERSECT

    return maker.named_shape(name, final_mode).at()


def get_shape_class(module, name):
    mv = getattr(module, name)
    if not isinstance(mv, type):
        return False

    if not hasattr(mv, "anchorscad") or not hasattr(mv, "__module__"):
        return False

    if mv.__module__ != module.__name__:
        return False

    if mv.anchorscad.__class__.__name__ == "Anchors":
        return mv

    return False


def find_all_shape_classes(module):
    """Returns all the shape classes (those containing __anchorscad__) and returns
    a list.
    """
    shape_classes = []
    for name in dir(module):
        shape_class = get_shape_class(module, name)
        if shape_class:
            shape_classes.append(shape_class)
    return shape_classes


HASH_MODULO = int(1e8)


def _sanitize_name_single_name(s: Union[str, Tuple[str, ...]]) -> str:
    """Sanitizes a string to be a valid identifier."""
    # Replace contiguous whitespace and invalid characters with a single underscore.
    sanitized = re.sub(r"\s+|\W|^(?=\d)", "_", s)

    # Handle multiple invalid sections by appending hash to each invalid segment
    if not sanitized.isidentifier():
        segments = re.split(r"_+", sanitized)
        hashed_segments = [
            f"{seg}_{abs(hash(seg)) % HASH_MODULO}" if not seg.isidentifier() else seg
            for seg in segments
        ]
        sanitized = "_".join(hashed_segments)

    return sanitized


def sanitize_name(s: Union[str, Tuple[str, ...]]) -> str:
    """Sanitizes a string ot tuple of them to be a valid identifier."""
    if isinstance(s, tuple):
        return "_".join(_sanitize_name_single_name(name) for name in s)
    return _sanitize_name_single_name(s)


@datatree
class RenderOptions:
    render_attributes: ModelAttributes
    level: int
    class_name: tuple
    names_re: re.Pattern = None

    def __post_init__(self):
        if not self.class_name:
            self.class_name = ("*",)
        self.class_name_re = re.compile(
            "|".join(tuple("(?:" + fnmatch.translate(n) + ")" for n in self.class_name))
        )

    def match_name(self, cname):
        return self.class_name_re.match(cname)


def nameof(name, example_version):
    if example_version:
        return "".join((name, example_version))
    return name


def render_examples(
    module,
    render_options,
    consumer,
    graph_consumer,
    paths_consumer,
    injected_field_consumer,
    shape_consumer=None,
    start_example=None,
    end_example=None,
    parts_consumer=None,
):
    """Scans a module for all Anchorscad shape classes and renders examples."""
    classes = find_all_shape_classes(module)
    # Lazy import renderer since renderer depends on this.
    import anchorscad.renderer as renderer

    shape_count = 0
    example_count = 0
    error_count = 0
    parts_count = 0
    for clz in classes:
        if render_options.match_name(clz.__name__):
            shape_count += 1
            for e in clz.examples():
                example_count += 1
                if start_example:
                    start_example(clz, e)
                try:
                    maker, shape = clz.example(e)
                    name = nameof(e, shape.get_example_version())
                    result = renderer.render(
                        maker, initial_frame=None, initial_attrs=render_options.render_attributes
                    )

                    consumer(result.rendered_shape, clz, name, e)
                    graph_consumer(result.graph, clz, name, e)
                    paths_consumer(result.paths, clz, name, e)
                    injected_field_consumer(clz, name, e)
                    if shape_consumer:
                        shape_consumer(maker, shape, clz, name, e)

                    parts_count += len(result.parts)
                    if parts_consumer:
                        parts_consumer(result.parts, clz, name, e)
                except BaseException as ex:
                    error_count += 1
                    traceback.print_exception(*sys.exc_info(), limit=20)
                    sys.stderr.write(f"Error while rendering {clz.__name__} example:{e}:\n{ex}\n")
                    traceback.print_exception(*sys.exc_info())
                finally:
                    if end_example:
                        end_example(clz, e)
    return shape_count, example_count, error_count, parts_count


@datatree(provide_override_field=False)
class ModuleDefault:
    """Default anchorscad_main command line default values.

    Adding the following to an anchorscad_main module will result
    in the default to be --write instead of --no-write.

    MAIN_DEFAULT=ModuleDefault(True)

    If you want to change the default to provide all resources, you can
    set the all flag to True. e.g.

    MAIN_DEFAULT=ModuleDefault(all=1)

    If you want to set the default to provide all resources except for
    graph files, you can set the all flag to 2. e.g.

    MAIN_DEFAULT=ModuleDefault(all=2, write_graph_files=False)

    Similarly, write_graph_files and write_graph_svg_files apply
    as well.
    """

    write_files: bool = dtfield(None, "Writes OpendSCAD models to files.")
    write_graph_files: bool = dtfield(
        None, "Produces a graph of shape_names in .dot GraphViz format."
    )
    write_graph_svg_files: bool = dtfield(
        None, "Produces a graph of shape_names in .dot and .svg formats."
    )
    write_path_files: bool = dtfield(
        None, "Produces an html file containg 2D paths if any are used."
    )
    write_injection_files: bool = dtfield(
        None, "Produces an html file containg datatree injected field mappings."
    )
    write_part_files: bool = dtfield(None, "Writes OpenSCAD models for parts to files.")
    all: int = dtfield(
        0,
        "If set to 1, set all options to true. "
        "If set to 2, set all options to true if not otherwise set.",
    )

    def __post_init__(self):
        for f in self.__dataclass_fields__:
            if f == "all":
                continue
            if self.all == 1:
                setattr(self, f, True)
            elif getattr(self, f) is None:
                setattr(self, f, self.all == 2)

    def apply(self, obj):
        """Apply the default values to obj."""
        for f in self.__dataclass_fields__:
            if f == "all":
                continue
            curval = getattr(obj, f)
            if curval is None:
                setattr(obj, f, getattr(self, f))


class ArgumentParserWithReconstruct(argparse.ArgumentParser):
    """Like Python's argparse.ArgumentParser but also able to
    reconstruct a set of command line params from the argp
    values."""

    MISSING_VALUE = object()

    @datatree
    class ParameterDef:
        dest: str
        option_strings: str = None
        actions: dict = dtfield(default_factory=dict)
        param_args: tuple = dtfield(default=None, init=False)

        def get_value(self, name):
            if name in self.param_args[1]:
                return self.param_args[1][name]
            return ArgumentParserWithReconstruct.MISSING_VALUE

        def get_default(self):
            return self.get_value("default")

        def get_nargs(self):
            return self.get_value("nargs")

    def reconstruct(self, argp, overrides=Node):
        """Returns an argv for the current argp."""
        parameter_defs = getattr(self, "parameter_defs", {})

        post_result = []
        result = []
        for pdef in parameter_defs.values():
            aval = getattr(argp, pdef.dest, None)
            if overrides and pdef.dest in overrides:
                aval = overrides[pdef.dest]
            if aval is None:
                continue

            if pdef.actions:
                if aval:
                    if "store_true" in pdef.actions:
                        param_args = pdef.actions["store_true"]
                        result.append(param_args[0][0])
                else:
                    if "store_false" in pdef.actions:
                        param_args = pdef.actions["store_false"]
                        result.append(param_args[0][0])
            else:
                if pdef.get_default() is aval:
                    continue
                nargs = pdef.get_nargs()
                if nargs is self.MISSING_VALUE or nargs == 1:
                    result.append(pdef.param_args[0][0])
                    result.append(str(aval))
                if nargs in ["*", "+", "..."]:
                    arg_name = pdef.param_args[0][0]
                    if arg_name[0] in self.prefix_chars:
                        post_result.append(arg_name)
                    post_result.extend(str(a) for a in aval)

        return tuple(result + post_result)

    def get_parameter_defs(self):
        parameter_defs = getattr(self, "parameter_defs", None)
        if not parameter_defs:
            parameter_defs = {}
            self.parameter_defs = parameter_defs
        return parameter_defs

    def get_parameter_def(self, dest):
        parameter_defs = self.get_parameter_defs()
        result = parameter_defs.get(dest, None)
        if result is None:
            result = self.ParameterDef(dest)
            parameter_defs[dest] = result
        return result

    def add_argument(self, *args, **kwds):
        """Overrides ArgumentParser's function of the same name."""
        if "dest" in kwds:
            dest = kwds["dest"]
        else:
            dest = args[0].strip(self.prefix_chars)

        parameter_def = self.get_parameter_def(dest)
        if "action" in kwds:
            action = kwds["action"]
            parameter_def.actions[action] = (args, kwds)
        else:
            parameter_def.param_args = (args, kwds)

        return argparse.ArgumentParser.add_argument(self, *args, **kwds)


class ExampleCommandLineRenderer:
    """Command line parser and runner for invoking the renderer on examples."""

    DESCRIPTION = """\
    Renders Anchorscad examples their respective scad files.
    
    Example opensacd scad files also render anchors so that it's useful to visualise
    both the location and the orientation of the anchor.
    """

    EXAMPLE_USAGE = """\
    To render the Arrow shape in the core anchorscad example shapes. This will generate 
    an opensacd (.scad) file for all the selected shape classes in the Anchorscad.core 
    module.
    
        python3 -m Anchorscad.core --no-write --class_name Arrow 
        
    """

    def __init__(self, args, do_exit_on_completion=None):
        self.counts = (0,) * 3
        self.args = args
        argq = ArgumentParserWithReconstruct(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=self.DESCRIPTION,
            epilog=textwrap.dedent(self.EXAMPLE_USAGE),
        )

        self.argq = argq
        self.add_base_args()
        self.add_more_args()
        if do_exit_on_completion is None:
            self.do_exit_on_completion = (not hasattr(sys, "ps1")) or sys.flags.interactive
        else:
            self.do_exit_on_completion = do_exit_on_completion
        self.parse()

    def add_base_args(self):
        self.argq.add_argument(
            "--no-write",
            dest="write_files",
            action="store_false",
            help="Perform a test run. It will not make changes to file system.",
        )

        self.argq.add_argument(
            "--write", dest="write_files", action="store_true", help="Writes models to files."
        )
        self.argq.set_defaults(write_files=None)

        self.argq.add_argument(
            "--no-write-parts",
            dest="write_part_files",
            action="store_false",
            help="Perform a test run. It will not make changes to file system.",
        )

        self.argq.add_argument(
            "--write-parts",
            dest="write_part_files",
            action="store_true",
            help="Writes models for sub-parts to files.",
        )
        self.argq.set_defaults(write_part_files=None)

        self.argq.add_argument(
            "--no-graph_write",
            dest="write_graph_files",
            action="store_false",
            help="Produces a graph of shape_names in .dot GraphViz format.",
        )

        self.argq.add_argument(
            "--graph_write",
            dest="write_graph_files",
            action="store_true",
            help="Produces a graph of shape_names in .dot GraphViz format.",
        )
        self.argq.set_defaults(write_graph_files=None)

        self.argq.add_argument(
            "--no-svg_write",
            dest="write_graph_svg_files",
            action="store_false",
            help="Produces a graph of shape_names in .dot and .svg formats.",
        )

        self.argq.add_argument(
            "--svg_write",
            dest="write_graph_svg_files",
            action="store_true",
            help="Produces a graph of shape_names in .dot and .svg formats.",
        )
        self.argq.set_defaults(write_graph_svg_files=None)

        self.argq.add_argument(
            "--out_file_name",
            type=str,
            default=os.path.join("examples_out", "anchorcad_{class_name}_{example}_example.scad"),
            help="The OpenSCAD formatted output filename.",
        )

        self.argq.add_argument(
            "--part_out_file_name",
            type=str,
            default=os.path.join(
                "examples_out", "anchorcad_{class_name}_{example}_{part}_example.scad"
            ),
            help="The OpenSCAD formatted output filename for multi part models.",
        )

        self.argq.add_argument(
            "--graph_file_name",
            type=str,
            default=os.path.join("examples_out", "anchorcad_{class_name}_{example}_example.dot"),
            help="The GraphViz shape_name graph output filename.",
        )

        self.argq.add_argument(
            "--no_write_path_files",
            dest="write_path_files",
            action="store_false",
            help="No creation of html files containg 2D paths if any are used.",
        )

        self.argq.add_argument(
            "--write_path_files",
            dest="write_path_files",
            action="store_true",
            help="Produces an html file containg 2D paths if any are used.",
        )
        self.argq.set_defaults(write_path_files=None)

        self.argq.add_argument(
            "--no_write_injection_files",
            dest="write_injection_files",
            action="store_false",
            help="Produces an html file containg datatree injection mapping.",
        )

        self.argq.add_argument(
            "--write_injection_files",
            dest="write_injection_files",
            action="store_true",
            help="Produces an html file containg datatree injection mapping.",
        )
        self.argq.set_defaults(write_injection_files=None)

        self.argq.add_argument(
            "--paths_file_name",
            type=str,
            default=os.path.join(
                "examples_out", "anchorcad_{class_name}_{example}_example.paths.html"
            ),
            help="File name for the 2D paths rendered in html.",
        )

        self.argq.add_argument(
            "--injected_fields_file_name",
            type=str,
            default=os.path.join(
                "examples_out", "anchorcad_{class_name}_{example}_example.injected_fields.html"
            ),
            help="File name for the mapping of datatree injected fields.",
        )

        self.argq.add_argument(
            "--level",
            type=int,
            default=10,
            help=(
                "The 'level' at or above of the shape classes to render. "
                "Shape classes with a lower level than this are excluded unless "
                "they are specifically named."
            ),
        )

        self.argq.add_argument(
            "--class_name",
            type=str,
            default="*",
            nargs="*",
            help="The name/s of the shape classes to render.",
        )

        self.argq.add_argument(
            "--warn_deprecated_anchors_use",
            dest="warn_deprecated_anchors_use",
            action="store_true",
            help="Turn on warnings of deprecated anchor usage.",
        )
        self.argq.set_defaults(warn_deprecated_anchors_use=False)

        self.argq.add_argument(
            "--no_warn_deprecated_anchors_use",
            dest="warn_deprecated_anchors_use",
            action="store_false",
            help="Turn off warning of deprecated anchor usage.",
        )

    def add_more_args(self):
        self.argq.add_argument(
            "--module", type=str, default=None, help="The python module to be loaded."
        )

        self.argq.add_argument(
            "--list_shapes", action="store_true", default=False, help=("List Shape class names.")
        )

    def parse(self):
        self.argp, argv = self.argq.parse_known_args(self.args)
        if argv:
            self.status = 1
            raise InvalidParametersException(f"Parameters provided were not parsed: {str(argv)}")
        DEPRECATED_ANCHOR_ANNOUNCER.warn_deprecated_anchors_use(
            self.argp.warn_deprecated_anchors_use
        )
        default_attributes = ModelAttributes(material=DEFAULT_EXAMPLE_MATERIAL)
        self.options = RenderOptions(
            render_attributes=default_attributes,
            level=self.argp.level,
            class_name=self.argp.class_name,
        )
        self.set_mkdir = set()
        self.counts = (0, 0)
        self.status = 1

    def reconstruct(self, **kwds):
        return self.argq.reconstruct(self.argp, overrides=kwds)

    def _load_anchorcad_module(self, module):
        if module:
            globalsd = {}
            localsd = {}
            exec(f"import {module} as _m", globalsd, localsd)
            self.module = localsd.get("_m")
            self.module_name = module
        else:
            self.module = sys.modules["__main__"]
            self.module_name = ""

        if hasattr(self.module, "MAIN_DEFAULT"):
            main_default = self.module.MAIN_DEFAULT
            main_default.apply(self.argp)

    def file_writer(self, obj, clz, example_name, base_example_name):
        fname = self.argp.out_file_name.format(class_name=clz.__name__, example=example_name)
        path = pathlib.Path(fname)
        if self.argp.write_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            obj.write(path)
        else:
            if path.parent not in self.set_mkdir and not path.parent.exists():
                self.set_mkdir.add(path.parent)
                sys.stderr.write(f'directory "{path.parent}" does not exist. Will be created.\n')
            strv = obj.dumps()
            sys.stdout.write(f"Shape: {clz.__name__} {example_name} {len(strv)}\n")

    def parts_writer(self, parts: Dict[str, Any], clz, example_name, base_example_name):
        if self.argp.write_part_files:
            for part_name, obj in parts.items():
                part_name_sanitized = "part-" + sanitize_name(part_name)
                fname = self.argp.part_out_file_name.format(
                    class_name=clz.__name__, example=example_name, part=part_name_sanitized
                )
                path = pathlib.Path(fname)
                path.parent.mkdir(parents=True, exist_ok=True)
                obj.write(path)
        else:
            if len(parts) == 1 and "default" in parts:
                return  # No need to print out stats on default part shapes.
            for part_name, obj in parts.items():
                part_name_sanitized = sanitize_name(part_name)
                fname = self.argp.part_out_file_name.format(
                    class_name=clz.__name__, example=example_name, part=part_name_sanitized
                )
                path = pathlib.Path(fname)
                parent = path.parent
                if parent in self.set_mkdir and not path.parent.exists():
                    self.set_mkdir.add(parent)
                    sys.stderr.write(
                        f'directory "{parent}" does not exist. Will be created if --write-part requested.\n'
                    )
                strv = obj.dumps()
                sys.stdout.write(
                    f"Shape: {clz.__name__} {example_name} part:{part_name} {len(strv)}\n"
                )

    def graph_file_writer(self, graph, clz, example_name, base_example_name):
        fname = self.argp.graph_file_name.format(class_name=clz.__name__, example=example_name)
        path = pathlib.Path(fname)
        if self.argp.write_graph_files or self.argp.write_graph_svg_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            if self.argp.write_graph_svg_files:
                graph.write_svg(path, example_name)
            else:
                graph.write(path, example_name)
        else:
            if path.parent not in self.set_mkdir and not path.parent.exists():
                self.set_mkdir.add(path.parent)
                sys.stderr.write(f'directory "{path.parent}" does not exist. Will be created.\n')
            strv = repr(graph)
            sys.stdout.write(f"Shape graph: {clz.__name__} {example_name} {len(strv)}\n")

    def path_file_writer(self, paths_dict, clz, example_name, base_example_name):
        """Render all the paths used in the shape to an html file."""
        if not paths_dict or len(paths_dict.paths) == 0:
            return  # No paths to render, get out quickly.

        fname = self.argp.paths_file_name.format(class_name=clz.__name__, example=example_name)
        html_renderer = HtmlRenderer(paths_dict.paths)
        path = pathlib.Path(fname)
        if self.argp.write_path_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            html_renderer.write(path, example_name)
        else:
            if path.parent not in self.set_mkdir and not path.parent.exists():
                self.set_mkdir.add(path.parent)
                sys.stderr.write(f'directory "{path.parent}" does not exist. Will be created.\n')
            strv = html_renderer.create_html(example_name)
            sys.stdout.write(f"Paths html render: {clz.__name__} {example_name} {len(strv)}\n")

    def injected_file_writer(self, clz, example_name, base_example_name):
        """Create an html file containing the injected field mappings."""
        fname = self.argp.injected_fields_file_name.format(
            class_name=clz.__name__, example=example_name
        )

        injectedFields = get_injected_fields(clz)
        if not injectedFields:
            return

        html_str = injectedFields.generate_html_page(lambda x: str(x))

        path = pathlib.Path(fname)
        if self.argp.write_path_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(html_str)
        else:
            if path.parent not in self.set_mkdir and not path.parent.exists():
                self.set_mkdir.add(path.parent)
                sys.stderr.write(f'directory "{path.parent}" does not exist. Will be created.\n')
            sys.stdout.write(
                f"Injected fields render: {clz.__name__} {example_name} {len(html_str)}\n"
            )

    def invoke_render_examples(self):
        self.counts = render_examples(
            self.module,
            self.options,
            self.file_writer,
            self.graph_file_writer,
            self.path_file_writer,
            self.injected_file_writer,
            parts_consumer=self.parts_writer,
        )

    def list_shapes(self):
        classes = find_all_shape_classes(self.module)
        for clz in classes:
            print(clz.__name__)

    def run_module(self):
        if self.argp.list_shapes:
            self.list_shapes()
        else:
            self.invoke_render_examples()

        sys.stderr.write(
            f"shapes: {self.counts[0]}\n"
            f"examples: {self.counts[1]}\n"
            f"errors: {self.counts[2]}\n"
            f"parts: {self.counts[3]}\n"
        )

    def fix_status(self):
        if self.status:
            return
        if self.counts[2]:
            self.status = 1

    def run(self):
        """Renders the example shapes on the Shape classes found in the specified module.
        Note that by default, run() will exit the process.
        """
        self.status = 0
        try:
            self._load_anchorcad_module(self.argp.module)
            if not self.argp.write_files:
                sys.stderr.write("Anchorscad example renderer running in (--no-write) mode.\n")

            self.run_module()

        except BaseException as ex:
            if self.do_exit_on_completion:
                sys.stderr.write(f"{str(ex)}\nAnchorscad example renderer exiting with errors.")
                self.status = 3
                traceback.print_exception(*sys.exc_info(), limit=20)
            raise
        finally:
            self.fix_status()
            if self.do_exit_on_completion:
                sys.exit(self.status)


def anchorscad_main(do_exit_on_completion=None):
    """Executes the standard command line runner for Anchorscad modules.

    To use this function it is reccommended to place the following 2 lines at the end of the module.
        if __name__ == "__main__":
            Anchorscad.anchorscad_main()

    """
    clr = ExampleCommandLineRenderer(sys.argv[1:], do_exit_on_completion)
    clr.run()
    return clr.status


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT = ModuleDefault(all=True)

if __name__ == "__main__":
    anchorscad_main()
