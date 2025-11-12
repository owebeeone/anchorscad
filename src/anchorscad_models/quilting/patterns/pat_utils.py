'''
Quilt pattern utilities.
'''

import anchorscad as ad
import anchorscad.svg_renderer as svgr
from anchorscad_models.quilting.patterns.csq_renderer import CsqPathRenderer
import argparse as ap
from dataclasses import dataclass, field
from typing import List
import sys


def maker_argparser():
    '''Take options --svg and --csq'''
    
    argparser = ap.ArgumentParser()
    argparser.add_argument('--svg', action='store_true', help='Output as SVG')
    argparser.add_argument(
        '--nosvg', dest='svg', action='store_false', help='Don\'t output as SVG')
    argparser.set_defaults(svg=True)
    argparser.add_argument('--csq', action='store_true', help='Output as CSQ')
    argparser.add_argument(
        '--nocsq', dest='csq', action='store_false', help='Don\'t output as CSQ')
    argparser.set_defaults(csq=True)
    
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
        
        

def main(path: ad.Path, argv: List[str] = None):
    '''
    Run the pattern.
    '''
    runner = PatternRunner(path, svgr_is_path_closed=False)
    runner.run(sys.argv[1:] if argv is None else argv)
