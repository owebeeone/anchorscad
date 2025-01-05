'''
Linear algebra tools for 3D transformations.

This is not a generic 3D matrix library but is designed to work with the limitations of
OpenScad's multmatrix transform function. It will perform all linear non skewing 3D
linear transformations.

Examples:

from linear import *

>>> rotX(90) * GVector([1, 2, 3])
GVector([1.0, -3.0, 2.0, 1.0])

# Because floating point numbers are imprecise, there is an 
# is_approx_equal function to handle the resulting small inexactness.
# Rotation by 90, 3 times is the same as rotating back 90.
>>> (rotX(90) * rotX(90) * rotX(90)).is_approx_equal(rotX(-90))
True

# Rotations are cumulative.
>>> (rotX(90) * rotX(90) * rotX(90) * rotX(90)).is_approx_equal(IDENTITY)
True

# Rotate about an arbitrary axis.
>>> rotV([1, 1, 0], 45) * GVector([0, 0, 1])
GVector([0.4999999999999999, -0.4999999999999999, 0.7071067811865476, 1.0])

'''

import numbers
try:    
    from types import NoneType
except ImportError:
    NoneType = None.__class__
import numpy as np
from typing import Callable, Tuple, Any, Union, List
from dataclasses import dataclass, MISSING
from abc import ABC, abstractmethod
import builtins


def _field_assign(obj, name, value):
    '''Field assignment that works on frozen objects.'''
    builtins.object.__setattr__(obj, name, value)


# Exceptions for dealing with argument checking.
class BaseException(Exception):
    '''Base exception functionality'''


class ConversionException(BaseException):
    '''Exception for conversion errors.'''


class MatrixShapeError(BaseException):
    '''Thrown when attempting to use a matrix of the wrong dimensions.'''


class MatrixInvalidError(BaseException):
    '''Failed consistency check of GMatrix.'''


class VectorInvalidError(BaseException):
    '''Failed consistency check for GVector.'''
    

def to_radians(degs: float) -> float:
    '''Convert degrees to radians.'''
    return degs * np.pi / 180.0

def to_degrees(radians: float) -> float:
    '''Convert radians to degrees.'''
    return radians * 180.0 / np.pi

def list_of(typ: Callable[[Any], Any], len_min_max: Tuple[int, int] = (3, 3), fill_to_min: Any = MISSING) -> Callable[[Any], list]:
    '''Defines a converter for an iterable to a list of elements of a given type.
    Args:
        typ: The type of list elements.
        len_min_max: A tuple of the (min,max) length, (0, 0) indicates no limits.
        fill_to_min: If the provided list is too short then use this value.
    Returns:
        A function that performs the conversion.
    '''
    description = 'list_of(%s, len_min_max=%r, fill_to_min=%r)' % (
        typ.__name__, len_min_max, fill_to_min)

    def list_converter(value: Any) -> list:
        '''Converts provided value as a list of the given type.
        value: The value to be converted
        '''
        converted_value = []
        for v in value:
            if len_min_max[1] and len(converted_value) >= len_min_max[1]:
                raise ConversionException(
                    'provided length too large, max is %d' % len_min_max[1])
            converted_value.append(typ(v))
        if len_min_max[0] and len(value) < len_min_max[0]:
            if fill_to_min is MISSING:
                raise ConversionException(
                    'provided length (%d) too small and fill_to_min is None, min is %d'
                    % (len(converted_value), len_min_max[0]))
            fill_converted = typ(fill_to_min) if fill_to_min is not None else None
            for _ in range(len_min_max[0] - len(converted_value)):
                converted_value.append(fill_converted)
        return converted_value

    list_converter.__name__ = description
    return list_converter


def strict_float(v: Union[int, float]) -> np.float64:
    '''Converter for a floating point value. Specifically does not allow str.
    Returns a numpy.float64 value.
    '''
    if isinstance(v, str):
        raise TypeError(
            'Was provided a string value but expecting a numeric value')
    return np.float64(v)

LIST_2_FLOAT = list_of(strict_float, len_min_max=(2, 2), fill_to_min=1.0)
LIST_3_FLOAT = list_of(strict_float, len_min_max=(3, 3), fill_to_min=1.0)
LIST_4_FLOAT = list_of(strict_float, len_min_max=(4, 4), fill_to_min=0.0)
LIST_3_4_FLOAT = list_of(strict_float, len_min_max=(3, 4), fill_to_min=None)
LIST_3_4X4_FLOAT = list_of(LIST_4_FLOAT, len_min_max=(3, 4))

