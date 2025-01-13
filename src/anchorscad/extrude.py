'''
Created on 7 Jan 2021

@author: gianni
'''

from collections.abc import Iterable
from abc import ABC, abstractmethod
from types import FunctionType
from typing import Any, Callable, Dict, List, Tuple, Union, overload

from frozendict import frozendict

import anchorscad.core as core
from datatrees import datatree, dtfield
from dataclasses import replace
import anchorscad_lib.linear as l
from anchorscad.path_utils import remove_colinear_points
import numpy as np
import traceback as tb
import numbers
import manifold3d as m3d


class DuplicateNameException(Exception):
    '''The name requested is already used.'''

class MoveNotAllowedException(Exception):
    '''Attempt to insert a move in a closed path.'''
    
class InvalidSplineParametersException(Exception):
    '''PathBuiler.spine requires 3 control points or 2 points and a length.'''
    
class IncorrectAnchorArgsException(Exception):
    '''Unable to interpret args.'''
    
class UnknownOperationException(Exception):
    '''Requested anchor is not found.'''
    
class UnableToFitCircleWithGivenParameters(Exception):
    '''There was no solution to the requested arc. Try a spline.'''
    
class TooFewPointsInPath(Exception):
    '''There were too few points in the given path.'''
    
class MultiplePathPolygonBuilderNotImplemented(Exception):
    '''Paths with multiple polygons are not implemented yet.'''
    
class PathElelementNotFound(Exception):
    '''The requested path element was not found.'''

class AzimuthNotPossibleOnSegment(Exception):
    '''The requested azimuth is not possible for given segment.'''
    
class OffsetOutOfRange(Exception):
    '''Path segment position with the offset is not possible for the geometry.'''
    
class CutCausedMultiplePathsUnimplemented(Exception):
    '''Cutting a path at the Y axis caused the path to split into more than 1.'''
    
class NameNotFoundException(Exception):
    '''The requested name was not found.'''


EPSILON=1e-6

POINT2=Union[Tuple[float, float], np.ndarray, l.GVector, List[float]]
NAME=Any

def strict_t_or_none(v, t):
    if v is None or v == 'None':
        return None
    
    if isinstance(v, str):
        raise TypeError(
            'Was provided a string value but expecting a numeric value or None.')
    return t(v)

def strict_int_or_none(v):
    return strict_t_or_none(v, int)

def strict_float_or_none(v):
    return strict_t_or_none(v, float)

def strict_angle_or_none(v):
    return strict_t_or_none(v, l.angle)

LIST_2_FLOAT_OR_NONE = l.list_of(strict_float_or_none, len_min_max=(2, 2), fill_to_min=None)
LIST_2_INT_OR_NONE = l.list_of(strict_float_or_none, len_min_max=(2, 2), fill_to_min=None)
LIST_2_ANGLE_OR_NONE = l.list_of(strict_angle_or_none, len_min_max=(2, 2), fill_to_min=None)
LIST_3_ANGLE_OR_NONE = l.list_of(strict_angle_or_none, len_min_max=(3, 3), fill_to_min=None)
LIST_2_FLOAT = l.list_of(l.strict_float, len_min_max=(2, 3), fill_to_min=0.0)
LIST_3_FLOAT = l.list_of(l.strict_float, len_min_max=(3, 3), fill_to_min=0.0)
LIST_2X2_FLOAT = l.list_of(LIST_2_FLOAT, len_min_max=(2, 2), fill_to_min=None)
LIST_3X2_FLOAT = l.list_of(LIST_2_FLOAT, len_min_max=(3, 3), fill_to_min=None)
LIST_23X2_FLOAT = l.list_of(LIST_2_FLOAT, len_min_max=(2, 3), fill_to_min=None)

def _vlen2(v):
    '''Returns the sqaure of the length of a vector.'''
    return np.sum(v**2)

def _vlen(v):
    '''Returns the length of a vector.'''
    return np.sqrt(np.sum(v**2))

def _normalize(v):
    d = _vlen(v)
    if d == 0:
        raise ValueError('Cannot normalize a zero length vector.')
    return v / d

def extentsof(p: np.ndarray) -> np.ndarray:
    return np.array((p.min(axis=0), p.max(axis=0)))


@datatree(frozen=True)
class CubicSpline():
    '''Cubic spline evaluator, extents and inflection point finder.'''
    p: object=dtfield(doc='The control points for the spline.')
    dimensions: int=dtfield(
        self_default=lambda s: len(s.p[0]),
        init=True, 
        doc='The number of dimensions in the spline.')
    
    COEFFICIENTS=np.array([
        [-1.,  3, -3,  1 ],
        [  3, -6,  3,  0 ],
        [ -3,  3,  0,  0 ],
        [  1,  0,  0,  0 ]])
    
    #@staticmethod # For some reason this breaks on Raspberry Pi OS.
    def _dcoeffs_builder(dims):
        zero_order_derivative_coeffs=np.array([[1.] * dims, [1] * dims, [1] * dims, [1] * dims])
        derivative_coeffs=np.array([[3.] * dims, [2] * dims, [1] * dims, [0] * dims])
        second_derivative=np.array([[6] * dims, [2] * dims, [0] * dims, [0] * dims])
        return (zero_order_derivative_coeffs, derivative_coeffs, second_derivative)
    
    DERIVATIVE_COEFFS = tuple((
        _dcoeffs_builder(1), 
        _dcoeffs_builder(2), 
        _dcoeffs_builder(3), ))
    
    def _dcoeffs(self, deivative_order):
        return self.DERIVATIVE_COEFFS[self.dimensions - 1][deivative_order]
        
    def __post_init__(self):
        object.__setattr__(self, 'coefs', np.matmul(self.COEFFICIENTS, self.p))
    
    def _make_ta3(self, t):
        t2 = t * t
        t3 = t2 * t
        ta = np.tile([t3, t2, t, 1], (self.dimensions, 1)).T
        return ta
        
    def _make_ta2(self, t):
        t2 = t * t
        ta = np.tile([t2, t, 1, 0], (self.dimensions, 1)).T
        return ta
    
    def evaluate(self, t):
        return np.sum(np.multiply(self.coefs, self._make_ta3(t)), axis=0)
  
    @classmethod
    def find_roots(cls, a, b, c, *, t_range: Tuple[float, float]=(0.0, 1.0)):
        '''Find roots of quadratic polynomial that are between t_range.'''
        # a, b, c are quadratic coefficients i.e. at^2 + bt + c
        if a == 0:
            # Degenerate curve is a linear. Only one possible root.
            if b == 0:
                # Degenerate curve is constant so there is no 0 gradient.
                return ()
            t = -c / b
            
            return (t,) if  t >= t_range[0] and t <= t_range[1] else ()
    
        b2_4ac = b * b - 4 * a * c
        if b2_4ac < 0:
            if b2_4ac > -EPSILON: # Could be a rounding error, so treat as 0.
                b2_4ac = 0
            else:
                # Complex roots - no answer.
                return ()
    
        sqrt_b2_4ac = np.sqrt(b2_4ac)
        two_a = 2 * a
    
        values = ((-b + sqrt_b2_4ac) / two_a, (-b - sqrt_b2_4ac) / two_a)
        return tuple(t for t in values if t >= t_range[0] and t <= t_range[1])
    
    # Solve for minima and maxima over t. There are two possible locations 
    # for each axis. The results for t outside of the bounds 0-1 are ignored
    # since the cubic spline is only interpolated in those bounds.
    def curve_maxima_minima_t(self, t_range: Tuple[float, float]=(0.0, 1.0)):
        '''Returns a dict with an entry for each dimension containing a list of
        t for each minima or maxima found.'''
        # Splines are defined only for t in the range [0..1] however the curve may
        # go beyond those points. Each axis has a potential of two roots.
        d_coefs = self.coefs * self._dcoeffs(1)
        return dict((i, self.find_roots(*(d_coefs[0:3, i]), t_range=t_range)) 
                    for i in range(self.dimensions))

    def curve_inflexion_t(self, t_range: Tuple[float, float]=(0.0, 1.0)):
        '''Returns a dict with an entry for each dimension containing a list of
        t for each inflection point found.'''
        # Splines are defined only for t in the range [0..1] however the curve may
        # go beyond those points. Each axis has a potential of two roots.
        d_coefs = self.coefs * self._dcoeffs(2)
        return dict((i, self.find_roots(0., *(d_coefs[0:2, i]), t_range=t_range))
                    for i in range(self.dimensions))
    
    def derivative(self, t):
        return -np.sum(
            np.multiply(
                np.multiply(self.coefs, self._dcoeffs(1)), self._make_ta2(t)), axis=0)
    
    def normal2d(self, t, dims=[0, 1]):
        '''Returns the normal to the curve at t for the 2 given dimensions.'''
        d = self.derivative(t)
        vr = np.array([d[dims[1]], -d[dims[0]]])
        d = np.sqrt(np.sum(vr**2))
        return vr / d
    
    def extremes(self):
        roots = self.curve_maxima_minima_t()
        t_values = [0.0, 1.0]
        for v in roots.values():
            t_values.extend(v)
        t_values.sort()
        return np.array(tuple(self.evaluate(t) for t in t_values if t >= 0 and t <= 1))
    
    def extents(self):
        extr = self.extremes()
        return extentsof(extr)
    
    def transform(self, m: l.GMatrix) -> 'CubicSpline':
        '''Returns a new spline transformed by the matrix m.'''
        new_p = list((m * to_gvector(p)).A[0:self.dimensions] for p in self.p)
        return CubicSpline(np.array(new_p), self.dimensions)
    
    
    def azimuth_t(self, angle: Union[float, l.Angle]=0, t_end: bool=False, 
                t_range: Tuple[float, float]=(0.0, 1.0)) -> Tuple[float, ...]:
        '''Returns the list of t where the tangent is at the given angle from the beginning of the
        given t_range. The angle is in degrees or Angle.'''
        
        angle = l.angle(angle)
        
        start_slope = self.normal2d(t_range[1 if t_end else 0])
        start_rot: l.GMatrix = l.rotZ(sinr_cosr=(start_slope[1], -start_slope[0]))
        
        qs: CubicSpline = self.transform(l.rotZ(angle.inv()) * start_rot)
        
        roots = qs.curve_maxima_minima_t(t_range)

        return sorted(roots[0])


@datatree(frozen=True)
class QuadraticSpline():
    '''Quadratic spline evaluator, extents and inflection point finder.'''
    p: object=dtfield(doc='The control points for the spline.')
    dimensions: int=dtfield(
        self_default=lambda s: len(s.p[0]),
        init=True, 
        doc='The number of dimensions in the spline.')
    
    COEFFICIENTS=np.array([
        [  1., -2,  1 ],
        [ -2.,  2,  0 ],
        [  1.,  0,  0 ]])
    
    #@staticmethod # For some reason this breaks on Raspberry Pi OS.
    def _dcoeffs_builder(dims):
        zero_order_derivative_coeffs=np.array([[1.] * dims, [1] * dims, [1] * dims])
        derivative_coeffs=np.array([[2] * dims, [1] * dims, [0] * dims])
        second_derivative=np.array([[2] * dims, [0] * dims, [0] * dims])
        return (zero_order_derivative_coeffs, derivative_coeffs, second_derivative)
    
    DERIVATIVE_COEFFS = tuple((
        _dcoeffs_builder(1), 
        _dcoeffs_builder(2), 
        _dcoeffs_builder(3), ))
    
    def _dcoeffs(self, deivative_order):
        return self.DERIVATIVE_COEFFS[self.dimensions - 1][deivative_order]
        
    def __post_init__(self):
        object.__setattr__(self, 'coefs', np.matmul(self.COEFFICIENTS, self.p))
    
    def _qmake_ta2(self, t):
        ta = np.tile([t**2, t, 1], (self.dimensions, 1)).T
        return ta
        
    def _qmake_ta1(self, t):
        ta = np.tile([t, 1, 0], (self.dimensions, 1)).T
        return ta
    
    def evaluate(self, t):
        return np.sum(np.multiply(self.coefs, self._qmake_ta2(t)), axis=0)
    
    @classmethod
    def find_roots(cls, a, b, *, t_range: Tuple[float, float]=(0.0, 1.0)):
        '''Find roots of linear equation that are between t_range.'''
        # There either 1 or no roots.
        if a == 0:
            # Degenerate curve is constant so there is no 0 gradient.
            return ()
        
        # Only return the root if it is within the range.
        t = -b / a
        return (t,) if  t >= t_range[0] and t <= t_range[1] else ()

    # Solve for minima and maxima over t. There are two possible locations 
    # for each axis. The results for t outside of the bounds 0-1 are ignored
    # since the cubic spline is only interpolated in those bounds.
    def curve_maxima_minima_t(self, t_range: Tuple[float, float]=(0.0, 1.0)):
        '''Returns a dict with an entry for each dimension containing a list of
        t for each minima or maxima found.'''
        # Splines are defined only for t in the range [0..1] however the curve may
        # go beyond those points. Each axis has a potential of two roots.
        d_coefs = self.coefs * self._dcoeffs(1)
        return dict((i, self.find_roots(*(d_coefs[0:2, i]), t_range=t_range)) 
                    for i in range(self.dimensions))

    def curve_inflexion_t(self, t_range: Tuple[float, float]=(0.0, 1.0)):
        '''Returns a dict with an entry for each dimension containing a list of
        t for each inflection point found.'''
        
        # Quadradic splines have no inflection points since their second order
        # derivative is constant.
        return dict((i, ()) for i in range(self.dimensions))
    
    def derivative(self, t):
        return -np.sum(
            np.multiply(
                np.multiply(self.coefs, self._dcoeffs(1)), self._qmake_ta1(t)), axis=0)
    
    def normal2d(self, t, dims=[0, 1]):
        '''Returns the normal to the curve at t for the 2 given dimensions.'''
        d = self.derivative(t)
        vr = np.array([d[dims[1]], -d[dims[0]]])
        d = np.sqrt(np.sum(vr**2))
        return vr / d
    
    def extremes(self):
        roots = self.curve_maxima_minima_t()
        t_values = [0.0, 1.0]
        for v in roots.values():
            t_values.extend(v)
        t_values.sort()
        return np.array(tuple(self.evaluate(t) for t in t_values if t >= 0 and t <= 1))
    
    def extents(self):
        extr = self.extremes()
        return extentsof(extr)
    
    def transform(self, m: l.GMatrix) -> 'QuadraticSpline':
        '''Returns a new spline transformed by the matrix m.'''
        new_p = list((m * to_gvector(p)).A[0:self.dimensions] for p in self.p)
        return QuadraticSpline(np.array(new_p), self.dimensions)
    
    def azimuth_t(self, angle: float | l.Angle=0, t_end: bool=False, 
                t_range: Tuple[float, float]=(0.0, 1.0)) -> Tuple[float, ...]:
        '''Returns the list of t where the tangent is at the given angle from the beginning of the
        given t_range. The angle is in degrees or Angle.'''
        
        angle = l.angle(angle)
        
        start_slope = self.normal2d(t_range[1 if t_end else 0])
        start_rot: l.GMatrix = l.rotZ(sinr_cosr=(-start_slope[1], start_slope[0]))
        
        qs: QuadraticSpline = self.transform(angle.inv().rotZ * start_rot)
        
        roots = qs.curve_maxima_minima_t(t_range)

        return sorted(roots[0])


