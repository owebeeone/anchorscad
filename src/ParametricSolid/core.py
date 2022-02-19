'''
Created on 5 Jan 2021

@author: gianni
'''

import argparse
import builtins
import copy
from dataclasses import dataclass, field
import fnmatch
import inspect
import os
import pathlib
import re
import sys
import textwrap
import traceback

from frozendict import frozendict

from ParametricSolid import linear as l
from ParametricSolid.datatree import Node, BoundNode
import numpy as np
import pythonopenscad as posc


class CoreEception(Exception):
    '''Base exception functionality'''
    def __init__(self, message):
        self.message = message

class DuplicateNameException(CoreEception):
    '''Attempting to add a shape with a name that is already used.'''

class UnimplementedRenderException(CoreEception):
    '''Attempting to render from a class that has nor implemented render().'''

class IllegalParameterException(CoreEception):
    '''Received an unexpected parameter.'''   

class AnchorSpecifierNotFoundException(CoreEception):
    '''Requested anchor is not found.'''
    
class IncorrectAnchorArgs(CoreEception):
    '''Attempted to call an anchor and it failed.'''

class InvalidNumberOfParametersException(CoreEception):
    '''Number of parameters provided is incorrect.'''
    
class IllegalStateException(CoreEception):
    '''An operation was attempted where not permitted.'''


class ShapeNode(Node):
    '''A datatree Node that by default preserves the names of the
    standard metadata variables (fn, fs and fa) and exposes them if available.'''
    DEFAULT_PRESERVE_SET={'fn', 'fs', 'fa'}
    DEFAULT_EXPOSE_IF_AVAIL={'fn', 'fs', 'fa'}
    
    def __init__(self, *args, expose_if_avail=None, preserve=None, **kwds):
        
        expose_if_avail = (self.DEFAULT_EXPOSE_IF_AVAIL
                           if expose_if_avail is None 
                           else self.DEFAULT_EXPOSE_IF_AVAIL.union(expose_if_avail))
        
        preserve = (self.DEFAULT_PRESERVE_SET
                           if preserve is None 
                           else self.DEFAULT_PRESERVE_SET.union(preserve))
        
        super().__init__(*args, 
                         expose_if_avail=expose_if_avail, 
                         preserve=preserve, 
                         **kwds)

def args(*args, **kwds):
    '''Returns a tuple or args and kwds passed to this function.'''
    return (args, kwds)

def kwargs_chain_pre_post(kwargs, pre=None, post=None):
    new_kwargs = None
    params = {'pre': pre, 'post': post}
    for k, v in params.items():
        if v:
            new_kwargs = dict(kwargs) if new_kwargs is None else new_kwargs
            oldpost = kwargs.get(k, l.IDENTITY)
            kwargs[k] = oldpost * v
    return new_kwargs if new_kwargs else kwargs

def args_to_str(args):
    '''Returns a string that represents the arguments passed into args().'''
    positional_bits = ', '.join(repr(v) for v in args[0])
    kwds_bits = ', '.join(f'{k}={v!r}' for k, v in args[1].items())
    return ', '.join((positional_bits, kwds_bits))

def surface_anchor_renderer(maker, anchor_args):
    '''Helper to crate example anchor coordinates on surface of objects.'''
    label = args_to_str(anchor_args.args)
    xform = anchor_args.apply(maker)
    maker.add_at(
        AnnotatedCoordinates(label=label)
            .solid(label).at('origin'), post=xform)

def inner_anchor_renderer(maker, anchor_args):
    '''Helper to crate example anchor coordinates inside an object.'''
    xform = anchor_args.apply(maker)
    maker.add_at(
        AnnotatedCoordinates().solid(args_to_str(anchor_args.args)).at('origin'),
                 post=xform)


@dataclass(frozen=True)
class AnchorArgs():
    args_: tuple=args()
    scale_anchor: object=None
    
    def apply(self, maker):
        result = apply_at_args(
            maker, *self.args_[1][0], **self.args_[1][1])
        if not self.scale_anchor is None:
            result = result * l.scale(self.scale_anchor)
        return result
        
    @property
    def name(self):
        return self.args_[1][0][0]
        
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


def surface_args(*args_, scale_anchor=None, **kwds):
    '''Defines an instance of an anchor example.'''
    return AnchorArgs((surface_anchor_renderer, (args_, kwds)),
                      scale_anchor=scale_anchor)

def inner_args(*args, **kwds):
    '''Defines an instance of an anchor example for anchors inside an object.'''
    return AnchorArgs((inner_anchor_renderer, (args, kwds)))

@dataclass(frozen=True)
class Colour(object):
    value: tuple
    
    def __init__(self, value):
        value = value.value if isinstance(value, Colour) else value
        object.__setattr__(
            self, 'value', tuple(posc.VECTOR3OR4_FLOAT(value)))


@dataclass(frozen=True)
class ModelAttributes(object):
    colour: Colour = None
    fa: float = None
    fs: float = None
    fn: int = None
    disable: bool = None
    show_only: bool = None
    debug: bool = None
    transparent: bool = None
    use_polyhedrons: bool = None
    
    def _merge_of(self, attr, other):
        self_value = getattr(self, attr)
        other_value = getattr(other, attr)
        if self_value == other_value:
            return self_value;
        if other_value == None:
            return self_value
        return other_value
    
    def _diff_of(self, attr, other):
        self_value = getattr(self, attr)
        other_value = getattr(other, attr)
        if self_value == other_value:
            return None
        return other_value

    def merge(self, other):
        '''Returns a copy of self with entries from other replacing self's.'''
        if not other:
            return self
        
        return ModelAttributes(**dict(
            (k, self._merge_of(k, other)) 
            for k in self.__annotations__.keys()))
    
    def diff(self, other):
        '''Returns a new ModelAttributes with the diff of self and other.'''
        if not other:
            return self
        return ModelAttributes(**dict(
            (k, self._diff_of(k, other)) 
            for k in self.__annotations__.keys()))

    
    def _as_non_defaults_dict(self):
        return dict((k, getattr(self, k)) 
                    for k in self.__annotations__.keys() if not getattr(self, k) is None)
    
    def _with(self, fname, value):
        d = self._as_non_defaults_dict()
        d[fname] = value
        return ModelAttributes(**d)
    
    def with_colour(self, colour):
        return self._with('colour', None if colour is None else Colour(colour))
    
    def with_fa(self, fa):
        return self._with('fa', fa)
    
    def with_fs(self, fs):
        return self._with('fs', fs)
    
    def with_fn(self, fn):
        return self._with('fn', fn)
    
    def with_disable(self, disable):
        return self._with('disable', disable)
    
    def with_show_only(self, show_only):
        return self._with('show_only', show_only)
    
    def with_debug(self, debug):
        return self._with('debug', debug)
    
    def with_transparent(self, transparent):
        return self._with('transparent', transparent)
    
    def with_use_polyhedrons(self, as_polyhedrons):
        return self._with('use_polyhedrons', as_polyhedrons)
    
    def fill_dict(self, out_dict, field_names=('fn', 'fs', 'fa')):
        for field_name in field_names:
            if field_name in out_dict:
                continue
            value = getattr(self, field_name)
            if value is None:
                continue
            out_dict[field_name] = value
        return out_dict
    
    def to_str(self):
        '''Generates a repr with just the non default values.'''
        return self.__class__.__name__ + '(' + ', '.join(
            f'{k}={v!r}' for k, v in self._as_non_defaults_dict().items()) + ')'
            
    def __str__(self):
        return self.to_str()
    
    def __repr__(self):
        return self.to_str()
    
    
EMPTY_ATTRS = ModelAttributes()

@dataclass(frozen=True)
class ShapeDescriptor:
    anchors: tuple

