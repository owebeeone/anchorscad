'''
Created on 25 Jan 2021

@author: gianni
'''

from dataclasses import dataclass


@dataclass(frozen=True)
class ShaftDimensions(object):
    '''Contains diameter dimensions for a screw type.
    '''
    actual: float
    thru_d: float
    tapping_d: float


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


SHAFT_MAP = {
    'M1.6' : ShaftDimensions(1.6, 1.8, 1.6),
    'M2' : ShaftDimensions(2.0, 2.4, 2.0),
    'M2.6' : ShaftDimensions(2.6, 2.8, 2.61),
    'M3' : ShaftDimensions(3.0, 3.25, 2.75),
    'M4' : ShaftDimensions(4.0, 4.06, 3.75),
    'M6' : ShaftDimensions(6.0, 6.14, 6.05),
    'BUGLE_14g-10' : ShaftDimensions(6.3, 6.7, 6.4),
    'DECK_10g-10' : ShaftDimensions(4.8, 5.1, 4.9),
    }


HEAD_MAP = {
    
    'M3' : HeadDimensions(
                head_top_d=6.2,
                head_bot_d=3.25,
                head_protrusion_height=1.5,
                head_mid_depth=0.1,
                head_countersink_depth=1.96),
    
    'BUGLE_14g-10' : HeadDimensions(
                head_top_d=14.2,
                head_bot_d=6.5,
                head_protrusion_height=1,
                head_mid_depth=0.7,
                head_countersink_depth=4.5),
    
    'DECK_10g-10' : HeadDimensions(
                head_top_d=9.15,
                head_bot_d=4.9,
                head_protrusion_height=1,
                head_mid_depth=0.7,
                head_countersink_depth=3.2)
    }



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
