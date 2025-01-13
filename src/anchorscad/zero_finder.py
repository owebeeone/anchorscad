'''
Created on 18 Sept 2022

@author: gianni
'''

from types import FunctionType
from numbers import Number
from dataclasses import dataclass


@dataclass(frozen=True)
class OptionalDetails:
    count_iter: int
    last_error: Number


def zero_of(
        func: FunctionType,
        init0_approx: Number,
        init1_approx: Number,
        max_error: Number=1e-7,
        max_iteration: int=20,
        provide_details: bool=False):
    """Returns the root of the given function (func) that takes a single parameter
    (x) and returns a value f(x) being the value of the funtion at x.
    Args:
      func: The single valued function.
      init0_approx: initial approximation on one side of the root
      init1_approx: initial approximation on the other side of the root
    """
    
    xn = init0_approx
    yn = func(xn)
    xn1 = init1_approx
    yn1 = func(xn1)
    
    assert max_error > 0
    assert (yn.real < 0) != (yn1.real < 0), \
        f'Signs of f(xn)={yn} and f(xn1)={yn1} must be different, '
    
    if abs(yn) < max_error:
        if provide_details:
            return xn, OptionalDetails(0, (abs(yn), abs(yn1)))
        return xn
    
    if abs(yn1) < max_error:
        if provide_details:
            return xn1, OptionalDetails(0, (abs(yn), abs(yn1)))
        return xn1
    
    for iternum in range(max_iteration):
    
        yiprime = (xn - xn1) / (yn - yn1)
        xn2 = 0.5 * ((xn + xn1) - (yn + yn1) * yiprime)
        yn2 = func(xn2)
        
        if abs(yn2) < max_error:
            if provide_details:
                return xn2, OptionalDetails(
                    iternum + 1, (abs(yn), abs(yn2), abs(yn1)))
            return xn2
    
        if (yn2.real < 0) == (yn1.real < 0):
            xn1 = xn2
            yn1 = yn2
        else:
            xn = xn2
            yn = yn2
        
        
    if provide_details:
        return None, OptionalDetails(iternum + 1, (abs(yn), abs(yn1)))
    
    return None