@dataclass(frozen=True)
class ShapeFrame(object):
    name: object  # Hashable
    shape: object  # Shape or Maker
    reference_frame: l.GMatrix
    attributes: ModelAttributes = None

    def inverted(self):
        return ShapeFrame(self.name, self.shape, self.reference_frame.I, self.attributes)
    
    def pre_mul(self, reference_frame):
        return ShapeFrame(
            self.name, self.shape, reference_frame * self.reference_frame, self.attributes)
        
    def post_mul(self, reference_frame):
        return ShapeFrame(
            self.name, self.shape, self.reference_frame * reference_frame, self.attributes)


def apply_post_pre(reference_frame, post: l.GMatrix=None, pre: l.GMatrix=None):
    '''Optionally applies a pre and post matrix to the given reference_frame.'''
    if pre:
        reference_frame = pre * reference_frame
    if post:
        reference_frame = reference_frame * post
    return reference_frame

def apply_at_args(
        shape, *pargs, 
        pre=None, post=None, alter_pre=None, alter_post=None, **kwds):
    local_frame = shape.at(*pargs, **kwds) if pargs or kwds else l.IDENTITY
    local_frame = apply_post_pre(local_frame, pre=pre, post=post)
    if alter_pre or alter_post:
        local_frame = apply_post_pre(
            local_frame, pre=alter_pre, post=alter_post)
    return local_frame

def apply_anchor_args(shape, anchor_args): 
    return apply_at_args(shape, *anchor_args[1][0], **anchor_args[1][1])

def find_intersection(maker, plane_anchor, line_anchor):
    '''Finds intersection of anchors on a maker.
    Args:
      maker: The Shape where anchors are found.
      plane_anchor: The anchor plane in surface_args() format.
      line_anchor: The anchor line in surface_args() format.
    Returns:
      A GMatrix representing the point of intersection or None if 
      the line and plane don't intersect.
    '''
    plane = plane_anchor.apply(maker)
    line = line_anchor.apply(maker)
    return l.plane_line_intersect(plane, line)

def find_all_intersect(maker, plane_anchor, *line_anchors):
    '''Returns a tuple of GMatrix "points" marking the intersection of
    line_anchors and the plane_anchor. 
    Args:
      maker: The Shape where anchors are found.
      plane_anchor: The anchor plane in surface_args() format.
      line_anchors: The args list of anchor line in surface_args() format.
    Returns:
      A tuple of results of intersections of the plane_anchor and the
      given line_anchots.
    '''
    return tuple(find_intersection(maker, plane_anchor, la) 
                 for la in line_anchors)

@dataclass(frozen=True)
class NamedShapeBase(object):
    shape: object  # Shape or Maker or LazyShape
    shape_type: object  # Hashable
    name: object  # Hashable
    attributes: ModelAttributes = None

    def _as_non_defaults_dict(self):
        return dict((k, getattr(self, k)) 
                    for k in self.__annotations__.keys() if not getattr(self, k) is None)
    
    def _with(self, fname, value):
        d = self._as_non_defaults_dict()
        d[fname] = value
        return self.__class__(**d)
        
    def with_attributes(self, attributes):
        return self.__class__(**self._with('attributes', attributes))
        
    def get_attributes_or_default(self) :
        attributes = self.attributes
        if not attributes:
            attributes = EMPTY_ATTRS
        return attributes
        
    def colour(self, colour):
        return self._with(
            'attributes', self.get_attributes_or_default().with_colour(colour))
    
    def fa(self, fa):
        return self._with(
            'attributes', self.get_attributes_or_default().with_fa(fa))
    
    def fs(self, fs):
        return self._with(
            'attributes', self.get_attributes_or_default().with_fs(fs))
    
    def fn(self, fn):
        return self._with(
            'attributes', self.get_attributes_or_default().with_fn(fn))
    
    def disable(self, disable):
        return self._with(
            'attributes', self.get_attributes_or_default().with_disable(disable))
    
    def show_only(self, show_only):
        return self._with(
            'attributes', self.get_attributes_or_default().with_show_only(show_only))
    
    def debug(self, debug):
        return self._with(
            'attributes', self.get_attributes_or_default().with_debug(debug))
    
    def transparent(self, transparent):
        return self._with(
            'attributes', self.get_attributes_or_default().with_transparent(transparent))

    def use_polyhedrons(self, as_polyhedrons):
        return self._with(
            'attributes', self.get_attributes_or_default().with_use_polyhedrons(as_polyhedrons))


class NamedShape(NamedShapeBase):
    
    def at(self, 
           *pargs, 
           post: l.GMatrix=None, 
           pre: l.GMatrix=None, 
           args=None,
           anchor=None, 
           **kwds):
        '''Creates a shape containing the nominated shape at the reference frame given.
        *args, **kwds: Parameters for the shape given. If none is provided then IDENTITY is used.
        pre: The pre multiplied transform.
        post: The post multiplied transform,
        '''
        
        if (pargs or kwds) and (args or anchor) or (args and anchor):
            raise IllegalParameterException(
                'Only one form of anchor parameters allowed.')
            
        alter_pre = None
        alter_post = None
        if anchor:
            args = anchor.args
        if args:
            pargs = args[0]
            kwds = args[1]
            alter_pre = kwds.pop('pre', None)
            alter_post = kwds.pop('post', None)
        
        if not pargs and not kwds:
            reference_frame = l.IDENTITY
        else:
            reference_frame = self.shape.at(*pargs, **kwds)
        
        reference_frame = apply_post_pre(reference_frame, pre=pre, post=post)
        if alter_pre or alter_post:
            reference_frame = apply_post_pre(reference_frame, pre=alter_pre, post=alter_post)
        
        return self.projection(reference_frame)
        
    def projection(self, reference_frame: l.GMatrix):
        return Maker(
            self.shape_type, 
            ShapeFrame(self.name, self.shape, reference_frame), 
            attributes=self.attributes)

class ShapeNamer:
    def named_shape(self, name, mode_shape_frame):
        assert False, 'This method needs to be overridden in child classes.'
        
    # Shape like functions.    
    def solid(self, name):
        return self.named_shape(name, ModeShapeFrame.SOLID)
    
    def hole(self, name):
        return self.named_shape(name, ModeShapeFrame.HOLE)
    
    def cage(self, name):
        return self.named_shape(name, ModeShapeFrame.CAGE)
    
    def composite(self, name):
        return self.named_shape(name, ModeShapeFrame.COMPOSITE)
    
    def intersect(self, name):
        return self.named_shape(name, ModeShapeFrame.INTERSECT)
    
    def hull(self, name):
        return self.named_shape(name, ModeShapeFrame.HULL)
    
    def minkowski(self, name):
        return self.named_shape(name, ModeShapeFrame.MINKOWSKI)

    def named_shape_by_index(self, name, index, *modes):
        '''Select the shape mode by the index given over the provided modes.'''
        return self.named_shape(name, modes[index])
    
    def solid_hole(self, name, is_hole):
        '''Choose the mode as solid or hole determined by the is_hole parameter.'''
        return self.named_shape_by_index(
            name, is_hole, ModeShapeFrame.SOLID, ModeShapeFrame.HOLE)
        
    def solid_cage(self, name, is_cage):
        '''Choose the mode as solid or cage determined by the is_cage parameter.'''
        return self.named_shape_by_index(
            name, is_cage, ModeShapeFrame.SOLID, ModeShapeFrame.CAGE)

class ShapeMaker:
    def as_maker(self, name, mode_shape_frame, reference_frame):
        assert False, 'This method needs to be overridden in child classes.'

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


class LazyNamedShape(NamedShapeBase):
    '''Provides attributes but no transformation to a maker.'''
    
    def to_named_shape(self, shape):
        values = self._as_non_defaults_dict()
        values['shape'] = shape
        return NamedShape(**values)