def _normal_of_2d(v1, v2, dims=[0, 1]):
    vr = np.array(v1)
    vr[dims[0]] = v1[dims[1]] - v2[dims[1]]
    vr[dims[1]] = v2[dims[0]] - v1[dims[0]]
    d = np.sqrt(np.sum(vr * vr))
    return vr / d

def adder(a, b):
    if a is None:
        return None
    if b is None:
        return a
    return a + b

def _traceback(trace_level: int=5) -> tb.FrameSummary:
    '''Returns the frame summary for the frame_no.'''
    return tb.extract_stack(limit=trace_level)[1 - trace_level]


@datatree(frozen=True, provide_override_field=False)
class OpBase(ABC):
    '''Base class for path operations (move, line, arc and spline).
    '''
    # Implementation state should consist of control points that can be easily 
    # transformed via a matrix multiplication.
    
    trace: tb.FrameSummary=dtfield(
        default_factory=_traceback, 
        repr=False,
        compare=False)
    
    def _as_non_defaults_dict(self):
        return dict((k, getattr(self, k)) 
                    for k in self.__annotations__.keys() 
                        if getattr(self, k) is not None and k != 'prev_op')
        
    def is_move(self):
        return False
    
    def render_as_svg(self, svg_model):
        raise NotImplementedError('Derived class must implement this.')
    
    def get_centre(self):
        '''Returns the centre of the operation, if the operation has a centre.'''
        return None

    def azimuth_t(self, angle: Union[float, l.Angle]=0, t_end: bool=False, 
                t_range: Tuple[float, float]=(0.0, 1.0)) -> Tuple[float, ...]:
        # Base implementation defaults to not having an azimuth.
        return None
    
    def position(self, t: float, apply_offset: bool=True):
        '''Returns the position of the operation at t with the offset applied.'''
        base_pos = self.base_position(t)
        if apply_offset:
            offset: float = self.get_offset()
            if not offset:
                return self.base_position(t)
            d = self.direction_normalized(t)
            n = np.array([d[1], -d[0]])
            return base_pos + n * offset
        return base_pos
    
    @abstractmethod
    def lastPosition(self) -> np.ndarray:
        '''Returns the end (t=1) position of the operation.'''
        pass
    
    @abstractmethod
    def base_position(self, t: float) -> np.ndarray:
        '''Returns the pre offset position of the operation at t.'''
        pass
    
    @abstractmethod
    def direction_normalized(self, t: float) -> np.ndarray:
        '''Returns the direction of the operation at t.'''
        pass
    
    @abstractmethod
    def transform(self, m : l.GMatrix) -> 'OpBase':
        '''Returns a new operation transformed by the matrix m.'''
        pass
    
    def apply_modifier(self, path_modifier: 'PathModifier', next_op: 'OpBase') -> 'OpBase':
        '''Returns a new operation with the modifier applied.'''
        
        return replace(self, path_modifier=path_modifier)
    
    def get_offset(self):
        '''Returns the offset of the operation.'''
        if self.path_modifier is None:
            return 0.0
        return self.path_modifier.offset
    
    @abstractmethod
    def extremes(self) -> np.array:
        pass
    

@datatree
class OpMetaData():
    '''The Op and parameters used to generate the point.'''
    op: OpBase
    point: tuple
    count: int=None
    t: float=None
    dupe_ops_md: list=dtfield(default_factory=list, init=False)

    
@datatree()
class MapBuilder:
    '''Builder for a map of points to the OpMetaData associated with the point.'''
    opmap: List[OpMetaData]=dtfield(default_factory=list)
    
    def append(self, op: OpBase, point: tuple, count: int=None, t: float=None):
        self.opmap.append(OpMetaData(op, point, count, t))


@datatree()
class NullMapBuilder:
    '''A null builder'''
    opmap: List[OpMetaData]=None
    
    def append(self, op: OpBase, point: tuple, count: int=None, t: float=None):
        pass


@datatree(frozen=True)
class JoinType:
    '''The type of offset to apply.'''
    join_type: int


@datatree(frozen=True)
class PathModifier:
    '''A modifier for a path. This is used to provide an calculate anchors.'''
    
    OFFSET_ROUND=JoinType(m3d.JoinType.Round)
    OFFSET_MITRE=JoinType(m3d.JoinType.Miter)
    OFFSET_SQUARE=JoinType(m3d.JoinType.Square)
    
    offset: float=0.0
    join_type: JoinType=dtfield(OFFSET_ROUND, doc='The type of joins to apply.')
    mitre_limit: float=dtfield(2, doc='The miter limit for the offset.')
    circular_segments: int=dtfield(
        8, 
        doc='The number of circular segments to use for the offset. meta_data.fn is used if None.')
    trim_negx: bool=dtfield(False, doc='Trim the parts of the path that have negative X.')
    
    def add_offset(self, offset: float) -> 'PathModifier':
        return replace(self, offset=self.offset + offset)
    
    def round(self) -> 'PathModifier':
        return replace(self, join_type=self.OFFSET_ROUND)
    
    def mitre(self) -> 'PathModifier':
        return replace(self, join_type=self.OFFSET_MITRE)
    
    def square(self) -> 'PathModifier':
        return replace(self, join_type=self.OFFSET_SQUARE)
    
    def segments(self, segments: int) -> 'PathModifier':
        return replace(self, circular_segments=segments)
    
    @classmethod
    def with_offset(cls, offset: float) -> 'PathModifier':
        return PathModifier(offset=offset)
    
    @classmethod
    def with_segments(cls, circular_segments: int) -> 'PathModifier':
        return PathModifier(circular_segments=circular_segments)
    
    @classmethod
    def as_round(cls) -> 'PathModifier':
        return PathModifier(join_type=cls.OFFSET_ROUND)
    
    @classmethod
    def as_mitre(cls) -> 'PathModifier':
        return PathModifier(join_type=cls.OFFSET_MITRE)
    
    @classmethod
    def as_square(cls) -> 'PathModifier':
        return PathModifier(join_type=cls.OFFSET_SQUARE)


MISSING_PATH_MODIFIER = object()


def _eval_overlapping_range(a, b, tolerance=EPSILON):
    '''Returns the range of a that overlaps with b. The ranges may be directional,
    i.e. a may be [0, 10] or [10, 0] and are identical.'''
    
    a = a if a[0] < a[1] else (a[1], a[0])
    b = b if b[0] < b[1] else (b[1], b[0])
    
    # If the ranges do not overlap then return None.
    if b[0] + tolerance > a[1] or b[1] < a[0] + tolerance:
        return None

    return (max(a[0], b[0]), min(a[1], b[1]))   

def _eval_removed_range(base_range: np.ndarray, remove_range: np.ndarray, tolerance=EPSILON) -> Tuple[np.ndarray]:
    '''Returns 0, 1 or 2 ranges that are the result of removing the remove_range from
    the base_range.
    The ranges must overlap or touch.
    If the remove range is None or smaller than the tolerance then the base range is returned.
    '''
    
    if remove_range is None or np.abs(remove_range[0] - remove_range[1]) < tolerance:
        return (base_range,)
    
    # If the start of the ranges is the same:
    if np.abs(remove_range[0] - base_range[0]) < tolerance:
        # if the end of the remove range is the same or greater than the base range
        if remove_range[1] - base_range[1] > -tolerance:
            return ()  # Nothing remains.
        # The remove range is inside the base range.
        return (np.array((remove_range[1], base_range[1])),)
        
    # If the end of the ranges is the same:
    if np.abs(remove_range[1] - base_range[1]) < tolerance:
        # The remove range is inside the base range.
        return (np.array((base_range[0], remove_range[0])),)
    
    return (np.array((base_range[0], remove_range[0])),
                np.array((remove_range[1], base_range[1])))

   
@datatree
class Segment:
    points: List[np.ndarray]  # 2 points
    
    def __init__(self, points: List[np.ndarray]):
        self.points = np.array(LIST_2_FLOAT(points))

    def isparallel(self, other: 'Segment', tolerance=EPSILON):
        '''Returns true if the two segments are parallel.'''
        v1 = self.points[1] - self.points[0]
        v2 = other.points[1] - other.points[0]
        cross = v1[0]*v2[1] - v1[1]*v2[0]
        return np.abs(cross) < tolerance
    
    def iscolinear(self, other: 'Segment', tolerance=EPSILON):
        '''Returns true if the two segments are colinear.'''
        return self.isparallel(other, tolerance) and self.ispointon(other.points[0], tolerance)
    
    def ispointon(self, point: np.ndarray, tolerance=EPSILON):
        '''Returns true if the point is on the segment.'''
        v1 = self.points[1] - self.points[0]
        v2 = point - self.points[0]
        cross = v1[0]*v2[1] - v1[1]*v2[0]
        return np.abs(cross) < tolerance
        
    def rebuild_segment(self, 
            ranges: List[np.ndarray], direction: np.ndarray, origin: np.ndarray) -> 'Segment':
        '''Returns a new segment that is the range of this segment.'''
        if not ranges:
            return None # No range left.
        
        assert len(ranges) == 1, 'Merge of ranges not implemented yet.'
        
        range = ranges[0]
        
        points = [origin + direction * range[0], origin + direction * range[1]]
        
        return Segment(points)
        
    
    def _remove_coincidence(self, other: 'Segment') -> Tuple['Segment', 'Segment']:
        '''Removes the coincident part of the segments. This assumes they are colinear'''
        # The vector referenced to the start of this segment.
        v = self.points[1] - self.points[0]
        v_len = _vlen(v)
        v_dir = v / v_len
        
        # The start and ends of the last segment which may overlap.
        w = other.points - self.points[0]
    
        other_range = np.dot(w, v_dir)
        self_range = np.array([0.0, v_len])
        overlapping_range = _eval_overlapping_range(self_range, other_range)
        
        self_remaining = _eval_removed_range(self_range, overlapping_range)
        other_remaining = _eval_removed_range(other_range, overlapping_range)
        
        new_self = self.rebuild_segment(self_remaining, v_dir, self.points[0])
        new_other = self.rebuild_segment(other_remaining, v_dir, self.points[0])
        
        return new_self, new_other
    
    def remove_colinear_segment(self, other: 'Segment', tolerance=EPSILON):
        '''Return a replacement set of segments.'''
        
        # if the segments are not colinear, then no change is needed.
        if not self.iscolinear(other, tolerance):
            return self, other
        
        segments = self._remove_coincidence(other)
        
        return segments


def clean_polygons(points: np.ndarray, colinear_remove: bool, tolerance=EPSILON) -> np.ndarray:
    '''Returns a cleaned polygon. Removes colinear segments.'''
    if colinear_remove:
        points = remove_colinear_points(points, tolerance)
    
    last_len = 0
    
    # Remove colinear segments until there are no more to remove.
    while len(points) != last_len:
        
        last_len = len(points)
        if last_len < 3:
            return points
        
        last = Segment(points[-2:][::-1])
        first = Segment(points[:2])

        new_first, new_last = first.remove_colinear_segment(last)
        
        if not new_first:
            points = points[1:]
        else:
            points[0:2] = new_first.points
            
        if not new_last:
            points = points[:-1]
        else:
            points[-2:] = new_last.points[::-1]
            
        if colinear_remove:
            points = remove_colinear_points(points, tolerance)

    # Remove the last point if it is almost the same as the first.
    if np.abs(np.sum(points[0] - points[-1])) < tolerance:
        points = points[:-1]

    return points

@datatree
class MappedPolygon:
    '''A polygon with a map of points to the OpMetaData associated with the point.'''
    path: 'Path'
    meta_data: core.ModelAttributes
    map_builder_type: FunctionType=NullMapBuilder
    epsilon: float=EPSILON
    points: np.ndarray=dtfield(init=False)
    ranges: np.ndarray=dtfield(init=False)
    opmap: List[OpMetaData]=dtfield(init=False)
    cleaned_polygons: np.ndarray=dtfield(default=None, init=False)
    
    def __post_init__(self):
        self.points, self.ranges, self.opmap = self.path.polygons_with_map_ops(
            self.meta_data,
            map_builder_type=self.map_builder_type)
    
    def cleaned(self, tolerance=EPSILON):
        '''Returns a cleaned polygon. Removes colinear segments. If colinear_remove
        is False and removes overlappiing end segments.'''
        
        if self.cleaned_polygons is not None:
            return self.cleaned_polygons
    
        if not self.ranges:
        
            # Only remove colinear points if there is no request to segment lines.
            colinear_remove = not self.meta_data.segment_lines
            
            self.cleaned_polygons = clean_polygons(
                self.points, colinear_remove, tolerance=tolerance)
            
            return self.cleaned_polygons
        
        return self.points


@datatree
class _Segment:
    points: List[np.ndarray]  # 2D points
    start_idx: int = -1
    end_idx: int= -1

    IS_START = True
    
    def val(self):
        return self.points[0]
    
    def other_end_val(self):
        return self.points[-1]
    
    def set_idx(self, idx):
        self.start_idx = idx
        
    def set_end_idx(self, idx):
        self.end_idx = idx
        
    def segment(self) -> '_Segment':
        return self


@datatree
class _EndSegment:
    segment: Segment
    
    IS_START = False 
    
    def val(self):
        return self.segment.other_end_val()       
    
    def other_end_val(self):
        return self.segment.val()
    
    def set_idx(self, idx):
        self.segment.set_end_idx(idx)
        
    def segment(self) -> _Segment:
        return self.segment
        

