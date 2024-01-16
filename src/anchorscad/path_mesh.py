from dataclasses import dataclass, field
import numpy as np
from typing import Union, List, Tuple
from collections import defaultdict


def closest_points(points1: np.array, points2: np.array) \
        -> Tuple[np.array, np.array]:
    """
    Finds the indicied of the closest points respectively in each array.

    Args:
    points1: An ndarray of shape (N, D) containing points in the first set.
    points2: An ndarray of shape (M, D) containing points in the second set.

    Returns:
    2 arrays of shape (N,) and (M,) respectively containing the indices of the 
    closest points in each array.
    """

    # Calculate squared distances between all points.
    distances_sq = np.sum((points1[:, None, :] - points2[None, :, :])**2, axis=-1)

    #print(distances_sq.shape)
    #print(distances_sq)

    return np.argmin(distances_sq, axis=0), np.argmin(distances_sq, axis=1)


def correct_circular_sequence(numbers:List[int], set_size:int):
    '''Reorder a list of numbers representing a circular set (0 to N-1) 
    to form a continuous sequence considering the circular nature.

    The function finds the largest gap in the sequence, considering
    the circular nature (where 0 follows N-1), and reorders the list 
    starting from the number after this gap.

    Parameters:
    numbers (list or array-like): The input list or array of numbers.
    N (int): The size of the circular set, with values ranging from 0 to N-1.

    Returns:
    numpy.ndarray: A reordered array where the sequence is continuous,
    considering the circular nature of the set.
    
    Example:
    >>> correct_circular_sequence([0, 2, 3, 10, 12, 13, 14], 15)
    array([10, 12, 13, 14,  0,  2,  3])
    '''
    # Convert to numpy array and sort
    numbers = np.sort(np.array(numbers))

    # Calculate gaps, including the circular gap
    gaps = np.diff(np.append(numbers, numbers[0] + set_size))

    # Find the index of the largest gap
    max_gap_index = np.argmax(gaps)

    # Rearrange the array to start after the largest gap
    return np.roll(numbers, -max_gap_index - 1)


# Example usage
N = 15
numbers = [0, 2, 3, 10, 12, 13, 14]
numbers = [10, 11, 13]
numbers = [10, 11, 13, 1, 2]
result = correct_circular_sequence(numbers, N)
print(result)


@dataclass
class _TesselatorHelperSide:
    points: np.array
    index_offset: int
    map_closest: np.array
    tesselator: '_TesselatorHelper'
    other_side: '_TesselatorHelperSide' = field(init=False)
    incoming: List[List[int]] = field(init=False)

    def initialize_state(self) -> None:
        self.incoming = [[] for _ in range(len(self.points))]

    def populate_edges(self) -> None:
        self.other_side.initialize_state()
        for i, j in enumerate(self.map_closest):
            self.other_side.incoming[j].append(i)
            
    def prev(self, idx: int) -> int:
        return (idx - 1) % len(self.points)
    
    def next(self, idx: int) -> int:
        return (idx + 1) % len(self.points)
    
    def get_range_of(self, idx: int) -> Tuple[int, int]:
        # Returns the range of incoming edges that are inclusive.
        closest = self.map_closest[idx]
        incoming = self.incoming[idx]
        print(f'get_range_of({idx}) closest={closest} incoming={incoming}')
        # if there are no incoming edges then the closest point 
        # is the only edge in range.
        if len(incoming) == 0 or len(incoming) == 1 and incoming[0] == closest:
            val = (closest, closest)
            print(f'+++ returning {val}')
            return val
        
        nd2 = len(self.points) // 2
        
        if abs(incoming[0] - incoming[-1]) > nd2:
            incoming = incoming[::-1]
            # Possible wrap around range.
            val = (incoming[-1], closest)
            print(f'+++ returning {val}')
            return val
        
        diff_closest = abs(closest - incoming[0])
        if diff_closest > nd2:
            # This may be a wrap around range.
            if abs(closest - incoming[-1]) > nd2:
                val = (incoming[-1], closest)
                print(f'+++ returning {val}')
                return val
            val = (closest, self.other_prev(incoming[0]))
            print(f'+++ returning {val}')
            return val

        if closest < incoming[0]:
            # This may be a wrap around range.
            if incoming[-1] < closest:
                val = (closest, incoming[-1])
                print(f'+++ returning {val}')
                return val
        
        if closest > incoming[-1]:
            val = (incoming[0], closest)
            print(f'+++ returning {val}')
            return val
        val = (incoming[0], self.other_next(incoming[-1]))
        print(f'+++ returning {val}')
        return val
        
    def other_next(self, idx: int) -> int:
        return self.other_side.next(idx)
    
    def other_prev(self, idx: int) -> int:
        return self.other_side.prev(idx)
    
    def overlaps(self, range1: Tuple[int, int], range2: Tuple[int, int]) -> bool:
        # Overlapping here is defined as the two ranges having more than an end point
        # in common.
        if range1[0] >= range1[1]:
            # This is a wrap around range.
            if range2[0] >= range2[1]:
                # Both are wrap around ranges so they must overlap.
                return True
            return range2[1] >= range1[0] - 1 or range2[0] < range1[1]
        elif range2[0] >= range2[1]:
            # range2 is a wrap around range but range1 is not.
            return range1[1] >= range2[0] - 1 or range1[0] < range2[1]
        
        # Both ranges don't wrap:
        return not (range2[1] <= range1[0] or range1[1] <= range2[0])
            
    
    def other_overlaps(self, range1: Tuple[int, int], range2: Tuple[int, int]) -> bool:
        return self.other_side.overlaps(range1, range2)
    
    def handle_crossover(self, idx: int, adjacent:int) -> None:
        print(f'crossover at {idx}-{adjacent}')  
    
    def detect_crossover(self, idx: int) -> None:
        # First find the adjacent points crossovers.
        range_this = self.get_range_of(idx)
        range_next = self.get_range_of(self.next(idx))
        
        if self.overlaps(range_next, range_this):
            self.handle_crossover(idx, self.next(idx))
            print(f'overlaps at {range_this} {range_next} ')
            
    def fix_crossovers(self) -> None:
        for idx in range(len(self.points)):
            self.detect_crossover(idx)
        
            
    def distance_sq_between(self, this_side_idx: int, other_side_idx: int) -> float:
        return self.tesselator.distance2_between(this_side_idx, other_side_idx)