@dataclass(frozen=True)
class LazyShape(ShapeNamer):
    shape_type: type
    field_specifiers: tuple
    other_args: tuple
    
    def build(self, *params):
        if len(params) != len(self.field_specifiers):
            raise InvalidNumberOfParametersException(
                f'Received {len(params)} but expected {len(self.field_specifiers)}')

        args = copy.deepcopy(self.other_args)
        for field_specifier, value in zip(self.field_specifiers, params):
            if isinstance(field_specifier, str):
                args[1][field_specifier] = value
            else:
                field_specifier(value, args)
        
        return self.shape_type(*args[0], **args[1])

    def named_shape(self, name, mode_shape_frame):
        return LazyNamedShape(self, mode_shape_frame, name)


@dataclass(frozen=True)
class AtSpecifier:
    '''An 'at' specifier contains the args to call an Shape at() function. This allows 
    lazy evaluation of a Shape a() call.'''
    args_positional: tuple
    args_named: frozendict
    
    def apply(self, shape_obj):
        return apply_at_args(shape_obj, *self.args_positional, **self.args_named)

def at_spec(*args, **kwds):
    '''Returns an AtSpecifier with the parameters sent to this function.'''
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
    target_maker=None):
    '''Creates a shape with the provided lazy_named_shape and the first parameter being
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
    '''

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
    
    world_shape_to =  (shape_to_frame * shape_add_at_frame_inv)
    world_shape_from = (shape_from_frame * shape_add_at_frame_inv)
    
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
    
    target_maker.add_at(
        named_shape.projection(shape_from_frame), pre=add_at_frame)

    return target_maker
    

def lazy_shape(shape_type, *field_specifiers, other_args=args()):
    '''Returns a 'LazyShape', a factory for a shape. The parameters provided
    to the factory will be applied with 'other_args' to generate the final set
    of parameters to the Shape constructor.
    Args:
        shape_type: A Shape class or a factory function.
        field_specifiers: The field names what will be associated will be associated
        in the LazyShape.build() function.
        other_args: Other args passed to the shape_type constructor.
    '''
    return LazyShape(shape_type, field_specifiers, other_args)


@dataclass()
class ExampleParams():
    shape_args: tuple=args()
    anchors: tuple=()
    base_anchor: AnchorArgs=surface_args()
    
    def args_str(self):
        return f'(*{self.shape_args[0]!r}, **{self.shape_args[1]!r})'
    

class Shape(ShapeNamer, ShapeMaker):
    '''The base "shape" class for Anchorscad.
    '''
    EXAMPLE_VERSION=None
    EXAMPLE_ANCHORS=()
    EXAMPLE_SHAPE_ARGS=args()
    EXAMPLES_EXTENDED=frozendict()
    
    def __init__(self):
        pass
    
    def copy_if_mutable(self):
        return self
        
    def named_shape(self, name, mode_shape_frame):
        'Overrides ShapeNamer.named_shape'
        return NamedShape(self.copy_if_mutable(), mode_shape_frame, name)
    
    def as_maker(self, name, mode_shape_frame, reference_frame):
        'Overrides ShapeNamer.as_maker'
        return Maker(
            mode_shape_frame, ShapeFrame(name, self.copy_if_mutable(), reference_frame))

    def has_anchor(self, name):
        return name in self.anchorscad.anchors
    
    def anchor_names(self):
        return tuple(self.anchorscad.anchors.keys())
    
    def at(self, *args, anchor=None, **kwds):
        if anchor and (args or kwds):
            raise IncorrectAnchorArgs(
                'Must not provide any other args when anchor parameter specified')
        if anchor:
            return anchor.apply(self)
        
        anchor_name = args[0]
        args = args[1:]
        spec = self.anchorscad.get(anchor_name)
        if not spec:
            raise IncorrectAnchorArgs(
                f'Could not find {anchor_name!r} on {self.__class__.__name__}\n'
                f'Available names are {self.anchor_names()!r}')
            
        func = spec[0]
        try:
            return func(self, *args, **kwds)
        except TypeError as e:
            raise IncorrectAnchorArgs(
                f'Attempted to call {anchor_name!r} on {self.__class__.__name__}'
                f' with args={args!r} kwds={kwds!r}') from e
    
    def name(self):
        return self.anchorscad.name
    
    def render(self, renderer):
        raise UnimplementedRenderException(f'Unimplemented render in {self.name()!r}.')
    
    @classmethod
    def examples(cls):
        '''Returns a list of available examples.'''
        non_str_keys = tuple(
            repr(s) for s in cls.get_extended_example_keys() if not isinstance(s, str))
        assert not non_str_keys, (f'Shpae examples in "{cls.__name__}" contains non string keys: '
                                  f'{non_str_keys}. Recast these to strings.')
        assert not 'default' in cls.get_extended_example_keys(), (f'Shpae examples in "{cls.__name__}" '
                                                        f'must not contain key "default".')
        return ('default',) + tuple(cls.get_extended_example_keys())
    
    @classmethod
    def get_default_example_params(cls):
        return ExampleParams(
                cls.EXAMPLE_SHAPE_ARGS, cls.EXAMPLE_ANCHORS)
        
    def get_example_version(self):
        return self.EXAMPLE_VERSION
        
    @classmethod
    def get_extended_example_keys(cls):
        return cls.EXAMPLES_EXTENDED.keys()
    
    @classmethod
    def get_extended_example_params(cls, name):
        return cls.EXAMPLES_EXTENDED[name]
    
    @classmethod
    def example(cls, name='default'):
        if name == 'default':
            example_params = cls.get_default_example_params()
        else:
            example_params = cls.get_extended_example_params(name)

        try:
            entryname = (f'{cls.__name__}' + example_params.args_str())
            shape = cls(
                *example_params.shape_args[0], 
                **example_params.shape_args[1]
                )
            projection = example_params.base_anchor.apply(shape)
            maker = shape.solid(name).projection(projection)            
            
            for entry in example_params.anchors:
                entry.func(maker, entry)
        except BaseException:
            traceback.print_exception(*sys.exc_info(), limit=20) 
            sys.stderr.write(
                f'Error while rendering example for {cls.__name__}:{name!r}, see:\n')
            sys.stderr.write(
                f'  File "{inspect.getsourcefile(cls)}", {cls.__name__}:{name!r}\n')
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
            target_maker=None):
        '''Builds a shape of type cls between two nominated anchors.
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
        '''
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
            target_maker=target_maker)


@dataclass()
class _Mode():
    mode: str
    has_operator_container: bool=False
    
    def make_container(self, model):
        return model.Union()

@dataclass()
class SolidMode(_Mode):
    def __init__(self):
        super().__init__('solid')
        
    def pick_rendererx(self, renderer):
        return renderer.solid()    

@dataclass()
class HoleMode(_Mode):
    def __init__(self):
        super().__init__('hole')
        
    def pick_rendererx(self, renderer):
        return renderer.hole()
    
@dataclass()
class CompositeMode(_Mode):
    def __init__(self):
        super().__init__('composite')
        
    def pick_rendererx(self, renderer):
        return renderer.hole()

@dataclass()
class CageMode(_Mode):
    def __init__(self):
        super().__init__('cage')
        
    def pick_rendererx(self, renderer):
        return renderer.null()

@dataclass()
class IntersectMode(_Mode):
    def __init__(self):
        super().__init__('intersect', True)
        
    def pick_rendererx(self, renderer):
        return renderer.intersect()
    
    def make_container(self, model):
        return model.Intersection()

@dataclass()
class HullMode(_Mode):
    def __init__(self):
        super().__init__('hull', True)
        
    def pick_rendererx(self, renderer):
        return renderer.hull()
    
    def make_container(self, model):
        return model.Hull()

