'''
Created on 2023-08-20

@author: Gianni
'''

import anchorscad as ad
import numpy as np

@ad.datatree
class BendyProfile:

    h : float = 3
    upper_w : float = 0.05
    lower_w : float = 1.1

    def build(self) -> ad.Path:

        path = (ad.PathBuilder()
                .move((0, 0))
                .line((-self.lower_w / 2, 0), 'base_left')
                .line((-self.upper_w / 2, self.h), 'side_left')
                .line((0, self.h), 'top_left')
                .line((self.upper_w / 2, self.h), 'top_right')
                .line((self.lower_w / 2, 0), 'side_right')
                .line((0, 0), 'base_right')
                ).build()

        return path


@ad.shape
@ad.datatree
class BendySlit(ad.CompositeShape):
    '''
    A slit template for making benable plates.
    '''
    l : float = 20

    profile_node: ad.Node=ad.ShapeNode(BendyProfile)
    path: ad.Path=ad.dtfield(self_default=lambda s: s.profile_node().build())
    path_extents: list=ad.dtfield(self_default=lambda s: s.path.extents())

    cage_size: tuple= ad.dtfield(
        self_default=lambda s: (
            s.path_extents[1][0] - s.path_extents[0][0], 
            s.path_extents[1][1] - s.path_extents[0][1], 
            s.l))
    box_node: ad.Node=ad.ShapeNode(ad.Box, {'size': 'cage_size'}, expose_all=True)

    extrude_node: ad.Node=ad.ShapeNode(ad.LinearExtrude, {'h' : 'l'}, expose_all=True)

    hide_cage: bool=True
    cage_node: ad.Node=ad.CageOfNode()
    
    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False)

    def build(self) -> ad.Maker:

        cage_shape = self.box_node()

        maker = self.cage_node(cage_shape).at()

        shape = self.extrude_node()
        maker.add_at(shape.solid('slit').colour((1, 0, 0)).at('base_left', 0),
                     'face_edge', 'front', 0, post=ad.ROTY_180)
        
        return maker


@ad.shape
@ad.datatree
class BendyHoles(ad.CompositeShape):
    '''
    A hole template for making bendable plates.
    '''

    slit_node : ad.Node = ad.ShapeNode(BendySlit)
    slit_shape : ad.Shape = ad.dtfield(self_default=lambda s: s.slit_node())
    slit_end_shape : ad.Shape = ad.dtfield(
        self_default=lambda s: s.slit_node(l=0.5 * (s.slit_shape.l - s.col_gap)))

    rows : int = 45
    cols : int = 5
    row_gap : float = 1.4
    col_gap : float = 5

    slit_size : list = ad.dtfield(self_default=lambda s: s.slit_shape.cage_size)

    overall_size : tuple = ad.dtfield(
        self_default=lambda s: (
            s.slit_size[0] * s.rows + s.row_gap * (s.rows - 1),
            s.slit_size[2] * s.cols + s.col_gap * (s.cols - 1),
            s.slit_size[1]))
    
    box_node: ad.Node=ad.ShapeNode(ad.Box, {'size': 'overall_size'}, expose_all=True)
    
    hide_cage: bool=True
    cage_node: ad.Node=ad.CageOfNode()

    EXAMPLE_SHAPE_ARGS=ad.args(hide_cage=False)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        cage = self.box_node()
        maker = self.cage_node(cage).at()

        for row in range(self.rows):
            col_offs = 0 if row % 2 == 0 else 0.5

            if col_offs > 0:
                cols = self.cols -1
                position = ad.translate([
                    row * (self.slit_size[0] + self.row_gap), 
                    0, 
                    0])
                
                maker.add_at(
                    self.slit_end_shape.solid(('slit', row, 'front')).at('face_corner', 'front', 0),
                    'face_corner', 'top', 0, pre=position)
            else:
                cols = self.cols

            for col in range(cols):
                position = ad.translate([
                    row * (self.slit_size[0] + self.row_gap), 
                    (col + col_offs) * (self.slit_size[2] + self.col_gap), 
                    0])

                maker.add_at(
                    self.slit_shape.solid(('slit', row, col)).at('face_corner', 'front', 0),
                    'face_corner', 'top', 0, pre=position)

            if col_offs > 0:
                position = ad.translate([
                    row * (self.slit_size[0] + self.row_gap), 
                    (cols + col_offs) * (self.slit_size[2] + self.col_gap), 
                    0])
                
                maker.add_at(
                    self.slit_end_shape.solid(('slit', row, 'back')).at('face_corner', 'front', 0),
                    'face_corner', 'top', 0, pre=position)

        return maker
    

@ad.shape
@ad.datatree
class BendyPlate(ad.CompositeShape):
    '''
    A bendable plate example.
    '''

    holes_node : ad.Node = ad.ShapeNode(BendyHoles)
    holes_shape : ad.Shape = ad.dtfield(self_default=lambda s: s.holes_node())
    size : tuple = ad.dtfield(self_default=
            lambda s: np.array(s.holes_shape.overall_size) - 0.001 + np.array([10, 0, 0]))

    plate_node : ad.Node = ad.ShapeNode(ad.Box)
    plate_shape : ad.Shape = ad.dtfield(self_default=lambda s: s.plate_node())

    EXAMPLE_SHAPE_ARGS=ad.args(rows=50, cols=3, l=10)
    EXAMPLE_ANCHORS=()

    def build(self) -> ad.Maker:
        maker = self.plate_shape.solid('plate').at('centre')

        maker.add_at(
            self.holes_shape.hole('holes').at('centre'),
            'centre')

        return maker


MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
