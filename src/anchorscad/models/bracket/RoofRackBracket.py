'''
Created on 4-Jun-2023

@author: gianni
'''

import anchorscad as ad
import anchorscad.models.basic.stadium as stadium
import numpy as np

@ad.datatree
class RoofRackBarOutline:
    '''Provides the outline for the Prorack brand roof rack bar.
    This one is specific to bars shaped like and areofoil.
    '''
    
    thickness: float=24
    min_thickness: float=5
    width: float=85
    maximal_thickness_x: float=28
    minimum_thickness_x: float=3
    
    def build(self):
        
        p_max = (self.maximal_thickness_x, self.thickness / 2)
        p_max_dir = (p_max[0] - 1, p_max[1])
        
        p_min_dir = (self.width, 1)
        p_min = (self.width, 0)
        
        p_base_max = (self.maximal_thickness_x, - self.thickness / 2)
        p_base_max_dir = (p_base_max[0] + 1, p_base_max[1])
        
        path = (ad.PathBuilder()
            .move((0, 0), 'start', direction=(0, 1))
            .spline((p_max_dir, p_max), 'front_top', cv_len=(8.5, 14))
            .spline((p_min_dir, p_min), 'back_top', cv_len=(14, 6.5))
            .spline((p_base_max_dir, p_base_max), 'back_base', cv_len=(1, 14))
            .spline(((0, -1), (0, 0)), 'front_base', cv_len=(14, 8.5))
        ).build()

        return path

@ad.shape
@ad.datatree
class RoofRackBracketHole(ad.CompositeShape):
    '''
    Padding for a roof rack bracket. The bracket consists of a
    U bolt and a flat plate and this is the padding for the 
    flat plate and U bolt to snugly fit around the roof rack
    bar.
    '''
    
    width: float=3
    
    outline: ad.Node=ad.Node(RoofRackBarOutline, prefix='outline_')
    
    path: ad.Path=ad.dtfield(
        self_default=lambda s: s.outline().build())
    
    extrude_node : ad.Node=ad.ShapeNode(
        ad.LinearExtrude, {})
    
    notch_node : ad.Node=ad.ShapeNode(ad.Cylinder, 
            {'h': 'width'}, prefix='notch_', expose_all=True)
    notch_r: float=1.8
    
    fn: int=64

    NOTCH_ANCHOR=ad.surface_args('outline', 'front_top', 0.27, rh=1)
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        NOTCH_ANCHOR,
    )

    def build(self) -> ad.Maker:
        shape = self.extrude_node(path=self.path, h=self.width)
        
        maker = shape.solid('outline').at()

        notch_shape = self.notch_node(fn=4)
        maker.add_at(notch_shape.solid('notch').at('top'),
                     anchor=self.NOTCH_ANCHOR, post=ad.ROTX_270 * ad.tranY(-self.notch_r * 0.2))
        return maker
    
    @ad.anchor('The centre of the outline')
    def centre(self):
        return ad.translate((self.outline_width / 2, 0, self.width / 2))
    

@ad.shape
@ad.datatree
class RoofRackBracket(ad.CompositeShape):
    '''
    Padding for a roof rack bracket. The bracket consists of a
    U bolt and a flat plate and this is the padding for the 
    flat plate and U bolt to snugly fit around the roof rack
    bar.
    '''
    
    width: float=4
    padding: float=15
    
    bracket_hole: ad.Node=ad.Node(RoofRackBracketHole)
    
    cage_size: tuple=ad.dtfield(self_default=lambda s: 
        (s.outline_width + s.padding, s.outline_thickness + s.padding, s.width))
    
    cage_node : ad.Node=ad.ShapeNode(ad.Box, prefix='cage_')
    
    block_size: tuple=ad.dtfield(self_default=lambda s: 
        (s.cage_size[0], s.cage_size[1] / 2, s.cage_size[2]))
    
    block_node : ad.Node=ad.ShapeNode(ad.Box, prefix='block_')

    fn: int=64
    epsilon: float=0.01
    
    upper_half: bool=True
    
        
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'front'),
    )
    EXAMPLES_EXTENDED={'upper': ad.ExampleParams(
                            ad.args(upper_half=True)),
                       'lower': ad.ExampleParams(
                            ad.args(upper_half=False)),
                       }
        

    def build(self) -> ad.Maker:
        
        cage_shape = self.cage_node()
        maker = cage_shape.cage('cage').at('centre')
        
        face = 'back' if self.upper_half else 'front'
        
        block_shape = self.block_node()
        maker = maker.add_at(block_shape.solid('block').at('face_centre', face),
                             'face_centre', face)
        
        shape = self.bracket_hole(width=self.width + self.epsilon)
        
        # Align cage and hole centres.
        maker.add_at(shape.hole('rack_outline').at('centre'), 'centre')
        return maker

