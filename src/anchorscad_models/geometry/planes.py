'''
Created on 26 Jan 2021

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class Planes(ad.CompositeShape):
    '''
    A set of planes
    '''
    mat1: ad.GMatrix=ad.IDENTITY
    
    EXAMPLE_SHAPE_ARGS=ad.args()
    EXAMPLE_ANCHORS=()
    
    def build(self):
        maker = ad.Box([100, 100, 1]).solid(
            'plane1').colour([1, 1, 0, 0.5]).at('centre')
        
        return maker

    @ad.anchor('An example anchor specifier.')
    def side(self, *args, **kwds):
        return self.maker.at('face_edge', *args, **kwds)

if __name__ == '__main__':
    ad.anchorscad_main(False)