@dataclass
class _TesselatorHelperOtherSide(_TesselatorHelperSide):    
    # Override this to keep the indexes in the correct order.
    def distance_sq_between(self, this_side_idx: int, other_side_idx: int) -> float:
        return self.tesselator.distance2_between(other_side_idx, this_side_idx)

@dataclass
class _TesselatorHelper:

    side1: _TesselatorHelperSide = field(init=False)
    side2: _TesselatorHelperSide = field(init=False)
    distances_sq: np.array = field(init=False)
    map1_closest: np.array = field(init=False)
    map2_closest: np.array = field(init=False)

    def __init__(self, points1: np.array, index_offset1: int, points2: np.array, index_offset2: int) -> None:

        if index_offset1 > index_offset2:
            points1, points2, index_offset1, index_offset2 = \
                points2, points1, index_offset2, index_offset1
            
        # Make sure the index offsets are valid.
        assert (index_offset2 >= index_offset1 + len(points1)), \
            'The index offsets must not overlap between points.'

        self.distances_sq = np.sum((points1[:, None, :] - points2[None, :, :])**2, axis=-1)
        map2_closest = np.argmin(self.distances_sq, axis=0)
        map1_closest = np.argmin(self.distances_sq, axis=1)
        
        self.side1 = _TesselatorHelperSide(points1, index_offset1, map1_closest, self)
        self.side2 = _TesselatorHelperOtherSide(points2, index_offset2, map2_closest, self)
        self.side1.other_side = self.side2
        self.side2.other_side = self.side1

    def distance2_between(self, p1_idx: int, p2_idx: int) -> float:
        # Returns the squared distance between the points at the given indices
        # in the two sets of points.
        return self.distances_sq[p1_idx, p2_idx]

    def perform_tesselation(self) -> None:

        self._populate_closest_edges()
        
        self.side1.fix_crossovers()
        self.side2.fix_crossovers()
        
        self.identify_anchor_points()
        
    def identify_anchor_points(self) -> None:
        
        pass

    def add_edge(self, side: _TesselatorHelperSide, i: int, j: int) -> None:
        side.incoming[j].append(i)

    def _populate_closest_edges(self) -> None:
        self.side1.populate_edges()
        self.side2.populate_edges()



def tesselate_between_paths(
        points1: np.array, index_offset1: int, points2: np.array, index_offset2: int) \
        -> Tuple[np.array, ...]:
    """
    Creates a tesselation of the given points, where each point in the first set
    is connected to its closest point in the second set modulo the differing number
    of points in each set.

    This is particularly useful for creating a tesselation of two closed paths that
    have the same shape but may vary in size. This may apply to a polygon that has been 
    shrunk or expanded or scaled or modulated in some way that maintains a similar shape.


    Args:
    points1: An ndarray of shape (N, D) containing points in the first set.
    index_offset1: The index offset for the first set of points.
    points2: An ndarray of shape (M, D) containing points in the second set.
    index_offset2: The index offset for the second set of points.

    Returns:
    A list of faces, where each face is an array of indices with the given offsets
    applied.
    """

    # Make sure the index offsets are valid.
    assert (index_offset2 >= index_offset1 + len(points1)) or \
           (index_offset1 >= index_offset2 + len(points2)), \
           'The index offsets must not overlap.'

    # To make the algorithm simpler, we will make the smallest offset the first set.
    if index_offset1 > index_offset2:
        points1, points2, index_offset1, index_offset2 = \
            points2, points1, index_offset2, index_offset1

    helper = _TesselatorHelper(points1, index_offset1, points2, index_offset2)

    helper.perform_tesselation()
    
    #print(helper.side1.incoming)
    #print(helper.side2.incoming)

    return ()