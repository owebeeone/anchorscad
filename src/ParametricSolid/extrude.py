'''
Created on 7 Jan 2021

@author: gianni
'''

from collections.abc import Iterable
from dataclasses import dataclass, field
from types import FunctionType
from typing import List

from frozendict import frozendict

import ParametricSolid.core as core
import ParametricSolid.linear as l
import numpy as np
import pyclipper as pc


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


EPSILON=1e-6

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

LIST_2_FLOAT_OR_NONE = l.list_of(strict_float_or_none, len_min_max=(2, 2), fill_to_min='None')
LIST_2_INT_OR_NONE = l.list_of(strict_float_or_none, len_min_max=(2, 2), fill_to_min='None')
LIST_2_FLOAT = l.list_of(l.strict_float, len_min_max=(2, 3), fill_to_min=0.0)
LIST_3_FLOAT = l.list_of(l.strict_float, len_min_max=(3, 3), fill_to_min=0.0)
LIST_3X2_FLOAT = l.list_of(LIST_2_FLOAT, len_min_max=(3, 3), fill_to_min=None)
LIST_23X2_FLOAT = l.list_of(LIST_2_FLOAT, len_min_max=(2, 3), fill_to_min=None)

def _vlen(v):
    return np.sqrt(np.sum(v**2))

def _normalize(v):
    return v / _vlen(v)

def extentsof(p):
    return np.array((p.min(axis=0), p.max(axis=0)))


@dataclass(frozen=True)
class CubicSpline():
    '''Cubic spline evaluator, extents and inflection point finder.'''
    p: object
    dimensions: int=2
    
    COEFFICIENTS=np.array([
        [-1.,  3, -3,  1 ],
        [  3, -6,  3,  0 ],
        [ -3,  3,  0,  0 ],
        [  1,  0,  0,  0 ]])
    
    #@staticmethod
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
    
    class InvalidTypeForP(Exception):
        '''The parameter p must be a numpy.ndarray.'''
        
    def __post_init__(self):
        object.__setattr__(self, 'coefs', np.matmul(self.COEFFICIENTS, self.p))
    
    def _make_ta3(self, t):
        t2 = t * t
        t3 = t2 * t
        ta = [c * self.dimensions for c in [[t3], [t2], [t], [1]]]
        return ta
        
    def _make_ta2(self, t):
        t2 = t * t
        ta = [c * self.dimensions for c in [[t2], [t], [1], [0]]]
        return ta
    
    def evaluate(self, t):
        return np.sum(np.multiply(self.coefs, self._make_ta3(t)), axis=0)
    
  
    @classmethod
    def find_roots(cls, a, b, c, *, t_range=(0.0, 1.0)):
        '''Find roots of quaratic polynomial that are between t_range.'''
        # a, b, c are quadratic coefficients i.e. at^2 + bt + c
        if a == 0:
            # Degenerate curve is a linear. Only one possible root.
            if b == 0:
                # Degenerate curve is constant so there is no 0 gradient.
                return ()
            t = -c / b
            
            return (t,) if  t >= t_range[0] and t <= t_range[1] else ()
    
        b2_4ac = b * b - 4 * a * c;
        if b2_4ac < 0:
            # Complex roots - no answer.
            return ()
    
        sqrt_b2_4ac = np.sqrt(b2_4ac)
        two_a = 2 * a
    
        values = ((-b + sqrt_b2_4ac) / two_a, (-b - sqrt_b2_4ac) / two_a)
        return tuple(t for t in values if t >= t_range[0] and t <= t_range[1])
    
    # Solve for minima and maxima over t. There are two possible locations 
    # for each axis. The results for t outside of the bounds 0-1 are ignored
    # since the cubic spline is only interpolated in those bounds.
    def curve_maxima_minima_t(self, t_range=(0.0, 1.0)):
        '''Returns a dict with an entry for each dimension containing a list of
        t for each minima or maxima found.'''
        # Splines are defined only for t in the range [0..1] however the curve may
        # go beyond those points. Each axis has a potential of two roots.
        d_coefs = self.coefs * self._dcoeffs(1)
        return dict((i, self.find_roots(*(d_coefs[0:3, i]), t_range=t_range)) 
                    for i in range(self.dimensions))
    
    
    def cuve_inflexion_t(self, t_range=(0.0, 1.0)):
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
        vr = np.array([d[dims[0]], -d[dims[1]]])
        l = np.sqrt(np.sum(vr**2))
        return vr / l
    
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