@dataclass()
class MinkowskiMode(_Mode):
    def __init__(self):
        super().__init__('minkowski', True)
        
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
    
    
@dataclass(frozen=True)
class ModeShapeFrame():
    SOLID=SolidMode()
    HOLE=HoleMode()
    CAGE=CageMode()
    COMPOSITE=CompositeMode()
    INTERSECT=IntersectMode()
    HULL=HullMode()
    MINKOWSKI=MinkowskiMode()
    
    mode: _Mode
    shapeframe: ShapeFrame
    attributes: ModelAttributes = None
    
    def inverted(self):
        return ModeShapeFrame(self.mode, 
                              self.shapeframe.inverted(), 
                              attributes=self.attributes)
    
    def pre_mul(self, reference_frame):
        return ModeShapeFrame(self.mode, 
                              self.shapeframe.pre_mul(reference_frame), 
                              attributes=self.attributes)
    
    def post_mul(self, reference_frame):
        return ModeShapeFrame(self.mode, 
                              self.shapeframe.post_mul(reference_frame), 
                              attributes=self.attributes)

    def reference_frame(self):
        return self.shapeframe.reference_frame
    
    def name(self):
        return self.shapeframe.name
    
    def shape(self):
        return self.shapeframe.shape
    
    def colour(self):
        return None if self.attributes is None else self.attributes.colour
    
    def to_str(self):
        parts=(
            repr(self.shape()),
            '.',
            self.mode.mode,
            '(',
            repr(self.name())
            )
        
        attr_parts = ()
        if self.attributes:
            attr_parts = (
                ').attributes(',
                repr(self.attributes)
                )
        projectopm_parts = (
            ').projection(',
            repr(self.reference_frame()),
            ')'
            )
        return ''.join(parts + attr_parts + projectopm_parts)
    
@dataclass(frozen=True)
class CageOfProperties:
    '''Properties used by
      shape: Shape to be made a cage.
      name: The name to be applied to the shape.
      colour: The colour applied to the shape.
    '''
    
    name: str='cage'
    colour: tuple=(0.0, 1.0, 0.35, 0.4)
    
    def apply(self, shape, as_cage, name=None):
        '''Apply this object's properties to shape.
        Args:
              shape: Shape to be made a cage.
              as_cage: If true, the shape will be treated as a cage and not rendered
                       If false, it will be rendered transparent with the given colour.
        '''
        if isinstance(shape, BoundNode):
            shape = shape()
        if name is None:
            name = self.name
        if as_cage:
            return shape.cage(name)
        return (shape.solid(name)
                    .colour(self.colour)
                    .transparent(True))


def cageof(shape: Shape=None, 
           as_cage: bool=True,
           cage_name: object=None,
           properties: CageOfProperties=CageOfProperties()):
    '''Conditionally returns either a cage mode or solid (but transparent)
    Maker. This can be used as a datateee Node and parameters will become
    encapsulating class fields.
    Args:
      shape: Shape to be made a cage.
      as_cage: If true, the shape will be treated as a cage and not rendered
               If false, it will be rendered transparent with the given colour.
      cage_properties: to be applied.
    '''
    return properties.apply(shape, as_cage, name=cage_name)

class CageOfNode(Node):

    def __init__(self, *args_, prefix=''):
        super().__init__(cageof, 'as_cage', *args_, prefix=prefix)

@dataclass
class Maker(Shape):
    '''The builder of composite shapes. Provides the ability to anchor shapes at various other
    frames (anchors) associated with Shapes already added.
    '''
    reference_shape: ModeShapeFrame
    entries: dict
    
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
                    f'\'copy_of\' named parameter is provided and \'attributes\', \'mode\' or '
                    f'\'shape_frame\' parameters must not be provided but '
                    f'attributes={attributes!r}, mode={mode!r} and shape_frame={shape_frame!r}')
        
    def copy_if_mutable(self):
        return Maker(copy_of=self)
        
    def _add_mode_shape_frame(self, mode_shape_frame):
        # Check for name collision.
        name = mode_shape_frame.shapeframe.name
        previous = self.entries.get(name, None)
        if previous:
            raise DuplicateNameException(
                'Attempted to add %r when it already exists in with mode %r' % (
                    name, 
                    previous.mode.mode))
        self.entries[name] = mode_shape_frame
        return self

    def add(self, maker):
        if not isinstance(maker, Maker):
            raise IllegalParameterException(
                f'Expected a parameter of type {self.__class__.__name__!r} but received an '
                f'object of type {maker.__class__.__name__!r}.')
        
        for entry in maker.entries.values():
            self._add_mode_shape_frame(entry)
        
        return self
    
    def add_at(self, 
               maker, 
               *pargs, 
               pre=None, 
               post=None, 
               args=None, 
               anchor=None, 
               **kwds):
        '''Adds another maker at the anchor of the provided parameters.
        If args is provided, this is a packed set of args from core.args.
        '''
        if not isinstance(maker, Maker):
            raise IllegalParameterException(
                f'Expected a parameter of type {self.__class__.__name__!r} but received an '
                f'object of type {maker.__class__.__name__!r}.')
            
        if (pargs or kwds) and (args or anchor):
            raise IllegalParameterException(
                f'Recieved positional args and kwds when parameter "args" or anchor is also'
                'provided.')
        if anchor:
            pargs = anchor.pargs
            kwds = anchor.kwds

        alter_pre = None
        alter_post = None
        if args:
            pargs = args[0]
            kwds = dict(args[1])
            alter_pre = kwds.pop('pre', None)
            alter_post = kwds.pop('post', None)
            
        local_frame = self.at(*pargs, **kwds) if pargs or kwds else l.IDENTITY
        local_frame = apply_post_pre(local_frame, pre=pre, post=post)
        if alter_pre or alter_post:
            local_frame = apply_post_pre(local_frame, pre=alter_pre, post=alter_post)
        
        for entry in maker.entries.values():
            self._add_mode_shape_frame(entry.pre_mul(local_frame))
            
        return self
        
    def add_shape(self, mode, shape_frame, attributes=None):
        return self._add_mode_shape_frame(ModeShapeFrame(
            mode, shape_frame.inverted(), attributes))
    
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
            attributes=attributes)
        
    def has_anchor(self, name):
        ref_shape = self.reference_shape.shapeframe.shape
        if ref_shape.has_anchor(name):
            return True
        return name in self.entries
    
    def anchor_names(self):
        return self.reference_shape.shape().anchor_names() + tuple(self.entries.keys()) 
    
    def at(self, *args, anchor=None, **kwds):
        if anchor and (args or kwds):
            raise IncorrectAnchorArgs(
                'Must not provide any other args when anchor parameter specified')
        if anchor:
            return anchor.apply(self)
        
        name = args[0]
        args = args[1:]
        shapeframe = self.reference_shape.shapeframe
        ref_shape = shapeframe.shape
        if ref_shape.has_anchor(name):
            entry = self.entries.get(self.reference_shape.name())
            return entry.reference_frame() * ref_shape.at(name, *args, **kwds)
        entry = self.entries.get(name)
        
        if entry is None:
            raise AnchorSpecifierNotFoundException(
                f'name={name!r} is not an anchor of the reference shape or a named shape. '
                f'Available names are {self.anchor_names()}.')
        
        return entry.reference_frame() * entry.shape().at(*args, **kwds)

    def name(self):
        return 'Maker({name!r})'.format(name=self.reference_shape.name())
    
    def to_str(self):
        parts = [self.reference_shape.to_str()]
        for entry in self.entries.values():
            if entry.name() == self.reference_shape.name():
                continue
            parts.append(f'.add(\n    {entry.inverted().to_str()})')
        return ''.join(parts)
    
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
                v.shapeframe.shape.__class__.__name__)
            try:
                v.shape().render(renderer)
            finally:
                renderer.pop()


@dataclass(frozen=True)
class AnchorSpec():
    '''Associated with @anchor functions.'''
    description: str


def anchor(description):
    '''Decorator for anchor functions.'''
    def decorator(func):
        func.__anchor_spec__ = AnchorSpec(description)
        return func
    return decorator

# Converter for a list or iterable to a vector that defaults missing values to 1.
VECTOR3_FLOAT_DEFAULT_1 = l.list_of(
    np.float64, 
    len_min_max=(3, 3), 
    fill_to_min=np.float64(1))


@dataclass(frozen=True)
class Anchors():
    name: str
    level: int
    anchors: frozendict
        
    def get(self, name):
        return self.anchors.get(name)
    
    
