import unittest
import numpy as np

from anchorscad_lib.test_tools import iterable_assert

from anchorscad.path_utils import remove_duplicate_adjacent_points, remove_colinear_points

class TestRemovePoints(unittest.TestCase):
    def test_remove_duplicate_adjacent_points(self):
        points = np.array([[0, 0], [1, 1], [1, 1.000000001], [2, 1], [2, 1], [3, 3], [4, 3], [5, 5]])
        new_points = remove_duplicate_adjacent_points(points, tolerance=1e-3)
        expected_points = np.array([[0, 0], [1, 1], [2, 1], [3, 3], [4, 3], [5, 5]])
        iterable_assert(self.assertAlmostEqual, new_points, expected_points)

    def test_remove_colinear_points(self):
        points = np.array([[0., 0], [1, 1], [2, 2], [3, 2], [4, 4], [5, 5], [6, 6]])
        new_points = remove_colinear_points(points)
        expected_points = np.array([[0, 0], [2, 2], [3, 2], [4, 4], [6, 6]])
        iterable_assert(self.assertAlmostEqual, new_points, expected_points)
        
    def test_remove_colinear_points_with_duplicates(self):
        points = np.array([[0., 0], [1, 1], [1, 1], [1, 1], [1, 1], [2, 2], [3, 2], [3, 2], [4, 4], [5, 5], [6, 6], [6, 6]])
        new_points = remove_colinear_points(points)
        expected_points = np.array([[0, 0], [2, 2], [3, 2], [4, 4], [6, 6]])
        iterable_assert(self.assertAlmostEqual, new_points, expected_points)

if __name__ == '__main__':
    unittest.main()