@datatree(frozen=True)
class Path():
    '''Encapsulated a "path" generate by a list of path "Op"s (move, line, arc etc).
    Each move op indicates a separate path. This can be a hole (anticlockwise) or a
    polygon (clockwise).
    A Path can generate a polygon with a differing number of facets or extents 
    (bounding box) or can be transformed into another path using a [ad.GMatrix].
    
    '''
    ops: Tuple[OpBase, ...]
    name_map: Dict[str, OpBase]  # frozendict
    path_modifier: PathModifier=dtfield(default=None)
    constructions: List['Construction']=dtfield(default=None)

    def get_node(self, name):
        return self.name_map.get(name, None)
    
    def get_centre_of(self, name):
        node = self.get_node(name)
        if not node:
            raise PathElelementNotFound(f'Unable to find path element: {name}')
        return node.get_centre()
    

    def azimuth_t(self, name, angle: float | l.Angle=0, t_end: bool=False, 
                t_range: Tuple[float, float]=(0.0, 1.0)) -> Tuple[float, ...]:
        '''Returns the list of t where the tangent is at the given angle changed
        from the beginning of the given t_range.
        Args:
            name: The name of the path element.
            angle: The angle (in degrees or l.Angle) which it is desired to find the t.
            t_end: If True then the angle is measured from the end of the segment.
            t_range: The range of t to search for the t value that matches the angle.
        '''
        
        node = self.get_node(name)
        if not node:
            raise PathElelementNotFound(f'Unable to find path element named: "{name}"')
        return node.azimuth_t(angle, t_end, t_range)
    
    def extents(self, include_constructions: bool=True):
        itr = iter(self.ops)
        extnts = extentsof(next(itr).extremes())
        for op in itr:
            ops_extremes = op.extremes()
            cated = np.concatenate((ops_extremes, extnts))
            extnts = extentsof(cated)
            
        if include_constructions and self.constructions:
            for c in self.constructions:
                c_extnts = c.extremes()
                cated = np.concatenate((c_extnts, extnts))
                extnts = extentsof(cated)

        return extnts
    
    def build(self, meta_data, map_builder_type=None):
        path_builder = []
        start_indexes = []
        map_builder = map_builder_type() if map_builder_type else NullMapBuilder()
        for op in self.ops:
            op.populate(path_builder, start_indexes, map_builder, meta_data)
        return (np.array(path_builder), start_indexes, map_builder)
    
    def points(self, meta_data):
        points, _, _ = self.build(meta_data)
        return points

    def polygons_with_map_ops(self, meta_data, map_builder_type=None):
        points, start_indexes, map_ops = self.build(
            meta_data, map_builder_type=map_builder_type)
        if len(start_indexes) == 1:
            return (points, None, map_ops.opmap)
        
        start_ranges = []
        # Close paths.
        for i in range(len(start_indexes)):
            start_point = start_indexes[i] - 1
            if i + 1 < len(start_indexes):
                end_point = start_indexes[i + 1] - 2
            else:
                end_point = len(points) - 1
            extra_point = ()
            if _vlen(points[start_point] - points[end_point]) > EPSILON:
                extra_point = (start_point,)
            start_ranges.append(tuple(range(start_point, end_point + 1)) + extra_point)
        return (points, tuple(start_ranges), map_ops.opmap)
    
    def polygon_with_maps(self, meta_data):
        return self.polygons_with_map_ops(
            meta_data, map_builder_type=MapBuilder)
    
    def polygons(self, meta_data, map_builder_type=None):
        points, ranges, _ = self.polygons_with_map_ops(meta_data, map_builder_type)
        if ranges:
            return points, ranges
        return (points,)
    
    def cleaned_polygons(self, meta_data, map_builder_type=None):
        points, ranges, _ = self.polygons_with_map_ops(meta_data, map_builder_type)
        if ranges:
            return points, ranges
        
        # Only remove colinear points if there is no request to segment lines.
        colinear_remove = not meta_data.segment_lines
        
        points = clean_polygons(points, colinear_remove)
        
        if self.path_modifier and self.path_modifier.offset != 0:
            
            cs = m3d.CrossSection([points])
            offset = self.path_modifier.offset
            
            if cs.is_empty():
                # AnchorSCAD Paths may be incorrectly ordered. Manifold3D requires a correct order
                # otherise it will return an empty cross section since it is deemed to be a hole.
                # TODO: Fix AnchorSCAD to handle multiple paths correctly.
                cs = m3d.CrossSection([points[0][::-1]])
                assert not cs.is_empty(), 'Empty cross section should not happen.'
            
            num_segments = meta_data.fn \
                if self.path_modifier.circular_segments is None \
                else self.path_modifier.circular_segments
                
            if not num_segments:
                num_segments = 8
                
            # This is where we call the manifold/clipper2 offset function.
            offset_cs = cs.offset(
                offset, 
                self.path_modifier.join_type.join_type, 
                miter_limit=self.path_modifier.mitre_limit, 
                circular_segments=num_segments)
            
            # Remove the negative parts of the offset. This is a workaround for the
            # when doing a RotateExtrude and the offset caused the path to cross the
            # Y axis.
            if self.path_modifier.trim_negx:
                offset_cs = self._trim_negx(offset_cs)
            
            points = offset_cs.to_polygons()
            
            return points
        
        if self.path_modifier and self.path_modifier.trim_negx:
            cs = m3d.CrossSection([points])
            if cs.is_empty():
                cs = m3d.CrossSection([points[::-1]])
            cs = self._trim_negx(cs)
                
            return cs.to_polygons()

        return (points,)
    
    def _trim_negx(self, cs: m3d.CrossSection):
        min_x, min_y, max_x, max_y = cs.bounds()
        
        if min_x < 0:
            sq = m3d.CrossSection.square([-min_x + EPSILON, max_y - min_y + EPSILON])
            sqt = sq.translate([min_x - EPSILON, min_y - EPSILON / 2])
            result_cs = cs - sqt
            
            return result_cs
        
        return cs
    
    def svg_path_render(self, svg_model):
        for op in self.ops:
            op.render_as_svg(svg_model)
        
        with svg_model.construction() as csvg_model:
            for c in self.constructions:
                for op in c.ops:
                    op.render_as_svg(csvg_model)

    def transform_to_builder(self, 
                             m: l.GMatrix, 
                             builder: Union['PathBuilder', None]=None, 
                             suffix: Any=None, 
                             appender: Callable[[Any, Any], Any]=adder,
                             skip_first_move: bool=None,
                             offset: float=None,
                             include_constructions: bool=True,
                             metadata: core.ModelAttributes=None) -> 'PathBuilder':
        '''Returns a PathBuilder with the new transformed path.
        Args:
          m: A GMatrix to transform the points.
          builder: Optional builder to append path to.
          suffix: Names from this path are suffixed by this.
          appender: Function to perform appending. Default is adder.
          skip_first_move: Skips the first move operation.
        '''
        if builder is None:
            skip_first_move = False if skip_first_move is None else skip_first_move
            path_modifier = None
            if self.path_modifier:
                if offset:
                    path_modifier = self.path_modifier.add_offset(offset)
            elif offset:
                path_modifier = PathModifier.with_offset(offset)
            else:
                skip_first_move = True if skip_first_move is None else skip_first_move
                
            if metadata and metadata.fn:
                path_modifier = path_modifier.segments(metadata.fn) \
                    if path_modifier \
                    else PathModifier.segments(metadata.fn)
            
            builder = PathBuilder(path_modifier=path_modifier)
        
        # Perform skip on first op if it is a move.
        iterops = iter(self.ops)
        if skip_first_move:
            try:
                op = next(iterops)
                if not op.is_move():
                    builder.add_op_with_params(
                        op.transform(m), appender(op.name, suffix), trace=op.trace)
            except StopIteration:
                pass
        
        for op in iterops:
            builder.add_op_with_params(
                op.transform(m), 
                appender(op.name, suffix), 
                path_modifier=builder.get_path_modifier(),
                trace=op.trace)
            
            
        if include_constructions and self.constructions:
            for c in self.constructions:
                with builder.construction() as cb:
                    cb.add_transformed(c, m, suffix, appender, offset, metadata)
                
        return builder
            
    def transform(
        self, m: l.GMatrix=l.IDENTITY, offset: float=None,
        metadata: core.ModelAttributes=None) -> 'Path':
        '''Returns a new Path but transformed by m with offset path modifier.'''
        return self.transform_to_builder(m=m, offset=offset, metadata=metadata).build()


def to_gvector(np_array):
    if len(np_array) == 2:
        return l.GVector([np_array[0], np_array[1], 0, 1])
    else:
        return l.GVector(np_array)
    
    
# Solution derived from https://planetcalc.com/8116/
def solve_circle_3_points(
    p1: POINT2, p2: POINT2, p3: POINT2) -> Tuple[np.ndarray, float]: 
    '''Returns the centre and radius of a circle that passes the 
    3 given points or tuple of (None, None) if the points are colinear.'''
    
    p = np.array([p1[0:2], p2[0:2], p3[0:2]])
    
    m = np.array([
        np.concatenate((p[0] * 2, [1])),
        np.concatenate((p[1] * 2, [1])),
        np.concatenate((p[2] * 2, [1]))
        ])

    try:
        mi = np.linalg.inv(m)
    except np.linalg.LinAlgError:
        return (None, None)
    
    v1 = -np.sum(p **2, axis=1)
    
    abc = np.matmul(mi, v1)
    centre = -abc[0:2]
    radius = np.sqrt(np.sum(centre **2) - abc[2])
    
    return (centre, radius)

def find_a_b_c_from_point_tangent(p, t):
    '''Given a point and direction of a line (t) compute the parameter (a, b, c) for the line:
    described by ax + by = c. Returns [a, b, c], p (as an numpy array) and t but also  normalized 
    (in both length and direction).
    '''
    p = np.array(p)
    t = np.array(t)
    tn = t / _vlen(t)
     
    a = tn[1]
    b = -tn[0]
    c = np.linalg.det([p, tn])
    
    d = np.array([a, b, c])
    if a < 0:
        d = -d
    elif a == 0 and b < 0:
        d = -d
        
    return d, p, t

def find_2d_line_intersection(l1, l2):
    '''Finds the point of intersection of l1 and l2. l1 and l2 are 3x1 quantities
    defined by [a, b, c] where ax + by = c defines the line.
    [a, b] should be normalized (vector length = 1).
    Returns the point of intersection, 0 if the lines are parallel or 1 if the lines are
    identical.
    Derived from the use of Cramer's rule.:
    https://math.libretexts.org/Bookshelves/Precalculus/Book%3A_Precalculus_(OpenStax)/\
    09%3A_Systems_of_Equations_and_Inequalities/9.08%3A_Solving_Systems_with_Cramer's_Rule
    '''
    m = np.array([l1[0:2], l2[0:2]])
    d = np.linalg.det(m)
    mT = np.transpose(m)
    
    if np.abs(d) < EPSILON:
        # if the c values are the same then the normals are the same line meaning that
        # the lines are colinear. If the c values are the same, then the lines are identical.
        if np.abs(l1[2] - l2[2]) < EPSILON:
            # lines are identical.
            return ('identical')
        else:
            return ('parallel')
    else:
        cn = np.array([l1[2], l2[2]])
        return np.array([np.linalg.det([cn, mT[1]]) / d, np.linalg.det([mT[0], cn]) / d])

def solve_circle_tangent_point(p1, t1, p2):
    '''Returns the (centre, radius) tuple of the circle whose tangent is p1, t1 second
    point is p2.'''
    # The centre must lie in the perpendicular to the tangent.
    l1, p1, tn1 = find_a_b_c_from_point_tangent(p1, [-t1[1], t1[0]])
    
    # The second line is defined by keeping the centre equidistant from p1 and p2
    # i.e.
    # len(p1-C) == len(p2-c)
    a = 2 * (p2[0] - p1[0])
    b = 2 * (p2[1] - p1[1])
    c = p2[0]**2 - p1[0]**2 + p2[1]**2 - p1[1]**2
    
    l2 = np.array([a, b, c])
    l2 = l2 / (np.sign(a if a != 0 else b) * _vlen(l2[0:2]))
    
    centre = find_2d_line_intersection(l1, l2)
    if isinstance(centre[0], str):
        return (None, None)
    
    radius = np.sqrt(np.sum((centre - p1) ** 2))
    return (centre, radius)

def solve_circle_tangent_radius(p, t, r, side=True):
    '''Finds the centre of the circle described by tangent, radius and side of line.
    Returns (centre, radius)'''
    p = np.array(p)
    t = np.array(t)
    tn = _normalize(t)
    r_side = r if side else -r
    centre = p + r_side * np.array([-tn[1], t[0]])
    return (centre, r)

def solve_circle_points_radius(p1, p2, r, left=True):
    '''Finds the centre of the circle described by a start and end points, radius and placement
    of centre.
    Returns (centre, radius)'''
    p1 = np.array(p1)
    p2 = np.array(p2)
    pd = p2 - p1
    leng = _vlen(pd) / 2
    pdn = pd / (2 * leng)
    if leng > r:
        return (None, None)
    if np.abs(leng - r) < EPSILON:
        centre = (p1 + p2) / 2
        return (centre, r)
    opp_side = np.sqrt(r**2 - leng **2)
    if left:
        dire = np.array([-pdn[1], pdn[0]]) #+90 degrees
    else:
        dire = np.array([pdn[1], -pdn[0]]) #-90 degrees
    centre = (p1 + p2) / 2 + dire * opp_side
    return (centre, r)

def _less_than(a, b):
    return (a - b) < EPSILON

def _greater_than(a, b):
    return (a - b) > EPSILON

@datatree()
class CircularArc:
    start_angle: float  # Angles in radians
    sweep_angle: float  # Angles in radians
    radius: float
    centre: np.array
    
    def derivative(self, t):
        '''Returns the derivative (direction of the curve at t).'''
        angle = t * self.sweep_angle + self.start_angle
        # Derivative direction depends on sense of angle.
        d = 1 if self.sweep_angle < 0 else -1
        return np.array([np.sin(angle), -np.cos(angle)]) * d
    
    def normal2d(self, t):
        '''Returns the normal to the curve at t.'''
        ddt = self.derivative(t)
        return np.array([-ddt[1], ddt[0]])
    
    def extremes(self):
        result = [self.evaluate(0.0), self.evaluate(1.0)]
        swa = self.sweep_angle
        angle_dir = 1. if swa >= 0 else -1.
        
        sa = self.start_angle
        ea = sa + self.sweep_angle
        sai = sa * 2 / np.pi
        eai = ea * 2 / np.pi
        
        end_test = _less_than if angle_dir > 0 else _greater_than
        ai = np.ceil(sai) if angle_dir > 0 else np.floor(sai)
        if np.abs(ai - sai) < EPSILON:
            ai += angle_dir
        r = self.radius
        count = 0
        while end_test(ai, eai) and count < 4:
            angle = ai * (np.pi / 2)
            result.append(
                r * np.array([np.cos(angle), np.sin(angle) ]) + self.centre)
            count += 1
            ai += angle_dir

        return result
    
    def extents(self) -> np.array:
        return extentsof(self.extremes())

    def evaluate(self, t: float, offset: float=0.0) -> np.array:
        radius = self.radius + offset
        if radius < 0: 
            # Negative radius is invalid. This segment shrank away and no longer provides
            # a point in the path.
            raise OffsetOutOfRange(
                f'Arc radius={self.radius} offset={offset} new radius={radius} is negative.')
        angle = t * self.sweep_angle + self.start_angle
        return np.array([np.cos(angle), np.sin(angle)]) * radius + self.centre
    
    def azimuth_t(self, angle: Union[float, l.Angle]=0, t_end: bool=False, 
                  t_range: Tuple[float, float]=(0.0, 1.0)) -> Tuple[float, ...]:
        
        radians = l.angle(angle).radians()
        swa = self.sweep_angle * (t_range[1] - t_range[0])

        t = t_range[1] + radians / swa if t_end else t_range[0] + radians / swa

        if t < t_range[0] or t > t_range[1]:
            return ()
        
        return (t,)

