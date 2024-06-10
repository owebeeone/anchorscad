'''
Created on 12 Sep 2021

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class TriangularPrism(ad.CompositeShape):
    '''
    Generates a triangular prism given the width depth and height.
    This is caged by a ad.Box for box anchors and also named 2D path
    anchors.
    '''
    size: tuple
    skew: float=ad.dtfield(0.0, 
            'Skew factor, 0.5 will create an isocelies triange 0 and 1 are right angled.')
    
    EXAMPLE_SHAPE_ARGS=ad.args([30, 10, 3], 0.5)
    EXAMPLE_ANCHORS=(ad.surface_args('base', 0.5),
                     ad.surface_args('face_centre', 1),)
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.size).cage(
            'cage').at('centre')
        
        path = (ad.PathBuilder()
            .move([0, 0])
            .line([self.size[1] * self.skew, self.size[0]], 'face1')
            .line([self.size[1], 0], 'face2')
            .line([0, 0], 'face3')
            .build())
            
        shape = ad.LinearExtrude(path, h=self.size[2])
        
        maker.add_at(shape.solid('prism').at('face3', 0.5, rh=0.5), 
                     'face_centre', 2, post=ad.ROTX_180)
        
        return maker

    @ad.anchor('Base of the prism corner.')
    def base(self, r=1, **kwds):
        return self.maker.at('prism', 'face3', r, **kwds) * ad.ROTY_180
    
    
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == '__main__':
    ad.anchorscad_main(False)
