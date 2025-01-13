'''
Created on ${date}

@author: ${user}
'''


from anchorscad_models.hinges.Hinge import Hinge

import anchorscad as ad


@ad.shape
@ad.datatree
class HingedFlap(ad.CompositeShape):
    '''
    Flaps with a hinge. Bacically a couple of places with a hinge in the middle.
    '''

    sep: float=ad.dtfield(0.25, doc='Separation between the front and back of the flap.')
    
    
    w: float=ad.dtfield(361 / 2, 'Width of the flap')
    front_h: float=ad.dtfield(89.1, "Height of the front of the flap")
    back_h: float=ad.dtfield(30, "Height of the back of the flap")
    t: float=ad.dtfield(1.8, "Thickness of the flap")
    st: float=ad.dtfield(6.5, "Thickness of the screen")
    
    bar_h: float=ad.dtfield(self_default=lambda s: s.w - 3, doc='Height of hinge bar')
    nib_r: float=ad.dtfield(2.5, doc='Radius of hinge bar')
    #nib_ang_len: float=ad.dtfield(2, 'Angle length of inner hinge nib')
    
    seg_count: int=ad.dtfield(11, 'Number of segments in hinge bar')
    bar_node: ad.Node=ad.ShapeNode(Hinge)
    hinge_shape: ad.Shape=ad.dtfield(
            self_default=lambda s: s.bar_node(), init=False)
    
    front_size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.w, s.t, s.front_h))
    front_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='front_'), init=False)
    
    back_size: tuple=ad.dtfield(
        doc='The (x,y,z) size of ShapeName',
        self_default=lambda s: (s.w, s.t, s.back_h))
    back_node: ad.Node=ad.dtfield(ad.ShapeNode(ad.Box, prefix='back_'), init=False)
    
    
    EXAMPLE_SHAPE_ARGS=ad.args(fn=64)
    XXEXAMPLE_ANCHORS=(
        ad.surface_args('hinge', 'hinge_base'),)

    def build(self) -> ad.Maker:
        # Add your shape building code here...
        front_shape = self.front_node()
        maker = front_shape.solid('front').at('face_centre', 'back')
        
        back_shape = self.back_node()
        back_maker = back_shape.solid('back').at('face_edge', 'top', 0, post=ad.ROTY_180 * ad.tranZ(-self.sep))
        
        maker.add_at(back_maker, 'face_edge', 'top', 0)
        
        hinge_chain_maker = self.hinge_shape.composite('hinge').at('hinge_base', post=ad.ROTX_90)
        
        maker.add_at(hinge_chain_maker, 'face_edge', 'top', 2, post=ad.tranY(self.t))
        #print(f"bar_h: {self.hinge_shape.hinge_bar_shape.bar_r}")
        #print(f"wanted bar_r: {6.5 / 2 + self.t + 1}")
        print(self.sep)
        
        return maker

    @ad.anchor('An example anchor')
    def example_anchor(self):
        return self.maker.at()


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
