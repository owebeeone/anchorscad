'''


@uthor: 	gianni
'''

from typing import List
import datatrees as dt
import numpy as np
from anchorscad.svg_renderer import Segments, Segment


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
        assert False, 'Not implemented'
        # last_path, last_pos = self._set_last_position(end_point)
        # sweep_angle=abs(sweep_angle)
        # large_arc = int(abs(sweep_angle) > np.pi)
        # self._builder.append(
        #     f'A {radius:G} {radius:G} 0 {large_arc:d} {sweep_flag:d} '
        #     f'{end_point[0]:G} {end_point[1]:G}')
        # seg = Segment(name=name, trace=trace, shape_type='arcto1',
        #               path=last_path + self._builder[-1], points=(last_pos, end_point))
        # self._segs.append(seg)

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
            str = '\n'.join(self._builder) + '\n'
            return fp.write(str)
