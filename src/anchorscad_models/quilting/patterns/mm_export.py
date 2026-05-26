'''
Export quilt paths at true model size (mm) to SVG and PDF.
'''

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Union

import anchorscad as ad
import anchorscad.svg_renderer as svgr

PAGE_SIZES_MM = {
    'A3': (297.0, 420.0),
    'A4': (210.0, 297.0),
    'A5': (148.0, 210.0),
    'LETTER': (215.9, 279.4),
    'LEGAL': (215.9, 355.6),
}


def parse_page_size(spec: str) -> tuple[float, float]:
    '''Parse a page size name (A4) or WIDTHxHEIGHT mm (e.g. 210x297).'''
    key = spec.strip().upper().replace('-', '')
    if key in PAGE_SIZES_MM:
        return PAGE_SIZES_MM[key]
    if 'X' in key:
        width_s, height_s = key.split('X', 1)
        return float(width_s), float(height_s)
    raise ValueError(
        f'Unknown page size {spec!r}; use A4, A3, A5, LETTER, LEGAL, or WIDTHxHEIGHT')


def path_to_mm_svg(
        path: ad.Path,
        margin_mm: float = 5.0,
        stroke_mm: float = 0.3,
        include_constructions: bool = True,
        page_size_mm: tuple[float, float] | None = None) -> str:
    '''Build an SVG string with 1 user unit = 1 mm (model coordinates).'''
    renderer = svgr.SvgPathRenderer(
        path_id='pattern', all_segments=None, is_path_closed=False)
    path.svg_path_render(renderer)
    renderer.close()

    extents = path.extents(include_constructions=include_constructions)
    x0, y0 = float(extents[0][0]), float(extents[0][1])
    x1, y1 = float(extents[1][0]), float(extents[1][1])
    content_w = x1 - x0 + 2 * margin_mm
    content_h = y1 - y0 + 2 * margin_mm
    if page_size_mm is None:
        width_mm, height_mm = content_w, content_h
        page_offset_x = 0.0
        page_offset_y = 0.0
    else:
        width_mm, height_mm = page_size_mm
        page_offset_x = max(0.0, (width_mm - content_w) / 2)
        page_offset_y = max(0.0, (height_mm - content_h) / 2)
    tx = page_offset_x + margin_mm - x0
    ty = page_offset_y + margin_mm + y1

    path_elems: List[str] = []
    for path_segment in renderer.get_paths():
        path_elems.append(f'<path d="{path_segment.shape_str}"/>')
    for _seg_id, segment in renderer.get_segments().items():
        path_elems.append(f'<path d="{segment.path}"/>')

    return '\n'.join((
        '<?xml version="1.0" encoding="UTF-8"?>',
        (f'<svg xmlns="http://www.w3.org/2000/svg" '
         f'width="{width_mm:G}mm" height="{height_mm:G}mm" '
         f'viewBox="0 0 {width_mm:G} {height_mm:G}">'),
        (f'<style>path {{ fill: none; stroke: #000; '
         f'stroke-width: {stroke_mm:G}mm; }}</style>'),
        f'<g transform="translate({tx:G},{ty:G}) scale(1,-1)">',
        *path_elems,
        '</g>',
        '</svg>',
    ))


def write_mm_svg(
        path: ad.Path,
        filename: Union[str, Path],
        margin_mm: float = 5.0,
        stroke_mm: float = 0.3,
        include_constructions: bool = True,
        page_size_mm: tuple[float, float] | None = PAGE_SIZES_MM['A4'],
        encoding: str = 'utf-8') -> Path:
    '''Write an mm-accurate SVG file.'''
    out = Path(filename)
    out.write_text(
        path_to_mm_svg(
            path,
            margin_mm=margin_mm,
            stroke_mm=stroke_mm,
            include_constructions=include_constructions,
            page_size_mm=page_size_mm),
        encoding=encoding)
    return out


def svg_file_to_pdf(svg_path: Union[str, Path], pdf_path: Union[str, Path]) -> Path:
    '''Convert an SVG file to PDF (cairosvg, else rsvg-convert if available).'''
    svg_path = Path(svg_path)
    pdf_path = Path(pdf_path)
    try:
        import cairosvg
        cairosvg.svg2pdf(url=str(svg_path.resolve()), write_to=str(pdf_path))
        return pdf_path
    except ImportError:
        pass
    import shutil
    rsvg = shutil.which('rsvg-convert')
    if rsvg:
        subprocess.run(
            [rsvg, '-f', 'pdf', '-o', str(pdf_path), str(svg_path)],
            check=True)
        return pdf_path
    raise RuntimeError(
        'PDF export needs cairosvg: uv pip install cairosvg '
        '(or install rsvg-convert / librsvg)')


def write_mm_pdf(
        path: ad.Path,
        pdf_filename: Union[str, Path],
        margin_mm: float = 5.0,
        stroke_mm: float = 0.3,
        include_constructions: bool = True,
        page_size_mm: tuple[float, float] | None = PAGE_SIZES_MM['A4'],
        svg_filename: Union[str, Path, None] = None) -> Path:
    '''Write mm-accurate PDF (via intermediate SVG).'''
    pdf_path = Path(pdf_filename)
    if svg_filename is None:
        svg_filename = pdf_path.with_suffix('.svg')
    write_mm_svg(
        path,
        svg_filename,
        margin_mm=margin_mm,
        stroke_mm=stroke_mm,
        include_constructions=include_constructions,
        page_size_mm=page_size_mm)
    return svg_file_to_pdf(svg_filename, pdf_path)
