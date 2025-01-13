

# Assuming path_mesh is a class in the path_mesh_test.py file, you can create unit tests using the unittest module in Python.

import unittest
from dataclasses import dataclass, field
from anchorscad.path_mesh import closest_points, tesselate_between_paths, overlaps, \
    _TesselatorHelper, circular_range, intersect, _create_tesselator_helper
from anchorscad import PathBuilder, MappedPolygon, ModelAttributes, EMPTY_ATTRS
from anchorscad.extrude_flex import PathOffsetMaker
import numpy as np
import time
import sys

import matplotlib.pyplot as plt

IS_CLOSED = False
IS_INTERACTIVE = False

class Finished(Exception):
    pass

@dataclass
class PlotBase:
    title: str
    cid: object = field(init=False)
    
    def onclick(self, event):
        global IS_INTERACTIVE
        IS_INTERACTIVE = True
    
    def onclose(self, event):
        global IS_CLOSED
        IS_CLOSED = True
        
    def init_plot(self):
        # Plot the results.
        fig, ax = plt.subplots()
        
        self.cid = fig.canvas.mpl_connect('close_event', lambda e : self.onclose(e))
        self.cid = fig.canvas.mpl_connect('button_press_event', lambda e : self.onclick(e))
        # Add a title to the plot.
        ax.set_title(self.title)
        ax.set_aspect('equal')
        # Use the "tight" layout.
        plt.tight_layout(pad=0, h_pad=0, w_pad=0, rect=[0, 0, 1, 1])
        ax.set_in_layout(False)
        plt.ion()
        # Render the image to the size of the screen.
        fig.set_size_inches(10.5, 10.5)
        
        return fig, ax
        

@dataclass
class PlotClosestPoints(PlotBase):
    points1: np.array
    points2: np.array
    s1: np.array
    s2: np.array
    title: str
    
    def __post_init__(self):
        self.plot_closest_points()
        
    def plot_closest_points(self):
        
        # Plot the results.
        fig, ax = self.init_plot()

        # Plot the points in points1 in red and points2 in blue.
        
        ax.plot(self.points1[:, 0], self.points1[:, 1], 'ro')
        for i in range(len(self.points1)):
            plt.annotate(str(i), (self.points1[i, 0], self.points1[i, 1]))
        ax.plot(self.points2[:, 0], self.points2[:, 1], 'bo')
        for i in range(len(self.points2)):
            plt.annotate(str(i), (self.points2[i, 0], self.points2[i, 1]))
        
        # Plot the lines from points1 to points2 using s1 and s2.
        for j, i in enumerate(self.s1):
            ax.plot([self.points1[i, 0], self.points2[j, 0]], 
                    [self.points1[i, 1], self.points2[j, 1]], 'g-')
        # Plot the lines from points2 to points1 using s2 and s1.
        for j, i in enumerate(self.s2):
            ax.plot([self.points2[i, 0], self.points1[j, 0]], 
                    [self.points2[i, 1], self.points1[j, 1]], 'p-')
        
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
            ax.plot([self.points2[i, 0], self.points2[i + 1, 0]], 
                    [self.points2[i, 1], self.points2[i + 1, 1]], 'c-')
                
        ax.plot([self.points2[-1, 0], self.points2[0, 0]],
                [self.points2[-1, 1], self.points2[0, 1]], 'p-')
    
        #plt.get_current_fig_manager().window.state('zoomed')    
        plt.show()