@dataclass()
class AnchorsBuilder():
    '''\
    name: is the shape class name to use
    '''
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


def shape(clazz_or_name=None, /, *, name=None, level=10):
    if isinstance(clazz_or_name, str):
        name = clazz_or_name
        clazz_or_name = None
    
    def decorator(clazz):
        builder = AnchorsBuilder(name, level)
        for func_name in dir(clazz):
            if func_name.startswith("__"):
                continue
            func = getattr(clazz, func_name)
            if not callable(func):
                continue
            if not hasattr(func, '__anchor_spec__'):
                continue
            builder.add(func_name, func, func.__anchor_spec__)
        clazz.anchorscad = builder.build()
        return clazz
    if clazz_or_name is None:
        return decorator
    
    return decorator(clazz_or_name)


@dataclass
class FabricatorParams:
    level: float


def fabricator(clazz=None, /, *, level=10):
    def wrap(clazz):
        clazz.anchorscad_fabricator = FabricatorParams(level)
        return clazz
    
    # See if we're being called as @datatree or @datatree().
    if clazz is None:
        # We're called with parens.
        return wrap

    # We're called as @datatree without parens.
    return wrap(clazz)


@shape('anchorscad/core/box')
@dataclass
class Box(Shape):
    '''Generates rectangular prisms (cubes where l=w=h).'''
    size: l.GVector
    
    # Orientation of the 6 faces.
    ORIENTATION = (
        l.rotX(90),
        l.rotX(90) * l.rotX(90),
        l.rotX(90) * l.rotY(-90),
        l.rotX(90) * l.rotX(180),
        l.rotX(90) * l.rotX(-90),
        l.rotX(90) * l.rotY(90))
    
    COORDINATES_CORNERS = (
        ((), (0,), (0, 2), (2,)),
        ((1,), (0, 1), (0,), ()),
        ((1,), (), (2,), (1, 2)),
        ((1, 2), (0, 1, 2), (0, 1), (1,)),
        ((2,), (0, 2), (0, 1, 2), (1, 2)),
        ((0, ), (0, 1), (0, 1, 2), (0, 2)),
        )
    
    COORDINATES_EDGE_HALVES = tuple(
        tuple([
            tuple([tuple(set(face[i]) ^ set(face[(i + 1) % 4])) for i in range(4)])
            for face in COORDINATES_CORNERS]))
    
    COORDINATES_CORNERS_ZEROS = tuple(
        tuple([
            tuple([tuple(set((0,1,2)) - set(coords)) for coords in face])
            for face in COORDINATES_CORNERS]))
    
    COORDINATES_CENTRES_AXIS = tuple(
        tuple(set((0,1,2)) - set(face[0]) - set(face[2 ])) 
        for face in COORDINATES_CORNERS[0:3])
    
    EXAMPLE_ANCHORS=tuple(
        (surface_args('face_corner', f, c)) for f in (0, 3) for c in range(4)
        ) + tuple(surface_args('face_edge', f, c) for f in (1, 3) for c in range(4)
        ) + tuple(surface_args('face_centre', f) for f in 
                  ('front', 'back', 'left', 'right', 'base', 'top')
        ) + (
            surface_args('face_edge', 2, 2, 0.1),
            surface_args('face_edge', 'left', 2, -0.5),
            inner_args('centre'),)
    EXAMPLE_SHAPE_ARGS=args([100, 120, 140])
    
    FACE_MAP=frozendict({
        0: 0,
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        'front': 0,
        'back': 3,
        'base': 1,
        'top': 4,
        'left': 2,
        'right': 5})
    
    def __init__(self, size=[1, 1, 1]):
        self.size = l.GVector(VECTOR3_FLOAT_DEFAULT_1(size))

    def render(self, renderer):
        renderer.add(renderer.model.Cube(self.size.A3))
        return renderer
    
    @anchor('Centre of box oriented same as face 0')
    def centre(self):
        return l.translate(l.GVector(self.size) / 2)
    
    @anchor('Corner of box given face (0-5) and corner (0-3)')
    def face_corner(self, face, corner, t=0, d=0):
        return self.face_edge(face, corner, t=t, d=d)
    
    @anchor('Edge centre of box given face (0-5) and edge (0-3)')
    def face_edge(self, face, edge, t=0.5, d=0):
        face = self.FACE_MAP[face]
        orientation = self.ORIENTATION[face] * l.rotZ(90 * edge)
        loc = l.GVector(self.size)  # make a copy.
        half_of = self.COORDINATES_EDGE_HALVES[face][edge]
        zero_of = self.COORDINATES_CORNERS_ZEROS[face][edge]
        for i in range(3):
            if i in half_of:
                if i in zero_of:
                    loc[i] = t * loc[i] + d
                else:
                    loc[i] = (1 - t) * loc[i] - d
            elif i in zero_of:
                loc[i]  = 0.0
        return l.translate(loc) * orientation
        
    @anchor('Centre of face given face (0-5)')
    def face_centre(self, face):
        face = self.FACE_MAP[face]
        orientation = self.ORIENTATION[face]
        loc = l.GVector(self.size)  # make a copy.
        keep_value = self.COORDINATES_CENTRES_AXIS[face % 3][0]
        for i in range(3):
            if i == keep_value:
                if face < 3:
                    loc[i] = 0.0
            else:
                loc[i] = loc[i] * 0.5
        return l.translate(loc) * orientation
    


TEXT_DEPTH_MAP={'centre':0.0, 'rear': -0.5, 'front':0.5}

def non_defaults_dict(dataclas_obj, include=None, exclude=()):
    if not (include is None or isinstance(include, tuple) or isinstance(include, dict)):
        raise IllegalParameterException(
            f'Expected parameter \'include\' to be a tuple but is a {include.__class__.__name__}')
    if not (exclude is None or isinstance(exclude, tuple) or isinstance(exclude, dict)):
        raise IllegalParameterException(
            f'Expected parameter \'exclude\' to be a tuple but is a {exclude.__class__.__name__}')
    return dict((k, getattr(dataclas_obj, k)) 
                for k in dataclas_obj.__annotations__.keys() 
                if (not k in exclude) and (
                    include is None or k in include) and not getattr(dataclas_obj, k) is None)

def non_defaults_dict_include(dataclas_obj, include, exclude=()):
    if not (include is None or isinstance(include, tuple) or isinstance(include, dict)):
        raise IllegalParameterException(
            f'Expected parameter \'include\' to be a tuple but is a {include.__class__.__name__}')
    if not (exclude is None or isinstance(exclude, tuple) or isinstance(exclude, dict)):
        raise IllegalParameterException(
            f'Expected parameter \'exclude\' to be a tuple but is a {exclude.__class__.__name__}')
    return dict((k, getattr(dataclas_obj, k)) 
                for k in include 
                if (not k in exclude) and not getattr(dataclas_obj, k) is None)
    
    

def values_dict(targetclas, dataclas_obj, exclude=()):
    '''Retrieves all values from the dataclas_obj that appear in the targetclas class.'''
    if not (exclude is None or isinstance(exclude, tuple) or isinstance(exclude, dict)):
        raise IllegalParameterException(
            f'Expected parameter \'exclude\' to be a tuple but is a {exclude.__class__.__name__}')
    return dict((k, getattr(dataclas_obj, k)) 
                for k in targetclas.__annotations__.keys() if (not k in exclude))
    
def create_from(targetclas, dataclas_obj, exclude=()):
    '''Creates a targetclas with all constructor parameters of the same name.
    Both targetclas and dataclas_obj__class__ should be annotated with @dataclass.
    '''
    return targetclas(**values_dict(targetclas, dataclas_obj, exclude))
    
