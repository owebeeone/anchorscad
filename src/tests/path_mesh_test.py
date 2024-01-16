

# Assuming path_mesh is a class in the path_mesh_test.py file, you can create unit tests using the unittest module in Python.

import unittest
from dataclasses import dataclass, field
from anchorscad.path_mesh import closest_points, tesselate_between_paths
import numpy as np
import sys

import matplotlib.pyplot as plt

IS_CLOSED = False

class Finished(Exception):
    pass

@dataclass
class MapClosestPoints:
    points1: np.array
    points2: np.array
    s1: np.array
    s2: np.array
    title: str
    cid: object = field(init=False)
    
    def __post_init__(self):
        self.plot_closest_points()
        
    def onclick(self, event):
        global IS_CLOSED
        IS_CLOSED = True
        
    def plot_closest_points(self):
        
        # Plot the results.
        fig, ax = plt.subplots()
        
        self.cid = fig.canvas.mpl_connect('close_event', lambda e : self.onclick(e))
        # Add a title to the plot.
        ax.set_title(self.title)
        ax.set_aspect('equal')
        # Use the "tight" layout.
        plt.tight_layout(pad=0, h_pad=0, w_pad=0, rect=[0, 0, 1, 1])
        ax.set_in_layout(False)
        plt.ion()
        
        # Plot the points in points1 in red and points2 in blue.
        
        ax.plot(self.points1[:, 0], self.points1[:, 1], 'ro')
        for i in range(len(self.points1)):
            plt.annotate(str(i), (self.points1[i, 0], self.points1[i, 1]))
        ax.plot(self.points2[:, 0], self.points2[:, 1], 'bo')
        for i in range(len(self.points2)):
            plt.annotate(str(i), (self.points2[i, 0], self.points2[i, 1]))
        
        # Plot the lines from points1 to points2 using s1 and s2.
        for j, i in enumerate(self.s1):
            ax.plot([self.points1[i, 0], self.points2[j, 0]], [self.points1[i, 1], self.points2[j, 1]], 'g-')
        # Plot the lines from points2 to points1 using s2 and s1.
        for j, i in enumerate(self.s2):
            ax.plot([self.points2[i, 0], self.points1[j, 0]], [self.points2[i, 1], self.points1[j, 1]], 'p-')
        
        # Plot the lines between points in points1 with each line
        # changing in colour gradially from green to yellow and add
        # a closing line from the last point to the first point.
        for i in range(len(self.points1) - 1):
            ax.plot([self.points1[i, 0], self.points1[i + 1, 0]],
                    [self.points1[i, 1], self.points1[i + 1, 1]], 'y-')
        
        ax.plot([self.points1[-1, 0], self.points1[0, 0]],
                [self.points1[-1, 1], self.points1[0, 1]], 'o-')
        
        # Plot the lines between points in points2 with each line
        # changing in colour gradially from green to yellow and add
        # a closing line from the last point to the first point.
        for i in range(len(self.points2) - 1):
            ax.plot([self.points2[i, 0], self.points2[i + 1, 0]], [self.points2[i, 1], self.points2[i + 1, 1]], 'c-')
                
        ax.plot([self.points2[-1, 0], self.points2[0, 0]],
                [self.points2[-1, 1], self.points2[0, 1]], 'p-')
        
        # Render the image to the size of the screen.
        fig.set_size_inches(10.5, 10.5)
    
        #plt.get_current_fig_manager().window.state('zoomed')    
        plt.show()

        

