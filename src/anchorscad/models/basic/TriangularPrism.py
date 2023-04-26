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
    
    EXAMPLE_SHAPE_ARGS=ad.args([30, 10, 3])
    EXAMPLE_ANCHORS=(ad.surface_args('base'),
                     ad.surface_args('face_centre', 1),)
    
    def build(self) -> ad.Maker:
        maker = ad.Box(self.size).cage(
            'cage').at('centre')
        
        path = (ad.PathBuilder()
            .move([0, 0])
            .line([0, self.size[0]], 'face1')
            .line([self.size[1], 0], 'face2')
            .line([0, 0], 'face3')
            .build())
            
        shape = ad.LinearExtrude(path, h=self.size[2])
        
        maker.add_at(shape.solid('prism').at('face3', 0.5, rh=0.5), 
                     'face_centre', 2, post=ad.ROTX_180)
        
        return maker

    @ad.anchor('Base of the prism.')
    def base(self, *args, **kwds):
        return self.maker.at('prism', 'face3', 1, *args, **kwds)
    
    
# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == '__main__':
    ad.anchorscad_main(False)
