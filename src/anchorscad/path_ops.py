'''
Created on 13 Feb 2021

@author: gianni
'''

from sortedcontainers import SortedDict
import numpy as np

KEY_SCALE_FACT=np.float64(1 << (64 - 64//4))

def find_msb_common_bits(v1, v2):
    return np.frexp(v1 ^ v2)[1]

def map_bounding_box_to_key(ul, br):
    iul = np.int64(np.array(ul) * KEY_SCALE_FACT)
    ibr = np.int64(np.array(br) * KEY_SCALE_FACT)
    
    bit_diverge = np.max(
        [find_msb_common_bits(iul[0], ibr[0]), find_msb_common_bits(iul[1], ibr[1])])
    
    if bit_diverge < 64 - 21:
        bit_diverge = 64 - 21
    
    i = 1 << 63
    o = 1 << 63
    r = 0
    x = int(iul[0])
    y = int(iul[1])
    for b in range(64, bit_diverge, -1):
        if i & x:
            r |= o
        o >>= 1
        if i & y:
            r |= o
        o >>= 1
        i >>= 1
        o >>= 1
    o <<= 1
    r |= o
    return r
    

class QuadTree:
    
    def __init__(self):
        self.sd = SortedDict()
        
    def insert(self, bbox, value):
        k = map_bounding_box_to_key(bbox[0], bbox[1])
        if k not in self.sd:
            self.sd[k] = []
            
        self.sd[k].append((bbox, value))
        
    def find_containing(self, bbox):
        pass
    


if __name__ == "__main__":
    print(map_bounding_box_to_key([1036, 200], [1034, 100]))
    print(map_bounding_box_to_key([1033, 100], [1033, 100]))
    m=10
    n=12
    print(map_bounding_box_to_key([1<<m, 1<<m], [1<<m, 1<<m]))
    print(map_bounding_box_to_key([1<<m, 1<<m], [1<<n, 1<<n]))
    print(map_bounding_box_to_key([1032.333, 100.333], [1032.333, 100.333]))
