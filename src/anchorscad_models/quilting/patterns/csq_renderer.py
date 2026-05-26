'''


@uthor: 	gianni
'''

from typing import List, Tuple
import datatrees as dt
import numpy as np
from anchorscad.svg_renderer import Segments, Segment


def _cubic_bezier_for_arc(
        start: np.ndarray,
        end: np.ndarray,
        centre: np.ndarray,
        sweep_angle: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''Cubic Bezier control points approximating a circular arc.'''
    v0 = start - centre
    v1 = end - centre
    k = (4.0 / 3.0) * np.tan(sweep_angle / 4.0)
    cp1 = start + k * np.array([-v0[1], v0[0]])
    cp2 = end - k * np.array([-v1[1], v1[0]])
    return cp1, cp2, end


def _arc_spline_segments(
        start: np.ndarray,
        end: np.ndarray,
        centre: np.ndarray,
        sweep_angle: float,
        max_sweep: float = np.pi / 2) -> List[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    '''Split a circular arc into cubic Bezier segments for CSQ export.'''
    v0 = start - centre
    radius = np.linalg.norm(v0)
    start_angle = np.arctan2(v0[1], v0[0])
    segment_count = max(1, int(np.ceil(abs(sweep_angle) / max_sweep)))
    sub_sweep = sweep_angle / segment_count
    segments = []
    current = start
    for i in range(segment_count):
        if i == segment_count - 1:
            sub_end = end
            sub_sweep_angle = sweep_angle - sub_sweep * (segment_count - 1)
        else:
            angle = start_angle + (i + 1) * sub_sweep
            sub_end = centre + radius * np.array([np.cos(angle), np.sin(angle)])
            sub_sweep_angle = sub_sweep
        segments.append(
            _cubic_bezier_for_arc(current, sub_end, centre, sub_sweep_angle))
        current = sub_end
    return segments


@dt.datatree
class _CsqPathRendererWith:
    path_renderer: 'CsqPathRenderer'=dt.dtfield(repr=False)
    prev_last_position: np.array=dt.dtfield(None, init=False)
    
    _builder: List[str] = dt.dtfield(default=None, init=False, repr=False)
    
    def __enter__(self) -> 'CsqPathRenderer':
        self.prev_last_position = self.path_renderer.last_position
        
        self._builder = self.path_renderer._builder
        self.path_renderer._builder = None
        
        return self.path_renderer
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.path_renderer.finish()
        self.path_renderer._builder = self._builder
        self.path_renderer.last_position = self.prev_last_position
        
        return None

@dt.datatree
class CsqPathRenderer(object):
    '''Render visitor/builder for anchorscad.Path. Creates an CSQ path string.'''
    last_position: np.array = None
    is_path_closed: bool = True
    path_id: str | None = None
    _builder: list = dt.dtfield(default=None, init=False, repr=False)
    _paths: list = dt.dtfield(default_factory=list, init=False)
    _segs: list = dt.dtfield(default_factory=Segments, init=False)

    def _set_last_position(self, new_last_position):
        if self._builder is None:
            self._builder = list()
        if self.last_position is None:
            self._builder = ['#CSQLI']
            old_pos = (0, 0)
            csq_path = ''
        else:
            old_pos = self.last_position
            csq_path = f'{self.last_position[0]:G},{self.last_position[1]:G},0'
        self.last_position = new_last_position
        return csq_path, old_pos

    def _finish_path(self):
        if self._builder:
            self._paths.append('\n'.join(self._builder))
            #self._builder = None

    def moveto(self, end_point, name, trace=None):
        # Starting a new path means closing the current if any.
        self._finish_path()
        self._set_last_position(end_point)
        svg_path = f'{end_point[0]:G},{end_point[1]:G},0'
        self._builder.append(svg_path)
        seg = Segment(path_id=self.path_id, name=name, trace=trace, shape_type='moveto',
                      path=svg_path, points=(end_point,))
        self._segs.append(seg)

    def lineto(self, end_point, name, trace=None):
        last_path, last_pos = self._set_last_position(end_point)
        self._builder.append(f'{end_point[0]:G},{end_point[1]:G},1')
        seg = Segment(path_id=self.path_id, name=name, trace=trace, shape_type='lineto',
                      path=last_path + self._builder[-1], points=(last_pos, end_point,))
        self._segs.append(seg)

    def arcto1(self, radius, sweep_angle, sweep_flag, end_point, centre, name, trace=None):
        last_path, last_pos = self._set_last_position(end_point)
        start = np.array(last_pos, dtype=float)
        end = np.array(end_point, dtype=float)
        centre = np.array(centre, dtype=float)
        spline_parts = []
        for cp1, cp2, sub_end in _arc_spline_segments(start, end, centre, sweep_angle):
            for point in (cp1, cp2, sub_end):
                self._builder.append(f'{point[0]:G},{point[1]:G},3')
                spline_parts.append(self._builder[-1])
        seg = Segment(
            path_id=self.path_id,
            name=name,
            trace=trace,
            shape_type='arcto1',
            path=last_path + ','.join(spline_parts),
            sweep_angle=sweep_angle,
            sweep_flag=int(sweep_flag),
            points=(last_pos, end_point, centre))
        self._segs.append(seg)

    def splineto(self, points, name, trace=None):
        last_path, last_pos = self._set_last_position(points[2])
        for p in points:
            self._builder.append(f'{p[0]:G},{p[1]:G},3')
        points = (last_pos, points[0], points[1], points[2])
        seg = Segment(path_id=self.path_id, name=name, trace=trace, shape_type='splineto',
                      path=last_path + self._builder[-1], points=points)
        self._segs.append(seg)

    def close(self):
        '''Closes the path by creating a line from the last added point to the
        previous moveto() position.'''
        pass

    def finish(self):
        self._finish_path()
        self.last_position = None

    def get_paths(self):
        self.finish()
        return self._paths

    def get_segments(self):
        return self._segs

    def construction(self, css_clazz='construction', shape_css_class='construction_shape'):
        return _CsqPathRendererWith(
            path_renderer=self)

    def write(self, filename, encoding="utf-8"):
        '''Writes the csq data to a file.
        Args:
            filename: The filename to create.
        '''
        with open(filename, 'w', encoding=encoding) as fp:
            paths = self.get_paths()
            return fp.write('\n\n'.join(paths) + '\n')