class GVector(object):
    '''A 3D (4x) vector.
    
    GVectors are not general 4 length vectors. The last/4th element is always 1.
    
    '''
    def __init__(self, v):
        '''
        Args:
            v: a length 3 or 4 list, iterable, numpy.matrix or numpy.ndarray. The
            If not provided, the last value will be defaulted to 1. If provided it 
            must be 1.
        '''
        self.v = self._validate(v)
        if np.abs(self.v[0, 3] - 1.0) > np.float64(1e-14):
            raise VectorInvalidError(
                'Last value must be 1 (or approx 1) was %f' % self.v[0, 3])

    @classmethod
    def _validate(cls, v):
        if isinstance(v, GVector):
            return v.v.copy()
        if isinstance(v, np.matrix):
            if np.shape(v) == (1, 4):
                return v
            elif np.shape(v) == (4, 1):
                return v.T
            elif np.shape(v) == (1, 3):
                return np.matrix(v.tolist()[0] + [1.])
            elif np.shape(v) == (3, 1):
                return np.matrix(v.T.tolist()[0] + [1.])
            else:
                raise MatrixShapeError(
                    'Matrix supplied is not a 4x1 or 1x4, Shape is %s' %
                    'x'.join(str(n) for n in np.shape(v)))
        elif isinstance(v, np.ndarray):
            if np.shape(v) == (4, ):
                return np.matrix(v)
            elif np.shape(v) == (3, ):
                return np.matrix(v.tolist() + [1.])
            elif np.shape(v) == (1, 4):
                return np.matrix(v)
            elif np.shape(v) == (4, 1):
                return np.matrix(v).T
            elif np.shape(v) == (1, 3):
                return np.matrix(v.tolist()[0] + [1.])
            elif np.shape(v) == (3, 1):
                return np.matrix(v.T.tolist()[0] + [1.])
            else:
                raise MatrixShapeError(
                    'Array supplied is not a 1x4 or 4x4, Shape is %s' %
                    'x'.join(str(n) for n in np.shape(v)))
        else:
            # Converts a len 3 iterable into a len 4 iterable (last elenent defaults to 1) or
            # a len 4 iterable.
            l = LIST_3_4_FLOAT(v)
            if len(l) == 3:
                l += [np.float64(1.0)]
            if len(l) == 4:
                return np.matrix(l)
            raise MatrixShapeError(
                'Array supplied is not a 3 or 4 length value, Length is %d' %
                len(v))
            
    def __str__(self):
        return str(self.L)

    def __repr__(self):
        return self.__class__.__name__ + '(' + str(self.L) + ')'

    def __add__(self, other):
        if not isinstance(other, GVector):
            other = GVector(other)
        return GVector(self.A3 + other.A3)

    def __radd__(self, other):
        if not isinstance(other, GVector):
            other = GVector(other)
        return GVector(other.A3 + self.A3)

    def __sub__(self, other):
        if not isinstance(other, GVector):
            other = GVector(other)
        return GVector(self.A3 - other.A3)

    def __rsub__(self, other):
        if not isinstance(other, GVector):
            other = GVector(other)
        return GVector(other.A3 - self.A3)
    
    def __mul__(self, scalar):
        v = strict_float(scalar)
        return GVector(self.A3 * v)

    def __rmul__(self, scalar):
        v = strict_float(scalar)
        return GVector(self.A3 * v)
    
    def __truediv__(self, scalar):
        v = strict_float(scalar)
        return GVector(self.A3 / v)

    def __rtruediv__(self, scalar):
        v = strict_float(scalar)
        return GVector(v / self.A3)
        
    def __neg__(self):
        return GVector(-(self.A3))

    def __pos__(self):
        return GVector(self.v.copy())

    def __getitem__(self, index):
        if isinstance(index, tuple):
            if len(index) == 1:
                return self.v.A1[index]
            return self.v[index]
        elif isinstance(index, slice):
            return self.A[index]
        return self.v[0, index]

    def __setitem__(self, index, value):
        if isinstance(index, tuple):
            if len(index) == 1:
                self.v.A1[index] = value
            else:
                self.v[index] = value
        else:
            self.v[0, index] = value

    def __eq__(self, other):
        return isinstance(other, GVector) and np.array_equal(self.v, other.v)

    def __ne__(self, other):
        return not self == other
    
    def __len__(self):
        return np.shape(self.v)[1]

    def dot3D(self, other):
        '''
        Returns the dot product being the product of the length of the self and other
        vectors and cos(andgle between the vectors self and other).
        '''
        return np.sum(self.v.A1[0:3] * other.v.A1[0:3])

    def length(self):
        '''Returns the length of this 3D vector.'''
        return np.sqrt(self.dot3D(self))

    def is_approx_equal(self, other, error=1.e-12):
        '''Returns true of the other vector is approximately equal to this.
        Args:
            other: The value to compare this to.
            error: The allowable size of error to compare equal.
        '''
        return (self - other).length() < error

    @property
    def N(self):
        '''
        Returns a new normalized (length 1 same direction) vector.
        '''
        return GVector(self.v.A1[0:3] / self.length())
    
    @property   
    def A2(self):
        '''Returns the numpy.array equivalent of this vector's first 2 elements.'''
        return self.v.A1[0:2]

    def cross3D(self, other):
        '''
        Returns a cross product of this vector and other.
        The resulting vector is perpendicular to both self and other 
        and it's length is the product of the lengths of self and other
        and sin(the angle between self and other).
        '''
        if not isinstance(other, GVector):
            other = GVector(other)
        a = self.v.A1
        b = other.v.A1
        return GVector([
                    a[1]*b[2] - a[2]*b[1],
                    a[2]*b[0] - a[0]*b[2],
                    a[0]*b[1] - a[1]*b[0],
                    1.0])

    @property
    def L(self):
        '''Returns the Python list equivalent of this vector.'''
        return self.v.tolist()[0]

    @property
    def A(self):
        '''Returns the numpy.array equivalent of this vector.'''
        return self.v.A1

    @property
    def A3(self):
        '''Returns the numpy.array equivalent of this vector's first 3 elements.'''
        return self.v.A1[0:3]
    
    @property
    def A2(self):
        '''Returns the numpy.array equivalent of this vector's first 2 elements.'''
        return self.v.A1[0:2]
    
    @property
    def x(self):
        '''Returns the x component of this GVector.'''
        return self.v[0, 0]
    
    @property
    def y(self):
        '''Returns the y component of this GVector.'''
        return self.v[0, 1]
    
    @property
    def z(self):
        '''Returns the z component of this GVector.'''
        return self.v[0, 2]
    
    def __hash__(self):
        return hash(tuple(self.L))


# GVector for the X axis.
X_AXIS: GVector = GVector([1, 0, 0])

# GVector for the y axis.
Y_AXIS: GVector = GVector([0, 1, 0])

# GVector for the z axis.
Z_AXIS: GVector = GVector([0, 0, 1])

# GVector for the z axis.
ZERO_VEC: GVector = GVector([0, 0, 0])


class GMatrix(object):
    '''A 4x4 matrix for 3D geometric transformations.
    
    This does not perform generic matrix operations. Subtract and add do not 
    follow generic matrix rules. The last row of the matrix is maintained as 
    [0, 0, 0,1].
    '''

    LAST_ROW = np.array([[0., 0., 0., 1.]])

    def __init__(self, v):
        '''
        Args:
          v: A 4x4 or 3x4 numpy.matrix, numpy.ndarray or a list of lists containing 
          or something that can be converted to a 4x4 of floating point numbers.
        '''
        self.m = self._validate(v)
        if self.m.A[3].tolist() != [0., 0., 0., 1.]:
            raise MatrixInvalidError(
                'Last row of GMatrix must be [0, 0, 0, 1] but found %r.' %
                self.m.A[3].tolist())

    @classmethod
    def from_zyx_axis(cls, x, y, z) -> 'GMatrix':
        '''Returns rotation only matrix from an x, y and z axis vector.'''
        v3A = [GVector(x).N.A[:3], 
               GVector(y).N.A[:3],
               GVector(z).N.A[:3]]
        return GMatrix(v3A)

    @classmethod
    def _validate(cls, v):
        if isinstance(v, GMatrix):
            return v.m.copy()
        
        # Sometimes isinstance breaks.