def optional_arrayeq(ary1, ary2):
    if ary1 is None:
        return ary2 is None
    return np.array_equal(ary1, ary2)


class PathBuilderPrimitives(ABC):
    '''The public interface for path builder primitives. This is used for building
    constructions as well as the path segments. PathBuilder uses this interface as 
    well as the _ConstructionBuilder.'''
    
    @abstractmethod
    def construction(self) -> '_Construction':
        '''Returns a new construction builder.'''
        pass

    @abstractmethod
    def last_op(self) -> OpBase:
        '''Returns the last operation.'''
        pass
    
    @abstractmethod
    def add_op(self, op: OpBase) -> 'PathBuilderPrimitives':
        '''Adds an operation to the path.'''
        pass
    
    @abstractmethod
    def is_multi_path(self) -> bool:
        '''Returns True if the builder allows multiple paths.'''
        pass
    
    @abstractmethod
    def get_path_modifier(self) -> PathModifier:
        '''Returns the path modifier.'''
        pass

    @abstractmethod
    def get_op(self, name) -> Union[OpBase, None]:
        '''Returns the op with the given.'''
        pass

    @datatree(frozen=True)
    class _LineTo(OpBase):
        '''Line segment from current position.'''
        point: np.array=None,
        prev_op: OpBase=dtfield(
            default=None,
            repr=False, 
            hash=False, 
            compare=False)
        name: str=None
        direction_override: np.array=None
        direction_norm: np.array=None
        meta_data: object=None
        path_modifier: 'PathModifier'=dtfield(default=MISSING_PATH_MODIFIER)
        
        def __post_init__(self):
            assert self.point is not None, 'point must be set.'
            assert self.path_modifier is not MISSING_PATH_MODIFIER, 'path_modifier must be set.'
            if self.prev_op is None:
                assert self.prev_op is not None, 'prev_op must be set.'
            if self.direction_override is None:
                d = self.point - self.prev_op.lastPosition()
                if _vlen2(d) > EPSILON:
                    object.__setattr__(
                        self, 'direction_override', self.point - self.prev_op.lastPosition())
            if self.direction_override is not None and self.direction_norm is None:
                object.__setattr__(
                    self, 'direction_norm', _normalize(self.direction_override))
            
        def lastPosition(self):
            return self.point
        
        def populate(self, path_builder, start_indexes, map_builder, meta_data):
            should_segment = meta_data.segment_lines or \
                (self.meta_data.segment_lines if self.meta_data else False)
            if not should_segment:
                path_builder.append(self.point)
                map_builder.append(self, self.point, 1, 1.0)
                return
            
            # Use this object's meta_data if it has it.
            meta_data = self.meta_data if self.meta_data else meta_data
            
            n = meta_data.fn
            if not n:
                if meta_data.fs:
                    last_pos = self.prev_op.lastPosition()
                    this_pos = self.point
                    n = _vlen(this_pos - last_pos) // meta_data.fs
                else:
                    n = 4 # Default to 4 segments.
            
            for i in range(1, n + 1):
                t = i / n
                point = self.base_position(t)
                path_builder.append(point)
                map_builder.append(self, point, n, t)
            
        def direction(self, t):
            return self.direction_override
        
        def direction_normalized(self, t):
            return self.direction_norm
        
        def normal2d(self, t, dims=[0, 1]):
            last_point = self.prev_op.lastPosition()
            return _normal_of_2d(last_point, self.direction(1) + last_point, dims)
        
        def extremes(self) -> np.array:
            p0 = self.prev_op.lastPosition()
            p1 = self.point
            return np.array((p0, p1))
        
        def extents(self):
            return extentsof(self.extremes())
            
        def base_position(self, t):
            return self.point + (t - 1) * self.direction(0)
        
        def transform(self, m):
            params = self._as_non_defaults_dict()
            params['point'] = (m * to_gvector(self.point)).A[0:len(self.point)]
            return (self.__class__, params)
        
        def render_as_svg(self, svg_model):
            svg_model.lineto(self.point, self.name, self.trace)
            
        def __eq__(self, other):
            if self.__class__ != other.__class__:
                return False
            return (
                (self.point == other.point).all()
                and self.name == other.name)
            
        def __hash__(self):
            return hash((tuple(self.point.flatten()), self.name))

    @datatree(frozen=True)
    class _MoveTo(OpBase):
        '''Move to position.'''
        point: np.array=dtfield(None, compare=False)
        dir: np.array=None
        prev_op: object=dtfield(
            default=None,
            repr=False, 
            hash=False, 
            compare=False)
        name: str=None
        path_modifier: 'PathModifier'=dtfield(default=MISSING_PATH_MODIFIER)
        
        def __post_init__(self):
            assert self.point is not None, 'point must be set.'
            assert self.path_modifier is not MISSING_PATH_MODIFIER, 'path_modifier must be set.'
            self.point.setflags(write=False)
            if self.dir is not None:
                self.dir.setflags(write=False)
            
        def lastPosition(self):
            return self.point
        
        def populate(self, path_builder, start_indexes, map_builder, meta_data):
            path_builder.append(self.point)
            start_indexes.append(len(path_builder))
            map_builder.append(self, self.point, 1, 0)
            
        def direction(self, t):
            return self.dir
            
        def direction_normalized(self, t):
            return _normalize(self.direction(t))
        
        def normal2d(self, t, dims=[0, 1]):
            return _normalize(self.dir)
        
        def extremes(self):
            p = self.point
            return np.array((p, p))
        
        def extents(self):
            return np.array([self.point, self.point])
        
        def base_position(self, t):
            return self.point  # Move is associated only with the move point. 

        def transform(self, m):
            params = self._as_non_defaults_dict()
            params['point'] = (m * to_gvector(self.point)).A[0:len(self.point)]
            return (self.__class__, params)
        
        def apply_modifier(self, path_modifier: 'PathModifier', next_op: 'OpBase') -> 'OpBase':
            '''Returns a new operation with the modifier applied.'''
            if self.dir is not None:
                return replace(self, path_modifier=path_modifier)
            dir = next_op.direction_normalized(0)
            return replace(self, dir=dir, path_modifier=path_modifier)
        
        def is_move(self):
            return True
        
        def render_as_svg(self, svg_model):
            svg_model.moveto(self.point, self.name, self.trace)

        def __eq__(self, other):
            if self.__class__ != other.__class__:
                return False
            return (
                (self.point == other.point).all()
                and optional_arrayeq(self.dir, other.dir)
                and self.name == other.name)
            
        def __hash__(self):
            return hash((
                tuple(self.point.flatten()), 
                None if self.dir is None else tuple(self.dir.flatten()), 
                self.name))

    @datatree(frozen=True, provide_override_field=False)
    class _SplineToBase(OpBase):
        '''Cubic Bezier Spline to.'''
        points: np.array=None
        prev_op: object=dtfield(
            default=None,
            repr=False, 
            hash=False, 
            compare=False)
        name: str=None
        meta_data: object=None
        path_modifier: 'PathModifier'=dtfield(default=MISSING_PATH_MODIFIER)
        
        SPLINE_CLASS=None # Derived class must set this.
        
        def __post_init__(self):
            assert self.points is not None, 'points must be set.'
            assert self.path_modifier is not MISSING_PATH_MODIFIER, 'path_modifier must be set.'
            self.points.setflags(write=False)
            to_cat = [[self.prev_op.lastPosition()],  self.points]
            spline_points = np.concatenate(to_cat)
            object.__setattr__(self, 'spline', self.SPLINE_CLASS(spline_points))
            
        def __eq__(self, other):
            if self.__class__ != other.__class__:
                return False
            return (
                (self.points == other.points).all()
                and self.name == other.name
                and self.meta_data == other.meta_data
                and self.path_modifier == other.path_modifier)
            
        def populate(self, path_builder, start_indexes, map_builder, meta_data):
            if self.meta_data and self.meta_data.fn:
                meta_data = self.meta_data
    
            count = meta_data.fn
            if not count:
                count = 10
    
            for i in range(1, count + 1):
                t = float(i) / float(count)
                point = self.spline.evaluate(t)
                path_builder.append(point)
                map_builder.append(self, point, count, t)
    
        def direction(self, t):
            return -self.spline.derivative(t)
        
        def direction_normalized(self, t):
            return _normalize(self.direction(t))
        
        def normal2d(self, t, dims=[0, 1]):
            return self.spline.normal2d(t, dims)
        
        def extremes(self):
            return self.spline.extremes()
        
        def extents(self):
            return self.spline.extents()
        
        def base_position(self, t):
            if t < 0:
                return self.direction(0) * t + self.prev_op.lastPosition()
            elif t > 1:
                return self.direction(1) * (t - 1) + self.lastPosition()
            return self.spline.evaluate(t)
        
        def transform(self, m: l.GMatrix):
            points = list((m * to_gvector(p)).A[0:len(p)] for p in self.points)
            points = np.array(LIST_23X2_FLOAT(points))
            params = self._as_non_defaults_dict()
            params['points'] = points
            return (self.__class__, params)

        def azimuth_t(self, angle: Union[float, l.Angle]=0, t_end: bool=False, 
                    t_range: Tuple[float, float]=(0.0, 1.0)) -> Tuple[float, ...]:
            
            return self.spline.azimuth_t(angle, t_end, t_range)

        def __hash__(self):
            return hash((tuple(self.points.flatten()), self.name, self.meta_data))
        
    @datatree(frozen=True, chain_post_init=True)
    class _SplineTo(_SplineToBase):
        
        SPLINE_CLASS = CubicSpline

        def __hash__(self):
            return super().__hash__()
        
        def __eq__(self, other):
            return super().__eq__(other)
        
        def lastPosition(self):
            return self.points[2]

        def render_as_svg(self, svg_model):
            svg_model.splineto(self.points, self.name, self.trace)
        
    @datatree(frozen=True, chain_post_init=True)
    class _QuadraticSplineTo(_SplineToBase):
        
        SPLINE_CLASS = QuadraticSpline

        def __hash__(self):
            return super().__hash__()
        
        def __eq__(self, other):
            return super().__eq__(other)
        
        def lastPosition(self):
            return self.points[1]

        def render_as_svg(self, svg_model):
            svg_model.qsplineto(self.points, self.name, self.trace)
            
                    
        def populate(self, path_builder, start_indexes, map_builder, meta_data):
            if self.meta_data and self.meta_data.fn:
                meta_data = self.meta_data
    
            count = meta_data.fn
            if not count:
                count = 10
    
            for i in range(1, count + 1):
                t = float(i) / float(count)
                point = self.spline.evaluate(t)
                path_builder.append(point)
                map_builder.append(self, point, count, t)


    @datatree(frozen=True)
    class _ArcTo(OpBase):
        '''Draw a circular arc.'''
        end_point: np.array=None
        centre: np.array=None
        path_direction: bool=None
        prev_op: object=dtfield(
            default=None,
            repr=False, 
            hash=False, 
            compare=False)
        name: str=None
        meta_data: object=None
        path_modifier: 'PathModifier'=dtfield(default=MISSING_PATH_MODIFIER)
        
        def __post_init__(self):
            assert self.end_point is not None, 'end_point must be set.'
            assert self.centre is not None, 'centre must be set.'
            assert self.path_direction is not None, 'path_direction must be set.'
            assert self.path_modifier is not MISSING_PATH_MODIFIER, 'path_modifier must be set.'
            self.centre.setflags(write=False)
            self.end_point.setflags(write=False)
            start_point = self.prev_op.lastPosition()
            r_start = start_point - self.centre
            radius_start = _vlen(r_start)
            r_end = self.end_point - self.centre
            radius_end = _vlen(r_end)
            assert np.abs(radius_start - radius_end) < EPSILON, (
                f'start and end point radius should be the same. {radius_start} != {radius_end}')
            s_normal = r_start / radius_start
            e_normal = r_end / radius_start
            cos_s = s_normal[0]
            sin_s = s_normal[1]
            start_angle = np.arctan2(sin_s, cos_s)
            
            cos_e = e_normal[0]
            sin_e = e_normal[1]
            end_angle = np.arctan2(sin_e, cos_e)
           
            end_delta = end_angle - start_angle
 
            if self.path_direction:
                # Should be clockwise.
                if end_delta < 0:
                    end_delta = 2 * np.pi + end_delta
            else:
                # Should be anti-clockwise
                if end_delta > 0:
                    end_delta = -2 * np.pi + end_delta
                    
            object.__setattr__(self, 'arcto', CircularArc(
                start_angle, end_delta, radius_start, self.centre))
            
        def get_centre(self):
            return self.centre

        def azimuth_t(self, angle: Union[float, l.Angle]=0, t_end: bool=False, 
                    t_range: Tuple[float, float]=(0.0, 1.0)) -> Tuple[float, ...]:
            
            return self.arcto.azimuth_t(angle, t_end, t_range)
            
        def lastPosition(self):
            return self.end_point
        
        def _sweep_away(self):
            '''Returns true if the arc sweeps away from the previous point.'''
            d = self.direction(0)
            radial = self.prev_op.lastPosition() - self.centre
            cross = d[0] * radial[1] - d[1] * radial[0]
            return cross > 0
            
        def populate(self, path_builder, start_indexes, map_builder, meta_data):
            if self.meta_data and self.meta_data.fn:
                meta_data = self.meta_data
    
            count = meta_data.fn
            if not count:
                count = 10
                
            for i in range(1, count + 1):
                t = float(i) / float(count)
                # The offset is only applied to anchors. Offset to the path
                # is applied by against the polygon.
                point = self.arcto.evaluate(t, offset=0)
                path_builder.append(point)
                map_builder.append(self, point, count, t)
    
        def direction(self, t):
            return self.arcto.derivative(t)
        
        def direction_normalized(self, t):
            return _normalize(self.direction(t))
        
        def normal2d(self, t, dims=[0, 1]):
            return self.arcto.normal2d(t)
        
        def extremes(self):
            return self.arcto.extremes()
        
        def extents(self):
            return self.arcto.extents()
        
        def base_position(self, t):
            if t < 0:
                return self.direction(0) * t + self.prev_op.lastPosition()
            elif t > 1:
                return self.direction(1) * (t - 1) + self.end_point
            return self.arcto.evaluate(t)
        
        def transform(self, m):
            end_point = (m * to_gvector(self.end_point)).A[0:len(self.end_point)]
            centre = (m * to_gvector(self.centre)).A[0:len(self.centre)]
            params = {
                'end_point': end_point,
                'centre': centre,
                'path_direction': self.path_direction}
            return (self.__class__, params)

        def render_as_svg(self, svg_model):
            svg_model.arcto1(
                self.arcto.radius,
                self.arcto.sweep_angle,
                self.path_direction,
                self.end_point,
                self.centre,
                self.name,
                self.trace)
            
        def __eq__(self, other):
            if self.__class__ != other.__class__:
                return False
            return (
                (self.end_point == other.end_point).all()
                and (self.centre == other.centre).all()
                and self.path_direction == other.path_direction
                and self.name == other.name
                and self.meta_data == other.meta_data)
        
        def __hash__(self):
            return hash(
                (tuple(self.end_point),
                 tuple(self.centre), 
                 self.path_direction, 
                 self.name, 
                 self.meta_data))

    def _add_op_map(self, op):
        if op.name:
            if op.name in self.name_map:
                raise DuplicateNameException(f'Duplicate name ({op.name!r}) is already used.')
            self.name_map[op.name] = op
            
       
    def move(self, point, name=None, direction=None) -> 'PathBuilderPrimitives':
        if not self.is_multi_path() and self.last_op() is not None:
            raise MoveNotAllowedException('Move is not allowed in non multi-path builder.')
        if direction is not None:
            direction = np.array(LIST_2_FLOAT(direction))
        return self.add_op(self._MoveTo(point=np.array(LIST_2_FLOAT(point)),
                                        dir=direction,
                                        prev_op=self.last_op(), name=name,
                                        path_modifier=self.get_path_modifier()))
                        
    def line(self, 
                   point: Union[np.array, Tuple[float, float], List[float]],
                   name: Any=None, 
                   metadata: core.ModelAttributes=None, 
                   direction_override=None,
                   _trace_level: int=4
                   ) -> 'PathBuilderPrimitives':
        '''A line from the current point to the given point is added.
        Args:
            point: The absolute end point of this line.
            name: The name of this node. Naming a node will make it an anchor.
            metadata: Provides parameters for rendering that override the renderer metadata.
            direction_override: The reported direction of the line. If None, the direction is
                calculated from the previous point.
        '''
        assert self.last_op(), "Cannot line to without starting point"

        if direction_override is not None:
            direction_override = np.array(LIST_2_FLOAT(point))
    
        return self.add_op(self._LineTo(point=np.array(LIST_2_FLOAT(point)), 
                            prev_op=self.last_op(),
                            name=name,
                            meta_data=metadata,
                            direction_override=direction_override,
                            path_modifier=self.get_path_modifier(),
                            trace=_traceback(_trace_level)))
    
    def line_wop(self, prev_op_func: Callable[[OpBase], Tuple[float, float]], 
                 name=None, metadata=None, direction_override=None) -> 'PathBuilderPrimitives':
        '''A line from the current point to the point returned by calling prev_op_func
        with the most recent op.
        Args:
            prev_op_func: A function that takes the last operation and returns a point.
            name: The name of this node. Naming a node will make it an anchor.
            metadata: Provides parameters for rendering that override the renderer metadata.
            direction_override: The reported direction of the line. If None, the direction is
                calculated from the previous point.
        '''
        
        point = prev_op_func(self.last_op())
        return self.line(point, name, metadata, direction_override, _trace_level=5)

        
    def stroke(self,
               length: float,
               angle: float | l.Angle | None=None,
               xform: l.GMatrix | None=None, 
               abs_angle: float | l.Angle | None=None,
               name: Any=None,
               metadata: core.ModelAttributes=None) -> 'PathBuilderPrimitives':
        '''A line from the current point to a length away given
        by following the tangent from the previous op transformed by rotating
        by angle or a GMatrix transform.
        Args:
            length: The length of the line.
            angle: The angle to rotate the tangent by.
            xfom: A GMatrix transform to apply to the tangent.
            abs_angle: The absolute angle to rotate the tangent by (overrides angle and xform)
            name: The name of this node. Naming a node will make it an anchor.
            metadata: Provides parameters for rendering that override the renderer metadata.
        '''
        assert length >= 0, f"Cannot stroke with a negative length of {length}"
        assert len(self.ops) > 0, "Cannot line to without starting point"
        angle = l.angle(angle)
        abs_angle = None if abs_angle is None else l.angle(angle=abs_angle) 
        d_vector = to_gvector(self.last_op().direction_normalized(1.0))
        if abs_angle is not None:
            d_vector = abs_angle.rotZ * d_vector
        else:
            if angle is not None:
                d_vector = angle.rotZ * d_vector
            if xform is not None:
                d_vector = xform * d_vector
                
            if length > 0:
                d_vector = d_vector * length
                point = d_vector + to_gvector(self.last_op().lastPosition())
                point = point.A[:2]
            else:
                d_vector = d_vector * 0.001
                point = self.last_op().lastPosition()

        return self.add_op(self._LineTo(point=point, 
                                        prev_op=self.last_op(),
                                        name=name,
                                        direction_override=d_vector.A[:2],
                                        meta_data=metadata,
                                        path_modifier=self.get_path_modifier()))
            
    def relative_line(self,
               relative_pos,
               name=None,
               metadata=None) -> 'PathBuilderPrimitives':
        '''A line from the current point to the relative X,Y position given.'''
        point = (np.array(LIST_2_FLOAT(relative_pos)) 
                 + self.last_op().lastPosition())
        return self.add_op(self._LineTo(point=point[:2], 
                                        prev_op=self.last_op(), name=name,
                                        meta_data=metadata,
                                        path_modifier=self.get_path_modifier()))
        
    def _rotate(self, direction: l.GVector, angle: l.Angle | None, 
                xform: l.GMatrix | None) -> l.GVector:
        
        if xform:
            d_vector = xform * direction
        elif angle is not None:
            d_vector = angle.rotZ * direction
        else:
            d_vector = direction
        return d_vector
    
    def _rotate_n(self, 
                  direction: l.GVector, 
                  angle: Tuple[l.Angle | float | None, ...],
                  xform: tuple[l.GMatrix, ...], 
                  size: int) -> List[l.GVector]:
        d = size if size else max(len(angle), len(xform))
        directions = []
        for i in range(d):
            v_angle = angle[i] if len(angle) > i else None
            v_xform = xform[i] if len(xform) > i else None
            directions.append(self._rotate(direction, v_angle, v_xform))
        return directions

    
    def rspline(self, length_or_rpoint: float, cv_len: tuple[float, ...]=(1, 1), 
                angle: Tuple[l.Angle | float | None, ...]=(0, 0, 0),
                xform: tuple[l.GMatrix, ...]=(None, None, None), 
                name: Any=None, 
                metadata: core.ModelAttributes=None, 
                rel_len: tuple[float, ...]=None) -> 'PathBuilderPrimitives':
        '''Like [spline] but the control points are relative to the last point and direction.
        In a similar vein to [stroke], it will determine the end point by following the previous
        direction rotated by the given angle. The control point 1 and 2 angle is provided by
        degrees or radians.
        Args:
            length_or_rpoint: The length of the new control point (direct line length 
                    from the last position to control point 3) or a relative position
                    to the final point (control point 3).
            cv_len: If provided will force the length of the control point (1 an 2)
                    to be the given length. (length parameter is for control point 3)
                    Default is (1, 1)
            name: The name of this node. Naming a node will make it an anchor.
            metadata: Provides parameters for rendering that override the renderer metadata.
            angle: A 3 tuple that contains a rotation angle for control points 1, 2 and 3
                    respectively from the previous direction.
            xform: like angle but in a GMatrix transform, if provided it overrides any
                    angle values provided.
            rel_len: Forces control points to have relatively the same length as the
                    distance from the end points. If cv_len is set it is used as a multiplier.
        '''
        
        if isinstance(length_or_rpoint, numbers.Number):
            length = length_or_rpoint
            assert length > 0, f"Cannot rspline with zero or negative length: {length}"
            rpoint = None
        else:
            length = None
            rpoint = l.GVector(LIST_3_FLOAT(length_or_rpoint))

        assert len(self.ops) > 0, "Cannot rspline to without starting point"

        angles = LIST_3_ANGLE_OR_NONE(angle)
        if xform is None:
            xform = (None, None, None)
        
        direction = to_gvector(self.last_op().direction_normalized(1.0))
        directions = self._rotate_n(direction, angles, xform, 3)
        
        last_pos = to_gvector(self.last_op().lastPosition())
        points = [None, None, None]
        if rpoint:
            points[2] = rpoint + last_pos
        else:
            if length > 0:
                d_vector = directions[2] * length
            else:
                d_vector = directions[2] * 0.001
            points[2] = d_vector + last_pos
            
        for i in range(2):
            assert cv_len[i], f"Cannot rspline with zero cv_len[{i}]: {cv_len[i]}"
            
            d_vector = directions[i] * cv_len[i]
            if i == 1:
                points[i] = points[2] - d_vector
            else:
                # Control point 1 goes in the opposite direction to the previous direction.
                points[i] = last_pos + d_vector
        
        points_2d = list(p.A[:2] for p in points)

        return self.spline(points_2d, name, metadata, rel_len)
    
    def qspline(self, points, name=None, metadata=None) -> 'PathBuilderPrimitives':
        '''A quadratic spline from the current point to the given points.
        Points consists of a control point (points[0]) and an end point (points[1]).
        '''
        assert len(self.ops) > 0, "Cannot line to without starting point"
        points = np.array(LIST_2X2_FLOAT(points))
        return self.add_op(
            self._QuadraticSplineTo(
                points=points, 
                prev_op=self.last_op(), 
                name=name, 
                meta_data=metadata,
                path_modifier=self.get_path_modifier()))
        
    
    def spline(self, points, name: Any=None, metadata: core.ModelAttributes=None, 
               cv_len: tuple[float | None, float | None]=(None, None), 
               angle: Tuple[l.Angle | float | None, ...]=(0, 0), 
               rel_len=None) -> 'PathBuilderPrimitives':
        '''Adds a cubic Bezier spline node to the path.
        Args:
            points: Either 3 point list (first control point is the last point) or a 
                    2 point list and cv_len with the first element set to the distance 
                    the control point follows along the previous operations last direction.
            cv_len: If provided will force the length of the control point (1 an 2)
                    to be the given length from the respective start and end points.
            name: The name of this node. Naming a node will make it an anchor.
            metadata: Provides parameters for rendering that override the renderer metadata.
            degrees: A 2 tuple that contains a rotation angle for control points 1 and 2
                    respectively.
            radians: line degrees but in radians. If radians are provided they override any
                    degrees values provided.
            rel_len: Forces control points to have relatively the same length as the
                    distance from the end points. If cv_len is set it is used as a multiplier.
        '''
        assert len(self.ops) > 0, "Cannot line to without starting point"
        angles = LIST_2_ANGLE_OR_NONE(angle)
        cv_len = LIST_2_FLOAT_OR_NONE(cv_len) if cv_len else (None, None)
        points = np.array(LIST_23X2_FLOAT(points))
        if len(points) == 2:
            if cv_len[0] is None:
                raise InvalidSplineParametersException(
                    'Only 2 control points provided so the direction of the previous operation'
                    ' will be used but a size (in cv_len. This needs a control vector size.')
            if self.last_op().direction_normalized(1.0) is None:
                raise InvalidSplineParametersException(
                    'Only 2 control points provided so the direction of the previous operation'
                    ' will be used but the previous operation (move) does not provide direction.')
            cv0 = self.last_op().lastPosition()
            cv1 = self.last_op().direction_normalized(1.0) * cv_len[0] + cv0
            cv2 = points[0]
            cv3 = points[1]
        else:
            cv0 = self.last_op().lastPosition()
            cv1 = points[0]
            cv2 = points[1]
            cv3 = points[2]
        if rel_len is not None:
            d = np.sqrt(np.sum((cv0 - cv3)**2))
            cv_len = tuple(rel_len * d if v is None else v * d * rel_len for v in cv_len)
        cv1 = self.squeeze_and_rot(cv0, cv1, cv_len[0], angles[0])
        cv2 = self.squeeze_and_rot(cv3, cv2, cv_len[1], angles[1])
        
        points = np.array(LIST_3X2_FLOAT([cv1, cv2, cv3]))
        return self.add_op(self._SplineTo(points=points,
                                          prev_op=self.last_op(), 
                                          name=name, 
                                          meta_data=metadata,
                                          path_modifier=self.get_path_modifier()))
        
    def arc_tangent_radius_sweep(self,
                                 radius: float,
                                 sweep_angle: float | l.Angle=0,
                                 sweep_direction: bool=None,
                                 side: bool=False, 
                                 angle: float | l.Angle=0, 
                                 direction: tuple[float, float]=None, 
                                 name=None,
                                 metadata=None) -> 'PathBuilderPrimitives':
        '''Defines a circular arc starting at the previous operator's end point
        with the given direction and sweeping the given sweep angle.'''
        start = self.last_op().lastPosition()
        if direction is None:
            direction = self.last_op().direction_normalized(1.0)
        else:
            direction = _normalize(direction)
        
        angle = l.angle(angle)
        t_dir = (angle.rotZ * to_gvector(direction))
        direction = t_dir.A[0:len(direction)]
        centre, _ = solve_circle_tangent_radius(start, direction, radius, side)

        n_start = (start - centre) / radius
        cos_s = n_start[0]
        sin_s = n_start[1]
        
        sweep_angle = l.angle(sweep_angle)
        
        if isinstance(sweep_angle, l.AngleSinCos):
            sin_sweep, cos_sweep = sweep_angle.sinr_cosr()
            assert sweep_direction is not None, 'If sweep_angle sinr_cosr is specified a ' \
                'sweep_direction must also be specified.'
            path_direction = sweep_direction
        else:
            sin_sweep, cos_sweep = sweep_angle.sinr_cosr()
            path_direction = sweep_angle.degrees() >= 0
        
        cos_e = cos_s * cos_sweep - sin_s * sin_sweep
        sin_e = sin_s * cos_sweep + sin_sweep * cos_s
        last = np.array([cos_e * radius + centre[0], sin_e * radius + centre[1]])
        
        
        return self.add_op(self._ArcTo(
            end_point=last, 
            centre=centre,
            path_direction=path_direction, 
            prev_op=self.last_op(), 
            name=name, 
            meta_data=metadata, 
            path_modifier=self.get_path_modifier()))

    def arc_centre_sweep(self,
                         centre: tuple[float, float], 
                         sweep_angle: float | l.Angle=0,
                         name=None,
                         metadata=None) -> 'PathBuilderPrimitives':
        '''Defines a circular arc starting at the previous operator's end point
        and sweeping the given angle about the given centre.'''
        start = self.last_op().lastPosition()
        
        centre = np.array(centre)
        t_start = start - centre
        radius = _vlen(t_start)
        n_start = t_start / radius
        cos_s = n_start[0]
        sin_s = n_start[1]
        
        sweep_angle = l.angle(sweep_angle)
            
        sin_sweep, cos_sweep = sweep_angle.sinr_cosr()
        
        cos_e = cos_s * cos_sweep - sin_s * sin_sweep
        sin_e = sin_s * cos_sweep + sin_sweep * cos_s
        last = np.array([cos_e * radius + centre[0], sin_e * radius + centre[1]])
        
        path_direction = sweep_angle.degrees() >= 0
        
        return self.add_op(self._ArcTo(end_point=last, 
                                       centre=centre, 
                                       path_direction=path_direction, 
                                       prev_op=self.last_op(), 
                                       name=name, 
                                       meta_data=metadata,
                                       path_modifier=self.get_path_modifier()))
        
        
    def arc_points_radius(self, 
            end: POINT2, 
            radius: float, 
            is_left:bool =True, 
            direction: Union[bool, None] = None, 
            name:NAME =None,
            metadata:core.ModelAttributes=None) -> 'PathBuilderPrimitives':
        '''Defines a circular arc starting at the previous operator's end point
        and ending at "end" with the given radius.'''
        last = np.array(end)
        start = self.last_op().lastPosition()
        centre, _ = solve_circle_points_radius(start, last, radius, is_left)
        if centre is None:
            raise UnableToFitCircleWithGivenParameters(
                f'Unable to fit circle, radius={radius}, start={start} last={last}.')
        if direction is None:
            direction = not is_left
        return self.add_op(self._ArcTo(end_point=last,
                                       centre=centre,
                                       path_direction=direction,
                                       prev_op=self.last_op(), 
                                       name=name,
                                       meta_data=metadata,
                                       path_modifier=self.get_path_modifier()))
    
    def arc_points(self, middle, last, name=None, direction=None, 
                   metadata=None) -> 'PathBuilderPrimitives':
        '''Defines a circular arc starting at the previous operator's end point
        and passing through middle and ending at last.'''
        last = np.array(last)
        start = self.last_op().lastPosition()
        centre, radius = solve_circle_3_points(start, middle, last)
        n_points = np.array([start - centre, middle - centre, last - centre]) / radius
        start_angle = np.arctan2(n_points[0][1], n_points[0][0])
        middle_angle = np.arctan2(n_points[1][1], n_points[1][0])
        end_angle = np.arctan2(n_points[2][1], n_points[2][0])
        
        middle_delta = middle_angle - start_angle
        end_delta = end_angle - start_angle
        
        # The direction should mean that the middle position traversed before last position.
        path_direction = True
        if direction is not None:
            path_direction = direction
        elif middle_delta < 0:
            if end_delta < 0:
                if middle_delta < end_delta:
                    path_direction = False
            else: 
                end_delta = -2 * np.pi + end_delta      
                if middle_delta > end_delta:
                    path_direction = False
        else:
            if end_delta > 0:
                if middle_delta > end_delta:
                    path_direction = False
            else: 
                end_delta = 2 * np.pi + end_delta     
                if middle_delta > end_delta:
                    path_direction = False
        
        return self.add_op(self._ArcTo(end_point=last, 
                                       centre=centre,
                                       path_direction=path_direction,
                                       prev_op=self.last_op(),
                                       name=name,
                                       meta_data=metadata,
                                       path_modifier=self.get_path_modifier()))
    
    def arc_tangent_point(self, 
                          last: tuple[float, float], 
                          angle: l.Angle | float =0, 
                          direction: tuple[float, float] | None=None, 
                          name: Any=None, 
                          metadata: core.ModelAttributes=None) -> 'PathBuilderPrimitives':
        '''Defines a circular arc starting at the previous operator's end point
        and ending at last. The tangent (vector given by the direction parameter or
        if not provided by the last segment's direction vector) may be optionally
        rotated by the given angle (degrees or radians).'''
        last = np.array(last)
        start = self.last_op().lastPosition()
        if direction is None:
            direction = self.last_op().direction_normalized(1.0)
        else:
            direction = _normalize(np.array(direction))
        angle = l.angle(angle)
        t_dir = angle.rotZ * to_gvector(direction)
        direction = t_dir.A[0:len(direction)]
        centre, radius = solve_circle_tangent_point(start, direction, last)
        if centre is None:
            # This degenerates to a line.
            return self.line(last, name=name)
        n_start = (start - centre) / radius
        cos_s = n_start[0]
        sin_s = n_start[1]
        c_dir = l.GVector([-sin_s, cos_s, 0])
        
        path_direction = (t_dir.dot3D(c_dir) > 0)
        
        return self.add_op(self._ArcTo(
            end_point=last, 
            centre=centre, 
            path_direction=path_direction, 
            prev_op=self.last_op(), name=name, meta_data=metadata,
            path_modifier=self.get_path_modifier()))
        
    def arc_line_to_arc_centre_radius(self, 
            radius: float, 
            end_centre: np.array,
            end_radius: float,
            end_side: bool=False, 
            angle: Union[float, l.Angle]=0, 
            direction: np.array=None, 
            side: bool=False, # True is left side
            name: Any=None, 
            metadata=None) -> 'PathBuilderPrimitives':
        '''Defines 2 segments, a circular arc starting at the previous operator's end point
        with the given radius and a line that is tangent to the aforementioned arc and
        the arc defined by the end_centre and end_radius. The second arc is not added by this
        method, only the first arc and the tangent line between the two arcs.
        
        Note that the 
        
        Args:
            radius: The radius of the first arc.
            end_centre: The centre of the second arc (not added by this method).
            end_radius: The radius of the second arc (not added by this method).
            end_side: If True the arc will be on the left side of end_centre.
            angle: The angle to rotate the previous end point direction by.
            direction: If given, overrides the previous end point direction.
            side: If True the arc will be on the left side of the previous end point.
            name: The name of this node. Naming a node will make it an anchor but the
                name of the arc (first segment) is made as a tuple of this name and 'arc',
                i.e. ('arc', name) and similarly for the line, ('line', name).
            metadata: Provides parameters for rendering that overrides the metadata 
                provided by the renderer.
        '''
        
        angle = l.angle(angle)
    
    def squeeze_and_rot(self, point: tuple[float, float], control: tuple[float, float], cv_len: float, angle: l.Angle | None):
        if cv_len is None and not angle:
            return control
        gpoint = l.GVector(LIST_3_FLOAT(point))
        gcontrol = l.GVector(LIST_3_FLOAT(control))
        g_rel = (gcontrol - gpoint)
        if cv_len is not None and g_rel.length() > EPSILON:
            g_rel = g_rel.N * cv_len

        if angle:
            g_rel = angle.rotZ * g_rel
    
        return (gpoint + g_rel).A[0:len(point)]
    
    def at(self, name: Any, t: float, apply_offset: bool=True) -> np.ndarray:
        '''Returns the point on the path at the given t value.'''
        op: OpBase = self.get_op(name)
        if not op:
            raise NameNotFoundException(f'Name {name!r} not found.')
        return op.position(t, apply_offset)
    
    def direction_at(self, name: Any, t: float) -> np.ndarray:
        '''Returns the direction on the path at the given t value.'''
        op: OpBase = self.get_op(name)
        if not op:
            raise NameNotFoundException(f'Name {name!r} not found.')
        return op.direction_normalized(t)
        

