'''
Various converters used in conjunction with the xdatatree for converting
GMatrix and GVector objects to and from strings used in 3mf file attributes
for matrix, transform and vector strings.
'''

from anchorscad import GMatrix, GVector, datatree, dtfield

from typing import Union
import re
import numpy as np


def float_to_str(value: float) -> str:
  """Removes a trailing "." from a floating point number string.
  Args:
    string: A string.
  Returns:
    A string with the trailing "." removed, if it exists.
  """
  string = str(value).rstrip('0')
  if string.endswith('.'):
    return string[:-1]
  else:
    return string


@datatree
class MatrixConverter:
    '''Convert a 16 value string like "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1" to a
    GMatrix and back.'''
    matrix: GMatrix = dtfield(doc='The matrix as a GMatrix')

    def __init__(self, matrix_str: Union[str, GMatrix]):
        if isinstance(matrix_str, GMatrix):
            self.matrix = matrix_str
        else:
            nparray = np.array([float(x) for x in re.split(r'\s+', matrix_str)])
            self.matrix = GMatrix(nparray.reshape((4, 4)))
    
    def __str__(self):
        return ' '.join([float_to_str(x) for x in self.matrix.A.flatten()])
    
    def __repr__(self):
        return self.__str__()
    

@datatree
class TransformConverter:
    '''Convert a 12 value string like "1 0 0 0 1 0 0 0 1 40 40 10" to a GMatrix
    and back.'''
    matrix: GMatrix = dtfield(doc='The matrix as a GMatrix')

    def __init__(self, matrix_str: Union[str, GMatrix]):
        
        if isinstance(matrix_str, GMatrix):
            self.matrix = matrix_str
        else:
            nparray = np.array([float(x) for x in re.split(r'\s+', matrix_str)])
            self.matrix = GMatrix(nparray.reshape((3, 4), order='F'))
    
    def __str__(self):
        nparray = self.matrix.A[0:3].reshape((1, 12), order='F')
        return ' '.join([float_to_str(x) for x in nparray[0]])
    
    def __repr__(self):
        return self.__str__()

    
@datatree
class VectorConverter:
    '''Convert a string like "1 2 3" to a GVector and back.'''
    vector: GVector = dtfield(doc='The vector as a GVector')

    def __init__(self, vector_str: Union[str, GVector]):
        if isinstance(vector_str, GVector):
            self.vector = vector_str
        else:
            self.vector = GVector([float(x) for x in re.split(r'\s+', vector_str)])
    
    def __str__(self):
        return ' '.join([float_to_str(x) for x in self.vector.A[0:3]])
    
    def __repr__(self):
        return self.__str__()