ARGS_XLATION_TABLE={'fn': '_fn', 'fa': '_fa', 'fs': '_fs'}
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
        xlation_table2=ARGS_XLATION_TABLE):
    cur_attrs = renderer.get_current_attributes()
    params = cur_attrs.fill_dict(
        non_defaults_dict(shape, include=include, exclude=exclude), attr_names)
    if xlation_table:
        params = translate_names(params, xlation_table=xlation_table)
    if xlation_table2:
        params = translate_names(params, xlation_table=xlation_table2)
    return params


@shape('anchorscad/core/text')
@dataclass
class Text(Shape):
    '''Generates 3D text.'''
    text: posc.str_strict=None
    size: float=10.0
    depth: float=1.0
    font: posc.str_strict=None
    halign: posc.of_set('left', 'center', 'right')='left'
    valign: posc.of_set('top', 'center', 'baseline' 'bottom')='bottom'
    spacing: float=1.0
    direction: posc.of_set('ltr', 'rtl', 'ttb', 'btt')='ltr'
    language: posc.str_strict=None
    script: posc.str_strict=None
    fn: int=None
    
    
    EXAMPLE_ANCHORS=(surface_args('default', 'rear'),)
    EXAMPLE_SHAPE_ARGS=args('Text Example')

    def render(self, renderer):
        params = fill_params(self, renderer, ('fn',), exclude=('depth',))
        text_obj = renderer.model.Translate([0, 0, -0.5])(
             renderer.model.Linear_Extrude(1)(
                 renderer.model.Text(**params)))
        if self.depth == 1:
            return renderer.add(text_obj)
        
        scale_obj = renderer.model.Scale([1, 1, self.depth])
        scale_obj(text_obj)
        return renderer.add(scale_obj)
    
    @anchor('The default position for this text. depth=(rear, centre, front)')
    def default(self, depth='centre', rd=None):
        if rd is None:
            rd = TEXT_DEPTH_MAP[depth]
        return l.translate([0, 0, self.depth * rd])
    

ANGLES_TYPE = l.list_of(l.strict_float, len_min_max=(3, 3), fill_to_min=0.0)
@shape('anchorscad/core/sphere')
@dataclass
class Sphere(Shape):
    '''Generates a Sphere.'''
    r: float=1.0
    fn: int=None
    fa: float=None
    fs: float=None

    EXAMPLE_ANCHORS=(surface_args('top'),
                     surface_args('base'),
                     inner_args('centre'),
                     surface_args('surface', [90, 30, 45]),
                     surface_args('surface', [-45, 0, 0]),
                     surface_args('surface', [0, 0, 0]),)
    EXAMPLE_SHAPE_ARGS=args(20)
    

    def render(self, renderer):
        params = fill_params(self, renderer, ('fn', 'fa', 'fs'))
        params = translate_names(params)
        renderer.add(renderer.model.Sphere(**params))
        return renderer
    
    @anchor('The base of the cylinder')
    def base(self):
        return l.rotX(180) * l.translate([0, 0, self.r])
    
    @anchor('The top of the cylinder')
    def top(self):
        return l.translate([0, 0, self.r])
    
    @anchor('The centre of the cylinder')
    def centre(self):
        return l.rotX(180)
    
    @anchor('A location on the sphere.')
    def surface(self, degrees: ANGLES_TYPE=ANGLES_TYPE([0, 0, 0]), radians: ANGLES_TYPE=None):
        if radians:
            angle_type = 'radians'
            angles = ANGLES_TYPE(radians)
        else:
            angle_type = 'degrees'
            angles = ANGLES_TYPE(degrees)
        
        return (l.rotY(**{angle_type: angles[2]}) 
             * l.rotX(**{angle_type: angles[1]}) 
             * l.rotZ(**{angle_type: angles[0]})
             * l.translate([self.r, 0, 0])
             * l.ROTV111_120)

CONE_ARGS_XLATION_TABLE={'r_base': 'r1', 'r_top': 'r2'}
@shape('anchorscad/core/cone')
@dataclass
class Cone(Shape):
    '''Generates cones or horizontal conical slices and cylinders.'''
    h: float=1.0
    r_base: float=1.0
    r_top: float=0.0
    fn: int=None
    fa: float=None
    fs: float=None
    
    EXAMPLE_ANCHORS=(
        surface_args('base'),
        surface_args('top'),
        surface_args('surface', 20, 0),
        surface_args('surface', 10, 45),
        surface_args('surface', 3, 90, tangent=False),
        inner_args('centre'))
    EXAMPLE_SHAPE_ARGS=args(h=50, r_base=30, r_top=5, fn=30)
    
    def __post_init__(self):
        if self.h < 0:
            raise IllegalParameterException(
                f'Parameter h({self.h}) is less than 0.')
        if self.r_base < 0:
            raise IllegalParameterException(
                f'Parameter r_base({self.r_base}) is less than 0.')
        if self.r_top < 0:
            raise IllegalParameterException(
                f'Parameter r_top({self.r_top}) is less than 0.')
        
    def render(self, renderer):
        params = fill_params(self, renderer, ('fn', 'fa', 'fs'))
        params = translate_names(params, CONE_ARGS_XLATION_TABLE)
        params.pop('r', None)  # If self is a Cylinder, we don't want r.
        renderer.add(renderer.model.Cylinder(r=None, **params))
        return renderer
    
    @anchor('The base of the cylinder')
    def base(self, h=0, rh=None):
        if rh:
            h = h + rh * self.h
        transform = l.ROTX_180
        if not h:
            return transform
        return l.tranZ(h) * transform
    
    @anchor('The top of the cylinder')
    def top(self, h=0, rh=None):
        if rh:
            h = h + rh * self.h
        return l.translate([0, 0, self.h - h])
    
    @anchor('The centre of the cylinder')
    def centre(self):
        return l.translate([0, 0, self.h / 2]) * l.ROTX_180
    
    @anchor('A location on the curved surface.')
    def surface(self, h=0, degrees=0.0, radians=None, tangent=True, 
                rh=None, radius_delta=0.0):
        if h is None:
            h = 0.0
        if not rh is None:
            h = h + self.h * rh
        r = (h / self.h) if self.h else 0
        x = r * self.r_top + (1 - r) * self.r_base + radius_delta
        if tangent:
            m = l.rot_to_V([-1, 0, 0], [self.r_top - self.r_base, 0, self.h]) * l.rotZ(90)
        else:
            m = l.ROTV111_120
        return l.rotZ(degrees=degrees, radians=radians) * l.translate([x, 0, h]) * m
    
@shape('anchorscad/core/cone')
@dataclass
class Cylinder(Cone):
    '''Creates a Cone that has the same top and base radius. (a cylinder)'''
    h: float=1.0
    r: float=None
    r_base: float=None
    r_top: float=field(init=False)
    # The fields below should be marked kw only (Python 3.10 feature).
    fn: int=None
    fa: float=None
    fs: float=None
    
    EXAMPLE_SHAPE_ARGS=args(h=50, r=30, fn=30)
    
    def __post_init__(self):
        if self.r is None:
            if self.r_base is None:
                self.r = 1.0
            else:
                self.r = self.r_base
        self.r_base = self.r
        self.r_top = self.r
            
        Cone.__post_init__(self)

class CompositeShape(Shape):
    '''Provides functionality for composite shapes. Subclasses must set 'maker' in
    the initialization of the class.'''
    
    def render(self, renderer):
        return self.maker.render(renderer)
            
    def copy_if_mutable(self):
        result=copy.copy(self)
        result._set_maker(Maker(copy_of=self.maker))
        return result

    @anchor('Access to inner elements of this composite shape.')
    def within(self, *args, **kwds):
        return self.maker.at(*args, **kwds)
    
    def has_anchor(self, name):
        return name in self.anchorscad.anchors or self.maker.has_anchor(name)
    
    def anchor_names(self):
        return tuple(self.anchorscad.anchors.keys()) + self.maker.anchor_names()
    
    def at(self, anchor_name, *args, **kwds):
        spec = self.anchorscad.get(anchor_name)
        if spec:
            func = spec[0]
            try:
                return func(self, *args, **kwds)
            except TypeError as e:
                raise IncorrectAnchorArgs(
                    f'Attempted to call {anchor_name!r} on {self.__class__.__name__}'
                    f' with args={args!r} kwds={kwds!r}') from e
        if self.maker.has_anchor(anchor_name):
            return self.maker.at(anchor_name, *args, **kwds)
        else:
            raise IncorrectAnchorArgs(
                f'Could not find {anchor_name!r} on {self.__class__.__name__}\n'
                f'Available names are {self.anchor_names()!r}')
    
    def _set_maker(self, maker):
        builtins.object.__setattr__(self, 'maker', maker)
        
    def set_maker(self, maker):
        if hasattr(self, 'maker'):
            raise IllegalStateException('Cannot set maker more than once.')
        self._set_maker(maker)