@datatree(frozen=True)
class Construction:
    ops: List[OpBase]=None
    
    def extremes(self) -> np.ndarray:
        itr = iter(self.ops)
        extnts = extentsof(next(itr).extremes())
        for op in itr:
            ops_extremes = op.extremes()
            cated = np.concatenate((ops_extremes, extnts))
            extnts = extentsof(cated)
        return extnts


@datatree(frozen=True)
class _Construction(PathBuilderPrimitives):
    
    pathBuilder: 'PathBuilder'
    ops: List[OpBase]=dtfield(default_factory=list, init=False)
    
    def construction(self) -> '_Construction':
        raise NotImplementedError('Cannot nest constructions.')
    
    def is_multi_path(self) -> bool:
        '''Constructions allow multiple paths.'''
        return True

    def last_op(self) -> OpBase:
        '''Returns the last operation.'''
        return self.ops[-1] if self.ops else None
    
    def get_path_modifier(self) -> PathModifier:
        '''Returns the path modifier.'''
        return self.pathBuilder.get_path_modifier()
    
    def add_op(self, op: OpBase) -> 'PathBuilderPrimitives':
        '''Adds an operation to the path.'''
        self.pathBuilder._add_op_map(op)
        self.ops.append(op)
        return self
    
    def add_op_with_params(self, op_parts, op_name=None, path_modifier=None, trace=None):
        params_dict = op_parts[1]
        params_dict['prev_op'] = self.last_op()
        params_dict['path_modifier'] = path_modifier
        
        if op_name:
            params_dict['name'] = op_name
        if trace:
            params_dict['trace'] = trace
        return self.add_op((op_parts[0])(**params_dict))
    
    def __enter__(self) -> '_Construction':
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        discard: bool = exc_value is not None
        self.pathBuilder._end_construction(self, discard=discard)

        return None # Do not suppress exceptions.
    
    def extremes(self) -> np.ndarray:
        itr = iter(self.ops)
        extnts = extentsof(next(itr).extremes())
        for op in itr:
            ops_extremes = op.extremes()
            cated = np.concatenate((ops_extremes, extnts))
            extnts = extentsof(cated)
        return extnts
    
    def add_transformed(self, 
                  construction: Construction,
                  m: l.GMatrix, 
                  builder: 'PathBuilderPrimitives', 
                  suffix: Any=None, 
                  appender: Callable[[Any, Any], Any]=adder):
        '''Transforms the Ops in the priced construction with the given matrix
        into the given builder.'''
        
        for op in construction.ops:
            self.add_op_with_params(
                op.transform(m), 
                appender(op.name, suffix), 
                path_modifier=builder.get_path_modifier(),
                trace=op.trace)
            
    def get_op(self, name) -> OpBase | None:
        return self.pathBuilder.get_op(name)
    

