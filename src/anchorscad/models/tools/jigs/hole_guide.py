'''
Created on 28 May 2022

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class HoleGuide(ad.CompositeShape):
    '''Drill guide for placement of holes in specific locations.
    '''
    r: float=5.0/2
    h: float=25
    offs: float=5
    h_cyl: float=ad.dtfield(
        doc='Height of guide holes',
        self_default=lambda s: s.h + s.epsilon + 100)
    stock_size: float=(79.5 + 0.3, 9.8 + 0.3, 15)
    t: float=4
    epsilon: float=0.01
    
    size: tuple=ad.dtfield(
        doc='The (x,y,z) size of jig',
        self_default=lambda s: (
            s.stock_size[0] + s.t * 2, 
            s.stock_size[1] + s.t * 2, 
            s.stock_size[2] + s.h + s.epsilon))
    stock_box_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Box, {'size': 'stock_size'}), init=False)
    box_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, 'size'), init=False)
    cyl_node: ad.Node=ad.dtfield(
        ad.ShapeNode(ad.Cylinder, 'r', {'h': 'h_cyl'}), init=False)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=32)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        shape = self.box_node()
        maker = shape.solid('jig').at('centre')
        
        stock = self.stock_box_node()
        maker.add_at(stock.hole('stock').at('face_centre', 'base'),
                     'face_centre', 'base', post=ad.tranZ(self.epsilon))
        
        guide_hole = self.cyl_node()
        for i in range(2):
            maker.add_at(
                guide_hole.hole(('guide', i)).at('top'),
                'stock', 'face_edge', 'top', i * 2 + 1, 
                post=ad.ROTX_180 * ad.translate(
                    [0, -self.r -self.offs, self.epsilon / 2]))
        
        return maker


MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()
