'''
Created on 26 Sept 2022

@author: gianni
'''

import numpy as np
import anchorscad.linear as l
import anchorscad.datatrees as dt
from dataclasses_json import dataclass_json, config
from dataclasses import dataclass
import os
import sys
from functools import lru_cache


LIST_3_FLOAT_0 = l.list_of(l.strict_float, len_min_max=(3, 3), fill_to_min=0.0)

@lru_cache(maxsize=None)  # Cache the normalized paths to avoid recalculating
def normalize_path(abs_path):
    # Try to make the path relative to the Python module path (sys.path)
    for path in sys.path:
        if abs_path.startswith(path):
            return os.path.relpath(abs_path, path).replace('\\', '/')

    # If not relative to any Python module path, make it relative to the current working directory
    return os.path.relpath(abs_path, os.getcwd()).replace('\\', '/')


def get_path_and_line_number(trace):
    return normalize_path(trace.filename), trace.lineno


@dataclass_json
@dt.datatree(provide_override_field=False)
class Segment(object):
    path_id: str
    name: object
    trace: object = dt.dtfield(
        metadata=config(encoder=get_path_and_line_number))
    shape_type: str
    path: str
    points: tuple
    id: str = dt.dtfield(self_default=lambda s: s.next_id())

    curr_idx = 0  # Ad ID generator.

    @classmethod
    def next_id(cls):
        cls.curr_idx += 1
        return f'seg_id{cls.curr_idx}'


@dataclass_json
@dt.datatree(provide_override_field=False)
class Segments(object):
    segdict: dict = dt.dtfield(default_factory=dict)

    def append(self, seg):
        self.segdict[seg.id] = seg

    def items(self):
        return self.segdict.items()


@dt.datatree(provide_override_field=False)
class SvgPathRenderer(object):
    '''Render visitor/builder for anchorscad.Path. Creates an SVG path string.'''
    path_id: str
    all_segments: Segments
    last_position: np.array = None
    is_path_closed: bool = True
    _builder: list = dt.dtfield(default=None, init=False, repr=False)
    _paths: list = dt.dtfield(default_factory=list, init=False)
    _segs: Segments = dt.dtfield(default_factory=Segments, init=False)
    _seg_node: dt.Node = dt.Node(Segment, 'path_id')

    def _set_last_position(self, new_last_position):
        if self.last_position is None:
            self._builder = list()
            old_pos = (0, 0)
            svg_path = ''
        else:
            old_pos = self.last_position
            svg_path = f'M {self.last_position[0]:G} {self.last_position[1]:G} '
        self.last_position = new_last_position
        return svg_path, old_pos

    def _finish_path(self):
        if self._builder:
            self._paths.append(' '.join(self._builder))
            #self._builder = None
            
    def _add_seg(self, seg):
        self._segs.append(seg)
        if self.all_segments:
            self.all_segments.append(seg)

    def moveto(self, end_point, name, trace=None):
        # Starting a new path means closing the current if any.
        self._finish_path()
        self._set_last_position(end_point)
        svg_path = f'M {end_point[0]:G} {end_point[1]:G}'
        self._builder.append(svg_path)
        seg = self._seg_node(name=name, trace=trace, shape_type='moveto',
                             path=svg_path, points=(end_point,))
        self._add_seg(seg)

    def lineto(self, end_point, name, trace=None):
        last_path, last_pos = self._set_last_position(end_point)
        self._builder.append(f'L {end_point[0]:G} {end_point[1]:G}')
        seg = self._seg_node(name=name, trace=trace, shape_type='lineto',
                      path=last_path + self._builder[-1], points=(last_pos, end_point,))
        self._add_seg(seg)

    def arcto1(self, radius, sweep_angle, sweep_flag, end_point, centre, name, trace=None):
        last_path, last_pos = self._set_last_position(end_point)
        sweep_angle=abs(sweep_angle)
        large_arc = int(abs(sweep_angle) > np.pi)
        self._builder.append(
            f'A {radius:G} {radius:G} 0 {large_arc:d} {sweep_flag:d} '
            f'{end_point[0]:G} {end_point[1]:G}')
        seg = self._seg_node(name=name, trace=trace, shape_type='arcto1',
                path=last_path + self._builder[-1], points=(last_pos, end_point, centre))
        self._add_seg(seg)

    def splineto(self, points, name, trace=None):
        last_path, last_pos = self._set_last_position(points[2])
        self._builder.append(
            'C ' + ' '.join(f'{p[0]:G} {p[1]:G}' for p in points))
        points = (last_pos, points[0], points[1], points[2])
        seg = self._seg_node(name=name, trace=trace, shape_type='splineto',
                      path=last_path + self._builder[-1], points=points)
        self._add_seg(seg)
        
    def qsplineto(self, points, name, trace=None):
        last_path, last_pos = self._set_last_position(points[1])
        self._builder.append(
            'Q ' + ' '.join(f'{p[0]:G} {p[1]:G}' for p in points))
        points = (last_pos, points[0], points[1])
        seg = self._seg_node(name=name, trace=trace, shape_type='qsplineto',
                      path=last_path + self._builder[-1], points=points)
        self._add_seg(seg)

    def close(self):
        '''Closes the path by creating a line from the last added point to the
        previous moveto() position.'''
        if self.is_path_closed:
            self._builder.append('Z')
        self._finish_path()
        self.last_position = None

    def finish(self):
        self._finish_path()
        self.last_position = None

    def get_paths(self):
        self.finish()
        return self._paths

    def get_segments(self):
        return self._segs