@datatree(provide_override_field=False)
class PathBuilder(PathBuilderPrimitives):
    '''Builds a Path from a series of points, lines, splines and arcs.'''
    ops: List[OpBase]=dtfield(default_factory=list, init=False)
    constructions: List[Construction]=dtfield(
        default_factory=list, init=False,
        doc='Constructions. These are not included in the path but are rendered in SVG.')
    name_map: Dict[Any, OpBase]=dtfield(default_factory=dict, init=False)
    
    construction_stack: List[_Construction]=dtfield(default_factory=list, init=False)
    
    multi: bool=False
    path_modifier: PathModifier=None
    
    def is_multi_path(self) -> bool:
        '''Returns True if the builder allows multiple paths.'''
        return self.multi
    
    def get_path_modifier(self) -> PathModifier:
        '''Returns the path modifier.'''
        return self.path_modifier
        
    def construction(self) -> _Construction:
        '''Returns a construction context manager used inside 'with' statements.'''
        c = _Construction(self)
        self.construction_stack.append(c)
        return c

    def _end_construction(self, c: _Construction, discard: bool):
        assert c == self.construction_stack[-1], 'Construction stack mismatch.'
        self.construction_stack.pop()
        if discard:
            # Remove the names from the name map. (Exception was raised.)
            for op in c.ops:
                self.name_map.pop(op.name, None)
        else:
            self.constructions.append(Construction(tuple(c.ops)))
            
    def add_op(self, op) -> 'PathBuilder':
        self._add_op_map(op)
        self.ops.append(op)
        return self
    
    def get_op(self, name) -> OpBase | None:
        return self.name_map.get(name, None)
    
    def add_op_with_params(self, op_parts, op_name=None, path_modifier=None, trace=None):
        params_dict = op_parts[1]
        params_dict['prev_op'] = self.last_op()
        params_dict['path_modifier'] = path_modifier
        
        if op_name:
            params_dict['name'] = op_name
        if trace:
            params_dict['trace'] = trace
        return self.add_op((op_parts[0])(**params_dict))

    def last_op(self):
        return self.ops[-1] if self.ops else None
 
    def get_node(self, name):
        return self.name_map.get(name, None)
    
    def build(self):
        return Path(
            tuple(self.ops), 
            frozendict(self.name_map), 
            path_modifier=self.get_path_modifier(),
            constructions=tuple(self.constructions))
    

class ExtrudedShape(core.Shape):
        
    def has_anchor(self, name):
        return name in self.anchorscad.anchors or name in self.path.name_map
    
    def anchor_names(self):
        return tuple(self.anchorscad.anchors.keys()) + tuple(self.path.name_map.keys())
    
    def at(self, anchor_name, *args, **kwds):
        spec = self.anchorscad.get(anchor_name)
        if spec:
            func = spec[0]
            try:
                return func(self, *args, **kwds)
            except TypeError as ex:
                raise IncorrectAnchorArgsException(
                    f'{ex}\nAttempted to call {anchor_name} on {self.__class__.__name__}'
                    f' with args={args!r} kwds={kwds!r}') from ex
        else:
            return self.node(anchor_name, *args, forward=False, **kwds)
            
    def to_3d_from_2d(self, vec_2d, h=0):
        return l.IDENTITY * l.GVector([vec_2d[0], vec_2d[1], h])
    
    @core.anchor('Anchor to the path for a given operation.')
    def node(self, path_node_name, *args, op='edge', forward=True, **kwds):
        if op == 'edge':
            return self.edge(path_node_name, *args, **kwds)
        
        op = self.path.name_map.get(path_node_name)
        if core.Shape.has_anchor(self, op) and forward:
            return self.at(op, path_node_name, *args, forward=False, **kwds)
        raise UnknownOperationException(
            f'Undefined anchor operation {op!r} for node {path_node_name!r}.')
        
    def eval_z_vector(self, h):
        return l.GVector([0, 0, h])

@datatree
class PolyhedronBuilderContext:
    points: tuple
    path: tuple=None
    
    def __post_init__(self):
        if not self.path:
            self.path = tuple(range(0, len(self.points)))
        if len(self.path) < 3:
            raise TooFewPointsInPath()
        unique_indexes = sorted(set(self.path))
        # Create a set of points with only the points used in path.
        self.vec_points = tuple(to_gvector(self.points[i]) for i in unique_indexes)
        reverse_map = dict((p, i) for i, p in enumerate(self.path))
        # Re-map the path to the new indexes.
        self.vec_path = tuple(reverse_map[p] for p in self.path)


def quad(prev_offs, curr_offs, pi, pj, direction):
    i, j = (pi, pj) if direction else (pj, pi)
    return (
        prev_offs + j,
        curr_offs + j,  
        curr_offs + i,
        prev_offs + i,
        )
    
    
