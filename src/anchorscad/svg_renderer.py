'''
Created on 26 Sept 2022

@author: gianni
'''

from dataclasses import dataclass, field
import numpy as np
import anchorscad.linear as l


@dataclass
class SvgPathRenderer(object):
    last_position: np.array=None
    _builder: list=field(default=None, init=False, repr=False)
    _paths: list=field(default_factory=list, init=False)
    
    def _set_last_position(self, new_last_position):
        if self.last_position is None:
            self._builder = list()
        self.last_position = new_last_position
                
    def _finish_path(self):
        if self._builder:
            self._paths.append(' '.join(self._builder))
            self._builder = None
    
    def moveto(self, end_point, name):
        self._finish_path()  # Starting a new path means closing the current if any.
        self._set_last_position(end_point)
        self._builder.append(f'M {end_point[0]:G} {end_point[1]:G}')
    
    def lineto(self, end_point, name):
        self._set_last_position(end_point)
        self._builder.append(f'L {end_point[0]:G} {end_point[1]:G}')
        pass
    
    def arcto1(self, radius, sweep_angle, sweep_flag, end_point, name):
        self._set_last_position(end_point)
        large_arc = int(sweep_angle > 180)
        self._builder.append(
            f'A {radius:G} {radius:G} 0 {large_arc:d} {sweep_flag:d} '
            f'{end_point[0]:G} {end_point[1]:G}')
    
    def splineto(self, points, name):
        self._set_last_position(points[2])
        self._builder.append(
            f'C ' + ' '.join(f'{p[0]:G} {p[1]:G}' for p in points))
        
    def close(self):
        '''Closes the path by creating a line from the last added point to the
        previous moveto() position.'''
        self._builder.append('Z')
        self._finish_path()
        self.last_position = None
    
    def finish(self):
        self._finish_path()
        self.last_position = None
        
    def get_paths(self):
        self.finish()
        return self._paths


@dataclass
class SvgRenderer(object):
    '''Renders Anchorscad Path objects to SVG.'''
    path: object
    margin_size: float=100.0
    target_image_size: tuple=(600.0, 600.0)
    fill_color: str='#bfbf10'
    stroke_width: float=0.2
    stroke_colour: str='black'
    path_render: SvgPathRenderer=field(default_factory=SvgPathRenderer)
    
    def __post_init__(self):
        self.path.svg_path_render(self.path_render)
        self.path_render.close()
        self.model_transform = self._get_optimal_transform()
    
    def _get_optimal_transform(self):
        '''Find a transform that places the '''
        extents = self.path.extents()
        size = extents[1] - extents[0]
        target_size = np.array(self.target_image_size)
        target_size3d = np.append(target_size, [[0]])
        img_size = target_size - self.margin_size
        scale = img_size / size
        min_scale = np.min(scale)
        scale_vec = (min_scale, min_scale, 1)
        centre = np.append((extents[1] + extents[0]) / -2.0, [[0]])
        return l.translate(target_size3d / 2.0) * l.scale(scale_vec) * l.translate(centre)
    
    def get_svg_header(self):
        w = self.target_image_size[0]
        h = self.target_image_size[1]
        return (
            f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">',
            '</svg>')
        
    def get_svg_transform(self):
        m = self.model_transform.L
        return ((f'<g transform="matrix({m[0][0]:G},{m[1][0]:G},{m[0][1]:G},'
                 + f'{m[1][1]:G},{m[0][3]:G},{m[1][3]:G})">'),
                 '</g>')
        
    def get_svg_path(self):
        ps = self.path_render.get_paths()
        sc = self.stroke_colour
        sw = self.stroke_width
        fc = self.fill_color
        return tuple(
            f'<path d="{p}" stroke="{sc}" stroke-width="{sw:G}" fill="{fc}"/>'
            for p in ps)
        
    def to_svg_string(self):
        '''Returns the SVG image as a string.'''
        hdr = self.get_svg_header()
        g = self.get_svg_transform()
        p = self.get_svg_path()
        seq = (hdr[0], g[0], *p, g[1], hdr[1], '')
        return '\n'.join(seq)