@shape('anchorscad/core/arrow')
@dataclass(frozen=True)
class Arrow(CompositeShape):
    r_stem_top: float=1.0
    r_stem_base: float=None # Defaults to r_stem_top
    l_stem: float=6.0
    l_head: float=3
    r_head_base: float=2
    r_head_top: float=0.0
    fn: int=None
    fa: float=None
    fs: float=None
    
    EXAMPLE_ANCHORS=(
        surface_args('base'),
        surface_args('top'),
        surface_args('stem', 'top'))
    EXAMPLE_SHAPE_ARGS=args(
        r_stem_top=4, r_stem_base=6, l_stem=35, l_head=20, r_head_base=10, fn=30)
    
    
    def __post_init__(self):
        if self.r_stem_base is None:
            self.r_stem_base = self.r_stem_top
            
        f_args = non_defaults_dict(self, include=ARGS_XLATION_TABLE)
        
        head = Cone(h=self.l_head, r_base=self.r_head_base, r_top=self.r_head_top, **f_args)
        stem = Cone(h=self.l_stem, r_base=self.r_stem_base, r_top=self.r_stem_top, **f_args)
        maker = stem.solid('stem').at('base')
        maker.add_at(head.solid('head').at('base', post=l.rotX(180)), 'top')
        self.set_maker(maker)
        
    @anchor('The base of the stem of the object')
    def base(self, *args, **kwds):
        return self.maker.at('stem', 'base', *args, **kwds)
    
    @anchor('The top of the head')
    def top(self, *args, **kwds):
        return self.maker.at('head', 'top', *args, **kwds)
    
    @anchor('Access to inner elements of this shape.')
    def within(self, *args, **kwds):
        return self.maker.at(*args, **kwds)


@shape('anchorscad/core/coordinates_cage')
@dataclass
class CoordinatesCage(Shape):
    base_frame: l.GMatrix=l.IDENTITY

    def render(self, renderer):
        return renderer
    
    @anchor('The untransformed origin.')
    def origin(self):
        return l.IDENTITY
    
    @anchor('x axis orientation')
    def x(self):
        return self.base_frame
    
    @anchor('y axis orientation')
    def y(self):
        return l.ROTV111_120 * self.base_frame
    
    @anchor('z axis orientation')
    def z(self):
        return l.ROTV111_240 * self.base_frame
    

@shape('anchorscad/core/coordinates')
@dataclass
class Coordinates(CompositeShape):
    
    overlap: float=3.0
    colour_x: Colour=Colour([1, 0, 0])
    colour_y: Colour=Colour([0, 1, 0])
    colour_z: Colour=Colour([0, 0, 1])
    r_stem_top: float=0.75
    r_stem_base: float=None # Defaults to r_stem_top
    l_stem: float=10.0
    l_head: float=3
    r_head_base: float=1.5
    r_head_top: float=0.0
    fn: int=None
    fa: float=None
    fs: float=None
    
    def __post_init__(self):
        if self.r_stem_base is None:
            self.r_stem_base = self.r_stem_top
        exclude=('overlap', 'colour_x', 'colour_y', 'colour_z', )
        arrow = Arrow(**non_defaults_dict(self, exclude=exclude))
        maker = CoordinatesCage().cage('origin').at('origin')
            
        t = l.translate([0, 0, -self.overlap])
        
        maker .add_at(arrow.solid('x_arrow').colour(self.colour_x).at(
            'base', pre=t * l.rotZ(180)), 'x', pre=l.rotY(-90))
        maker .add_at(arrow.solid('y_arrow').colour(self.colour_y).at(
            'base', pre=t * l.rotZ(180)), 'y', pre=l.rotZ(-90))
        maker .add_at(arrow.solid('z_arrow').colour(self.colour_z).at(
            'base', pre=t * l.rotZ(180)), 'z', pre=l.rotX(-90))
        self.maker = maker
            
    @anchor('The base of the stem of the object')
    def origin(self):
        return l.IDENTITY
    
    @anchor('Access to inner elements of this shape.')
    def within(self, *args, **kwds):
        return self.maker.at(*args, **kwds)
    
@shape('anchorscad/core/annotated_coordinates')
@dataclass
class AnnotatedCoordinates(CompositeShape):
    
    coordinates: Coordinates=Coordinates()
    coord_labels: frozendict=None
    text_stem_size_ratio:float = 0.3
    coord_label_at: tuple=args(post=l.translate([0, 0, 1]) * l.rotY(-90))
    label: str=None
    label_pos_ratio: l.GVector=l.GVector([0.5, 0.5, 0.5])
    
    EXAMPLE_SHAPE_ARGS=args(label='This is label')
    
    
    def __post_init__(self):
        
        if not self.coord_labels:
            self.coord_labels = frozendict({'x': 'x', 'y': 'y', 'z': 'z'})
        
        maker = self.coordinates.solid('coords').at('origin')
        if self.coord_labels:
            for k, s in self.coord_labels.items():
                txt = Text(s, size=self.text_stem_size_ratio * self.coordinates.l_stem)
                maker.add_at(txt.solid(k).at('default', 'centre'), 
                             'within', f'{k}_arrow', 'top', 
                             *self.coord_label_at[0], **self.coord_label_at[1])
        if self.label:
            txt = Text(self.label, 
                       halign='left', 
                       size=self.text_stem_size_ratio * self.coordinates.l_stem)
            xform = l.translate(
                [-10 * self.text_stem_size_ratio, -5 * -self.text_stem_size_ratio, 0]) * l.rotZ(-45)
            maker.add(txt.solid('label').colour([0, 1, 0.5]).at('default', 'centre', post=xform))

        self.maker = maker
    
    @anchor('The base of the stem of the object')
    def origin(self, *args, **kwds):
        return l.IDENTITY

    
def get_shape_class(module, name):
    mv = getattr(module, name)
    if not isinstance(mv, type):
        return False
    
    if not hasattr(mv, 'anchorscad') or not hasattr(mv, '__module__'):
        return False
    
    if mv.__module__ != module.__name__:
        return False
    
    if mv.anchorscad.__class__.__name__ == 'Anchors':
        return mv
    
    return False

def find_all_shape_classes(module):
    '''Returns all the shape classes (those containing __anchorscad__) and returns 
    a list.
    '''
    shape_classes = []
    for name in dir(module):
        shape_class = get_shape_class(module, name)
        if shape_class:
            shape_classes.append(shape_class)
    return shape_classes


@dataclass
class RenderOptions:
    render_attributes: ModelAttributes
    level: int
    class_name: tuple
    names_re: re.Pattern=None
    
    def __post_init__(self):
        if not self.class_name:
            self.class_name = ('*',)
        self.class_name_re = re.compile('|'.join(
            tuple('(?:' + fnmatch.translate(n) + ')' for n in self.class_name)))

    def match_name(self, cname):
        return self.class_name_re.match(cname)
                
def nameof(name, example_version):
    if example_version:
        return ''.join((name, example_version))
    return name