@datatree
class PolyhedronBuilder:
    ctxt: PolyhedronBuilderContext
    points: List[Tuple[float]] = dtfield(default_factory=list, init=False)
    faces: List[Tuple[int, ...]] = dtfield(default_factory=list, init=False)
        
    def add_transformed(self, tansform):
        new_points = list(tansform * p for p in self.ctxt.vec_points)
        offset = len(self.points)
        self.points.extend(new_points)
        return offset
        
    def add_end_face(self, offset, reverse):
        face = tuple(offset + p for 
                     p in (reversed(self.ctxt.vec_path) 
                           if reverse 
                           else self.ctxt.vec_path))
        self.faces.append(face)
        
    def add_sequence(self, transforms, direction):
        t0 = transforms[0]
        offset0 = self.add_transformed(t0)
        prev_offs = offset0
        for t in transforms[1:]:
            next_offset = self.add_transformed(t)
            self.join_layers(prev_offs, next_offset, direction)
            prev_offs = next_offset
        return offset0, next_offset

    def join_layers(self, prev_offs, next_offset, direction):
        path = self.ctxt.vec_path
        path_end = len(path) - 1
        for i in range(path_end):
            self.faces.append(
                quad(prev_offs, next_offset, path[i], path[i + 1], direction))
        # Add the last quad only if it's not empty.
        if path[path_end] != path[0]:
            self.faces.append(
                quad(prev_offs, next_offset, path[path_end], path[0], direction))
        
    def make_two_ended(self, transforms, direction=True):
        first_offs, last_offs = self.add_sequence(transforms, direction)
        self.add_end_face(first_offs, direction)
        self.add_end_face(last_offs, not direction)

    def make_loop(self, transforms, direction):
        first_offs, last_offs = self.add_sequence(transforms, direction)
        self.join_layers(last_offs, first_offs, direction)
        
    def get_points_3d(self):
        return tuple(p.A3 for p in self.points)
    
    @classmethod
    def create_builders_from_paths(cls, points_paths):
        points = points_paths[0]
        paths = None if len(points_paths) == 1 else points_paths[1]
        
        builders = []
        # paths can be a single path or be a collection of paths.
        if not paths:
            builders.append(cls(
                PolyhedronBuilderContext(
                    points,
                    tuple(i for i in range(len(points))))))
        else:
            if isinstance(paths[0], Iterable):
                for path in paths:
                    builders.append(cls(
                        PolyhedronBuilderContext(points, path)))
            else:
                builders.append(cls(
                    PolyhedronBuilderContext(points, path)))

        return builders


class PathGenerator:
    '''Interface for a path generator. The PathGenerator controls the tesselation
    resolution along the path.'''
    
    def get_r_generator(self, metadata):
        '''Returns an iterable for the 'r' value, a value between 0 and 1 that
        describes how far along the extrusion the path is.'''
        raise NotImplementedError
    
    def get_polygons_at(self, r):
        '''Returns the 'polygons' (the result of Path.polygons()) for a given r
        where r is between 0 and 1.'''
        raise NotImplementedError


@datatree
class BasicPathGenerator(PathGenerator):
    '''Provides an isomorphic path.'''
    path: Path
    polygons: tuple=dtfield(init=False)
    
    def get_r_generator(self, metadata):
        self.polygons = self.path.cleaned_polygons(metadata)
        if len(self.polygons) == 1:
            self.polygons = self.polygons + (None,)
        fn = metadata.fn
        return (i / fn for i in range(fn + 1))
    
    def get_polygons_at(self, r):
        return self.polygons


@datatree
class Polyhedron2BuilderContext:
    path_generator: PathGenerator
    metadata: object
    
    def get_paths(self):
        return ((r,) + self.path_generator.get_polygons_at(r) 
                for r 
                in self.path_generator.get_r_generator(self.metadata))



@datatree
class Polyhedron2Builder:
    ctxt: Polyhedron2BuilderContext
    xform_function: FunctionType
    
    def __post_init__(self):
        self.points = []
        self.index_paths = []
        self.faces = []
    
    def make_open(self):
        self.make_body()
        self.faces.append(self.index_paths[0])
        self.faces.append(list(reversed(self.index_paths[-1])))
        
    def make_closed(self):
        self.make_body()
        self.make_face(self.index_paths[-1], self.index_paths[0])
        
    def make_body(self):
        for r, points, paths in self.ctxt.get_paths():
            if not paths:
                paths = (tuple(range(len(points))),)
                
            if len(paths) != 1:
                raise MultiplePathPolygonBuilderNotImplemented()
            
            offset_indexes = len(self.points)
            self.index_paths.append(
                tuple(i + offset_indexes for i in paths[0]))
                
            xform = self.xform_function(r)
            self.points.extend(xform * p for p in points)
            
            if len(self.index_paths) > 1:
                self.make_face_from_last_polys()
                
    def make_face_from_last_polys(self):
        self.make_face(self.index_paths[-2], self.index_paths[-1])

    def make_face(self, path1, path2):
        face = list(path1)
        face.extend(list(reversed(path2)))
        face.append(path1[-1])
        self.faces.append(face)

class LinearExtrudeTransformGenerator:
    scale: List[float]=(1.0, 1.0)
    twist_degrees: float=None
    twist_radians: float=None
    
    def __call__(self, r):
        return (l.tranZ(self.h * r) 
                * l.scale((1 + (self.scale[0] - 1) * r, 
                           1 + (self.scale[1] - 1) * r, 
                           1))) 


class RotateExtrudeTransformGenerator:
    scale: List[float]=(1.0, 1.0)
    twist_degrees: float=None
    twist_radians: float=None
    
    def __call__(self, r):
        return (l.tranZ(self.h * r) 
                * l.scale((1 + (self.scale[0] - 1) * r, 
                           1 + (self.scale[1] - 1) * r, 
                           1))) 


def test():
    SCALE = 2
    path = (PathBuilder(multi=True)
            .move([0, 0])
            .line([100 * SCALE, 0], 'linear')
            .spline([[150 * SCALE, 100 * SCALE], [20 * SCALE, 100 * SCALE]],
                     name='curve', cv_len=(0.5,0.4), angle=(90,), rel_len=0.8)
            .line([0, 100 * SCALE], 'linear2')
            .line([0, 0], 'linear3')
            
            .move([10, 10])
            .line([11, 10])
            .line([11, 11])
            .move([20, 10])
            .line([21, 10])
            .line([21, 11])
            .build())
    
    pg = BasicPathGenerator(path)
    md = core.EMPTY_ATTRS.with_fn(10)
    p2bc = Polyhedron2BuilderContext(pg, md)
    for r, points, paths in p2bc.get_paths():
        print(f'r={r}, points={points}, paths={paths}') 


@core.shape
@datatree
class LinearExtrude(ExtrudedShape):
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
                core.surface_args('azimuth', 'curve', az_angle=45, rh=0.05),
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
                )),
        'example4': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([_SCALE * 50, 0])
                    .qspline([(100 * _SCALE, 100 * _SCALE), (0, _SCALE * 50)], name='curve')
                    .line([_SCALE * 50, 0], 'linear1')
                    .build(),
                h=50,
                fn=80,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0, 0),
                core.surface_args('linear1', 0.5, 25 * _SCALE),
                core.surface_args('curve', 0, 0),
                core.surface_args('curve', 0.6, 0),
                core.surface_args('curve', 1, 0),
                )),
        'example5': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([5 * _SCALE, 0])
                    .line([50 * _SCALE, 0], 'linear1')
                    .arc_tangent_point([55 * _SCALE, 5 * _SCALE], name='curve1')
                    .line([55 * _SCALE, 50 * _SCALE], 'linear2')
                    .arc_tangent_point([50 * _SCALE, 55 * _SCALE], name='curve2')
                    .line([5 * _SCALE, 55 * _SCALE], 'linear3')
                    .arc_tangent_point([0 * _SCALE, 50 * _SCALE], name='curve3')
                    .line([0 * _SCALE, 5 * _SCALE], 'linear4')
                    .arc_tangent_point([5 * _SCALE, 0 * _SCALE], name='curve4')
                    .build(),
                h=55,
                fn=64,
                #slices=20,
                #twist=90,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('centre_of', 'curve1', 0, normal_segment='linear3'),
                core.surface_args('centre_of', 'curve2', 0),
                core.surface_args('centre_of', 'curve3', 0),
                core.surface_args('centre_of', 'curve4', 0)
                )),
        'example7': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([_SCALE * 50, 0])
                    .spline([
                        (100 * _SCALE, 100 * _SCALE), 
                        (100 * _SCALE, 100 * _SCALE), 
                        (0, _SCALE * 50)], name='curveX')
                    .line([_SCALE * 50, 0], 'linear1')
                    .build(),
                h=40 * _SCALE,
                fn=80,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0.5, 0),
                # core.surface_args('linear1', 0.5, 25 * _SCALE),
                core.surface_args('curveX', 0, 0),
                core.surface_args('curveX', 0.1, 0),
                core.surface_args('curveX', 0.2, 0),
                core.surface_args('curveX', 0.3, 0),
                core.surface_args('curveX', 0.4, 0),
                core.surface_args('curveX', 0.5, 0),
                core.surface_args('curveX', 0.6, 0),
                core.surface_args('curveX', 1, 0),
                core.surface_args('curveX', 1, 120),
                core.surface_args('azimuth', 'curveX', az_angle=0, rh=1),
                core.surface_args('azimuth', 'curveX', az_angle=2, rh=1 ),
                core.surface_args('azimuth', 'curveX', az_angle=20, rh=1),
                core.surface_args('azimuth', 'curveX', az_angle=30, rh=1),
                core.surface_args('azimuth', 'curveX', az_angle=40, rh=1),
                core.surface_args('azimuth', 'curveX', az_angle=140, rh=1),
                )),
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
    def edge(self, path_node_name, t=0, h=0, rh=None, align_twist=False, align_scale=False, apply_offset=True):
        '''Anchors to the edge and surface of the linear extrusion.
        Args:
            path_node_name: The path node name to attach to.
            t: 0 to 1 being the beginning and end of the segment. Numbers out of 0-1
               range will depart the path linearly.
            h: The absolute height of the anchor location.
            rh: The relative height (0-1).
            align_twist: Align the anchor for the twist factor.
            apply_offset: If True and the Path has an offset, then the offset will be
                           applied to the position. This provides an easy way to align
                           the anchor to the base Path of the extrusion.
        '''
        if rh is not None:
            h = h + rh * self.h
        op = self.path.name_map.get(path_node_name)
        if not op:
            raise UnknownOperationException(f'Could not find {path_node_name}')
        pos = self.to_3d_from_2d(op.position(t), h)
        normal_t = 0 if t < 0 else 1 if t > 1 else t 
        twist_vector = self.to_3d_from_2d(op.position(normal_t, apply_offset=apply_offset), 0)
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
    def centre_of(self, segment_name, t=0, rh=0, normal_segment=None, angle=0) -> l.GMatrix:
        '''Returns a transformation to the centre of the given segment (arc) with the
        direction aligned to the coordinate system. The rh parameter is the 
        relative height (0-1) of the arc centre. The normal_segment is the name of the
        segment to align the normal to. If not given the normal will be aligned to the
        segment given by segment_name at the given t value.'''

        angle = l.angle(angle)
        centre_2d = self.path.get_centre_of(segment_name)
        if centre_2d is None:
            raise UnknownOperationException(f'Segment has no "centre" property: {segment_name}')
        
        op = self.path.name_map.get(normal_segment if normal_segment else segment_name)
        if not op:
            raise UnknownOperationException(f'Could not find normal segment name "{normal_segment}"')
        normal = op.normal2d(t)
        
        return (l.translate([centre_2d[0], centre_2d[1], rh * self.h])
                * l.rotZSinCos(-normal[1], -normal[0])
                * l.ROTY_180
                * l.ROTZ_90
                * angle.rotZ)
        
    @core.anchor('Azimuth to segment start.')
    def azimuth(self, segment_name, az_angle: Union[float, l.Angle]=0, t_index: int=0, 
                t_end: bool=False, h=0, rh=None, align_twist=False, align_scale=False, 
                t_range: Tuple[float, float]=(0.0, 1.0), apply_offset=True) -> l.GMatrix:
        '''Returns a transformation to the point on the given curve segment (cubic, quadratic, 
        or arc) where the normal forms the specified azimuth from the start of the given t_range.
        This allows anchors to be located by angle along the curve segment.'''
        
        azimuth_t = self.path.azimuth_t(segment_name, az_angle, t_end, t_range)

        if not azimuth_t or len(azimuth_t) < t_index + 1:
            params_str = f'az_angle={az_angle} t_index={t_index} t_end={t_end} t_range={t_range}'
            if azimuth_t:
                # Requesting the second root but it's not there.
                raise AzimuthNotPossibleOnSegment(
                    f'Requested t_index not available for "{segment_name}" with {params_str}')
            raise AzimuthNotPossibleOnSegment(
                f'Azimuth not possible for segment "{segment_name}" with {params_str}')
            
        t = azimuth_t[t_index]
        return self.edge(segment_name, t, h, rh, align_twist, align_scale, apply_offset=apply_offset)
        

