'''
Created on 25 Feb 2022

@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class DiceWithDigits(ad.CompositeShape):
    '''
    A six sided dice with numbered faces (instead of dots).
    '''

    size: tuple=(20,) * 3

    EXAMPLE_SHAPE_ARGS=ad.args(size=(50,) * 3)
    FACE_MAP = (2, 1, 3, 5, 6, 4)

    def build(self) -> ad.Maker:
        maker = ad.Box(self.size).solid('dice').at()
        for i in range(6):
            maker.add_at(
                ad.Text(text=str(self.FACE_MAP[i]),
                        size=self.size[0] * 0.75,
                        depth=self.size[0] / 15,
                        halign='centre',
                        valign='centre')
                .hole(i).colour([1, 0.5, 0.3]).at('default'),
                'face_centre', i
                )
        return maker


# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main(False)