@ad.shape
@ad.datatree
class RoofRackBracketUBoltCutout(ad.CompositeShape):
    ''''''
    d: float=11
    base_w: float=83
    depth: float=150
    
    ubolt_r: float=ad.dtfield(self_default=lambda s: s.d / 2)
    ubolt_inner_r: float=15
    ubolt_w: float=9
    ubolt_sequence: tuple=ad.dtfield(self_default=lambda s:
        (('P', ad.args(h=s.depth)),
         ('R', ad.args(sweep_degrees=90)),
         ('P', ad.args(h=s.base_w - 2 * s.ubolt_inner_r)),
         ('R', ad.args(sweep_degrees=90)),
         ('P', ad.args(h=s.depth)),))

    ubolt_node: ad.Node=ad.ShapeNode(stadium.StadiumSequence, prefix='ubolt_')
    
    
    EXAMPLE_ANCHORS=(
        ad.surface_args('ubolt', 'element-0', 'stadium', 'right', 0.5),
        ad.surface_args('ubolt', 'element-4', 'stadium', 'right', 0.5, rh=1),
    )
    
    def build(self) -> ad.Maker:
        
        ubolt_shape = self.ubolt_node()
        
        maker = ubolt_shape.solid('ubolt').at('base')
        
        extension_len = self.ubolt_inner_r * 2 + self.ubolt_w
        extension = ubolt_shape.prism_node(h=extension_len)
        
        maker.add_at(extension.solid('extension1').at('top'), 
                     'element-0', 'top', post=ad.ROTX_180)
        
        maker.add_at(extension.solid('extension2').at('top'), 
                     'ubolt', 'element-4', 'base', post=ad.ROTX_180)
        
        flat_extension_len = self.base_w + self.ubolt_inner_r
        flat_extension = ubolt_shape.prism_node(h=flat_extension_len, square_right=True)
        
        maker.add_at(flat_extension.solid('flat_base').at('stadium', 'top', 0, rh=0.5), 
                     'ubolt', 'element-2', 'stadium', 'top', 0, rh=0.5)
        
        return maker
    
    def overall_width(self):
        p1 = self.maker.at('ubolt', 'element-0', 'stadium', 'right', 0.5)
        p2 = self.maker.at('ubolt', 'element-4', 'stadium', 'right', 0.5, rh=1)
        return ad.distance_between(p1, p2)

