'''
Created on 30 Apr 2022

@author: gianni
'''

import anchorscad as ad
import numpy as np


class InvalidNumberOfSides(Exception):
    '''Number of sides parameter is invalid.'''


def regular_polygon(nsides: int=3, r: float=1.0, ellipse_radius: tuple=None):
    '''Returns an anchorscad.Path containing a N sided regular polygon or
    points on a ellipse if ellipse_radius tuple (xr, yr) is provided.
    Args:
      nsides: Number of sides of regular prism.
      r: Prism edges lie on circle with radius r.
      ellipse_radius: If provided, overrides r and corresponds to ellipse
          (x, y) radius.
    '''
    if nsides <= 2:
        raise InvalidNumberOfSides(f'Needs more than 2 sides, provided={nsides}')
    
    if ellipse_radius:
        xr, yr = ellipse_radius
    else:
        xr = yr = r
    
    angle = 2 * np.pi / nsides
    builder = ad.PathBuilder().move((0, 0), name='centre', direction=(-1, 0))
    builder.line((-xr, 0), 'radial')
    for i in range(1, nsides + 1):
        pos = (-xr * np.cos(angle * i), yr * np.sin(angle * i))
        builder.line(pos, ('side', i - 1))

    return builder.build()


@ad.shape()
@ad.datatree
class RegularPrism(ad.CompositeShape):
    '''
    A regular N sided prism.
    '''
    nsides: int=ad.dtfield(3, 'Number of sides of regular prism')
    r: float=ad.dtfield(1.0, 'Prism edges lie on circle with radius r.')
    ellipse_radius: tuple=ad.dtfield(
        None, 'Prism edges lie on ellipse with (xradius, yradius). '
              'If provided overrides parameter r')
    polygon_node: ad.Node=ad.dtfield(ad.Node(regular_polygon), init=False)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.polygon_node())
    extrude_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.LinearExtrude), init=False)
    
    EXAMPLE_SHAPE_ARGS=ad.args(nsides=5, ellipse_radius=(40, 20), h=20)
    EXAMPLE_ANCHORS=(ad.surface_args('base'),
                     ad.surface_args('top'),
                     ad.surface_args('centre'),
                     ad.surface_args('side', 0, rh=0.5),
                     ad.surface_args('side', 4, rh=0.5),)
    
    EXAMPLES_EXTENDED={
        'example2': ad.ExampleParams(
            shape_args=ad.args(
                nsides=5, 
                ellipse_radius=(30, 25),
                h=50,
                ),
            anchors=(
                ad.surface_args('base'),
                ad.surface_args('top'),
                ad.surface_args('side', 0, rh=0.5),
                ad.surface_args('side', 4, rh=0.5),
                )),
        'example3': ad.ExampleParams(
            shape_args=ad.args(
                nsides=32, 
                ellipse_radius=(30, 30),
                h=50,
                ),
            anchors=(
                ad.surface_args('base'),
                ad.surface_args('top'),
                ad.surface_args('side', 0, rh=0.5),
                ad.surface_args('side', 2, rh=0.5),
                )),
        }

    def build(self) -> ad.Maker:
        return self.extrude_node().solid('prism').at('centre', post=ad.ROTX_270)

    @ad.anchor('Base of prism')
    def base(self, h=0, rh=None):
        if rh:
            h = h + rh * self.h
        transform = ad.ROTX_180
        if not h:
            return transform
        return ad.tranZ(h) * transform
    
    @ad.anchor('centre of prism.')
    def centre(self, h=0, rh=0.5):
        return self.base(h=h, rh=rh)
    
    @ad.anchor('Top of prism')
    def top(self, h=0, rh=None):
        if rh:
            h = h + rh * self.h
        return ad.tranZ(self.h - h)
    
    @ad.anchor('Side of prism')
    def side(self, n, t=0.5, h=0, rh=0):
        if rh:
            h = h + rh * self.h
        return self.at(('side', n), t) * ad.ROTY_180 * ad.tranY(h)


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
