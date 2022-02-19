'''
Created on 25 Jan 2021

@author: gianni
'''

from dataclasses import dataclass

from ParametricSolid.core import shape, CompositeShape
from anchorscad.models.basic.pipe import Pipe

@dataclass(frozen=True)
class ShaftDimensions(object):
    '''Contains diameter dimensions for a screw type.
    '''

    actual: float
    thru_d: float
    tapping_d: float
    
SHAFT_MAP = {
    'M2' : ShaftDimensions(2.0, 2.4, 2.0),
    'M2.6' : ShaftDimensions(2.6, 2.8, 2.61),
    'M4' : ShaftDimensions(4.0, 4.06, 3.75),
    'M6' : ShaftDimensions(6.0, 6.14, 6.05),
    }


@dataclass(frozen=True)
class HeadDimensions(object):
    '''Contains dimensions for a screw type.
    '''

    head_top_d: float
    head_bot_d: float
    head_protrusion_height: float
    head_mid_depth: float
    head_countersink_depth: float
    
    def overall_screw_head_height(self):
        return self.head_countersink_depth + self.head_mid_depth; 


@dataclass(frozen=True)
class HoleDimensions(object):
    '''Contains dimensions for screw holes.
    '''
    thru_dia: float
    tap_dia: float


M_HOLE = {
    2 : HoleDimensions(thru_dia=2.22, tap_dia=2.09),
    2.5 : HoleDimensions(thru_dia=2.70, tap_dia=2.65),
    2.6 : HoleDimensions(thru_dia=2.80, tap_dia=2.67),
    3 : HoleDimensions(thru_dia=3.25, tap_dia=3.05),
    }

def holeMetricDims(m_size):
    return M_HOLE[m_size]