LOG10_5 = np.log10(0.5)
LOG10_25 = np.log10(0.25)
GRAD_EPSILON = 0.001


def find_grad_multiple(target_size: np.array, allowed_multiples_log10):
    '''Find a size, model space for the graduations on the measurement bar
    on the SVG model.

    Returns the graduation size in model space to use for all axes and the number
    of graduations between major entities.

    Args:
      target_size: The minimum size in model space of graduations.
      allowed_multiples_log10: The allowed multiples (logs of numbers between 0.1 and 1)
    '''
    targets_log10 = np.log10(abs(target_size))
    targets_ciel_log10 = np.ceil(targets_log10)
    rounded = np.round(targets_log10)
    target_10 = np.ceil(
        np.where(np.abs(rounded - targets_log10) < GRAD_EPSILON,
                 rounded, targets_ciel_log10))
    selected = target_10
    for am in sorted(allowed_multiples_log10, reverse=True):
        possible = (target_10 + am)
        selected = np.where(possible >= (
            targets_log10 - GRAD_EPSILON / 2), possible, selected)

    grad_size = np.max(selected)
    grid_res, divider = ((10.0, np.power(10.0, grad_size + 1))
                         if np.abs(np.round(grad_size) - grad_size) < GRAD_EPSILON
                         else (np.power(10.0, (np.ceil(grad_size) - grad_size)),
                               np.power(10.0, np.ceil(grad_size))))

    return np.power(10.0, grad_size), np.round(grid_res), divider


@dt.datatree(frozen=True)
class SvgAxisAttributes(object):
    '''Attributes for axes being rendered.'''
    css_class_name: str = None
    axis_width_px: float = 2
    axis_colour: str = '#1010103f'

    def get_style(self, scale, style_prefix):
        return f'''{style_prefix}.{self.css_class_name} {{
            stroke: {self.axis_colour};
            stroke-width: {self.axis_width_px / scale};
            }}'''


