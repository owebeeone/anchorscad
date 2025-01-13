'''
Created on 24 Nov 2021

@author: gianni
'''


import anchorscad as ad
from anchorscad import Fabricator, \
    StlRecipeArgs, ImageRecipeArgs, RecipiesBuilder


@ad.datatree
@ad.fabricator
class BoxFabricator(Fabricator):
    '''
    Example fabricator to generate stl and png image.
    '''
    file_basename: str=None  # Use the class name if unset.
    stl_args: StlRecipeArgs=StlRecipeArgs(True)
    image_args: ImageRecipeArgs=ImageRecipeArgs(imgsize=(1280, 1024))

    def __post_init__(self):
        self.recipies = (RecipiesBuilder()
            .add(
                name='box1',
                shape_func=lambda : ad.Box((10, 20, 30)),
                anchor=ad.surface_args(
                            'face_centre', 0, post=ad.tranX(40)),
                place_at=ad.surface_args(
                            'plate', 100, 100)
                )
            .add(
                name='box2',
                shape_func=lambda : ad.Box((10, 20, 30)),
                anchor=ad.surface_args(
                            'face_centre', 3, post=ad.tranX(40)),
                place_at=ad.surface_args(
                            'plate', 100, -100)
                )
            .build())

    
if __name__ == "__main__":
    ad.anchorscad_main(False)