@core.shape
@datatree
class RotateExtrude(ExtrudedShape):
    '''Generates a circular/arc extrusion of a given Path.'''
    path: Path=core.dtfield(doc='The path to extrude.')
    angle: l.Angle | float=core.dtfield(360, doc='The sweep angle to extrude.')
    convexity: int=core.dtfield(10, doc='Openscad convexity parameter.')
    path_fn: int=None
    fn: int=None
    fa: float=None
    fs: float=None
    use_polyhedrons: bool=core.dtfield(
        None, doc='Use polyhedrons instead of rotate_extrude.')

    _SCALE=1.0
    
    EXAMPLE_SHAPE_ARGS=core.args(
        PathBuilder()
            .move([0, 0])
            .line([110 * _SCALE, 0], 'linear')
            .arc_tangent_point([10 * _SCALE, 100 * _SCALE], name='curve', angle=120)
            .line([0, 100 * _SCALE], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
        angle=120,
        fn=80,
        use_polyhedrons=True
        )

    EXAMPLE_ANCHORS=(
                core.surface_args('edge', 'linear', 0.5),
                core.surface_args('linear2', 0.5, 10),
                core.surface_args('linear2', 0, 40),
                core.surface_args('linear2', 1, 40),
                core.surface_args('linear3', 0.5, 20),
                core.surface_args('curve', 0, 45),
                core.surface_args('curve', 0.1, 40),
                core.surface_args('curve', 0.2, 40),
                core.surface_args('curve', 0.3, 40),
                core.surface_args('curve', 0.4, 40),
                core.surface_args('curve', 0.5, 40),
                core.surface_args('curve', 0.6, 40),
                core.surface_args('curve', 0.7, 40),
                core.surface_args('curve', 0.8, 40),
                core.surface_args('curve', 0.9, 40),
                core.surface_args('curve', 1, 70),
                core.surface_args('linear2', 0.1, 0.9),
                core.surface_args('linear2', 0.5, 0.9),
                core.surface_args('linear2', 1.0, 0.9),
                core.surface_args('centre_of', 'curve', 0),
                )
    
    EXAMPLES_EXTENDED={
        'example2': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([0, 0])
                    .line([110 * _SCALE, 0], 'linear')
                    .line([25 * _SCALE, 25 * _SCALE], 'linear1')
                    .arc_tangent_point([10 * _SCALE, 100 * _SCALE], name='curve', angle=-40)
                    .line([0, 100 * _SCALE], 'linear2')
                    .line([0, 0], 'linear3')
                    .build(),
                angle=120,
                fn=80,
                ),
            anchors=(
                core.surface_args('linear', 0.5),
                core.surface_args('linear', 1),
                core.surface_args('linear1', 0.5),
                core.surface_args('linear1', 1),
                core.surface_args('curve', 0.2),
                core.surface_args('curve', 1),)),
        'example4': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([_SCALE * 50, 0])
                    .qspline([(100 * _SCALE, 100 * _SCALE), (0, _SCALE * 50)], name='curve')
                    .line([_SCALE * 50, 0], 'linear1')
                    .build(),
                angle=120,
                fn=80,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0.5, 0),
                # core.surface_args('linear1', 0.5, 25 * _SCALE),
                core.surface_args('curve', 0, 0),
                core.surface_args('curve', 0.1, 0),
                core.surface_args('curve', 0.2, 0),
                core.surface_args('curve', 0.3, 0),
                core.surface_args('curve', 0.4, 0),
                core.surface_args('curve', 0.5, 0),
                core.surface_args('curve', 0.6, 0),
                core.surface_args('curve', 1, 0),
                core.surface_args('curve', 1, 120),
                core.surface_args('azimuth', 'curve', az_angle=10, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=20, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=30, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=40, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=50, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=0, angle=121),
                core.surface_args('azimuth', 'curve', az_angle=-5, t_end=True, angle=120),
                )),
        'example7': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([_SCALE * 50, 0])
                    .spline([
                        (100 * _SCALE, 100 * _SCALE), 
                        (100 * _SCALE, 100 * _SCALE), 
                        (0, _SCALE * 50)], name='curve')
                    .line([_SCALE * 50, 0], 'linear1')
                    .build(),
                angle=120,
                fn=80,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0.5, 0),
                # core.surface_args('linear1', 0.5, 25 * _SCALE),
                core.surface_args('curve', 0, 0),
                core.surface_args('curve', 0.1, 0),
                core.surface_args('curve', 0.2, 0),
                core.surface_args('curve', 0.3, 0),
                core.surface_args('curve', 0.4, 0),
                core.surface_args('curve', 0.5, 0),
                core.surface_args('curve', 0.6, 0),
                core.surface_args('curve', 1, 0),
                core.surface_args('curve', 1, 120),
                core.surface_args('azimuth', 'curve', az_angle=0, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=2, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=20, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=30, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=40, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=140, angle=120),
                core.surface_args('azimuth', 'curve', az_angle=-1, t_end=True, angle=120),
                )),
        'arc_azimuth': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([0, _SCALE * -25])
                    .line([_SCALE * 25, _SCALE * -25], 'linear1')
                    .arc_tangent_point([_SCALE * 25, _SCALE * -50], name='curve1')
                    .arc_tangent_point([_SCALE * 25, _SCALE * 50], angle=180, name='curve2')
                    .arc_tangent_point([_SCALE * 25, _SCALE * 25], angle=180, name='curve3')
                    .line([0, _SCALE * 25], 'linear2')
                    .line([0, _SCALE * -25], 'linear3')
                    .build(),
                angle=120,
                fn=80,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0.5, 0),
                core.surface_args('azimuth', 'curve1', az_angle=l.angle(-45), angle=120),
                core.surface_args('azimuth', 'curve1', az_angle=45, t_end=True, angle=120),
                core.surface_args('azimuth', 'curve2', az_angle=45, angle=120),
                core.surface_args('azimuth', 'curve2', az_angle=-45, t_end=True, angle=120),
                )),
        'arc_azimuth2': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([0, _SCALE * 25])
                    .line([_SCALE * 25, _SCALE * 25], 'linear1')
                    .arc_tangent_point([_SCALE * 25, _SCALE * 50], name='curve1')
                    .arc_tangent_point([_SCALE * 25, _SCALE * -50], angle=180, name='curve2')
                    .arc_tangent_point([_SCALE * 25, _SCALE * -25], angle=180, name='curve3')
                    .line([0, _SCALE * -25], 'linear2')
                    .line([0, _SCALE * 25], 'linear3')
                    .build(),
                angle=120,
                fn=80,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0.5, 0),
                # core.surface_args('azimuth', 'curve1', az_angle=45, angle=120),
                # core.surface_args('azimuth', 'curve1', az_angle=-45, t_end=True, angle=120),
                # core.surface_args('azimuth', 'curve2', az_angle=-45, angle=120),
                # core.surface_args('azimuth', 'curve2', az_angle=45, t_end=True, angle=120),
                )),
        'offset_ex': core.ExampleParams(
            description='An example of using the offset modifier with a Path containing a '
                        'variety of primitive segments.',
            shape_args=core.args(
                PathBuilder(path_modifier=PathModifier(trim_negx=True).round().add_offset(_SCALE * 8))
                    .move([5 * _SCALE, _SCALE * -25])
                    .line([_SCALE * 25, _SCALE * -25], 'linear1')
                    .arc_tangent_point([_SCALE * 25, _SCALE * -50], name='curve1')
                    .spline(
                        ([_SCALE * 50, _SCALE * -50], [_SCALE * 5, _SCALE * 50], [_SCALE * 25, _SCALE * 50]), 
                        angle=(0, 180), rel_len=0.5, name='curve2')
                    .qspline(([_SCALE * 55, _SCALE * 45], [_SCALE * 25, _SCALE * 25]), name='curve3')
                    .line([5 * _SCALE, _SCALE * 25], 'linear2')
                    .line([5 * _SCALE, _SCALE * -25], 'linear3')
                    .build(),
                angle=120,
                fn=80,
                use_polyhedrons=False
                ),
            anchors=(
                core.surface_args('linear1', 0.5, 0),
                core.surface_args('azimuth', 'curve1', az_angle=l.angle(-45), angle=120),
                core.surface_args('azimuth', 'curve1', az_angle=45, t_end=True, angle=120),
                core.surface_args('azimuth', 'curve2', az_angle=45, angle=120),
                core.surface_args('azimuth', 'curve2', az_angle=-45, t_end=True, angle=120),
                core.surface_args('curve3', 0.5),
                )),
        }
    
    def select_attrs(self, renderer):
        meta_data = renderer.get_current_attributes()
        if self.fn:
            return meta_data.with_fn(self.fn)
        if self.path_fn:
            return meta_data.with_fn(self.path_fn)
        return meta_data
    
    def select_path_attrs(self, renderer):
        meta_data = self.select_attrs(renderer)
        if self.path_fn:
            meta_data = meta_data.with_fn(self.path_fn)
        return meta_data
    
    def render(self, renderer):
        renderer.add_path(self.path)
        if self.use_polyhedrons or (self.use_polyhedrons is None and
            renderer.get_current_attributes().use_polyhedrons):
            return self.render_as_polyhedron(renderer)
        else:
            return self.render_rotate_extrude(renderer)

    def render_rotate_extrude(self, renderer):
        points = self.path.cleaned_polygons(self.select_path_attrs(renderer))
        if len(points) > 1:
            cpoints = np.concatenate(points)
            indexes = []
            count = 0
            for p in points:
                indexes.append([range(count, count + len(p))])
                count += len(p)
            polygon = renderer.model.Polygon(*cpoints, paths=indexes)
        else:
            polygon = renderer.model.Polygon(*points)
        # min_x, min_y, max_x, max_y = self.bounding_box(points)
        # if min_x < 0 and max_x > 0:
        #     # The path is can't be rotated around because it crosses the Y axis.
        #     # Create a bounding box around the part that crosses the Y axis
        #     # and difference that.
        #     if not self.path.path_modifier.trim_negx:
        #         raise ValueError('Path crosses Y axis and trim_negx is False.')
        #     sq = renderer.model.square([-min_x + EPSILON, max_y - min_y + EPSILON])
        #     tsq = renderer.model.translate([min_x - EPSILON, min_y - EPSILON / 2])(sq)
        #     polygon = renderer.model.difference()(polygon, tsq)
        params = core.fill_params(
            self, 
            renderer, 
            tuple(core.ARGS_XLATION_TABLE.keys()), 
            exclude=('path', 'path_fn', 'degrees', 'radians', 'use_polyhedrons'))

        params['angle'] = l.angle(self.angle).degrees() # Openscad uses degrees for angle.
        
        return renderer.add(renderer.model.rotate_extrude(**params)(polygon))
    
    # def bounding_box(self, points: np.array):
    #     '''Returns the bounding box of the given set of points.'''
    #     min_v = np.min(points, axis=1)[0]
    #     max_v = np.max(points, axis=1)[0]
    #     return (min_v[0], min_v[1], max_v[0], max_v[1])
    
    def generate_transforms(self, renderer):
        '''Generates a list of transforms for the given set of parameters.'''
        fn = self.select_attrs(renderer).fn
        segments = fn if fn else 16

        rotations = l.angle(self.angle).radians() / (np.pi * 2)
        if np.abs(rotations) > 1:
            rotations = np.sign(rotations)
        
        segments = int(np.abs(rotations) * segments)
        if segments < 4:
            segments = 4
            
        rot = np.pi * 2 * rotations / segments
        return rotations, (l.ROTX_90,) + tuple(
            l.rotZ(radians=rot * i) * l.ROTX_90
            for i in range(1, segments + 1))
        
    def render_as_polyhedron(self, renderer):
        builders = PolyhedronBuilder.create_builders_from_paths(
            self.path.cleaned_polygons(self.select_path_attrs(renderer)))
        
        rotations, transforms = self.generate_transforms(renderer)
        pos_dir = rotations < 0
        is_one_revolution = (np.absolute(rotations) + EPSILON) > 1
        for builder in builders:
            if is_one_revolution:
                builder.make_loop(transforms, pos_dir)
            else:
                builder.make_two_ended(transforms, pos_dir)
            renderer.add(
                renderer.model.polyhedron(
                    points=builder.get_points_3d(),
                    faces=builder.faces))
        return renderer

    def to_3d_from_2d(self, vec_2d, angle: float | l.Angle=0.):
        angle = l.angle(angle)
        return angle.rotZ * l.ROTX_90 * l.GVector([vec_2d[0], vec_2d[1], 0])
    
    def _z_radians_scale_align(self, rel_h, twist_vector):
        xelipse_max = self.scale[0] * rel_h + (1 - rel_h)
        yelipse_max = self.scale[1] * rel_h + (1 - rel_h)
        eliplse_angle = np.arctan2(xelipse_max * twist_vector.y, yelipse_max * twist_vector.x)
        circle_angle = np.arctan2(twist_vector.y, twist_vector.x)
        return eliplse_angle - circle_angle

    @core.anchor('Anchor to the path edge projected to surface.')
    def edge(self, path_node_name, t=0, angle=0, apply_offset=True):
        '''Anchors to the edge projected to the surface of the rotated extrusion.
        Args:
            path_node_name: The path node name to attach to.
            t: 0 to 1 being the beginning and end of the segment. Numbers out of 0-1
               range will depart the path linearly.
            angle: The angle along the rotated extrusion.
            apply_offset: If True and the Path has an offset, then the offset will be
                    applied to the position. This provides an easy way to align
                    the anchor to the base Path of the extrusion.
        '''
        angle: l.Angle = l.angle(angle)
        if path_node_name not in self.path.name_map:
            raise PathElelementNotFound(f'Could not find {path_node_name}')
        op = self.path.name_map.get(path_node_name)
        if op is None:
            raise PathElelementNotFound(f'Could not find {path_node_name}')
        normal = op.normal2d(t)
        pos = op.position(t, apply_offset=apply_offset)
        
        return (angle.rotZ
                     * l.ROTX_90  # Projection from 2D Path to 3D space
                     * l.translate([pos[0], pos[1], 0])
                     * l.ROTY_90  
                     * l.rotXSinCos(normal[1], -normal[0]))

    @core.anchor('Centre of the extrusion arc.')
    def centre(self):
        return l.IDENTITY
    
    @core.anchor('Centre of segment.')
    def centre_of(self, segment_name: Any, t: float=0, angle: l.Angle | float=0, normal_segment: Any=None) -> l.GMatrix:
        '''Returns a transformation to the centre of the given segment (arc) with the
        direction aligned to the coordinate system.'''

        centre_2d = self.path.get_centre_of(segment_name)
        if centre_2d is None:
            raise UnknownOperationException(f'Segment has no "centre" property: {segment_name}')
        
        op = self.path.name_map.get(normal_segment if normal_segment else segment_name)
        if not op:
            raise UnknownOperationException(f'Could not find normal segment name "{normal_segment}"')
        normal = op.normal2d(t)
        angle = l.angle(angle)
        return (angle.rotZ
                * l.ROTX_90  # Projection from 2D Path to 3D space
                * l.translate([centre_2d[0], centre_2d[1], 0])
                * l.rotZSinCos(-normal[1], -normal[0]))
        
    @core.anchor('Azimuth to segment start.')
    def azimuth(self, segment_name, az_angle: Union[float, l.Angle]=0,  t_index: int=0,
                t_end: bool=False, angle: float | l.Angle=0, 
                t_range: Tuple[float, float]=(0.0, 1.0), apply_offset=True) -> l.GMatrix:
        '''Returns a transformation to the point on the given curve segment (cubic, quadratic, 
        or arc) where the normal forms the specified azimuth from the start of the given t_range.
        This allows anchors to be located by angle along the curve segment.'''
        
        azimuth_t = self.path.azimuth_t(
            segment_name, az_angle, t_end, t_range)

        if not azimuth_t or len(azimuth_t) < t_index + 1:
            params_str = f'az_angle={az_angle} t_index={t_index} t_end={t_end} t_range={t_range}'
            if azimuth_t:
                # Requesting the second root but it's not there.
                raise AzimuthNotPossibleOnSegment(
                    f'Requested t_index not available for "{segment_name}" with {params_str}')
            raise AzimuthNotPossibleOnSegment(
                f'Azimuth not possible for segment "{segment_name}" with {params_str}')
            
        t = azimuth_t[t_index]
        return self.edge(segment_name, t, angle, apply_offset=apply_offset)
        

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=core.ModuleDefault(all=True)

if __name__ == "__main__":
    #test()
    core.anchorscad_main(False)
    