@dt.datatree
class SvgGraduationRenderer(object):
    '''Renders graduations/ticks and grids.
    '''
    img_scale: float = dt.dtfield(None)
    grad_top_left_px: l.GVector = dt.dtfield(None)
    grad_bot_right_px: l.GVector = dt.dtfield(None)
    grad_top_left_ms: l.GVector = dt.dtfield(None)
    grad_bot_right_ms: l.GVector = dt.dtfield(None)
    approx_grad_spacing_px: int = 10
    grad_width_px: float = (1.0, 1.5, 1.7)
    grad_lengths_px: float = (3, 5, 10)
    grad_text_offset_px: tuple = (5, 5)
    grad_text_scale: float = 1
    grad_text_colour: str = '#101010'
    grad_line_colour: str = '#0000af'
    grad_multiples_log10: tuple = (0, LOG10_5, LOG10_25)
    grad_grid_attrs: tuple = (
        None,
        SvgAxisAttributes('grid_fives', 1, '#7010500f'),
        SvgAxisAttributes('grid_tens', 1.5, '#0070102f'))
    grad_axis_attr: SvgAxisAttributes = SvgAxisAttributes(
        'grid_axes', 1.7, '#0000ffff')
    GRAD_NAMES = ('graduation_small', 'graduation_medium', 'graduation_large')
    GRID_NAMES = ('grid_tens', 'grid_fives')

    def render(self):
        '''Returns a tuple of lists of strings. The first is placed before the rendered shape
        and the second after.'''
        grad_countsA = np.floor((self.grad_bot_right_px.A2
                                 - self.grad_top_left_px.A2) / self.approx_grad_spacing_px)

        grad_sizes = (self.grad_bot_right_ms.A2
                      - self.grad_top_left_ms.A2) / grad_countsA

        grad_size, elems, divider = find_grad_multiple(
            grad_sizes, self.grad_multiples_log10)

        grid_axes = []
        grads = []
        lc = self.grad_line_colour
        w = np.array(self.grad_width_px) / self.img_scale
        l = np.array(self.grad_lengths_px) / self.img_scale
        gw = w[0]
        sp = [0.] * 2
        ep = [0.] * 2
        st = [0.] * 2
        v = 0.0
        sc = self.grad_text_scale / self.img_scale
        txt_offs = np.array(self.grad_text_offset_px) / self.img_scale
        gclass = self.GRAD_NAMES[0]

        def add_grad(grads):
            grads.append(
                f'<path d="M {sp[0]:G} {sp[1]:G} L {ep[0]:G} {ep[1]:G}" class="{gclass}"/>')

        def add_text(grads):
            grads.append(
                '<text text-anchor="end" transform='
                + f'"translate({st[0]:G} {st[1]:G}) rotate({angle}) scale(1, -1)">{v:G}</text>')

        for d, od, angle, sign in ((0, 1, 270, -1), (1, 0, 0, 1)):
            current = np.ceil(self.grad_top_left_ms[d] / grad_size)
            end = np.round(0.5 + self.grad_bot_right_ms[d] / grad_size)

            if current >= end:
                current, end = end, current

            while current < end:

                v = current * grad_size
                # Make -0 be 0.
                v = abs(v) if abs(v) < GRAD_EPSILON else v
                grad_size_idx = 0
                if np.modf(abs(v) / divider + GRAD_EPSILON / 10)[0] < 2 * GRAD_EPSILON:
                    grad_size_idx = 2
                elif np.modf(abs(v) / (divider / 2) + GRAD_EPSILON / 10)[0] < 2 * GRAD_EPSILON:
                    grad_size_idx = 1

                gclass = self.GRAD_NAMES[grad_size_idx]

                sp[d] = v
                sp[od] = self.grad_top_left_ms[od]
                ep[d] = v
                end_1 = ep[od] = sp[od] + sign * l[grad_size_idx]

                st[d] = sp[d] - txt_offs[0]
                st[od] = sp[od] - sign * txt_offs[1]

                grad_attrs = self.grad_grid_attrs[grad_size_idx]

                add_grad(grads)
                if grad_size_idx == 2 or (grad_size_idx == 1 and elems > 3):
                    add_text(grads)

                sp[od] = self.grad_bot_right_ms[od]
                ep[od] = sp[od] - sign * l[grad_size_idx]
                add_grad(grads)

                if grad_attrs:
                    aw = grad_attrs.axis_width_px / self.img_scale
                    alc = grad_attrs.axis_colour
                    sp[od] = end_1
                    grads.append(
                        f'<path d="M {sp[0]:G} {sp[1]:G} L {ep[0]:G} {ep[1]:G}" class="{grad_attrs.css_class_name}"/>')

                if abs(v) < GRAD_EPSILON and self.grad_axis_attr:
                    aw = self.grad_axis_attr.axis_width_px / self.img_scale
                    alc = self.grad_axis_attr.axis_colour
                    sp[od] = end_1
                    grid_axes.append(
                        f'<path d="M {sp[0]:G} {sp[1]:G} L {ep[0]:G} {ep[1]:G}" class="{self.grad_axis_attr.css_class_name}"/>')

                current += 1

        return grid_axes, grads

    def get_styles(self, style_prefix):
        '''Returns a string containing the CSS for the graduations.'''
        grad_styles = tuple(f'''{style_prefix}.{self.GRAD_NAMES[i]} {{
            stroke: {self.grad_line_colour};
            stroke-width: {self.grad_width_px[i] / self.img_scale};
            fill: none;
        }}''' for i in range(3))

        grid_styles = tuple(self.grad_grid_attrs[i].get_style(
            self.img_scale, style_prefix) for i in range(3) if self.grad_grid_attrs[i])

        axis_styles = (self.grad_axis_attr.get_style(self.img_scale, style_prefix),)
        text_styles = (f'''{style_prefix}text {{
            fill: {self.grad_text_colour};
            font-size: {self.grad_text_scale / self.img_scale}em;
            }}''',)
        return grad_styles + grid_styles + axis_styles + text_styles