#         if v.__class__.__name__ == GMatrix.__name__:
#             if isinstance(v.m, np.matrix):
#                 return v.m.copy()

        if isinstance(v, np.matrix):
            shape = np.shape(v)
            if shape == (4, 4):
                return v
            elif shape == (3, 4):
                return cls._add_last_row(v)
            else:
                raise MatrixShapeError(
                    'Matrix supplied is not a 4x4 or 3x4, Shape is %s' %
                    'x'.join(str(n) for n in np.shape(v)))
        elif isinstance(v, np.ndarray):
            shape = np.shape(v)
            if shape == (4, 4):
                return np.matrix(v)
            elif shape == (3, 4):
                return np.matrix(cls._add_last_row(v))
            elif shape == (3, 3):
                return np.matrix(cls._add_last_row(LIST_3_4X4_FLOAT(v)))
            else:
                raise MatrixShapeError(
                    'Array supplied is not a 4x4 or 3x4, Shape is %s' %
                    'x'.join(str(n) for n in np.shape(v)))
        else:
            vm = np.matrix(LIST_3_4X4_FLOAT(v))
            if np.shape(vm) == (4, 4):
                return vm
            elif np.shape(vm) == (3, 4):
                return cls._add_last_row(vm)
            else:
                raise MatrixShapeError(
                    'Matrix supplied is not a 4x4 or 3x4, Shape is %s' %
                    'x'.join(str(n) for n in np.shape(vm)))

    @classmethod
    def _add_last_row(cls, m):
        return np.append(m, cls.LAST_ROW, axis=0)

    def __str__(self):
        return '[\n    ' + ',\n    '.join([str(i) for i in self.L]) + ']'
    
    def __repr__(self):
        return self.__class__.__name__ + '(' + str(self) + ')'

    def __mul__(self, other) -> 'GMatrix':
        if isinstance(other, GMatrix):
            return GMatrix(self.m * other.m)
        if isinstance(other, GVector):
            return GVector(self.m * other.v.T)
        return GMatrix(self.m[0:3] * other)

    def __rmul__(self, other) -> 'GMatrix':
        if isinstance(other, GMatrix):
            return GMatrix(other.m * self.m)
        if isinstance(other, GVector):
            return GVector(other.v * self.m)
        return GMatrix(other * self.m)

    def __add__(self, other) -> 'GMatrix':
        if isinstance(other, GMatrix):
            return GMatrix(self.m[0:3] + other.m[0:3])
        return GMatrix(self.m[0:3] + GMatrix(other).m[0:3])

    def __radd__(self, other) -> 'GMatrix':
        if isinstance(other, GMatrix):
            return GMatrix(self.m[0:3] + other.m[0:3])
        return GMatrix(self.m[0:3] + GMatrix(other).m[0:3])

    def __sub__(self, other) -> 'GMatrix':
        if isinstance(other, GMatrix):
            return GMatrix(self.m[0:3] - other.m[0:3])
        return GMatrix(self.m[0:3] - GMatrix(other).m[0:3])

    def __rsub__(self, other) -> 'GMatrix':
        if isinstance(other, GMatrix):
            return GMatrix(other.m[0:3] - self.m[0:3])
        return GMatrix(GMatrix(other).m[0:3] - self.m[0:3])

    def __neg__(self) -> 'GMatrix':
        return GMatrix(-self.m[0:3])

    def __pos__(self) -> 'GMatrix':
        return GMatrix(self.m.copy())

    def __invert__(self) -> 'GMatrix':
        return GMatrix(self.m.I)

    def __getitem__(self, index):
        return self.A[index]

    def __setitem__(self, index, value):
        self.m[index] = value

    def __eq__(self, other):
        return isinstance(other, GMatrix) and np.array_equal(self.m, other.m)

    def __ne__(self, other):
        return not self == other
    
    def descale(self) -> 'GMatrix':
        '''Returns a matrix with a scale of 1 but unchanged rotation and translation.'''
        vecs = tuple(GVector(self.A[i][0:3]).N for i in range(3))
        return translate(self.A[0:3, -1]) * self.from_zyx_axis(*vecs)

    def length(self):
        '''Returns the Euclidian length of all components in the matrix.'''
        a1 = self.m[0:3].A1
        return np.sqrt((a1 * a1).sum())

    def is_approx_equal(self, other, error=1.e-12):
        return (self - other).length() < error

    def copy(self) -> 'GMatrix':
        return GMatrix(self)
    
    def get_translation(self) -> GVector:
        return GVector(self.m.T.A[3])
    
    def get_rotation(self) -> 'GMatrix':
        return GMatrix(self.A[0:3,0:3])
    
    def get_axis(self, index) -> GVector:
        v = self.A[index]
        return GVector(v[0:3])

    @property
    def I(self) -> 'GMatrix':
        '''Returns the inverted matrix.
        i.e.
           M.I * M == IDENTITY
        '''
        return GMatrix(self.m.I)

    @property
    def L(self) -> List:
        '''Returns the Python list equivalent of this matrix.'''
        return self.m.tolist()

    @property
    def A(self) -> np.array:
        '''Returns the numpy.array equivalent of this matrix.'''
        return self.m.A
    
    @property
    def A2(self) -> np.array:
        '''Returns the numpy.array equivalent of the 2x2 upper left rotation 
        components of this matrix.'''
        return self.m.A[0:2, 0:2]
    
    @property
    def N(self) -> 'GMatrix':
        '''Returns a de-scaled (normalized) matrix.'''
        return self.descale()
    
    def __hash__(self) -> int:
        return hash(tuple(tuple(x) for x in self.A))


