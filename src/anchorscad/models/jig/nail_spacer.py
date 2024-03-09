'''
Created on 9-Mar-2024

@author: gianni

A spacer for making a row of nails along the edge of a board (for makking a loom).

The jib comes in left and right sides. The NailSpacerAssembly class generates a model
with both sides separated by a gap to make it easier to load into the slicer in a single file.
'''

import anchorscad as ad
from typing import List, Tuple

HOLE_FUDGE=0.2  # Hole size fudge factort to allow for printing tolerances.

@ad.datatree
class BlockPathBuilder:
    '''Builder for a Path for the main jig block.'''
    
    w: float=ad.dtfield(30 + HOLE_FUDGE, doc='Width of stock being nailed')
    mw: float=ad.dtfield(4, doc='Margin width')
    mh: float=ad.dtfield(4, doc='Margin height')
    mtaper: float=ad.dtfield(0.5, doc='Margin taper')
    m: float=ad.dtfield(5, doc='Margin')
    el: float=ad.dtfield(20, doc='Exposed nail length')
    
    def build(self) -> ad.Path:
        builder = (ad.PathBuilder()
                .move((0, 0))
                .line((-self.w / 2, 0), 'left-base')
                .line((-self.w / 2 - self.mtaper, -self.mh), 'left-inner')
                .line((-self.w / 2 - self.mw, -self.mh), 'left-outer-base')
                .stroke(self.mh + self.el, -90, name='left')
                .stroke(self.mw  + self.w / 2, -90, name='left-top')
                .stroke(self.mw  + self.w / 2, name='right-top')
                .stroke(self.mh + self.el, -90, name='right')
                .stroke(self.mw - self.mtaper, -90, name='right-outer-base')
                .line((self.w / 2, 0), 'right-inner')
                .line((0, 0), 'right-base')
                )
                    
        return builder.build()


@ad.shape
@ad.datatree
class NailHole(ad.CompositeShape):
    '''
    A class representing a nail hole.
    '''
    
    r: float=ad.dtfield(2.8 / 2 + HOLE_FUDGE, doc='Radius of the hole')
    h: float=ad.dtfield(10, doc='Height of the hole, using the height of the head of the rail for consistency')
    epsilon: float=ad.dtfield(0.01, doc='Epsilon for the hole (avoiding aliasing)')
    
    hh: float=ad.dtfield(2.9, doc='Height of the head of the rail')
    hr: float=ad.dtfield(4.5 / 2, doc='Radius of the head of the rail')
    
    shaft_node: ad.Node=ad.ShapeNode(ad.Cylinder, 'r', 'h')
    head_node: ad.Node=ad.ShapeNode(ad.Cylinder, {'r': 'hr', 'h': 'hh'})
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    
    def build(self) -> ad.Maker:
        shaft = self.shaft_node()
        maker = shaft.solid('shaft').at('base')
        
        head = self.head_node()
        maker.add_at(head.solid('head').at('top'), 'top')
        
        return maker

@ad.shape
@ad.datatree
class NailSpacer(ad.CompositeShape):
    '''
    A two piece jig for spacing nails along the edge of a board.
    
    The same type of nail is used for both the nail and the pins to hold the jig together.
    
    This model will print the left or right side of the jig depending on the side parameter.
    '''
    
    path_builder: ad.Node = ad.ShapeNode(BlockPathBuilder)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.path_builder().build())
    
    n: int=ad.dtfield(15, doc='Number of holes for nails')
    p: float=ad.dtfield(10, doc='Pitch of the holes')
    r: float=ad.dtfield(2.8 / 2 + HOLE_FUDGE, doc='Radius of the holes')
    
    pin_h: float=ad.dtfield(51, doc='Height of the pin')
    
    h: float=ad.dtfield(self_default=lambda s: s.p * (s.n + 0.5), doc='Height of the shape')
    epsilon: float=ad.dtfield(0.01, doc='Epsilon for holes (avoiding aliasing)')
    
    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude)
    
    nhh: float=ad.dtfield(
        self_default=lambda s: s.el + s.epsilon * 2, doc='Height of the nail hole')

    nail_hole_node: ad.Node=ad.ShapeNode(NailHole, {'h': 'nhh'}, expose_all=True) 
    
    path_extents: List[List[float]]=ad.dtfield(
        self_default=lambda s: s.path.extents(), doc='Extents of the path.')
    
    cut_box_size: Tuple[float, float, float]=ad.dtfield(
        self_default=lambda s: (
            (s.path_extents[1][0] - s.path_extents[0][0]) / 2 + s.epsilon, 
            s.path_extents[1][1] - s.path_extents[0][1] + s.epsilon, 
            s.h + s.epsilon), 
        doc='Size of the cut box')
    cut_box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='cut_box_'))
    
    side: bool=ad.dtfield(True, doc='Render left or right side of the block')

    
    EXAMPLE_SHAPE_ARGS=ad.args(side=False, fn=32)
    EXAMPLE_ANCHORS=()
    
    EXAMPLES_EXTENDED={
        'right': ad.ExampleParams(
            shape_args=ad.args(side=False, fn=32)),
        'left': ad.ExampleParams(
            shape_args=ad.args(side=False, fn=32)),
    }

    def build(self) -> ad.Maker:
        shape = self.extrude_node()
        maker = shape.solid('block').at('right-top', 0)
        
        nail_hole = self.nail_hole_node()
        
        # Use the name nails as pin holes.
        pin_hole = self.nail_hole_node(h=self.pin_h)
        
        for i in range(self.n + 1):
            hole = nail_hole.hole(('nail', i)).at('top')
            maker.add_at(
                hole, 'right-top',
                post=ad.ROTY_180 * ad.translate((0, self.p * i, self.epsilon)))
            
            pin = pin_hole.hole(('pin', i)).at('top')
            
            if i > 0:
                maker.add_at(
                    pin, 'right', 
                    post=ad.ROTY_180 * ad.translate((-self.el / 2, self.p * (i - 0.5), self.epsilon)))
            
        cut_box = self.cut_box_node().solid('cut_box').at('face_centre', 'left', post=ad.ROTX_180)
        
        whole_maker = maker.solid('whole').at('left')

        if self.side:
            whole_maker.add_at(cut_box, 'left', 0.5, rh=0.5)
        else:
            whole_maker.add_at(cut_box, 'right', 0.5, rh=0.5)
        
        return whole_maker.intersect('block').at('right-top', rh=0.5)



@ad.shape
@ad.datatree
class NailSpacerAssembly(ad.CompositeShape):
    '''
    An assembly of two NailSpacer left and right sides,
    
    This generates the right and left sides of a NailSpacer and separates them as two solids.
    If lazy union is enabled in OpenSCAD and the 3mf file format is used, the two solids will be 
    separate meshes when exported in 3mf if the "lazy union" feature enabled.
    '''
    
    sep: float=ad.dtfield(5, doc='Separation between the left and right sides')
    fn: int=ad.dtfield(32, doc='Number of facets')
    nail_spacer_node: ad.Node=ad.ShapeNode(NailSpacer)

    def build(self) -> ad.Maker:
        left = self.nail_spacer_node(side=True)
        right = self.nail_spacer_node(side=False)
        
        # Make the left and right sides different materials,this causes these to be separate solids
        # when lazy union is enabled in OpenSCAD and exported in 3mf file format.
        left_maker = left.solid('left').material(ad.Material('left')).at(post=ad.tranX(self.sep / 2))
        right_maker = right.solid('right').material(ad.Material('right')).at(post=ad.tranX(-self.sep / 2))
        left_maker.add(right_maker)
        
        return left_maker
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
