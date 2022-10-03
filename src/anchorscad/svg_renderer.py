'''
Created on 26 Sept 2022

@author: gianni
'''

import numpy as np
import anchorscad.linear as l
import anchorscad.datatrees as dt


LIST_3_FLOAT_0 = l.list_of(l.strict_float, len_min_max=(3, 3), fill_to_min=0.0)


@dt.datatree
class SvgPathRenderer(object):
    '''Render visitor/builder for anchorscad.Path. Creates an SVG path string.'''
    last_position: np.array = None
    _builder: list = dt.dtfield(default=None, init=False, repr=False)
    _paths: list = dt.dtfield(default_factory=list, init=False)

    def _set_last_position(self, new_last_position):
        if self.last_position is None:
            self._builder = list()
        self.last_position = new_last_position

    def _finish_path(self):
        if self._builder:
            self._paths.append(' '.join(self._builder))
            self._builder = None

    def moveto(self, end_point, name):
        # Starting a new path means closing the current if any.
        self._finish_path()
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
    axis_width_px: float = 2
    axis_colour: str = '#1010103f'


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
    grad_line_colour: str = '#0000af'
    grad_multiples_log10: tuple = (0, LOG10_5, LOG10_25)
    grad_grid_attrs: tuple = (
        None,
        SvgAxisAttributes(1, '#7010500f'),
        SvgAxisAttributes(1.5, '#0070102f'))
    grad_axis_attr: SvgAxisAttributes = SvgAxisAttributes(1.7, '#0000ffff')
    GRAD_NAMES = ('graduation_small', 'graduation_medium', 'graduation_large')

    def render(self):
        '''Returns a tuple of lists of strings. The first is placed before the rendered shape
        and the second after.'''
        grad_countsA = np.floor((self.grad_bot_right_px.A2
                                 - self.grad_top_left_px.A2) / self.approx_grad_spacing_px)

        grad_sizes = (self.grad_bot_right_ms.A2
                      - self.grad_top_left_ms.A2) / grad_countsA

        grad_size, elems, divider = find_grad_multiple(
            grad_sizes, self.grad_multiples_log10)

        rear_grads = []
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
                f'<text text-anchor="end" font-size="{sc:G}em" transform='
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

                gw = w[grad_size_idx]
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
                        f'<path d="M {sp[0]:G} {sp[1]:G} L {ep[0]:G} {ep[1]:G}" stroke="{alc}" stroke-width="{aw}"/>')

                if abs(v) < GRAD_EPSILON and self.grad_axis_attr:
                    aw = self.grad_axis_attr.axis_width_px / self.img_scale
                    alc = self.grad_axis_attr.axis_colour
                    sp[od] = end_1
                    rear_grads.append(
                        f'<path d="M {sp[0]:G} {sp[1]:G} L {ep[0]:G} {ep[1]:G}" stroke="{alc}" stroke-width="{aw}"/>')

                current += 1

        return rear_grads, grads

    def get_grad_css(self):
        '''Returns a string containing the CSS for the graduations.'''
        styles = tuple(f'''.{self.GRAD_NAMES[i]} {{
            stroke: {self.grad_line_colour};
            stroke-width: {self.grad_width_px[i] / self.img_scale};
            fill: none;
        }}''' for i in range(3))
        return styles


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
        return (f'<path d="M {l} {t} L {r} {t} L {r} {b} L {l} {b} Z" stroke="{lc}" '
                f'stroke-width="{w}" fill="{fc}"/>',)


@dt.datatree
class SvgRenderer(object):
    '''Renders Anchorscad Path objects to SVG.'''
    path: object
    img_margin_size: float = 65.0
    grad_margin_size: float = 50.0
    target_image_size: tuple = (600.0, 600.0)
    fill_color: str = '#bfbf10'
    stroke_width_px: float = 1.5
    stroke_colour: str = 'black'

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
        self_default=lambda s: s.path_render_node())
    grad_render_node: dt.Node = dt.dtfield(
        dt.Node(SvgGraduationRenderer), init=False)
    frame_render_node: dt.Node = dt.dtfield(
        dt.Node(SvgFrameRenderer, prefix='frame_'), init=False)

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
        styles = renderer.get_grad_css()
        return (styles, *renderer.render())

    def get_frame(self):
        renderer = self.frame_render_node()
        return renderer.render(
            self.grad_top_left_ms, self.grad_bot_right_ms, self.img_scale)

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
        sw = self.stroke_width_px / self.img_scale
        fc = self.fill_color
        return tuple(
            f'<path d="{p}" stroke="{sc}" stroke-width="{sw:G}" fill="{fc}"/>'
            for p in ps)

    def get_svg_styles(self):
        return ("<style>", "</style>")

    def to_svg_string(self):
        '''Returns the SVG image as a string.'''
        hdr = self.get_svg_header()
        styles = self.get_svg_styles()
        g = self.get_svg_transform()
        p = self.get_svg_path()
        gstyles, rgs, gs = self.get_grads()
        seq = (hdr[0], *styles[:-1], *gstyles, styles[-1], g[0], *self.get_frame(),
               *rgs, *p, *gs, g[1], hdr[1], '')
        return '\n'.join(seq)

    def write(self, filename, encoding="utf-8"):
        '''Writes the svg xml to a file.
        Args:
            filename: The filename to create.
        '''
        with open(filename, 'w', encoding=encoding) as fp:
            return fp.write(self.to_svg_string())
