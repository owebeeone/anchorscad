'''
Quilt pattern utilities.
'''

import anchorscad as ad
import anchorscad.svg_renderer as svgr
from anchorscad_models.quilting.patterns.csq_renderer import CsqPathRenderer
from anchorscad_models.quilting.patterns.mm_export import (
    parse_page_size, write_mm_pdf, write_mm_svg)
import argparse as ap
from dataclasses import dataclass, field
from typing import List
import sys


def maker_argparser():
    '''Take options --svg, --csq, and --pdf'''
    
    argparser = ap.ArgumentParser()
    argparser.add_argument('--svg', action='store_true', help='Output as SVG')
    argparser.add_argument(
        '--nosvg', dest='svg', action='store_false', help='Don\'t output as SVG')
    argparser.set_defaults(svg=True)
    argparser.add_argument('--csq', action='store_true', help='Output as CSQ')
    argparser.add_argument(
        '--nocsq', dest='csq', action='store_false', help='Don\'t output as CSQ')
    argparser.set_defaults(csq=True)
    argparser.add_argument(
        '--pdf', action='store_true',
        help='Output mm-accurate SVG and PDF (test_mm.svg, test.pdf)')
    argparser.add_argument(
        '--nopdf', dest='pdf', action='store_false', help='Don\'t output PDF')
    argparser.set_defaults(pdf=False)
    argparser.add_argument(
        '--pdf-margin', type=float, default=5.0, metavar='MM',
        help='Margin around pattern in mm for PDF/SVG export (default: 5)')
    argparser.add_argument(
        '--pdf-stroke', type=float, default=0.3, metavar='MM',
        help='Line width in mm for PDF/SVG export (default: 0.3)')
    argparser.add_argument(
        '--pdf-page-size', default='A4', metavar='SIZE',
        help='Page size: A4 (default), A3, A5, LETTER, LEGAL, or WIDTHxHEIGHT mm')
    
    return argparser

@ad.datatree
class PatternRunner:
    '''
    A class for running a pattern.
    '''
    svgr_path: ad.Path = ad.dtfield(None, 'The path to run the pattern on.')
    svgr_fill_color: str = ad.dtfield('none', 'The fill colour for the SVG')
    path_id: str = ad.dtfield("default", 'The path ID for the SVG')
    svgr_node: ad.Node = ad.Node(
        svgr.SvgRenderer, {'path_id': 'path_id'}, prefix='svgr_', expose_all=True)
    args: ap.ArgumentParser = field(default_factory=maker_argparser, init=False)
    
    csq_node: ad.Node = ad.Node(
        CsqPathRenderer, {'path_id': 'path_id'}, prefix='csq_', expose_all=True)
    
    
    def run(self, argv: List[str] = None):
        '''
        Run the pattern.
        '''
        
        argp = self.args.parse_args(argv)
        
        if argp.svg:
            svg_renderer = self.svgr_node()
            svg_renderer.write('test.svg')
            
        if argp.csq:
            csq_renderer = self.csq_node()
            self.svgr_path.svg_path_render(csq_renderer)
            csq_renderer.write('test.csq')

        if argp.pdf:
            page_size_mm = parse_page_size(argp.pdf_page_size)
            write_mm_svg(
                self.svgr_path,
                'test_mm.svg',
                margin_mm=argp.pdf_margin,
                stroke_mm=argp.pdf_stroke,
                page_size_mm=page_size_mm)
            write_mm_pdf(
                self.svgr_path,
                'test.pdf',
                margin_mm=argp.pdf_margin,
                stroke_mm=argp.pdf_stroke,
                page_size_mm=page_size_mm,
                svg_filename='test_mm.svg')


def main(path: ad.Path, argv: List[str] = None):
    '''
    Run the pattern.
    '''
    runner = PatternRunner(path, svgr_is_path_closed=False)
    runner.run(sys.argv[1:] if argv is None else argv)