@dataclass
class PlotRanges(PlotBase):
    tess_helper: _TesselatorHelper
    title: str
    cid: object = field(init=False)
    
    def __post_init__(self):
        self.plot_edges()
               
    def plot_points(self, fig, ax):
        # Plot the points in points1 in red and points2 in blue.
        points1 = self.tess_helper.side1.points
        points2 = self.tess_helper.side2.points
        
        ax.plot(points1[:, 0], points1[:, 1], 'ro')
        for i in range(len(points1)):
            plt.annotate(str(i), (points1[i, 0], points1[i, 1]))
            
        ax.plot(points2[:, 0], points2[:, 1], 'bo')
        for i in range(len(points2)):
            plt.annotate(str(i), (points2[i, 0], points2[i, 1]))

        # Plot the lines between points in points1 with each line
        # changing in colour gradially from green to yellow and add
        # a closing line from the last point to the first point.
        for i in range(len(points1) - 1):
            ax.plot([points1[i, 0], points1[i + 1, 0]],
                    [points1[i, 1], points1[i + 1, 1]], 'y-')
        
        ax.plot([points1[-1, 0], points1[0, 0]],
                [points1[-1, 1], points1[0, 1]], 'o-')
        
        # Plot the lines between points in points2 with each line
        # changing in colour gradially from green to yellow and add
        # a closing line from the last point to the first point.
        for i in range(len(points2) - 1):
            ax.plot([points2[i, 0], points2[i + 1, 0]], 
                    [points2[i, 1], points2[i + 1, 1]], 'c-')
                
        ax.plot([points2[-1, 0], points2[0, 0]],
                [points2[-1, 1], points2[0, 1]], 'p-')
        
    
    def get_range_for_side(self, side, i):
        return side.ranges[i]
        
    def plot_ranges_for_side(self, side, fig, ax, colour):
        
        #side = self.tess_helper.side1
        for i in range(len(side.ranges)):
            r = self.get_range_for_side(side, i)
            for j in circular_range(r, len(side.other_side.points)):
                ax.plot([side.points[i, 0], side.other_side.points[j, 0]],
                        [side.points[i, 1], side.other_side.points[j, 1]], colour)

    def plot_ranges(self, fig, ax):
        #self.plot_ranges_for_side(self.tess_helper.side1, fig, ax, 'g-')
        self.plot_ranges_for_side(self.tess_helper.side2, fig, ax, 'p-')            
        
    def plot_edges(self):
        
        # Plot the results.
        fig, ax = self.init_plot()
        
        self.plot_points(fig, ax)
        
        self.plot_ranges(fig, ax)
        
        #plt.get_current_fig_manager().window.state('zoomed')    
        plt.show()
        