@dt.datatree
class SvgFrameRenderer(object):
    '''Renders a frame around the shape.'''
    width_px: int = 2
    line_colour: str = '#00003f'
    fill_colour: str = '#f7f7f7'

    def render(self, top_left, bot_right, scale):
        l = f'{top_left[0]:G}'
        t = f'{top_left[1]:G}'
        r = f'{bot_right[0]:G}'
        b = f'{bot_right[1]:G}'
        lc = self.line_colour
        fc = self.fill_colour
        w = self.width_px / scale
        return (f'<path d="M {l} {t} L {r} {t} L {r} {b} L {l} {b} Z" class="frame"/>',)

    def get_styles(self, scale, style_prefix):
        '''Returns a string containing the CSS for the frame.'''
        styles = (f'''{style_prefix}.frame {{
            stroke: {self.line_colour};
            stroke-width: {self.width_px / scale};
            fill: {self.fill_colour};
        }}''',)
        return styles


@dt.datatree
class SvgRenderer(object):
    '''Renders Anchorscad Path objects to SVG.'''
    path: object
    img_margin_size: float = 65.0
    grad_margin_size: float = 50.0
    target_image_size: tuple = (600.0, 600.0)
    fill_color: str = '#bfbf10'
    stroke_width_px: float = 1.5
    stroke_hover_width_px: float = 4.5
    stroke_colour: str = 'black'
    stroke_hover_colour: str = 'red'
    stroke_selected_colour: str = 'green'
    stroke_selected_width_px: float = 6.5
    stroke_metadata_colour: str = 'blue'
    stroke_metadata_width_px: float = 3.5
    stroke_metadata_dash_width_px: float = 10
    dot_metadata_colour: str = 'darkgreen'
    dot_metadata_radius_px: float = 6.5

    img_scale: float = dt.dtfield(init=False)
    model_transform: l.GMatrix = dt.dtfield(init=False)
    extents: np.array = dt.dtfield(init=False)

    margin_top_left_px: l.GVector = dt.dtfield(None, init=False)
    margin_bot_right_px: l.GVector = dt.dtfield(None, init=False)
    margin_top_left_ms: l.GVector = dt.dtfield(None, init=False)
    margin_bot_right_ms: l.GVector = dt.dtfield(None, init=False)

    grad_top_left_px: l.GVector = dt.dtfield(None, init=False)
    grad_bot_right_px: l.GVector = dt.dtfield(None, init=False)
    grad_top_left_ms: l.GVector = dt.dtfield(None, init=False)
    grad_bot_right_ms: l.GVector = dt.dtfield(None, init=False)

    path_render_node: dt.Node = dt.dtfield(
        dt.Node(SvgPathRenderer), init=False)
    path_render: SvgPathRenderer = dt.dtfield(
        self_default=lambda s: s.path_render_node(path_id=s.path_id, all_segments=s.all_segments))
    grad_render_node: dt.Node = dt.dtfield(
        dt.Node(SvgGraduationRenderer), init=False)
    frame_render_node: dt.Node = dt.dtfield(
        dt.Node(SvgFrameRenderer, prefix='frame_'), init=False)
    
    json_indent: int = 2
    path_id: str = None
    svg_class: str = None
    style_prefix: str = dt.dtfield(
        init=False,
        self_default=lambda s: f'#{s.path_id} > g > ' if s.path_id else '')
    all_segments: Segments = None

    def __post_init__(self):
        self.path.svg_path_render(self.path_render)
        self.path_render.close()
        self.model_transform = self._get_optimal_transform()
        inv_xform = self.model_transform.I
        self.margin_top_left_px = l.GVector(
            LIST_3_FLOAT_0([self.img_margin_size, ] * 2))
        self.margin_bot_right_px = l.GVector(LIST_3_FLOAT_0(
            self.target_image_size)) - self.margin_top_left_px
        self.margin_top_left_ms = inv_xform * self.margin_top_left_px
        self.margin_bot_right_ms = inv_xform * self.margin_bot_right_px

        self.grad_top_left_px = l.GVector(
            LIST_3_FLOAT_0([self.grad_margin_size, ] * 2))
        self.grad_bot_right_px = l.GVector(LIST_3_FLOAT_0(
            self.target_image_size)) - self.grad_top_left_px
        self.grad_top_left_ms = inv_xform * self.grad_top_left_px
        self.grad_bot_right_ms = inv_xform * self.grad_bot_right_px

    def _get_optimal_transform(self):
        '''Find a transform that places the path in the centre of the SVG image
        with the requested margins.'''
        extents = self.path.extents()
        self.extents = extents
        size = extents[1] - extents[0]
        target_size = np.array(self.target_image_size)
        target_size3d = np.append(target_size, [[0]])
        img_size = target_size - self.img_margin_size * 2
        scale_d2 = img_size / size
        img_scale = np.min(scale_d2)
        self.img_scale = img_scale
        scale_vec = (img_scale, -img_scale, 1)
        centre = np.append((extents[1] + extents[0]) / -2.0, [[0]])
        return l.translate(target_size3d / 2.0) * l.scale(scale_vec) * l.translate(centre)

    def get_grads(self):
        renderer = self.grad_render_node()
        styles = renderer.get_styles(self.style_prefix)
        return (styles, *renderer.render())

    def get_frame(self):
        renderer = self.frame_render_node()
        styles = renderer.get_styles(self.img_scale, self.style_prefix)
        return (styles, renderer.render(
            self.grad_top_left_ms, self.grad_bot_right_ms, self.img_scale))

    def get_svg_header(self):
        w = self.target_image_size[0]
        h = self.target_image_size[1]
        elems = (
            f'width="{w}"',
            f'height="{h}"',
            f'id="{self.path_id}"' if self.path_id else None,
            f'class="{self.svg_class}"' if self.svg_class else None,)
        elems_str = ' '.join(e for e in elems if e)
        return (
            f'<svg {elems_str} xmlns="http://www.w3.org/2000/svg">',
            '</svg>')

    def get_svg_transform(self):
        m = self.model_transform.L
        return ((f'<g transform="matrix({m[0][0]:G},{m[1][0]:G},{m[0][1]:G},'
                 + f'{m[1][1]:G},{m[0][3]:G},{m[1][3]:G})">'),
                '</g>')

    def get_svg_path(self):
        ps = self.path_render.get_paths()
        sc = self.stroke_colour
        sw = self.stroke_width_px / self.img_scale
        fc = self.fill_color
        paths = list(
            f'<path d="{p}" class="shape"/>'
            for p in ps)

        segments = []
        for seg in self.path_render.get_segments().items():
            segments.append(
                f'<path d="{seg[1].path}" id="{seg[1].id}" class="segment"/>')

        return (paths, segments)

    def get_svg_styles(self):
        shape_style = f'''{self.style_prefix}.shape {{
            stroke: {self.stroke_colour};
            stroke-width: {self.stroke_width_px / self.img_scale:G};
            fill: {self.fill_color};
        }}'''
        seg_styles = (f'''{self.style_prefix}.segment {{
            stroke: {self.stroke_colour};
            stroke-width: {self.stroke_width_px / self.img_scale:G};
            fill: none;
            pointer-events: stroke;
        }}''',
        f'''{self.style_prefix}.segment.selected,''',
        f'''{self.style_prefix}.segment.selected:hover {{
            stroke: {self.stroke_selected_colour};
            stroke-width: {self.stroke_selected_width_px / self.img_scale:G};
            fill: #0000;
            pointer-events: stroke;
        }}''',
        f'''{self.style_prefix}.segment:hover {{
            stroke: {self.stroke_hover_colour};
            stroke-width: {self.stroke_hover_width_px / self.img_scale:G};
            fill: #0000;
            pointer-events: stroke;
        }}''',
        f'''{self.style_prefix}.dot {{
            fill: {self.dot_metadata_colour};
            r: {self.dot_metadata_radius_px / self.img_scale:G};
        }}''',
        f'''{self.style_prefix}.control-line {{
            stroke: {self.stroke_metadata_colour};
            stroke-width: {self.stroke_metadata_width_px / self.img_scale:G};
            stroke-dasharray: {self.stroke_metadata_dash_width_px / self.img_scale:G};
        }}''')
        return ("<style>", shape_style, *seg_styles, "</style>")

    def to_svg_string(self):
        '''Returns the SVG image as a string.'''
        hdr = self.get_svg_header()
        styles = self.get_svg_styles()
        g = self.get_svg_transform()
        p, segs = self.get_svg_path()
        gstyles, rgs, gs = self.get_grads()
        fstyles, frame = self.get_frame()
        seq = (hdr[0], *styles[:-1], *gstyles, *fstyles, styles[-1], g[0], *frame,
               *rgs, *p, *gs, *segs, g[1], hdr[1], '')
        return '\n'.join(seq)

    def write(self, filename, encoding="utf-8"):
        '''Writes the svg xml to a file.
        Args:
            filename: The filename to create.
        '''
        with open(filename, 'w', encoding=encoding) as fp:
            return fp.write(self.to_svg_string())



