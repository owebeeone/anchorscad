import numpy as np

EPSILON = 1e-5


def remove_adjacent_indices(indicies: np.ndarray):
    '''When removing points from a polygon, we don't want to remove points that are adjacent to each other
    otherwise we may be removing more than we want. Here we decide to remove either
    even or odd indicies, depending on which one is more frequent. And then we repeat
    the operation until no more points are removed.
    '''
    odd_indicies = indicies[indicies % 2 == 1]
    odd_indicies_count = len(odd_indicies)
    even_indicies_count = len(indicies) - odd_indicies_count
    if odd_indicies_count >= even_indicies_count:
        return odd_indicies, even_indicies_count > 0
    return indicies[indicies % 2 == 0], odd_indicies_count > 0

def remove_duplicate_adjacent_points(points: np.ndarray, tolerance: float=EPSILON) -> np.ndarray:
    '''Remove points that are almost identical to their neighbors. Assume points describe a 
    polygon, this will remove points that are almost describing the same as the adjacent points.'''
    
    tolerance_squared = tolerance ** 2
    has_changes = True
    while has_changes:
        # Calculate the direction of vectors between adjacent points.
        directions = np.diff(points, axis=0)
        indicies = np.where(np.sum(directions ** 2, axis=1) < tolerance_squared)[0] + 1
        
        # If we got nothing to remove, we are done.
        if len(indicies) == 0:
            return points
        
        indicies, has_changes = remove_adjacent_indices(indicies)
        
        points = np.delete(points, indicies, axis=0)
        
    return points

def remove_colinear_points(points: np.ndarray, tolerance: float=EPSILON) -> np.ndarray:
    '''Remove points that are colinear with their neighbors. Assume points describe a polygon.
    Points that almost describe a straight line are removed.
    '''
    # Remove duplicate adjacent points first. This algorithm below assumes that there are no
    # duplicate adjacent points.
    points = remove_duplicate_adjacent_points(points, tolerance=tolerance)
    
    # Find where the determinant is larger than the tolerance.
    tolerance_squared = tolerance ** 2
    has_changes = True
    while has_changes:
        # Calculate the direction of vectors between adjacent points
        directions = np.diff(points, axis=0)
        
        # Calculate the determinant of each pair of adjacent directions. If the determinant is
        # close to zero, then the points are colinear (as long as the points are not too close).
        # If they are too close, then we assume they are the same point and we remove them.
        determinants = np.linalg.det(np.stack((directions[:-1], directions[1:]), axis=1))
        
        indicies = np.where(np.abs(determinants) < tolerance_squared)[0] + 1
        
        # If we got nothing to remove, we are done.
        if len(indicies) == 0:
            return points
        
        indicies, has_changes = remove_adjacent_indices(indicies)
        
        points = np.delete(points, indicies, axis=0)
    
    return points