# The identity matrix.
IDENTITY: GMatrix = GMatrix([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]])

# Mirrors the X axis.
MIRROR_X: GMatrix = GMatrix([
    [-1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]])

# Mirrors the Y axis.
MIRROR_Y: GMatrix = GMatrix([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, -1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]])

# Mirrors the Z axis.
MIRROR_Z: GMatrix = GMatrix([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]])

def clean(v: float, epsilon: float=1.e-13) -> float:
    '''Clean rounding errors for zeros.'''
    if np.abs(v) < epsilon:
        return 0.
    return v

def clean_equal(v1: float, v2: float, epsilon: float=1.e-13) -> float:
    '''Clean rounding errors for zeros.'''
    if np.abs(v1 - v2) < epsilon:
        return True
    return False

@dataclass(frozen=True)
class Angle(ABC):
    '''Abstract class for angles.'''

    @abstractmethod
    def radians(self) -> float:
        '''Returns the angle in radians.'''
        pass
    
    def degrees(self) -> float:
        '''Returns the angle in degrees.'''
        return to_degrees(self.radians())
    
    @abstractmethod
    def sinr_cosr(self) -> np.ndarray:
        '''Returns the sin and cosine of the angle.'''
        pass
    
    def cosr_sinr(self) -> np.ndarray:
        '''Returns the cosine and sine of the angle.'''
        return self.sinr_cosr()[::-1]
    
    @abstractmethod
    def inv(self) -> 'Angle':
        '''Returns the inverse of the angle.'''
        pass
    
    def pos_radians(self) -> float:
        '''Returns the angle in radians as a positive value.'''
        return self.radians() % np.pi
    
    @property
    def rotX(self) -> GMatrix:
        '''Returns a GMatrix that causes a rotation about X for the angle.'''
        sinr_cosr = self.sinr_cosr()
        return rotXSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    
    @property
    def rotY(self) -> GMatrix:
        '''Returns a GMatrix that causes a rotation about Y for the angle.'''
        sinr_cosr = self.sinr_cosr()
        return rotYSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    
    @property
    def rotZ(self) -> GMatrix:
        '''Returns a GMatrix that causes a rotation about Z for the angle.'''
        sinr_cosr = self.sinr_cosr()
        return rotZSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    
    def rotV(self, v: GVector) -> GMatrix:
        '''Returns a GMatrix that causes a rotation about the given vector for the angle.'''
        sinr_cosr = self.sinr_cosr()
        return rotVSinCos(v, clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    
    def __add__(self, other: 'Angle') -> 'Angle':
        '''Adds two angles.'''
        return AngleRadians(self.radians() + other.radians())
    
    def __sub__(self, other: 'Angle') -> 'Angle':
        '''Subtracts two angles.'''
        return AngleRadians(self.radians() - other.radians())
    
    def __mul__(self, scalar: float) -> 'Angle':
        '''Multiplies the angle by a scalar.'''
        return AngleRadians(self.radians() * scalar)
    
    def __truediv__(self, scalar: float) -> 'Angle':
        '''Divides the angle by a scalar.'''
        return AngleRadians(self.radians() / scalar)
    
    def __neg__(self) -> 'Angle':
        '''Returns the negative of the angle.'''
        return AngleRadians(-self.radians())
    
    def __sub__(self, other: 'Angle') -> str:
        '''Returns subtraction of angles.'''
        return AngleRadians(self.radians() - other.radians())
    
    @abstractmethod
    def __bool__(self) -> bool:
        '''Returns False if the angle is 0, True otherwise.'''
        pass
    
    def __eq__(self, other: 'Angle') -> bool:
        '''Returns True if the angles are equal.'''
        return clean_equal(self.radians(), other.radians())
    
    def sweepRadians(self, positive_dir: bool, non_zero:bool = True) -> float:
        '''Returns the sweep angle in the positive or negative direction.
        Args:
            positive_dir: If True, the angle is in the positive direction and the
                the returned value will be converted to an equivalent positive angle.
                If negative, the angle is in the negative direction and the returned
                value will be converted to an equivalent negative angle.
            non_zero: If True and the angle is zero, then the a single full revolution
                will be returned in the direction specified by positive_dir.
        '''
        radians = self.radians()
        if non_zero and np.abs(radians) < 1.e-13:
            return 2 * np.pi if positive_dir else -2 * np.pi 
        if positive_dir:
            if radians >= 0:
                return radians
            n = radians // (2 * np.pi)
            return radians - 2 * np.pi * (2 * n + 1)            
        
        # Negative direction.
        if radians <= 0:
            return radians
        n = radians // (2 * np.pi)
        return radians - 2 * np.pi * (2 * n + 1)


@dataclass(frozen=True)
class AngleDegrees(Angle):
    degrees_v: float
    
    def __post_init__(self):
        # Ensure that the value is numeric.
        assert not isinstance(self.degrees_v, Angle), 'degrees should be a numeric value not Angle.'
    
    def radians(self) -> float:
        return to_radians(self.degrees_v)
    
    def degrees(self) -> float:
        return self.degrees_v
    
    def sinr_cosr(self) -> np.ndarray:
        radians_v = self.radians()
        return np.array((np.sin(radians_v), np.cos(radians_v)))
    
    def inv(self) -> 'AngleDegrees':
        return AngleDegrees(-self.degrees_v)
    
    def __repr__(self) -> str:
        return f'angle({self.degrees_v})'
    
    def __neg__(self) -> 'AngleDegrees':
        return AngleDegrees(-self.degrees_v)

    def __bool__(self) -> bool:
        return not clean_equal(self.degrees_v, 0.0)
    
    def __neg__(self) -> 'Angle':
        '''Returns the negative of the angle.'''
        return AngleDegrees(-self.degrees())
    
    def __add__(self, other: 'Angle') -> 'Angle':
        '''Adds two angles.'''
        return AngleDegrees(self.degrees() + other.degrees())
    
    def __sub__(self, other: Angle) -> str:
        '''Returns subtraction of angles.'''
        return AngleDegrees(self.degrees() - other.degrees())
    
    def __eq__(self, other: 'Angle') -> bool:
        '''Returns True if the angles are equal.'''
        if isinstance(other, AngleSinCos):
            sinr_cosr = self.sinr_cosr()
            return clean_equal(
                    sinr_cosr[0], other.sinr_cosr_v[0]
                ) and clean_equal(
                    sinr_cosr[1], other.sinr_cosr_v[1])
        return clean_equal(self.degrees_v, other.degrees())


@dataclass(frozen=True)
class AngleRadians(Angle):
    radians_v: float

    def radians(self) -> float:
        return self.radians_v
    
    def degrees(self) -> float:
        return to_degrees(self.radians_v)
    
    def sinr_cosr(self) -> Tuple[float, float]:
        return np.array((np.sin(self.radians_v), np.cos(self.radians_v)))
    
    def inv(self) -> 'AngleRadians':
        return AngleRadians(-self.radians_v)
    
    def __repr__(self) -> str:
        return f'angle(radians={self.radians_v})'
    
    def __bool__(self) -> bool:
        return not clean_equal(self.radians_v, 0.0)
    
    def __eq__(self, other: 'Angle') -> bool:
        '''Returns True if the angles are equal.'''
        if isinstance(other, AngleSinCos):
            sinr_cosr = self.sinr_cosr()
            return clean_equal(
                    sinr_cosr[0], other.sinr_cosr_v[0]
                ) and clean_equal(
                    sinr_cosr[1], other.sinr_cosr_v[1])
        return clean_equal(self.radians_v, other.radians())
    

@dataclass(frozen=True)
class AngleSinCos(Angle):
    sinr_cosr_v: np.ndarray
    
    def __post_init__(self):
        if not isinstance(self.sinr_cosr_v, np.ndarray) or self.sinr_cosr_v.flags.writeable:
            sinr_cosr = np.array(self.sinr_cosr_v)
            sinr_cosr.flags.writeable = False
            _field_assign(self, 'sinr_cosr_v', sinr_cosr)

    def radians(self) -> float:
        return np.arctan2(self.sinr_cosr_v[0], self.sinr_cosr_v[1])
    
    def degrees(self) -> float:
        return to_degrees(self.radians())
    
    def sinr_cosr(self) -> Tuple[float, float]:
        return self.sinr_cosr_v
    
    def inv(self) -> 'AngleSinCos':
        return AngleSinCos((-self.sinr_cosr_v[0], self.sinr_cosr_v[1]))
    
    def __repr__(self) -> str:
        return f'angle(sinr_cosr={self.sinr_cosr_v})'
    
    def __bool__(self) -> bool:
        return not (clean_equal(self.sinr_cosr_v[0], 0.0) and clean_equal(self.sinr_cosr_v[1], 1.0))
    
    def __add__(self, other: Angle) -> Angle:
        '''Adds two angles.'''
        if isinstance(other, AngleSinCos):
            return AngleSinCos(
                (self.sinr_cosr_v[0] * other.sinr_cosr_v[1] 
                    + other.sinr_cosr_v[0] * self.sinr_cosr_v[1],
                self.sinr_cosr_v[1] * other.sinr_cosr_v[1] 
                    - self.sinr_cosr_v[0] * other.sinr_cosr_v[0])) 
        return super().__add__(other)
    
         
    def __neg__(self) -> 'Angle':
        '''Returns the negative of the angle.'''
        return AngleSinCos((-self.sinr_cosr_v[0], self.sinr_cosr_v[1]))
    
    def __sub__(self, other: 'Angle') -> str:
        '''Returns subtraction of angles.'''
        return self.__add__(-other)
    
    def __eq__(self, other: 'Angle') -> bool:
        '''Returns True if the angles are equal.'''
        sinr_cosr = other.sinr_cosr()
        return clean_equal(
                sinr_cosr[0], self.sinr_cosr_v[0]
            ) and clean_equal(
                sinr_cosr[1], self.sinr_cosr_v[1])
    
    
def angle(degrees: Union[Angle, float, NoneType]=0, 
          radians: Union[float, NoneType]=None, 
          sinr_cosr: Union[Tuple[float, float], NoneType]=None,
          cosr_sinr: Union[Tuple[float, float], NoneType]=None,
          angle: Union[Angle, numbers.Number, NoneType]=None, 
          direction: Union[GVector, Tuple[float], NoneType]=None) -> Angle:
    '''Returns an Angle object for the given angle in degrees, radians, cos/sin parn,
    sin/cos pair, angle or a direction vector.
    
    Only one of angle, direction, sinr_cosr or radians, degrees is used in the order
    stated here.
    
    This is the preferred way to pass an angle as it is less verbose than having to
    accept radians, degrees, sinr_cosr or any other units in the function signature.
    
    Passing degrees, radians, sinr_cosr to functions is considered deprecated.
    '''
    if angle is not None:
        if isinstance(angle, Angle):
            return angle
        if isinstance(angle, numbers.Number):
            return AngleDegrees(angle)
    if direction is not None:
        if isinstance(direction, GVector):
            darray = direction.A[:2]
        else:
            darray = np.array(direction[:2])
        darray2 = darray * darray
        d_cosr_sinr = darray / np.sqrt(darray2.sum())
        return AngleSinCos(d_cosr_sinr[::-1])
    if cosr_sinr is not None:
        return AngleSinCos(cosr_sinr[::-1])
    if sinr_cosr is not None:
        return AngleSinCos(sinr_cosr)
    if radians is None:
        if isinstance(degrees, Angle):
            return degrees
        if degrees is None:
            degrees = 0
        return AngleDegrees(degrees)
    return AngleRadians(radians)


def inv_rot(rot_func: Callable[..., GMatrix], 
            degrees: Union[Angle, numbers.Number, NoneType]=0, 
            radians: Union[float, NoneType]=None, 
            sinr_cosr: Union[Tuple[float, float], NoneType]=None, 
            angle: Union[Angle, numbers.Number, NoneType]=None) -> GMatrix:
    '''Returns the result of calling the rotation function, rot_func, with the
    inverse of the rotation angle.
    
    Args:
        rot_func: A function that returns a GMatrix for a given rotation.
        degrees: The rotation angle in degrees.
        radians: The rotation angle in radians.
        sinr_cosr: A tuple containing the sine and cosine of the rotation angle.
        angle: An Angle object.
    '''
    if not angle is None:
        if isinstance(angle, Angle):
            return rot_func(angle=angle.inv())
        return rot_func(degrees=-angle)
    if sinr_cosr:
        return rot_func(sinr_cosr=(-sinr_cosr[0], sinr_cosr[1]))
    if radians is None:
        if isinstance(degrees, Angle):
            return rot_func(degrees=degrees.inv())
        return rot_func(degrees=-degrees)
    return rot_func(radians=-radians)


def angle_to_radians(degrees: Union[Angle, numbers.Number, NoneType]=0, 
            radians: Union[float, NoneType]=None, 
            sinr_cosr: Union[Tuple[float, float], NoneType]=None, 
            angle: Union[Angle, numbers.Number, NoneType]=None) -> float:
    '''Returns the angle in radians for the given angle in degrees, radians or sin/cos pair.
    Only one of sinr_cosr or radians or degrees is used in the order
    stated here.
    '''
    if not angle is None:
        if isinstance(angle, Angle):
            return angle.radians()
        return to_radians(angle)
    if not sinr_cosr is None:
        return np.arctan2(sinr_cosr[0], sinr_cosr[1])
    if radians is None:
        if isinstance(degrees, Angle):
            return degrees.radians()
        return to_radians(degrees)
    return radians

    
def rotation_to_str(degrees: Union[Angle, numbers.Number, NoneType]=90, 
         radians: Union[float, NoneType]=None, 
         sinr_cosr: Union[Tuple[float, float], NoneType]=None, 
         angle: Union[Angle, numbers.Number, NoneType]=None, 
         prefix: str='') -> str:
    '''Returns a string indicating the selected rotation method. This is used
    for logging and debugging.'''
    if not angle is None:
        return f'{prefix}angle={angle}'
    if sinr_cosr:
        return f'{prefix}sinr_cosr={sinr_cosr}'
    if radians is None:
        return f'{prefix}degrees={degrees}'
    return f'{prefix}radians={radians}'


def rotZ(degrees: Union[Angle, numbers.Number, NoneType]=90, 
         radians: Union[float, NoneType]=None, 
         sinr_cosr: Union[Tuple[float, float], NoneType]=None, 
         angle: Union[Angle, numbers.Number, NoneType]=None) -> GMatrix:
    '''Returns a GMatrix that causes a rotation about Z given an angle
    either in degrees, radians or a sin/cos pair.
    Only one of sinr_cosr or radians or degrees is used in the order
    stated here.'''
    if not angle is None:
        sinr_cosr = angle.sinr_cosr()
        return rotZSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    if not sinr_cosr is None:
        return rotZSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    if radians is None:
        if isinstance(degrees, Angle):
            sinr_cosr = degrees.sinr_cosr()
            return rotZSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
        radians = to_radians(degrees)
    cosr = clean(np.cos(radians))
    sinr = clean(np.sin(radians))
    return rotZSinCos(sinr, cosr)

def rotZSinCos(sinr, cosr) -> GMatrix:
    '''Returns a GMatrix that causes a rotation about Z for the given sin/cos pair.'''
    return GMatrix(np.matrix([[cosr, -sinr, 0.0, 0], 
                              [sinr, cosr, 0, 0], 
                              [0, 0, 1, 0], 
                              [0, 0, 0, 1]]))
ROTZ_90: GMatrix = rotZ(90)
ROTZ_180: GMatrix = rotZ(180)
ROTZ_270: GMatrix = rotZ(-90)

def rotX(degrees: Union[Angle, numbers.Number, NoneType]=90, 
         radians: Union[float, NoneType]=None, 
         sinr_cosr: Union[Tuple[float, float], NoneType]=None, 
         angle: Union[Angle, numbers.Number, NoneType]=None) -> GMatrix:
    '''Returns a GMatrix that causes a rotation about X given an angle
    either in degrees, radians or a sin/cos pair.
    Only one of sinr_cosr or radians or degrees is used in the order
    stated here.
    '''
    if not angle is None:
        sinr_cosr = angle.sinr_cosr()
        return rotXSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    if sinr_cosr:
        return rotXSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    if radians is None:
        if isinstance(degrees, Angle):
            sinr_cosr = degrees.sinr_cosr()
            return rotXSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
        radians = to_radians(degrees)
    cosr = clean(np.cos(radians))
    sinr = clean(np.sin(radians))
    return rotXSinCos(sinr, cosr)
    
def rotXSinCos(sinr, cosr) -> GMatrix:
    '''Returns a Gmatrix for a rotation about the X axis given a sin/cos pair.'''
    return GMatrix(np.matrix([[1.0, 0, 0, 0], 
                              [0, cosr, -sinr, 0], 
                              [0, sinr, cosr, 0], 
                              [0, 0, 0, 1]]))
ROTX_90: GMatrix = rotX(90)
ROTX_180: GMatrix = rotX(180)
ROTX_270: GMatrix = rotX(-90)
    
def rotY(degrees: Union[Angle, numbers.Number, NoneType]=90, 
         radians: Union[float, NoneType]=None, 
         sinr_cosr: Union[Tuple[float, float], NoneType]=None, 
         angle: Union[Angle, numbers.Number, NoneType]=None) -> GMatrix:
    '''Returns a GMatrix that causes a rotation about Y given an angle
    either in degrees, radians or a sin/cos pair.
    Only one of sinr_cosr or radians or degrees is used in the order
    stated here.'''
    if not angle is None:
        sinr_cosr = angle.sinr_cosr()
        return rotYSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    if sinr_cosr:
        return rotYSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    '''Returns a GMatrix that causes a rotation about Y a given number of degrees.'''
    if radians is None:
        if isinstance(degrees, Angle):
            sinr_cosr = degrees.sinr_cosr()
            return rotYSinCos(clean(sinr_cosr[0]), clean(sinr_cosr[1]))
        radians = to_radians(degrees)
    cosr = clean(np.cos(radians))
    sinr = clean(np.sin(radians))
    return rotYSinCos(sinr, cosr)
    
def rotYSinCos(sinr, cosr) -> GMatrix:
    return GMatrix(np.matrix([[cosr, 0.0, sinr, 0], 
                              [0, 1, 0, 0],
                              [-sinr, 0, cosr, 0], 
                              [0, 0, 0, 1]]))
ROTY_90: GMatrix = rotY(90)
ROTY_180: GMatrix = rotY(180)
ROTY_270: GMatrix = rotY(-90)
    

def normalize(v):
    '''Returns the normalised value of vector v.'''
    if not isinstance(v, GVector):
        v = GVector(v)
    return v.N

def rotVSinCos(v: Union[GVector, Tuple[float, float, float]], 
               sinr: float, 
               cosr: float) -> GMatrix:
    '''Returns a GMatrix that causes a rotation about an axis vector v the 
    given sin and cos of the rotation angle.'''
    u = normalize(v)
    ux = u.x
    uy = u.y
    uz = u.z
    u2 = u.A * u.A
    ux2 = u2[0]
    uy2 = u2[1]
    uz2 = u2[2]
    uxz = ux * uz
    uxy = ux * uy
    uyz = uy * uz
    lcosr = 1 - cosr
    return GMatrix(np.matrix(
        [[cosr + ux2 * lcosr, uxy * lcosr - uz * sinr, uxz * lcosr + uy * sinr, 0],
         [uxy * lcosr + uz * sinr, cosr + uy2 * lcosr, uyz * lcosr - ux * sinr, 0],
         [uxz * lcosr - uy * sinr, uyz * lcosr + ux * sinr, cosr + uz2 * lcosr, 0],
         [0.0, 0, 0, 1]]))


def rotV(v: Union[GVector, Tuple[float, float, float]],
         degrees: Union[Angle, numbers.Number, NoneType]=90, 
         radians: Union[float, NoneType]=None, 
         sinr_cosr: Union[Tuple[float, float], NoneType]=None, 
         angle: Union[Angle, numbers.Number, NoneType]=None) -> GMatrix:
    '''Returns a GMatrix that causes a rotation about the vector v given 
    an angle either in degrees, radians or a sin/cos pair.
    Only one of sinr_cosr or radians or degrees is used in the order
    stated here.'''
    if not angle is None:
        sinr_cosr = angle.sinr_cosr()
        return rotVSinCos(v, clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    if sinr_cosr:
        return rotVSinCos(v, clean(sinr_cosr[0]), clean(sinr_cosr[1]))
    if radians is None:
        if isinstance(degrees, Angle):
            sinr_cosr = degrees.sinr_cosr()
            return rotVSinCos(v, clean(sinr_cosr[0]), clean(sinr_cosr[1]))
        radians = to_radians(degrees)
    cosr = clean(np.cos(radians))
    sinr = clean(np.sin(radians))
    return rotVSinCos(v, sinr, cosr)

ROTV111_240: GMatrix =GMatrix([
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]])

ROTV111_120: GMatrix =GMatrix([
    [0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]])

def scale(s) -> GMatrix:
    '''Returns a GMatrix that scales by a vector [x,y,z] scalars or [s,s,s].'''
    try:
        v = LIST_3_FLOAT(s)
    except TypeError:
        v = LIST_3_FLOAT([s, s, s])
    
    return GMatrix(
        np.matrix([[v[0], 0.0, 0, 0], [0, v[1], 0, 0], [0, 0, v[2], 0], [0, 0, 0, 1]]))

def translate(v: GVector) -> GMatrix:
    '''Returns GMatrix that translates by the given vector.'''
    if not isinstance(v, GVector):
        v = GVector(v)
    return GMatrix(np.matrix(
        [[1., 0, 0, v.x], [0, 1, 0, v.y], [0, 0, 1, v.z], [0, 0, 0, 1]]))
    
def tranX(v: float) -> GMatrix:
    return translate([v, 0, 0])

def tranY(v: float) -> GMatrix:
    return translate([0, v, 0])

def tranZ(v: float) -> GMatrix:
    return translate([0, 0, v])

def rot_to_V(from_v: GVector, to_v: GVector) -> GMatrix:
    '''Computes the rotation so that transformation from from_v becomes 
    parallel to to_v'''
    if not isinstance(from_v, GVector):
        from_v = GVector(from_v)
    if not isinstance(to_v, GVector):
        to_v = GVector(to_v)

    from_vn = from_v.N
    to_vn = to_v.N

    cross = from_vn.cross3D(to_vn)
    sinr = cross.length()
    # If the rotation is very small just return the identity
    if abs(sinr) < 1e-12:
        return IDENTITY.copy()
    cosr = from_vn.dot3D(to_vn)
    
    return rotVSinCos(cross, sinr, cosr)

def rotAlign(preserve_axis: GVector, align_preserve_axis: GVector, plane_axis: GVector) -> GMatrix:
    '''Returns a GMatrix that rotates around the preserve_axis in order to align
    the align_preserve_axis with the plane described by plane_axis.
    '''
    preserve_axis = normalize(preserve_axis)
    align_preserve_axis = normalize(align_preserve_axis)
    plane_axis = normalize(plane_axis)
    
    # Ensure that align_pres_axis is orthogonal to preserve_axis
    align_pres_axis = preserve_axis.cross3D(align_preserve_axis).cross3D(preserve_axis).N
    
    # Find the rotation to the plane for the preserve_axis.
    to_plane = rotToPlane(preserve_axis, plane_axis)
    
    # Find the location that align_preserve_axis end up after the to_plane rotation. 
    t1_o_align_pres_axis = to_plane * align_pres_axis
    
    # Find the rotation to make align_to_plane hit the plane as well.
    align_to_plane = rotToPlane(t1_o_align_pres_axis, plane_axis)
    
    # Apply the transformations in order.
    result = to_plane.I * align_to_plane * to_plane

    return result

def rotToPlane(v, plane_normal) -> GMatrix:
    '''Find the transform that rotates v onto the plane described by plane_normal and going
    through the origin.
    '''
    v = normalize(v)
    plane_normal = normalize(plane_normal)
    
    dot = plane_normal.dot3D(v)
    cross = plane_normal.cross3D(v)
    angle = np.arctan2(cross.length(), dot)
    return rotV(cross, radians=np.pi/2 - angle)

def mirror(axis) -> GMatrix:
    '''Mirror at the origin about any plane. The axis provided is the normal to the mirror plane.
    '''
    axis = normalize(axis)
    dotx = X_AXIS.dot3D(axis)
    # Use one of the predefined mirror matricies, We first have to choose one that is
    # not colinear so we don't break rotV with a zero length cross vector.
    if abs(dotx) > 0.5:
        # closer to X axis than Y axis so pick Y axis mirror.
        ref_axis = Y_AXIS
        mm = MIRROR_Y
    else:
        # closer to Y axis so pick X axis.
        ref_axis = X_AXIS
        mm = MIRROR_X
    # Finds a rotation matrix that will rotate from the given axis to the reference axis.
    m = rot_to_V(axis, ref_axis)
    # Chain the matrix multiplications so we first rotate to the plane then mirror and
    # then rotate back to the original frame of reference.
    return m.I * mm * m

def _get_plane_normal(plane_mat, plane_mat_I=None) -> GMatrix:
    '''Returns a GMatrix representing the vector from the origin to the
    translation point normal to the projected X-Y plane.'''
    if not plane_mat_I:
        plane_mat_I = plane_mat.I
    p_z = plane_mat_I.get_axis(2)
    p_trans_dir = rot_to_V(Z_AXIS, p_z)
    p_trans = plane_mat.get_translation()
    p_tran_len = -p_z.dot3D(p_trans)
    return p_trans_dir * translate([0, 0, p_tran_len])

def plane_intersect(planeA: GMatrix, planeB: GMatrix) -> GMatrix:
    '''Find the intersecting line of 2 planes represented as the GMatrix x-y
    plane. i.e. The Z vector of the plane matrix parameters are the normal
    to the plane. The result is another GMatrix whose Z axis is the line
    direction. The X axis of the result will be co-planar with planeA and
    the Y axis will be normal to plane2. If the planes are co-planar, None
    is returned.
    
    Args:
      planeA: a GMatrix whose X-Y plane represents the plane (Z is normal).
      planeB: a GMatrix whose X-Y plane represents the plane (Z is normal).
    '''
    
    # We'll need this a couple of times.
    planeB_I = planeB.I

    # Find planeB in planeA's frame of reference.
    to_planeA = planeB_I * planeA
    to_planeA_I = to_planeA.I

    to_planeA_mat = _get_plane_normal(to_planeA_I, to_planeA)
    
    # From the origin to the translated origin of planeB, the solution
    # of the intersection is 2D line perpendicular to the translation
    # of to_planeA.
    to_pA_trans = to_planeA_mat.get_translation()
    
    # Project a point onto planeA.
    on_planeA = GVector([to_pA_trans.x, to_pA_trans.y, 0])
    
    # Find line direction using Z axis of plane.
    bz = to_planeA.get_axis(2)
    intersecting_line_dir = bz.cross3D(Z_AXIS)
    if clean(intersecting_line_dir.length(), epsilon=1.e-20) == 0:
        # Planes are coplanar or the origin of planA is on the intersection.
        return None
    
    intersection_direction = ROTX_90 * rot_to_V(intersecting_line_dir, Y_AXIS)
    x02 = clean(on_planeA.dot3D(on_planeA), epsilon=1.e-20)
    if x02 == 0:
        # Line intersects through the origin.
        interesct_line = intersection_direction
    else:
        # Compute the 2D line intersection.
        z0 = to_pA_trans.z
        line_offset = on_planeA * ((x02 + z0 * z0) / x02)
        
        # Compute the matrix representing the line.
        interesct_line = intersection_direction * translate(line_offset)

    # Put this back in the original/common frame of reference.
    return planeA * interesct_line.I
    
def plane_line_intersect(plane_in: GMatrix, line_in: GMatrix) -> GMatrix:
    '''Find the interesting point between a plane and a line.
    The plane is represented as by the GMatrix x-y plane (Z is normal). The
    line is also a GMatrix whose Z direction is the direction of the line and
    the line traverses the origin of the frame of reference. Returns None if 
    there is no intersection. Returns a GMatrix of the intersecting point 
    maintaining the orientation of the input line but translated so the 
    origin is at the point of intersection.'''
    # Algorithm adapted from:
    #    https://en.wikipedia.org/wiki/Line%E2%80%93plane_intersection
    
    plane = plane_in.I
    line = line_in.I
    
    p_z = plane.get_axis(2)
    l_z = line.get_axis(2)  # The line direction.
    d = clean(l_z.dot3D(p_z), epsilon=1.e-20)
    if d == 0:
        # line is parallel to plane.
        return None
    
    # Compute how far to extend line to reach the intersecting point.
    t = p_z.dot3D(plane_in.get_translation() - line_in.get_translation()) / -d
    
    result = line * translate(l_z * t)
    
    return result.I

def distance_between(pointA: GMatrix, pointB: GMatrix) -> float:
    '''Returns the distance from between 2 points.'''
    diff = pointA.get_translation() - pointB.get_translation()
    return clean(diff.length(), epsilon=1.e-20)

def distance_between_point_plane(point: GMatrix, plane: GMatrix) -> float:
    '''
    Calculate the perpendicular distance from a point to a plane.

    Parameters:
      point: GMatrix representing the point's frame. The origin of this 
            frame is the point.
      plane: GMatrix representing the plane's frame. The x-y plane of 
            this frame defines the plane.

    Returns:
      distance: The perpendicular distance from the point to the plane.
    '''
    # Extract the plane's normal vector (Z-axis) and normalize it
    plane_normal = plane.get_axis(2).N  # GVector

    # Extract the translation vectors
    plane_translation = plane.get_translation()  # GVector
    point_translation = point.get_translation()  # GVector

    # Compute the dot product of the plane's normal with its translation vector
    # This gives the plane's distance from the origin
    distance_plane = plane_normal.dot3D(plane_translation)

    # Compute the dot product of the plane's normal with the point's translation vector
    # This gives the point's distance from the origin in the direction of the plane's normal
    distance_point = plane_normal.dot3D(point_translation)

    return distance_point - distance_plane