@dataclass_json
@dataclass
class SvgMetadataEntry:
    id: str
    div_id: str
    path_id: str
    anchors: object
    

@dataclass_json
@dataclass
class SvgMetadataCollection:
    path_items: dict=dt.field(default_factory=dict)
    
    def insert(self, id, div_id, path_id, anchors):
        self.path_items[path_id] = SvgMetadataEntry(id, div_id, path_id, anchors)
    

HTML_TEMPLATE = '''\
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>{name}</title>
    <style type="text/css">
        body {{
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12px;
            margin: 0;
            padding: 0;
        }}
        .tooltip {{
            position: absolute;
            background-color: #ffffff;
            box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.5);
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12px;
            padding: 5px;
            border: 1px solid #ffffff;
            z-index: 100;
        }}
        #infoArea {{
            position: fixed;
            top: 10px; /* Adjust as needed */
            right: 10px; /* Adjust as needed */
            width: 50%; /* Set the width of the text area */
            height: 40px; /* Set the height of the text area */
            z-index: 1000; /* Ensure it floats above other elements */
            background-color: #fff;
            border: 1px solid #ccc;
            padding: 10px;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            resize: none; /* Optional: Disable resize if desired */
        }}
        #infoArea.hovering {{
            height: 30%;
        }}
        #infoArea.selected {{
            height: 50%;
        }}
        
    </style>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
    <script type="text/javascript">
    
        let image_metadata = {image_metadata};
        let segment_metadata = {segment_metadata};
        
        function deferrred() {{
            let JQ = $;  // Alias for jQuery.
            
            // Updates the text area with metadata information.
            function updateTextArea(content) {{
                JQ('#infoArea').val(content);
            }}
            
            function clearSelected(includeVisuals=true) {{
                $('.selected').removeClass('selected');
                if (includeVisuals) {{
                    $('.metadata-visuals').remove();
                }}
            }}
            
            function addDots(points, svgGroup) {{
                points.forEach(point => {{
                    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                    dot.setAttribute('cx', point[0]);
                    dot.setAttribute('cy', point[1]);
                    dot.classList.add('dot', 'metadata-visuals');
                    svgGroup.append(dot);
                }});
            }}
            
            function addControlLine(p1, p2, svgGroup) {{
                const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute('x1', p1[0]);
                line.setAttribute('y1', p1[1]);
                line.setAttribute('x2', p2[0]);
                line.setAttribute('y2', p2[1]);
                line.classList.add('control-line', 'metadata-visuals');
                svgGroup.append(line);
            }}
            
            function handleArc(segmentData, svgGroup) {{
                addDots(segmentData.points, svgGroup);
                addControlLine(segmentData.points[0], segmentData.points[2], svgGroup);
                addControlLine(segmentData.points[1], segmentData.points[2], svgGroup);
            }}

            function handleSpline(segmentData, svgGroup) {{
                addDots(segmentData.points, svgGroup);
                addControlLine(segmentData.points[0], segmentData.points[1], svgGroup);
                addControlLine(segmentData.points[2], segmentData.points[3], svgGroup);
            }}

            function handleLine(segmentData, svgGroup) {{
                addDots(segmentData.points, svgGroup);
            }}
            
            function handleQuadSpline(segmentData, svgGroup) {{
                addDots(segmentData.points, svgGroup);
                addControlLine(segmentData.points[0], segmentData.points[1], svgGroup);
                addControlLine(segmentData.points[1], segmentData.points[2], svgGroup);
            }}

            const SEGMENT_HANDLERS = {{
                'arcto1': handleArc,
                'splineto': handleSpline,
                'lineto': handleLine,
                'qsplineto': handleQuadSpline,
                // Add more shape types as needed
            }};
            
            function handleSegment(segmentData, svgGroup) {{
                const handler = SEGMENT_HANDLERS[segmentData.shape_type];
                
                if (handler) {{
                    handler(segmentData, svgGroup);
                }} else {{
                    console.error(`No handler found for shape_type: ${{segmentData.shape_type}}`);
                }}
            }}
            
            function getSvgGroup(pathId) {{
                return $(`#${{pathId}} > g`);
            }}
            
            var doclear = true;
            var timeSelected = 0;
            var lastEntered = null;
            
            // Run this function after the document has fully loaded
            JQ(document).ready(function() {{
                // Add event listeners to each segment using jQuery
                JQ('.segment').on('mouseenter', function() {{
                    // Get segment id and use it to fetch metadata from image_metadata
                    if (this === lastEntered) {{
                        return;
                    }}
                    $('#infoArea').addClass('selected').addClass('hovering');
                    clearSelected();
                    const segId = JQ(this).attr('id');
                    const segmentData = segment_metadata.segdict[segId];
                    handleSegment(segmentData, getSvgGroup(segmentData.path_id));
                    const pathId = segmentData.path_id;
                    const metadata = image_metadata.path_items[pathId]; // Assuming segment data from image_metadata map
                    const pathList = [];
                    metadata.anchors.anchor_paths.forEach(function(anchorPath) {{
                        pathList.push(``);
                        pathList.push(anchorPath.shape_path.join(', ') + ', ' + segmentData.name);
                    }});
                    const segmentInfo = `name: ${{segmentData.name}}\\n`
                            + `type: ${{segmentData.shape_type}}\\n`
                            + `Shape anchor paths:\\n${{pathList.join('\\n')}}`;
                    updateTextArea(segmentInfo);
                    doclear = true;
                }});

                    
                JQ('.segment').on('mouseleave', function() {{
                    if (doclear) {{
                        // Clear text area when mouse leaves the segment
                        updateTextArea('');
                        clearSelected();
                        lastEntered = null;
                    }}
                    $('#infoArea').removeClass('hovering');
                    const currentTime = Date.now();
                    const elapsed = currentTime - timeSelected;
                    if (elapsed > 1000) {{
                        doclear = true;
                    }}
                }});
                
                JQ('.segment').on('click', function() {{
                    // Persist the text area content when clicked.
                    doclear = false;
                    clearSelected(false);
                    timeSelected = Date.now();
                    $(this).addClass('selected');
                    $('#infoArea').addClass('selected').removeClass('hovering');
                }});
            }});
        }}
        document.addEventListener('DOMContentLoaded', deferrred);
    </script>
</head>
<body>
</body>
  <!-- Text area to display segment information -->
  <textarea 
        id="infoArea" 
        placeholder="Hover over a path segment to display information. Click to select."></textarea>

  {svg_divs}
</html>
'''