def render_examples(module, 
                    render_options, 
                    consumer, 
                    graph_consumer,
                    shape_consumer=None,
                    start_example=None,
                    end_example=None):
    '''Scans a module for all Anchorscad shape classes and renders examples.'''
    classes = find_all_shape_classes(module)
    # Lazy import renderer since renderer depends on this.
    import ParametricSolid.renderer as renderer
    
    shape_count = 0
    example_count = 0
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
                    poscobj, graph = renderer.render_graph(
                        maker, 
                        initial_frame=None, 
                        initial_attrs=render_options.render_attributes)
                    consumer(poscobj, clz, name, e)
                    graph_consumer(graph, clz, name, e)
                    if shape_consumer:
                        shape_consumer(maker, shape, clz, name, e)
                except BaseException as ex:
                    traceback.print_exception(*sys.exc_info(), limit=20) 
                    sys.stderr.write(
                        f'Error while rendering {clz.__name__} example:{e}:\n{ex}\n')
                    traceback.print_exception(*sys.exc_info()) 
                finally:
                    if end_example:
                        end_example(clz, e)
    return shape_count, example_count


class ExampleCommandLineRenderer():
    '''Command line parser and runner for invoking the renderer on examples.'''
        
    DESCRIPTION='''\
    Renders Anchorscad examples their respective scad files.
    
    Example opensacd scad files also render anchors so that it's useful to visualise
    both the location and the orientation of the anchor.
    '''
    
    EXAMPLE_USAGE='''\
    To render the Arrow shape in the core anchorscad example shapes. This will generate 
    an opensacd (.scad) file for all the selected shape classes in the Anchorscad.core 
    module.
    
        python3 -m Anchorscad.core --no-write --class_name Arrow 
        
    '''
    
    def __init__(self, args, do_exit_on_completion=None):
        argq = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=self.DESCRIPTION,
            epilog=textwrap.dedent(self.EXAMPLE_USAGE))

        argq.add_argument(
            '--class_name', 
            type=str,
            default='*',
            nargs='*',
            help='The name/s of the shape classes to render.')
        
        argq.add_argument(
            '--module', 
            type=str,
            default=None,
            help='The python module to be loaded.')
        
        argq.add_argument(
            '--no-write', 
            dest='write_files',
            action='store_false',
            help='Perform a test run. It will not make changes to file system.')
        
        argq.add_argument(
            '--write', 
            dest='write_files',
            action='store_true',
            help='Writes models to files.')
        argq.set_defaults(write_files=False)

        argq.add_argument(
            '--no-graph_write', 
            dest='write_graph_files',
            action='store_false',
            help='Produces a graph of shape_names in .dot GraphViz format.')
        
        argq.add_argument(
            '--graph_write', 
            dest='write_graph_files',
            action='store_true',
            help='Produces a graph of shape_names in .dot GraphViz format.')
        argq.set_defaults(write_graph_files=False)
        
        argq.add_argument(
            '--no-svg_write', 
            dest='write_graph_svg_files',
            action='store_false',
            help='Produces a graph of shape_names in .dot and .svg formats.')
        
        argq.add_argument(
            '--svg_write', 
            dest='write_graph_svg_files',
            action='store_true',
            help='Produces a graph of shape_names in .dot and .svg formats.')
        argq.set_defaults(write_graph_svg_files=False)
        
        argq.add_argument(
            '--out_file_name', 
            type=str,
            default=os.path.join(
                'examples_out', 'anchorcad_{class_name}_{example}_example.scad'),
            help='The OpenSCAD formatted output filename.')
        
        argq.add_argument(
            '--graph_file_name', 
            type=str,
            default=os.path.join(
                'examples_out', 'anchorcad_{class_name}_{example}_example.dot'),
            help='The GraphViz shape_name graph output filename.')
        
        argq.add_argument(
            '--level', 
            type=int,
            default=10,
            help=('The \'level\' at or above of the shape classes to render. '
                  'Shape classes with a lower level than this are excluded unless '
                  'they are specifically named.'))
        
        argq.add_argument(
            '--list_shapes', 
            action='store_true',
            default=False,
            help=('List Shape class names.'))
        
        self.argq = argq
        self.add_more_args()
        if do_exit_on_completion is None:
            self.do_exit_on_completion = not getattr(sys, 'ps1', sys.flags.interactive)
        else:
            self.do_exit_on_completion = do_exit_on_completion
        self.parse()
    
    def add_more_args(self):
        pass
        
    def parse(self):
        self.argp = self.argq.parse_args()
        self.options = RenderOptions(
            render_attributes=ModelAttributes(),
            level=self.argp.level,
            class_name=self.argp.class_name)
        self.set_mkdir = set()
        self.counts = (0, 0)
        self.status = 1
        
    def _load_anchorcad_module(self, module):
        if self.argp.module:
            globalsd = {}
            localsd = {}
            exec(f'import {module} as _m', globalsd, localsd)
            self.module = localsd.get('_m')
            self.module_name = module
        else:
            self.module = sys.modules['__main__']
            self.module_name = ''

    def file_writer(self, obj, clz, example_name, base_example_name):
        fname = self.argp.out_file_name.format(
            class_name=clz.__name__, example=example_name)
        path = pathlib.Path(fname)
        if self.argp.write_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            obj.write(path)
        else:
            if not path.parent in self.set_mkdir and not path.parent.exists():
                self.set_mkdir.add(path.parent)
                sys.stderr.write(f'directory "{path.parent}" does not exist. Will be created.\n')
            strv = obj.dumps()
            sys.stdout.write(
                f'Shape: {clz.__name__} {example_name} {len(strv)}\n')

    def graph_file_writer(self, graph, clz, example_name, base_example_name):
        fname = self.argp.graph_file_name.format(
            class_name=clz.__name__, example=example_name)
        path = pathlib.Path(fname)
        if self.argp.write_graph_files or self.argp.write_graph_svg_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            if self.argp.write_graph_svg_files:
                graph.write_svg(path, example_name)
            else:    
                graph.write(path, example_name)
        else:
            if not path.parent in self.set_mkdir and not path.parent.exists():
                self.set_mkdir.add(path.parent)
                sys.stderr.write(f'directory "{path.parent}" does not exist. Will be created.\n')
            strv = repr(graph)
            sys.stdout.write(
                f'Shape graph: {clz.__name__} {example_name} {len(strv)}\n')
        
    def invoke_render_examples(self):
        self.counts = render_examples(
            self.module, 
            self.options, 
            self.file_writer,
            self.graph_file_writer)
    
    def list_shapes(self):
        classes = find_all_shape_classes(self.module)
        for clz in classes:
            print(clz.__name__)
        
    def run_module(self):
                
        if self.argp.list_shapes:
            self.list_shapes()
        else:
            self.invoke_render_examples()
        
        sys.stderr.write(f'shapes: {self.counts[0]}\nexamples: {self.counts[1]}\n')

    def run(self):
        '''Renders the example shapes on the Shape classes found in the specified module.
        Note that by default, run() will exit the process.
        '''
        try:
            if not self.argp.write_files:
                sys.stderr.write(
                    f'Anchorscad example renderer running in (--no-write) mode.\n')
            if self.argp.module:
                self._load_anchorcad_module(self.argp.module)
            else:
                self.module = sys.modules['__main__']
                self.module_name = ''
            self.run_module()

        except BaseException as ex:
            if self.do_exit_on_completion:
                sys.stderr.write(f'{str(ex)}\nAnchorscad example renderer exiting with errors.')
                self.status= 3
            raise
        finally:
            if self.do_exit_on_completion:
                sys.exit(self.status) 
        
    
def anchorscad_main(do_exit_on_completion=None):
    '''Executes the standard command line runner for Anchorscad modules. 
    
    To use this function it is reccommended to place the following 2 lines at the end of the module.
        if __name__ == "__main__":
            Anchorscad.anchorscad_main()

    '''
    clr = ExampleCommandLineRenderer(sys.argv, do_exit_on_completion)
    clr.run()
    return clr.status


if __name__ == "__main__":
    anchorscad_main(False)
    
    
    