@ad.shape
@ad.datatree
class RoofRackBracketAssembly(ad.CompositeShape):
    '''Full assembly of the roof rack bracket. This is a block with a hole 
    for the roof rack bar and a U bolt. It can be slanted for pitch and yaw
    to accommodate the curve of the car's turret.'''

    label: str=ad.dtfield(
        default='Default', 
        doc='Embossed label to distinguish the different variations.')
    
    bolt_cutout_node: ad.Node=ad.ShapeNode(
        RoofRackBracketUBoltCutout, prefix='bolt_cutout_')
    
    bolt_cutout_shape: ad.Shape=ad.dtfield(
        self_default=lambda s: s.bolt_cutout_node())
    
    rack_hole: ad.Node=ad.ShapeNode(
        RoofRackBracketHole, prefix='rack_hole_')
    
    rack_hole_shape: ad.Shape=ad.dtfield(self_default=lambda s: s.rack_hole())
    
    margin: float=4
    vmargin: float=10
    vbase_size: float=5
    block_width: float=50
    rack_hole_width: float=70
    rack_hole_pitch: float=5
    rack_hole_yaw: float=5
    
    block_node: ad.Node=ad.ShapeNode(ad.Box, prefix='block_')
    
    epsilon: float=0.02
    
    block_size: tuple=ad.dtfield(
        self_default=lambda s: (
            s.bolt_cutout_shape.overall_width() + s.margin * 2,
            s.rack_hole_shape.outline_thickness + s.vmargin * 2,
            s.block_width - s.epsilon))
    
    base_block_node: ad.Node=ad.ShapeNode(ad.Box, prefix='base_block_')
    
    base_block_size: tuple=ad.dtfield(
        self_default=lambda s: (
            s.block_size[0],
            s.vbase_size,
            s.block_size[2]))
    
    
    slit_hole_node: ad.Node=ad.ShapeNode(ad.Box, prefix='slit_hole_')
    
    
    slit_size: float=2.5
    slit_margin: float=0.5
    slit_open: bool=False
    
    slit_hole_size: tuple=ad.dtfield(
        self_default=lambda s: (
            1 + s.block_size[0] / np.cos(ad.to_radians(s.rack_hole_pitch)),
            s.slit_size ,
            s.rack_hole_width + 2 * s.epsilon))
    
    # Label to distinguish the different variations.
    label_halign: str='centre'
    label_valign: str='centre'
    label_depth: float=2
    label_size: float=20
    label_node: ad.Node=ad.ShapeNode(
        ad.Text, {'text': 'label'}, prefix='label_', expose_all=True)
    
    fn: int=64    
        
    EXAMPLE_ANCHORS=(
        ad.surface_args('face_centre', 'back'),
    )

    EXAMPLES_EXTENDED={
        'right_front': ad.ExampleParams(
                    shape_args=ad.args(
                        rack_hole_pitch=1, 
                        rack_hole_yaw=-2,
                        label='R F'),
                    anchors=()),
        'left_front': ad.ExampleParams(
                    shape_args=ad.args(
                        rack_hole_pitch=0,
                        rack_hole_yaw=2,
                        label='L F'),
                    anchors=()),
        'right_back': ad.ExampleParams(
                    shape_args=ad.args(
                        rack_hole_pitch=1, 
                        rack_hole_yaw=-2,
                        label='R B'),
                    anchors=()),
        'left_back': ad.ExampleParams(
                    shape_args=ad.args(
                        rack_hole_pitch=0, 
                        rack_hole_yaw=2,
                        label='L B'),
                    anchors=())
    }
    
    def build(self) -> ad.Maker:
        
        block = self.block_node()
        
        maker = block.solid('block').transparent(False).at('centre')
        
        base_block = self.base_block_node()
        
        maker.add_at(base_block.solid('base_block').at('face_centre', 'front'),
                     'face_centre', 'front', post=ad.ROTX_180)
        
        rack_cutout = self.rack_hole()
        
        maker.add_at(rack_cutout.hole('rack_cutout').at('centre'), 
            'centre', 
            post=ad.rotZ(self.rack_hole_pitch) * ad.rotX(self.rack_hole_yaw))
        
        slit_cutout = self.slit_hole_node()
        
        maker.add_at(slit_cutout.hole('slit_cutout').at('centre'), 
                     'rack_cutout', 'centre')
        
        maker.add_at(
            self.bolt_cutout_shape.hole('bolt_cutout')
                .at('ubolt', 'element-2', 'stadium', 'left', 0.5, rh=0.5),
            'base_block', 'face_centre', 'front',
            post=ad.ROTX_180 * ad.ROTZ_90)
        
        label_shape = self.label_node()

        maker.add_at(label_shape.hole('label').colour((1, 0, 0)).at(),
                     'face_centre', 'back')
        

        # Making a "solid" of the maker isolates all the holes to this layer of
        # the assembly.
        maker_final = maker.solid('assembly').at()

        # Add a cap. This is small and flexible and ties the edges of the sliced
        # bracket. This is added after all the holes have been applied so the
        # exact position of the slit is inconsequential.
        cap_size = list(self.block_size)
        cap_size[0] = self.slit_margin
        cap_shape = self.block_node(size=cap_size)
        cap_mode = ad.ModeShapeFrame.CAGE if self.slit_open else ad.ModeShapeFrame.SOLID

        # The base "block" shape has the cap attached.
        maker_final.add_at(
            cap_shape.named_shape('cap', cap_mode).colour((0, 1, 0)).at('face_centre', 'left'),
            'block', 'face_centre', 'left'
        )

        return maker_final
    

# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(write_files=True, write_path_files=True)

if __name__ == "__main__":
    ad.anchorscad_main()