# Class to render a collection of paths to a single html page.
@dt.datatree
class HtmlRenderer:
    paths_dict: dict
    svg_renderer_node: dt.Node=dt.Node(SvgRenderer, exclude=('path',))
    metadata_collection: SvgMetadataCollection=dt.field(default_factory=SvgMetadataCollection)
    svg_divs: list=dt.field(default_factory=list)
    all_segments: Segments=dt.field(default_factory=Segments)
    
    def __post_init__(self):
        for i, (path, anchors) in enumerate(self.paths_dict.items()):
            path_id = f'path{i}'
            div_id = f'div{i}'
            self.metadata_collection.insert(i, div_id, path_id, anchors)
            self.svg_divs.append(self._create_div_from_path(div_id, path_id, path))
    
    def _create_div_from_path(self, div_id, path_id, path):
        '''Create a div containing the svg image for a path.'''
        svg_renderer = self.svg_renderer_node(
            path=path, svg_class='svg_path', path_id=path_id, all_segments=self.all_segments)
        
        svg_str = svg_renderer.to_svg_string()
        
        return f'''<div class="svg-path" id="{div_id}">
    <div class="svg">
        {'        '.join(svg_str.splitlines(True))}
    </div>\n</div>'''
    
    def create_html(self, name='AnchorScad Paths'):
        '''Create the html page.'''
        svg_divs = '\n'.join(self.svg_divs)
        image_metadata_json_src = self.metadata_collection.to_json(indent=self.json_indent)
        segment_metadata_json_src = self.all_segments.to_json(
            indent=self.json_indent)
        return HTML_TEMPLATE.format(
            name=name, 
            image_metadata=image_metadata_json_src, 
            segment_metadata=segment_metadata_json_src, 
            svg_divs=svg_divs)

    def write(self, filename, name='AnchorScad Paths', encoding="utf-8"):
        '''Writes the html page to a file.
        '''
        with open(filename, 'w', encoding=encoding) as fp:
            return fp.write(self.create_html(name))