def _normal_of_2d(v1, v2, dims=[0, 1]):
    vr = np.array(v1)
    vr[dims[0]] = v1[dims[1]] - v2[dims[1]]
    vr[dims[1]] = v2[dims[0]] - v1[dims[0]]
    l = np.sqrt(np.sum(vr * vr))
    return vr / l

@dataclass(frozen=True)
class OffsetType:
    offset_type: int
    
OFFSET_ROUND=OffsetType(pc.JT_ROUND)
OFFSET_MITER=OffsetType(pc.JT_MITER)
OFFSET_SQUARE=OffsetType(pc.JT_SQUARE)

def adder(a, b):
    if a is None:
        return None
    if b is None:
        return a
    return a + b


class OpBase:
    '''Base class for path operations (move, line, arc and spline).
    '''
    # Implementation state should consist of control points that can be easily 
    # transformed via a matrix multiplication.
    
    def _as_non_defaults_dict(self):
        return dict((k, getattr(self, k)) 
                    for k in self.__annotations__.keys() 
                        if not getattr(self, k) is None and k != 'prev_op')
        
    def is_move(self):
        return False

    def transform(self, m):
        raise NotImplemented('Derived class must implement this.')

@dataclass
class OpMetaData():
    '''The Op and parameters used to generate the point.'''
    op: OpBase
    point: tuple
    count: int=None
    t: float=None
    dupe_ops_md: list=field(default_factory=list, init=False)

    
@dataclass()
class MapBuilder:
    '''Builder for a map of points to the OpMetaData associated with the point.'''
    opmap: List[OpMetaData]=field(default_factory=list)
    
    def append(self, op: OpBase, point: tuple, count: int=None, t: float=None):
        self.opmap.append(OpMetaData(op, point, count, t))


@dataclass()
class NullMapBuilder:
    '''A null builder'''
    opmap: List[OpMetaData]=None
    
    def append(self, op: OpBase, point: tuple, count: int=None, t: float=None):
        pass


@dataclass(frozen=True)
class Path():
    '''Encapsulated a "path" generate by a list of path "Op"s (move, line, arc etc).
    Each move op indicates a separate path. This can be a hole (anticlockwise) or a
    polygon (clockwise).
    A Path can generate a polygon with a differing number of facets or extents 
    (bounding box) or can be transformed into another path using an l.GMatrix.
    
    '''
    ops: tuple
    name_map: frozendict

    def get_node(self, name):
        return self.name_map.get(name, None)
    
    def extents(self):
        itr = iter(self.ops)
        extnts = extentsof(next(itr).extremes())
        for op in itr:
            ops_extremes = op.extremes()
            cated = np.concatenate((ops_extremes, extnts))
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
        points, ranges, _ = self.polygons_with_map_ops(meta_data)
        if ranges:
            return points, ranges
        return (points,)

    def transform_to_builder(self, 
                             m, 
                             builder=None, 
                             suffix=None, 
                             appender=adder,
                             skip_first_move=None):
        '''Returns a PathBuilder with the new transformed path.
        Args:
          m: A GMatrix to transform the points.
          builder: Optional builder to append path to.
          suffix: Names from this path are suffixed by this.
          appender: Function to perform appending. Default is adder.
          skip_first_move: Skips the first move operation.
        '''
        if not builder:
            skip_first_move = False if skip_first_move is None else skip_first_move
            builder = PathBuilder()
        else:
            skip_first_move = True if skip_first_move is None else skip_first_move
        
        # Perform skip on first op if it is a move.
        iterops = iter(self.ops)
        if skip_first_move:
            try:
                op = next(iterops)
                if not op.is_move():
                    builder.add_op_with_params(
                        op.transform(m), appender(op.name, suffix))
            except StopIteration:
                pass
        
        for op in iterops:
            builder.add_op_with_params(
                op.transform(m), appender(op.name, suffix))

        return builder
            
    def transform(self, m):
        return self.transform_to_builder(m).build()