class TestPathMesh(unittest.TestCase):
    # def test_find_nearest_points_indexes_returns_expected_result(self):
    #     # Test case with specific 2D points
    #     points1 = [(1, 2), (3, 4), (5, 6)]
    #     points2 = [(1.1, 2.2), (3.3, 4), (5.5, 6.6)]
    #     expected_result = [0, 1, 2]
    #     self.assertEqual(find_nearest_points_indexes(points2, points1), expected_result)

    # # Add more test cases as needed
        
    # def test_find_nearest_points_indexes_returns_expected_result_3D(self):
    #     # Test case with specific 3D points
    #     points1 = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
    #     points2 = [(1.1, 2.2, 3.3), (4.4, 5.5, 6.6), (7.7, 8.8, 9.9)]
    #     expected_result = [0, 1, 2]
    #     self.assertEqual(find_nearest_points_indexes(points2, points1), expected_result)

    def make_points(self, n, r, offset):
        offset_ang = offset * 2 * np.pi / n
        return np.array(
            list((r * np.sin(t), r * np.cos(t)) 
                 for t in np.linspace(offset_ang, offset_ang + 2 * np.pi * (n - 1) / n, n)))
    
    def make_pointsx(self, n, r, offset):
        return np.array([(i + offset + r, i + r) for i in range(n)])
    
    # Makes points introducing random noise.
    def make_points_noise(self, min_radius, max_radius, n, radius_seed, angle_seed, offset_angle):
        radiuses = np.random.RandomState(radius_seed).uniform(min_radius, max_radius, n)
        angles = np.random.RandomState(angle_seed).uniform(0, 2 * np.pi, n)
        # Sort angles so that the points are in order.
        angles.sort()
        return np.array(
            list((r * np.sin(t + offset_angle), r * np.cos(t + offset_angle)) 
                 for r, t in zip(radiuses, angles)))
        


        
    def test_tesselate_with_noisy_points(self):
        # Test case with specific 3D points
        s = 54
        n = 15
        points1 = self.make_points_noise(15, 20, n, s + 10, s + 11, np.pi / 5)
        points2 = self.make_points_noise(25, 30, n + 10, s + 12, s + 13, 0)
        
        # Call closest_points() to and plot the results.
        s1, s2 = closest_points(points1, points2)
        #print(closest_points(points2, points1))
        
        #MapClosestPoints(points1, points2, s1, s2, f'Noisy points (seed={s} n={n})')
        #MapClosestPoints(points1, points2, s1, s2, 'Noisy points Test')

        #tesselate_between_paths(points1, 100, points2, 200)

        #self.assertEqual(closest_points_monotonic(points2, points1), expected_result)
        
    def test_wrap_around_test(self):
        
        points1 = np.array([
            (0, 1), 
            (0, 1.1), 
            (0, 1.2), 
            (0, 1.3), 
            (2, 2),
            (2, 0),
            (0, 0),
            (0, 0.0), 
            (0, 0.7), 
            (0, 0.8), 
            (0, 0.9)
            ])
        
        points2 = np.array([
            (0.1, 1), 
            (1, 1), 
            (1.8, 1.8), 
            (1.8, 0.2), 
            (0.2, 0.2)
            ])
        
        
        # Call closest_points() to and plot the results.
        s1, s2 = closest_points(points1, points2)
        print(s1, s2)
        
        MapClosestPoints(points1, points2, s1, s2, f'Wrap issue')
        
        tesselate_between_paths(points1, 100, points2, 200)


    def test_find_nearest_points_indexes_larger(self):
        # Test case with specific 3D points
        n = 11
        r = 10
        points1 = self.make_points(n-5, 10, 0)
        points2 = self.make_points(n-0, 11, 3)

        #print(closest_points(points2, points1))
        #tesselate_between_paths(points1, 100, points2, 200)

        #self.assertEqual(closest_points_monotonic(points2, points1), expected_result)

def pause_on_close():
    while not IS_CLOSED:
        manager = plt.get_current_fig_manager()
        if manager is not None:
            canvas = manager.canvas
            if canvas.figure.stale:
                canvas.draw_idle()
            canvas.start_event_loop(0.1)
    return

if __name__ == '__main__':
    test = unittest.main(exit=False)
    pause_on_close()
    sys.exit(not test.result.wasSuccessful())
    