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
    '''Reorder a list of elements in the set (0..set_size-1) 
    that forms a circular group of set_size elements.

    This takes a list of numbers that represent a quasi sequence in 
    the set (0..set_size-1) and reorders the list so that the sequence
    starts at the beginning of the sequence. e.g. for set_size=15,
    the input [0, 2, 10, 12, 13], the result will be [10, 12, 13, 0, 2].
    i.e the sequence starts at 10 and wraps around to 2 while the 
    elements 11, 14, and 1 are missing in the sequence.
    
    Parameters:
    numbers (list or array-like): The input list or array of numbers.
    set_size (int): The size of the circular set, with values ranging 
        from 0 to set_size-1.

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


def overlaps(range1: Tuple[int, int], range2: Tuple[int, int]) -> bool:
    # Overlapping here is defined as the two ranges having more than an end point
    # in common.
    wrap1 = range1[0] > range1[1]
    wrap2 = range2[0] > range2[1]
    if wrap1:
        # This is a wrap around range.
        if wrap2:
            # Both are wrap around ranges so they must overlap.
            return True
        return range2[0] < range1[1] or range2[1] > range1[0]
    elif wrap2:
        # range2 is a wrap around range but range1 is not.
        return range1[0] < range2[1] or range1[1] > range2[0]
    
    # Both ranges don't wrap:
    return not (range2[1] <= range1[0] or range1[1] <= range2[0])

def intersect(range1: Tuple[int, int], range2: Tuple[int, int]) \
    -> Tuple[Tuple[int, int], Tuple[int, int]]:
    '''Returns up to 2 ranges of numbers in a circular set that are in the 
    intersection of range1 and range2. The intersection of 2 circular ranges can be 2 
    discontinuous ranges.'''
    
    wrap1 = range1[0] > range1[1]
    wrap2 = range2[0] > range2[1]
    if wrap1:
        # This is a wrap around range.
        if wrap2:
            # Both are wrap around ranges so they must overlap.
            return ((max(range1[0], range2[0]), min(range1[1], range2[1])),)
        result = ()
        if range2[0] <= range1[1]:
            result = ((range2[0], min(range1[1], range2[1])),)
        
        if range2[1] >= range1[0]:
            result += ((max(range2[1], range1[0]), range1[0]),)
        return result
    elif wrap2:
        # range2 is a wrap around range but range1 is not.
        result = ()
        if range1[0] <= range2[1]:
            result = ((range1[0], range2[1]),)
        
        if range1[1] >= range2[0]:
            result += ((range1[1], range2[0]),)
        return result
    
    # Both ranges don't wrap:
    result = (max(range1[0], range2[0]), min(range1[1], range2[1]))
    if result[0] > result[1]:
        return ()
    return (result,)

def size_range(r: Tuple[int, int], size: int) -> int:
    '''Returns the number of elements of the range in the circular set of size.'''
    if not r:
        return 0
    if r[0] > r[1]:
        return size - r[0] + r[1] + 1
    return r[1] - r[0] + 1


@dataclass
class _TesselatorHelperSide:
    points: np.array
    index_offset: int
    map_closest: np.array
    tesselator: '_TesselatorHelper'
    other_side: '_TesselatorHelperSide' = field(init=False)
    incoming: List[List[int]] = field(init=False)
    ranges: List[Tuple[int, int]] = field(init=False)
    fixed_ranges: List[Tuple[int, int]] = field(init=False)

    def initialize_state(self) -> None:
        self.incoming = [[] for _ in range(len(self.points))]
        self.ranges = [None] * len(self.points)
        self.fixed_ranges = [None] * len(self.points)

    def populate_edges(self) -> None:
        self.other_side.initialize_state()
        for i, j in enumerate(self.map_closest):
            self.other_side.incoming[j].append(i)
        self.other_side.correct_sequences()

    def correct_sequences(self) -> None:
        # The incoming edges are not necessarily in the correct order,
        # this fixes that.
        # These index the other side's points so n is the number of
        # points in the other side.
        n = len(self.other_side.points)
        for i in range (len(self.points)):
            osi = self.incoming[i]
            if len(osi) > 0:
                self.incoming[i] = correct_circular_sequence(osi, n)
    
        for i in range (len(self.points)):
            self.ranges[i] = self._get_range_of(i)
            self.fixed_ranges[i] = self.ranges[i]
           
    def prev(self, idx: int) -> int:
        return (idx - 1) % len(self.points)
    
    def next(self, idx: int) -> int:
        return (idx + 1) % len(self.points)
    
    def _get_range_of(self, idx: int) -> Tuple[int, int]:
        # Returns the range of incoming edges that are inclusive.
        closest = self.map_closest[idx]
        incoming = self.incoming[idx]
        # if there are no incoming edges or has one and it's the same as closest,
        # then the closest point is the only point in the range.
        if len(incoming) == 0 or len(incoming) == 1 and incoming[0] == closest:
            return (closest, closest)
        
        n = len(self.other_side.points)
        
        if len(incoming) == 1:
            return tuple(correct_circular_sequence((incoming[0], closest), n))
        
        # Include the closest point if it is not already included.
        if not closest in incoming:
            # Use the correct_circular_sequence to make sure the sequence is consistent.
            incoming = correct_circular_sequence(tuple(incoming) + (closest,), n)
        
        return (incoming[0], incoming[-1])
    
    def get_range_of(self, idx: int) -> Tuple[int, int]:
        return self.ranges[idx]

    def get_fixed_range_of(self, idx: int) -> Tuple[int, int]:
        return self.fixed_ranges[idx]

        
    def other_next(self, idx: int) -> int:
        return self.other_side.next(idx)
    
    def other_prev(self, idx: int) -> int:
        return self.other_side.prev(idx)
    
    
    def handle_crossover(self, 
        idx: int, er: Tuple[int, int], 
        aidx:int, aer: Tuple[int, int],
        aer_test: Tuple[int, int],
        n: int) -> int:
        '''Handles a crossover between the current range and the next range.
        Returns 1 or -1 depending on whether the next or previous vertex needs
        checking.
        '''
        siz = size_range(er, n)
        asiz = size_range(aer, n)
        
        print(f'crossover at {idx}-{aidx}')  
        
        if siz == 1:
            if asiz == 1:
                # Overlap here means that er is beyond aer.
                self.fixed_ranges[idx] = (aer[0], aer[0])
                # Because we moved the current range, we need to go back and fix check
                # the previous range.
                return -1
            
        common = intersect(er, aer)
        
        # If the first point in common is not the same as 
        # the first point in aer, than that means we have to
        # move the current range to start at the start point and then
        # somehow bisect the ranges.
        if not common or common[0][0] != aer[0]:
            # We need to move the current range to start at the start point.
            self.fixed_ranges[idx] = (aer[0], aer[0])
            # Because we moved the current range, we need to go back and fix check
            # the previous range.
            return -1
        
        if asiz >= siz:
            self.fixed_ranges[idx] = (er[0], aer[0])
        else:
            self.fixed_ranges[idx] = (er[0], common[0][1])
            c1 = (common[0][1], aer[1])
            c2 = (common[0][1], er[1])
            if max(size_range(c1, n), size_range(c2, n)) > max(siz, asiz):
                assert False, 'This should not happen.'
            if size_range(c1, n) > size_range(c2, n):
                self.fixed_ranges[aidx] = c1
            else:
                self.fixed_ranges[aidx] = c2

        return 1
        
    def detect_crossover(self, idx: int) -> None:
        '''Returns 1 or -1 depending on whether the next or previous vertex needs
        checking.'''
        # First find the adjacent points crossovers.
        range_this = self.get_fixed_range_of(idx)
        nidx = self.next(idx)
        range_next = self.get_fixed_range_of(nidx)
        
        # It can be that this range starts after the next range which is
        # still a crossover so we make the test range end way beyond the
        # end of the next range and test that for overlap.
        n = len(self.other_side.points)
        mid_next = (n - (range_next[1] - range_next[0]) % n) // 2
        range_test = (range_next[0], (range_next[1] + mid_next) % n)
        
        if overlaps(range_this, range_test):
            offs = self.handle_crossover(idx, range_this, nidx, range_next, range_test, n)
            print(f'{self.name()} overlaps at this={range_this} next={range_next} test={range_test}')
            return offs
        
        return 1
            
    def fix_crossovers(self) -> None:
        count = 0
        n = len(self.points)
        while count < n:
            count += self.detect_crossover(count)
        
    def name(self) -> str:
        return 'side1'
    
    def distance_sq_between(self, this_side_idx: int, other_side_idx: int) -> float:
        return self.tesselator.distance2_between(this_side_idx, other_side_idx)

@dataclass
class _TesselatorHelperOtherSide(_TesselatorHelperSide):    
    # Override this to keep the indexes in the correct order.
    def distance_sq_between(self, this_side_idx: int, other_side_idx: int) -> float:
        return self.tesselator.distance2_between(other_side_idx, this_side_idx)
    
    def name(self) -> str:
        return 'side2'

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

def circular_range(start_end: Tuple[int], size: int) -> List[int]:
    '''Returns a list of numbers in the range [start, end] that wraps around
    the given size.
    
    Args:
    '''
    if len(start_end) == 0:
        return
    
    curr = start_end[0]
    yield curr
    
    while curr != start_end[1]:
        curr = (curr + 1) % size
        yield curr
        


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

    return helper