def make_offset_polygon2d(path, size, offset_type, meta_data, offset_meta_data=None):
    if not offset_meta_data:
        offset_meta_data = meta_data
    points, start_indexes, _ = path.build(meta_data)
    
    start_indexes = start_indexes + [len(points),]
    pco = pc.PyclipperOffset()
    scaled_size = pc.scale_to_clipper(size)
    pco.ArcTolerance = np.abs(scaled_size) * (1 -  np.cos(np.pi / offset_meta_data.fn))
    for i in range(len(start_indexes) - 1):
        pco.AddPath(
            pc.scale_to_clipper(points[start_indexes[i]:start_indexes[i+1]]), 
            offset_type.offset_type,
            pc.ET_CLOSEDPOLYGON)
    result = pco.Execute(scaled_size)
    
    return pc.scale_from_clipper(result)

    
def to_gvector(np_array):
    if len(np_array) == 2:
        return l.GVector([np_array[0], np_array[1], 0, 1])
    else:
        return l.GVector(np_array)
    
    
# Solution derived from https://planetcalc.com/8116/
def solve_circle_3_points(p1, p2, p3): 
    '''Returns the centre and radius of a circle that passes the 3 given points or and empty
    tuple if the points are colinear.'''
    
    p = np.array([p1, p2, p3])
    
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
    
    l = np.array([a, b, c])
    if a < 0:
        l = -l
    elif a == 0 and b < 0:
        l = -l
        
    return l, p, t

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
        dir = np.array([-pdn[1], pdn[0]]) #+90 degrees
    else:
        dir = np.array([pdn[1], -pdn[0]]) #-90 degrees
    centre = (p1 + p2) / 2 + dir * opp_side
    return (centre, r)

def _less_than(a, b):
    return (a - b) < EPSILON

def _greater_than(a, b):
    return (a - b) > EPSILON

@dataclass()
class CircularArc:
    start_angle: float  # Angles in radians
    sweep_angle: float   # Angles in radians
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
    
    def extents(self):
        extentsof(self.extremes())

    def evaluate(self, t):
        angle = t * self.sweep_angle + self.start_angle
        return np.array([np.cos(angle), np.sin(angle)]) * self.radius + self.centre