@dataclass
class PlotFixedRanges(PlotRanges):

    def get_range_for_side(self, side, i):
        return side.fixed_ranges[i]

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
        
    def make_path(self, n, r, offset):
        return self.make_path_from(self.make_points, n, r, offset)
        
    def make_path_from(self, func, *args, **kwds):
        points = func(*args, **kwds)
        builder = PathBuilder()
        builder.move(points[0])
        for i, p in enumerate(points[1:]):
            builder.line(p, name=('line', i))
            
        builder.line(points[0], name=('line', len(points) - 1))
        return builder.build()
        
    
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
        
    def maker_path_noise(self, min_radius, max_radius, n, radius_seed, angle_seed, offset_angle):
        return self.make_path_from(
            self.make_points_noise, min_radius, max_radius, n, radius_seed, angle_seed, offset_angle)
    
        
    def overlaps_helper(self, p1, p2):
        v1 = overlaps(p1, p2)
        v2 = overlaps(p2, p1)
        self.assertEqual(v1, v2)
        return v1

    def test_overlaps(self):
        
        self.assertFalse(self.overlaps_helper((4, 4), (4, 2)))
        self.assertFalse(self.overlaps_helper((4, 4), (4, 0)))
        self.assertFalse(self.overlaps_helper((6, 6), (7, 3)))
        self.assertTrue(self.overlaps_helper((7, 3), (1, 1)))
        
    def test_intersect(self):
        
        self.assertEqual(
            intersect((0, 1), (1, 1)), 
            ((1, 1),))
        
        self.assertEqual(
            intersect((5, 1), (1, 5)), 
            ((1, 1), (5, 5)))
        
        self.assertEqual(
            intersect((1, 5), (5, 1)), 
            ((1, 1), (5, 5)))
        
        self.assertEqual(
            intersect((1, 5), (6, 0)), 
            ())
    
        self.assertEqual(
            intersect((6, 0), (1, 5)), 
            ())

        self.assertEqual(
            intersect((0, 1), (3, 5)), 
            ())
                    
        self.assertEqual(
            intersect((1, 5), (6, 1)), 
            ((1, 1),))
        
        self.assertEqual(
            intersect((6, 1), (1, 5)), 
            ((1, 1),))
        
        self.assertEqual(
            intersect((38, 9), (7, 7)), 
            ((7, 7),))
        
        self.assertEqual(
            intersect((33, 1), (34, 34)), 
            ((33, 34),))
        
    def test_tesselate_with_noisy_points(self):
        # Test case with specific 3D points
        s = 15
        n = 20
        dn = 30
        sep = 6.4
        points1 = self.make_points_noise(22 - sep, 22, n, s + 10, s + 11, np.pi / 4.5)
        points2 = self.make_points_noise(31 - sep, 31, n + dn, s + 12, s + 13, 0)
        
        # Call closest_points() to and plot the results.
        s1, s2 = closest_points(points1, points2)
        #print(closest_points(points2, points1))
        
        PlotClosestPoints(
            points1=points1,
            points2=points2, 
            s1=s1, 
            s2=s2, 
            title=f'Noisy points (seed={s} n={n} dn={dn})')
        #MapClosestPoints(points1, points2, s1, s2, 'Noisy points Test')

        helper = _create_tesselator_helper(points1, 100, points2, 100 + n)
        
        PlotRanges(tess_helper=helper, 
                   title=f'Ranges Plot - Noisy points (seed={s} n={n} dn={dn})')
        
        PlotFixedRanges(tess_helper=helper, 
                   title=f'Fixed Ranges Plot - Noisy points (seed={s} n={n} dn={dn})')

        #self.assertEqual(closest_points_monotonic(points2, points1), expected_result)
        
    def test_tesselate_with_noisy_path(self):
        s = 15
        n = 20
        dn = 30
        sep = 6.4
        path = self.maker_path_noise(22 - sep, 22, n, s + 10, s + 11, np.pi / 4.5)
        
        mapped_poly = MappedPolygon(path, EMPTY_ATTRS.with_fn(32))
        
        path_offsetter = PathOffsetMaker(mapped_poly)
        
        points1 = path_offsetter.offset_polygon(5)
        points2 = path_offsetter.offset_polygon(-5)
        
                # Call closest_points() to and plot the results.
        s1, s2 = closest_points(points1, points2)
        #print(closest_points(points2, points1))
        
        PlotClosestPoints(
            points1=points1,
            points2=points2, 
            s1=s1, 
            s2=s2, 
            title=f'Noisy points (seed={s} n={n} dn={dn})')
        #MapClosestPoints(points1, points2, s1, s2, 'Noisy points Test')

        helper = _create_tesselator_helper(points1, 100, points2, 100 + len(points1))
        
        PlotRanges(tess_helper=helper, 
                   title=f'Ranges Plot - Noisy points (seed={s} n={n} dn={dn})')
        
        PlotFixedRanges(tess_helper=helper, 
                   title=f'Fixed Ranges Plot - Noisy points (seed={s} n={n} dn={dn})')
        
        
    def xtest_wrap_around_test(self):
        
        points1 = np.array([
            (0, 1), 
            (0, 1.1), 
            (0, 1.2), 
            (0, 1.3), 
            (2, 2),
            (2, 0),
            (0, 0.0), 
            (0, 0.7), 
            (0, 0.8), 
            (0, 0.9)
            ])
        
        points2 = np.array([
            (0.1, 1), 
            (0.7, 1.1), 
            (1.8, 1.8), 
            (1.8, 0.2), 
            (0.2, 0.2)
            ])
        
        points2 = np.roll(points2, -1, axis=0)
        
        
        # Call closest_points() to and plot the results.
        s1, s2 = closest_points(points1, points2)
        print(s1, s2)
        
        PlotClosestPoints(
            points1=points1, 
            points2=points2, 
            s1=s1, 
            s2=s2, 
            title=f'Wrap issue')
        
        helper = _create_tesselator_helper(points1, 100, points2, 200)
        PlotFixedRanges(tess_helper=helper, title='test_wrap_around_test')
        
        print(helper.tesselation())


    def test_find_nearest_points_indexes_larger(self):
        # Test case with specific 3D points
        n = 11
        r = 10
        points1 = self.make_points(n-5, 10, 0)
        points2 = self.make_points(n-0, 11, 3)

        #print(closest_points(points2, points1))
        #tesselate_between_paths(points1, 100, points2, 200)

        #self.assertEqual(closest_points_monotonic(points2, points1), expected_result)

def pause_on_close(timeout_seconds):
    start_time = time.time()
    is_timed_out = False
    while not IS_CLOSED and (not is_timed_out or IS_INTERACTIVE):
        manager = plt.get_current_fig_manager()
        if manager is not None:
            canvas = manager.canvas
            if canvas.figure.stale:
                # Update the screen as the canvas wasn't fully drawn yet.
                canvas.draw_idle()
            canvas.start_event_loop(0.1)
        is_timed_out = (time.time() - start_time >= timeout_seconds)
    return

if __name__ == '__main__':
    test = unittest.main(exit=False)
    pause_on_close(3)
    sys.exit(not test.result.wasSuccessful())