@dataclass()
class PathBuilder():
    ops: list
    name_map: dict
    multi: bool=False
    
    
    @dataclass(frozen=True)
    class _LineTo(OpBase):
        '''Line segment from current position.'''
        point: np.array
        prev_op: object=field(
            default=None, 
            init=True, 
            repr=False, 
            hash=False, 
            compare=False, 
            metadata=None)
        name: str=None
            
        def lastPosition(self):
            return self.point
        
        def populate(self, path_builder, start_indexes, map_builder, meta_data):
            path_builder.append(self.point)
            map_builder.append(self, self.point, 1, 1.0)
            
        def direction(self, t):
            return self.point - self.prev_op.lastPosition()
        
        def direction_normalized(self, t):
            return _normalize(self.direction(t))
        
        def normal2d(self, t, dims=[0, 1]):
            return _normal_of_2d(self.prev_op.lastPosition(), self.point, dims)
        
        def extremes(self):
            p0 = self.prev_op.lastPosition()
            p1 = self.point
            return np.array((p0, p1))
        
        def extents(self):
            return extentsof(self.extremes())
            
        def position(self, t):
            return self.point + (t - 1) * self.direction(0)
        
        def transform(self, m):
            params = self._as_non_defaults_dict()
            params['point'] = (m * to_gvector(self.point)).A[0:len(self.point)]
            return (self.__class__, params)
            
    
    @dataclass(frozen=True)
    class _MoveTo(OpBase):
        '''Move to position.'''
        point: np.array
        dir: np.array=None
        prev_op: object=field(
            default=None, 
            init=True, 
            repr=False, 
            hash=False, 
            compare=False, 
            metadata=None)
        name: str=None
            
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
            return None
        
        def extremes(self):
            p = self.point
            return np.array((p, p))
        
        def extents(self):
            return np.array([self.point, self.point])
        
        def position(self, t):
            return self.point  # Move is associated only with the move point. 

        def transform(self, m):
            params = self._as_non_defaults_dict()
            params['point'] = (m * to_gvector(self.point)).A[0:len(self.point)]
            return (self.__class__, params)
        
        def is_move(self):
            return True
            

    @dataclass(frozen=True)
    class _SplineTo(OpBase):
        '''Cubic Bezier Spline to.'''
        points: np.array
        prev_op: object=field(
            default=None, 
            init=True, 
            repr=False, 
            hash=False, 
            compare=False, 
            metadata=None)
        name: str=None
        meta_data: object=None
        
        def __post_init__(self):
            to_cat = [[self.prev_op.lastPosition()],  self.points]
            spline_points = np.concatenate(to_cat)
            object.__setattr__(self, 'spline', CubicSpline(spline_points))
            
        def lastPosition(self):
            return self.points[2]
            
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
        
        def position(self, t):
            if t < 0:
                return self.direction(0) * t + self.prev_op.lastPosition()
            elif t > 1:
                return self.direction(1) * t + self.points[2]
            return self.spline.evaluate(t)
        
        def transform(self, m):
            points = list((m * to_gvector(p)).A[0:len(p)] for p in self.points)
            points = np.array(LIST_23X2_FLOAT(points))
            params = self._as_non_defaults_dict()
            params['points'] = points
            return (self.__class__, params)
    
        
    @dataclass(frozen=True)
    class _ArcTo(OpBase):
        '''Draw a circular arc.'''
        end_point: np.array
        centre: np.array
        path_direction: bool
        prev_op: object=field(
            default=None, 
            init=True, 
            repr=False, 
            hash=False, 
            compare=False, 
            metadata=None)
        name: str=None
        meta_data: object=None
        
        def __post_init__(self):
            
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
            
        def lastPosition(self):
            return self.end_point
            
        def populate(self, path_builder, start_indexes, map_builder, meta_data):
            if self.meta_data and self.meta_data.fn:
                meta_data = self.meta_data
    
            count = meta_data.fn
            if not count:
                count = 10
                
            for i in range(1, count + 1):
                t = float(i) / float(count)
                point = self.arcto.evaluate(t)
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
        
        def position(self, t):
            if t < 0:
                return self.direction(0) * t + self.prev_op.lastPosition()
            elif t > 1:
                return self.direction(1) * t + self.end_point
            return self.arcto.evaluate(t)
        
        def transform(self, m):
            end_point = (m * to_gvector(self.end_point)).A[0:len(self.end_point)]
            centre = (m * to_gvector(self.centre)).A[0:len(self.centre)]
            params = {
                'end_point': end_point,
                'centre': centre,
                'path_direction': self.path_direction}
            return (self.__class__, params)
    
    
    def __init__(self, multi=False):
        self.ops = []
        self.name_map = {}
        self.multi = multi
        
    def add_op(self, op):
        if op.name:
            if op.name in self.name_map:
                raise DuplicateNameException(f'Duplicate name ({op.name!r}) is already used.')
            self.name_map[op.name] = op
        self.ops.append(op)
        return self
    
    def add_op_with_params(self, op_parts, op_name=None):
        params_dict = op_parts[1]
        params_dict['prev_op'] = self.last_op()
        if op_name:
            params_dict['name'] = op_name
        return self.add_op((op_parts[0])(**params_dict))

    def last_op(self):
        return self.ops[-1] if self.ops else None
        
    def move(self, point, name=None, direction=None):
        if not self.multi and self.ops:
            raise MoveNotAllowedException(f'Move is not allowed in non multi-path builder.')
        if direction:
            direction = np.array(LIST_2_FLOAT(direction))
        return self.add_op(self._MoveTo(np.array(LIST_2_FLOAT(point)),
                                        dir=direction,
                                        prev_op=self.last_op(), name=name))
                        
    def line(self, point, name=None):
        '''A line from the current point to the given point is added.'''
        assert len(self.ops) > 0, "Cannot line to without starting point"
        return self.add_op(self._LineTo(np.array(LIST_2_FLOAT(point)), 
                                        prev_op=self.last_op(), name=name))
        
    def stroke(self,
               length,
               degrees=0, 
               radians=None, 
               sinr_cosr=None,
               xform=None, 
               name=None):
        '''A line from the current point to a length away given
        by following the tangent from the previous op transformed by rotating
        by angle or a GMatrix xform.'''
        assert len(self.ops) > 0, "Cannot line to without starting point"
        d_vector = to_gvector(self.last_op().direction_normalized(1.0))
        if degrees or radians or sinr_cosr:
            d_vector = l.rotZ(degrees=degrees, 
                              radians=radians, 
                              sinr_cosr=sinr_cosr) * d_vector
        if xform:
            d_vector = xform * d_vector
            
        point = d_vector * length + to_gvector(self.last_op().lastPosition())
        return self.add_op(self._LineTo(point.A[:2], 
                                        prev_op=self.last_op(), name=name))
            
    def relative_line(self,
               relative_pos,
               name=None):
        '''A line from the current point to the relative X,Y position given.'''
        point = (np.array(LIST_2_FLOAT(relative_pos)) 
                 + self.last_op().lastPosition())
        return self.add_op(self._LineTo(point[:2], 
                                        prev_op=self.last_op(), name=name))

    def spline(self, points, name=None, metadata=None, 
               cv_len=(None, None), degrees=(0, 0), radians=(0, 0), rel_len=None):
        '''Adds a spline node to the path.
        Args:
            points: Either 3 point list (first control point is the last point) or a 
                    2 point list and cv_len with the first element set to the distance 
                    the control point follows along the previous operations last direction.
            cv_len: If provided will force the length of the control point (1 an 2)
                    to be the given length.
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
        degrees = LIST_2_INT_OR_NONE(degrees) if degrees else (None, None)
        radians = LIST_2_INT_OR_NONE(radians) if radians else (None, None)
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
        if not rel_len is None:
            l = np.sqrt(np.sum((cv0 - cv3)**2))
            cv_len = tuple(rel_len * l if v is None else v * l * rel_len for v in cv_len)
        cv1 = self.squeeze_and_rot(cv0, cv1, cv_len[0], degrees[0], radians[0])
        cv2 = self.squeeze_and_rot(cv3, cv2, cv_len[1], degrees[1], radians[1])
        
        points = np.array(LIST_3X2_FLOAT([cv1, cv2, cv3]))
        return self.add_op(
            self._SplineTo(points, prev_op=self.last_op(), name=name, meta_data=metadata))
        
    def arc_tangent_radius_sweep(self,
                                 radius,
                                 sweep_angle_degrees=0,
                                 sweep_angle_radians=None,
                                 sweep_sinr_cosr=None,
                                 sweep_direction=None,
                                 side=False, 
                                 degrees=0, 
                                 radians=None, 
                                 direction=None, 
                                 sinr_cosr=None,
                                 name=None,
                                 metadata=None):
        '''Defines a circular arc starting at the previous operator's end point
        with the given direction and sweeping the given sweep angle.'''
        start = self.last_op().lastPosition()
        if direction is None:
            direction = self.last_op().direction_normalized(1.0)
        else:
            direction = _normalize(direction)
        
        t_dir = (
            l.rotZ(degrees=degrees, radians=radians, sinr_cosr=sinr_cosr)
            * to_gvector(direction))
        direction = t_dir.A[0:len(direction)]
        centre, _ = solve_circle_tangent_radius(start, direction, radius, side)

        n_start = (start - centre) / radius
        cos_s = n_start[0]
        sin_s = n_start[1]
        
        if sweep_angle_radians is None:
            sweep_angle_radians = sweep_angle_degrees * np.pi / 180
        
        if not sweep_sinr_cosr is None:
            sin_sweep, cos_sweep = sweep_sinr_cosr
            assert not sweep_direction is None, 'If sweep_sinr_cosr is specified a ' \
                'sweep_direction must also be specified.'
            path_direction = sweep_direction
        else:
            sin_sweep = np.sin(sweep_angle_radians)
            cos_sweep = np.cos(sweep_angle_radians)
            path_direction = sweep_angle_radians >= 0
        
        cos_e = cos_s * cos_sweep - sin_s * sin_sweep
        sin_e = sin_s * cos_sweep + sin_sweep * cos_s
        last = np.array([cos_e * radius + centre[0], sin_e * radius + centre[1]])
        
        
        return self.add_op(self._ArcTo(
            last, centre, path_direction, 
            prev_op=self.last_op(), name=name, meta_data=metadata))
        
    
    def arc_centre_sweep(self,
                         centre, 
                         sweep_angle_degrees=0,
                         sweep_angle_radians=None,
                         name=None,
                         metadata=None):
        '''Defines a circular arc starting at the previous operator's end point
        and sweeping the given angle about the given centre.'''
        start = self.last_op().lastPosition()
        
        centre = np.array(centre)
        t_start = start - centre
        radius = _vlen(t_start)
        n_start = t_start / radius
        cos_s = n_start[0]
        sin_s = n_start[1]
        
        if sweep_angle_radians is None:
            sweep_angle_radians = sweep_angle_degrees * np.pi / 180
            
        sin_sweep = np.sin(sweep_angle_radians)
        cos_sweep = np.cos(sweep_angle_radians)
        
        cos_e = cos_s * cos_sweep - sin_s * sin_sweep
        sin_e = sin_s * cos_sweep + sin_sweep * cos_s
        last = np.array([cos_e * radius + centre[0], sin_e * radius + centre[1]])
        
        path_direction = sweep_angle_degrees >= 0

        return self.add_op(self._ArcTo(
            last, centre, path_direction, prev_op=self.last_op(), name=name, meta_data=metadata))
        
        
    def arc_points_radius(self, last, radius, is_left=True, direction=None, name=None, metadata=None):
        '''Defines a circular arc starting at the previous operator's end point
        and ending at last with the given radius.'''
        start = self.last_op().lastPosition()
        centre, _ = solve_circle_points_radius(start, last, radius, is_left)
        if centre is None:
            raise UnableToFitCircleWithGivenParameters(
                f'Unable to fit circle, radius={radius}, start={start} last={last}.')
        if direction == None:
            direction = not is_left
        return self.add_op(self._ArcTo(
            last, centre, direction, prev_op=self.last_op(), name=name, meta_data=metadata))
    
    def arc_points(self, middle, last, name=None, direction=None, metadata=None):
        '''Defines a circular arc starting at the previous operator's end point
        and passing through middle and ending at last.'''
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
        if not direction is None:
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
        
        return self.add_op(self._ArcTo(
            last, centre, path_direction, prev_op=self.last_op(), name=name, meta_data=metadata))
    
    def arc_tangent_point(self, last, degrees=0, radians=None, direction=None, 
                          name=None, metadata=None):
        '''Defines a circular arc starting at the previous operator's end point
        and ending at last. The tangent (vector given by the direction parameter or
        if not provided by the last segment's direction vector) may be optionally
        rotated by the given angle (degrees or radians).'''
        start = self.last_op().lastPosition()
        if direction is None:
            direction = self.last_op().direction_normalized(1.0)
        else:
            direction = _normalize(np.array(direction))
        
        t_dir = (
            l.rotZ(degrees=degrees, radians=radians) * to_gvector(direction))
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
            last, centre, path_direction, 
            prev_op=self.last_op(), name=name, meta_data=metadata))
    
    def squeeze_and_rot(self, point, control, cv_len, degrees, radians):
        if cv_len is None and not degrees and not radians:
            return control
        gpoint = l.GVector(LIST_3_FLOAT(point))
        gcontrol = l.GVector(LIST_3_FLOAT(control))
        g_rel = (gcontrol - gpoint)
        if not cv_len is None and g_rel.length() > EPSILON:
            g_rel = g_rel.N * cv_len

        if radians:
            g_rel = l.rotZ(radians=radians) * g_rel
        elif degrees:
            g_rel = l.rotZ(degrees=degrees) * g_rel
            
        return (gpoint + g_rel).A[0:len(point)]
        

    def get_node(self, name):
        return self.name_map.get(name, None)
    
    def build(self):
        return Path(tuple(self.ops), frozendict(self.name_map))
    

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

@dataclass
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
    
    
@dataclass
class PolyhedronBuilder:
    ctxt: PolyhedronBuilderContext
    
    def __post_init__(self):
        self.points = []
        self.faces = []
        
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
        self.add_end_face(first_offs, True == direction)
        self.add_end_face(last_offs, False == direction)

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
        raise NotImplemented
    
    def get_polygons_at(self, r):
        '''Returns the 'polygons' (the result of Path.polygons()) for a given r
        where r is between 0 and 1.'''
        raise NotImplemented


@dataclass
class BasicPathGenerator(PathGenerator):
    '''Provides an isomorphic path.'''
    path: Path
    polygons: tuple=field(init=False)
    
    def get_r_generator(self, metadata):
        self.polygons = self.path.polygons(metadata)
        if len(self.polygons) == 1:
            self.polygons = self.polygons + (None,)
        fn = metadata.fn
        return (i / fn for i in range(fn + 1))
    
    def get_polygons_at(self, r):
        return self.polygons


@dataclass
class Polyhedron2BuilderContext:
    path_generator: PathGenerator
    metadata: object
    
    def get_paths(self):
        return ((r,) + self.path_generator.get_polygons_at(r) 
                for r 
                in self.path_generator.get_r_generator(self.metadata))



@dataclass
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
                     name='curve', cv_len=(0.5,0.4), degrees=(90,), rel_len=0.8)
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
    

@core.shape('linear_extrude')
@dataclass
class LinearExtrude(ExtrudedShape):
    '''Generates a linear extrusion of a given Path.'''
    path: Path
    h: float=100
    twist: float=0.0
    slices: int=4
    scale: float=(1.0, 1.0)  # (x, y)
    fn: int=None
    use_polyhedrons: bool=None
    
    SCALE=2
    
    EXAMPLE_SHAPE_ARGS=core.args(
        PathBuilder()
            .move([0, 0])
            .line([100 * SCALE, 0], 'linear')
            .spline([[150 * SCALE, 100 * SCALE], [20 * SCALE, 100 * SCALE]],
                     name='curve', cv_len=(0.5,0.4), degrees=(90,), rel_len=0.8)
            .line([0, 100 * SCALE], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
        h=80,
        fn=30,
        twist=45,
        slices=40,
        scale=(1, 0.3),
        use_polyhedrons=False
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
                    .line([50 * SCALE, 0], 'linear1')
                    .line([50 * SCALE, 50 * SCALE], 'linear2')
                    .line([0, 50 * SCALE], 'linear3')
                    .line([0, 0], 'linear4')
                    .build(),
                h=50,
                ),
            anchors=(
                core.surface_args('linear1', 0, 0),
                core.surface_args('linear1', 0.5, 25 * SCALE),
                core.surface_args('linear2', 0, 0),
                core.surface_args('linear2', 1, 0),
                )),
        'example3': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([0, 0])
                    .line([50 * SCALE, 0], 'linear1')
                    .arc_tangent_point([0, 50 * SCALE], name='curve', degrees=90)
                    .line([0, 0], 'linear4')
                    .build(),
                h=50,
                fn=80
                ),
            anchors=(
                core.surface_args('linear1', 0, 0),
                core.surface_args('linear1', 0.5, 25 * SCALE),
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
        if self.use_polyhedrons or (self.use_polyhedrons is None and
            renderer.get_current_attributes().use_polyhedrons):
            return self.render_as_polyhedron(renderer)
        else:
            return self.render_as_linear_extrude(renderer)

    def render_as_linear_extrude(self, renderer):
        polygon = renderer.model.Polygon(*self.path.polygons(
            self if self.fn else renderer.get_current_attributes()))
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
        points_paths = self.path.polygons(
            self if self.fn else renderer.get_current_attributes())
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


@core.shape('arc_extrude')
@dataclass
class RotateExtrude(ExtrudedShape):
    '''Generates a circular/arc extrusion of a given Path.'''
    path: Path
    degrees: float=360
    radians: float=None
    convexity: int=10
    path_fn: int=None
    fn: int=None
    fa: float=None
    fs: float=None
    use_polyhedrons: bool=None

    SCALE=1.0
    
    EXAMPLE_SHAPE_ARGS=core.args(
        PathBuilder()
            .move([0, 0])
            .line([110 * SCALE, 0], 'linear')
            .arc_tangent_point([10 * SCALE, 100 * SCALE], name='curve', degrees=120)
            .line([0, 100 * SCALE], 'linear2')
            .line([0, 0], 'linear3')
            .build(),
        degrees=120,
        fn=80,
        use_polyhedrons=False
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
                )
    
    EXAMPLES_EXTENDED={
        'example2': core.ExampleParams(
            shape_args=core.args(
                PathBuilder()
                    .move([0, 0])
                    .line([110 * SCALE, 0], 'linear')
                    .line([25 * SCALE, 25 * SCALE], 'linear1')
                    .arc_tangent_point([10 * SCALE, 100 * SCALE], name='curve', degrees=-40)
                    .line([0, 100 * SCALE], 'linear2')
                    .line([0, 0], 'linear3')
                    .build(),
                degrees=120,
                fn=80,
                ),
            anchors=(
                core.surface_args('linear', 0.5),
                core.surface_args('linear', 1),
                core.surface_args('linear1', 0.5),
                core.surface_args('linear1', 1),
                core.surface_args('curve', 0.2),
                core.surface_args('curve', 1),))
        }
    
    def select_attrs(self, renderer):
        if self.path_fn:
            return core.ModelAttributes(fn=self.path_fn)
        if self.fn:
            return core.ModelAttributes(fn=self.fn)
        return renderer.get_current_attributes()
    
    def select_path_attrs(self, renderer):
        if self.path_fn:
            return core.ModelAttributes(fn=self.path_fn)
        return self.select_attrs(renderer)
    
    def render(self, renderer):
        if self.use_polyhedrons or (self.use_polyhedrons is None and
            renderer.get_current_attributes().use_polyhedrons):
            return self.render_as_polyhedron(renderer)
        else:
            return self.render_rotate_extrude(renderer)

    def render_rotate_extrude(self, renderer):
        polygon = renderer.model.Polygon(
            *self.path.polygons(self.select_path_attrs(renderer)))
        params = core.fill_params(
            self, 
            renderer, 
            tuple(core.ARGS_XLATION_TABLE.keys()), 
            exclude=('path', 'path_fn', 'degrees', 'radians', 'use_polyhedrons'))
        angle = self.degrees
        if self.radians:
            angle = self.radians * 180 / np.pi
        params['angle'] = angle
        
        return renderer.add(renderer.model.rotate_extrude(**params)(polygon))
    
    def generate_transforms(self, renderer):
        '''Generates a list of transforms for the given set of parameters.'''
        fn = self.select_attrs(renderer).fn
        segments = fn if fn else 16
        radians = self.radians
        if radians is None:
            radians = np.pi * self.degrees / 180.0
        
        rotations = radians / (np.pi * 2)
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
            self.path.polygons(self.select_path_attrs(renderer)))
        
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

    def to_3d_from_2d(self, vec_2d, angle=0., degrees=0, radians=None):
        return l.rotZ(
            degrees=degrees, radians=radians) * l.rotX(90) * l.GVector([vec_2d[0], vec_2d[1], 0])
    
    def _z_radians_scale_align(self, rel_h, twist_vector):
        xelipse_max = self.scale[0] * rel_h + (1 - rel_h)
        yelipse_max = self.scale[1] * rel_h + (1 - rel_h)
        eliplse_angle = np.arctan2(xelipse_max * twist_vector.y, yelipse_max * twist_vector.x)
        circle_angle = np.arctan2(twist_vector.y, twist_vector.x)
        return eliplse_angle - circle_angle

    @core.anchor('Anchor to the path edge projected to surface.')
    def edge(self, path_node_name, t=0, degrees=0, radians=None):
        '''Anchors to the edge projected to the surface of the rotated extrusion.
        Args:
            path_node_name: The path node name to attach to.
            t: 0 to 1 being the beginning and end of the segment. Numbers out of 0-1
               range will depart the path linearly.
            degrees or radians: The angle along the rotated extrusion.
        '''
        op = self.path.name_map.get(path_node_name)
        normal = op.normal2d(t)
        pos = op.position(t)

        return (l.rotZ(degrees=degrees, radians=radians)
                     * l.ROTX_90  # Projection from 2D Path to 3D space
                     * l.translate([pos[0], pos[1], 0])
                     * l.ROTY_90  
                     * l.rotXSinCos(normal[1], -normal[0]))
    
    @core.anchor('Centre of the extrusion arc.')
    def centre(self):
        return l.IDENTITY

if __name__ == "__main__":
    #test()
    core.anchorscad_main(False)
    
