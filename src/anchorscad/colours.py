

from dataclasses import dataclass
import numbers
import numpy as np
import colorsys

@dataclass(frozen=True)
class Colour:
    '''A colour class that can be used to specify rgb colours and convert them
    to and from hsv.'''
    
    value: tuple = (0, 0, 0, 1)

    # Colour map derived from:
    # https://github.com/openscad/openscad/blob/master/src/core/ColorNode.cc#L46
    COLOUR_MAP = {
        'antiquewhite': (250/255, 235/255, 215/255),
        'aqua': (0/255, 255/255, 255/255),
        'aquamarine': (127/255, 255/255, 212/255),
        'azure': (240/255, 255/255, 255/255),
        'beige': (245/255, 245/255, 220/255),
        'bisque': (255/255, 228/255, 196/255),
        'black': (0/255, 0/255, 0/255),
        'blanchedalmond': (255/255, 235/255, 205/255),
        'blue': (0/255, 0/255, 255/255),
        'blueviolet': (138/255, 43/255, 226/255),
        'brown': (165/255, 42/255, 42/255),
        'burlywood': (222/255, 184/255, 135/255),
        'cadetblue': (95/255, 158/255, 160/255),
        'chartreuse': (127/255, 255/255, 0/255),
        'chocolate': (210/255, 105/255, 30/255),
        'coral': (255/255, 127/255, 80/255),
        'cornflowerblue': (100/255, 149/255, 237/255),
        'cornsilk': (255/255, 248/255, 220/255),
        'crimson': (220/255, 20/255, 60/255),
        'cyan': (0/255, 255/255, 255/255),
        'darkblue': (0/255, 0/255, 139/255),
        'darkcyan': (0/255, 139/255, 139/255),
        'darkgoldenrod': (184/255, 134/255, 11/255),
        'darkgray': (169/255, 169/255, 169/255),
        'darkgreen': (0/255, 100/255, 0/255),
        'darkgrey': (169/255, 169/255, 169/255),
        'darkkhaki': (189/255, 183/255, 107/255),
        'darkmagenta': (139/255, 0/255, 139/255),
        'darkolivegreen': (85/255, 107/255, 47/255),
        'darkorange': (255/255, 140/255, 0/255),
        'darkorchid': (153/255, 50/255, 204/255),
        'darkred': (139/255, 0/255, 0/255),
        'darksalmon': (233/255, 150/255, 122/255),
        'darkseagreen': (143/255, 188/255, 143/255),
        'darkslateblue': (72/255, 61/255, 139/255),
        'darkslategray': (47/255, 79/255, 79/255),
        'darkslategrey': (47/255, 79/255, 79/255),
        'darkturquoise': (0/255, 206/255, 209/255),
        'darkviolet': (148/255, 0/255, 211/255),
        'deeppink': (255/255, 20/255, 147/255),
        'deepskyblue': (0/255, 191/255, 255/255),
        'dimgray': (105/255, 105/255, 105/255),
        'dimgrey': (105/255, 105/255, 105/255),
        'dodgerblue': (30/255, 144/255, 255/255),
        'firebrick': (178/255, 34/255, 34/255),
        'floralwhite': (255/255, 250/255, 240/255),
        'forestgreen': (34/255, 139/255, 34/255),
        'fuchsia': (255/255, 0/255, 255/255),
        'gainsboro': (220/255, 220/255, 220/255),
        'ghostwhite': (248/255, 248/255, 255/255),
        'gold': (255/255, 215/255, 0/255),
        'goldenrod': (218/255, 165/255, 32/255),
        'gray': (128/255, 128/255, 128/255),
        'green': (0/255, 128/255, 0/255),
        'greenyellow': (173/255, 255/255, 47/255),
        'grey': (128/255, 128/255, 128/255),
        'honeydew': (240/255, 255/255, 240/255),
        'hotpink': (255/255, 105/255, 180/255),
        'indianred': (205/255, 92/255, 92/255),
        'indigo': (75/255, 0/255, 130/255),
        'ivory': (255/255, 255/255, 240/255),
        'khaki': (240/255, 230/255, 140/255),
        'lavender': (230/255, 230/255, 250/255),
        'lavenderblush': (255/255, 240/255, 245/255),
        'lawngreen': (124/255, 252/255, 0/255),
        'lemonchiffon': (255/255, 250/255, 205/255),
        'lightblue': (173/255, 216/255, 230/255),
        'lightcoral': (240/255, 128/255, 128/255),
        'lightcyan': (224/255, 255/255, 255/255),
        'lightgoldenrodyellow': (250/255, 250/255, 210/255),
        'lightgray': (211/255, 211/255, 211/255),
        'lightgreen': (144/255, 238/255, 144/255),
        'lightgrey': (211/255, 211/255, 211/255),
        'lightpink': (255/255, 182/255, 193/255),
        'lightsalmon': (255/255, 160/255, 122/255),
        'lightseagreen': (32/255, 178/255, 170/255),
        'lightskyblue': (135/255, 206/255, 250/255),
        'lightslategray': (119/255, 136/255, 153/255),
        'lightslategrey': (119/255, 136/255, 153/255),
        'lightsteelblue': (176/255, 196/255, 222/255),
        'lightyellow': (255/255, 255/255, 224/255),
        'lime': (0/255, 255/255, 0/255),
        'limegreen': (50/255, 205/255, 50/255),
        'linen': (250/255, 240/255, 230/255),
        'magenta': (255/255, 0/255, 255/255),
        'maroon': (128/255, 0/255, 0/255),
        'mediumaquamarine': (102/255, 205/255, 170/255),
        'mediumblue': (0/255, 0/255, 205/255),
        'mediumorchid': (186/255, 85/255, 211/255),
        'mediumpurple': (147/255, 112/255, 219/255),
        'mediumseagreen': (60/255, 179/255, 113/255),
        'mediumslateblue': (123/255, 104/255, 238/255),
        'mediumspringgreen': (0/255, 250/255, 154/255),
        'mediumturquoise': (72/255, 209/255, 204/255),
        'mediumvioletred': (199/255, 21/255, 133/255),
        'midnightblue': (25/255, 25/255, 112/255),
        'mintcream': (245/255, 255/255, 250/255),
        'mistyrose': (255/255, 228/255, 225/255),
        'moccasin': (255/255, 228/255, 181/255),
        'navajowhite': (255/255, 222/255, 173/255),
        'navy': (0/255, 0/255, 128/255),
        'oldlace': (253/255, 245/255, 230/255),
        'olive': (128/255, 128/255, 0/255),
        'olivedrab': (107/255, 142/255, 35/255),
        'orange': (255/255, 165/255, 0/255),
        'orangered': (255/255, 69/255, 0/255),
        'orchid': (218/255, 112/255, 214/255),
        'palegoldenrod': (238/255, 232/255, 170/255),
        'palegreen': (152/255, 251/255, 152/255),
        'paleturquoise': (175/255, 238/255, 238/255),
        'palevioletred': (219/255, 112/255, 147/255),
        'papayawhip': (255/255, 239/255, 213/255),
        'peachpuff': (255/255, 218/255, 185/255),
        'peru': (205/255, 133/255, 63/255),
        'pink': (255/255, 192/255, 203/255),
        'plum': (221/255, 160/255, 221/255),
        'powderblue': (176/255, 224/255, 230/255),
        'purple': (128/255, 0/255, 128/255),
        'rebeccapurple': (102/255, 51/255, 153/255),
        'red': (255/255, 0/255, 0/255),
        'rosybrown': (188/255, 143/255, 143/255),
        'royalblue': (65/255, 105/255, 225/255),
        'saddlebrown': (139/255, 69/255, 19/255),
        'salmon': (250/255, 128/255, 114/255),
        'sandybrown': (244/255, 164/255, 96/255),
        'seagreen': (46/255, 139/255, 87/255),
        'seashell': (255/255, 245/255, 238/255),
        'sienna': (160/255, 82/255, 45/255),
        'silver': (192/255, 192/255, 192/255),
        'skyblue': (135/255, 206/255, 235/255),
        'slateblue': (106/255, 90/255, 205/255),
        'slategray': (112/255, 128/255, 144/255),
        'slategrey': (112/255, 128/255, 144/255),
        'snow': (255/255, 250/255, 250/255),
        'springgreen': (0/255, 255/255, 127/255),
        'steelblue': (70/255, 130/255, 180/255),
        'tan': (210/255, 180/255, 140/255),
        'teal': (0/255, 128/255, 128/255),
        'thistle': (216/255, 191/255, 216/255),
        'tomato': (255/255, 99/255, 71/255),
        'turquoise': (64/255, 224/255, 208/255),
        'violet': (238/255, 130/255, 238/255),
        'wheat': (245/255, 222/255, 179/255),
        'white': (255/255, 255/255, 255/255),
        'whitesmoke': (245/255, 245/255, 245/255),
        'yellow': (255/255, 255/255, 0/255),
        'yellowgreen': (154/255, 205/255, 50/255),
        'transparent': (0/255, 0/255, 0/255, 0/255),
    }
    
    def __init__(self, 
                 corr: object=None, 
                 g: float=None, 
                 b: float=None, 
                 a: float=None, 
                 hsv: tuple=None):
        '''Create a colour from a colour name, a hex colour specifier, RGB tuple, 
        RGBA tuple, or HSV tuple.
        
        Raw Colours are specified with floats between 0 and 1 or a tuple of 3 or 4 floats.
        e.g Colour(1, 0, 0) == Colour("red") and Colour((1, 0, 0)) == Colour("red")
        
        An alpha value can be specified as a separate argument or as the 4th element of
        an RGBA tuple.
        e.g. Colour(1, 0, 0, 0.5) == Colour("red", 0.5) == Colour((1, 0, 0), a=0.5)
        
        It is an error to specify both an alpha value and an alpha value in the tuple.
        
        HSV colour values can be specified as a tuple of 3 or 4 floats and passed in
        as the parameter hsv.  If hsv is specified, all other parameters must be None
        except for 'a' (alpha) whcih can be specified if the hsv tuple has 3 elements.
        e.g. Colour(hsv=(0, 1, 1)) == Colour("red") 
             Colour(hsv=(0, 1, 1, 0.5)) == Colour("red", 0.5)
             Colour('red').to_hsv() == (0, 1, 1, 1)
        
        Args:
          corr: A colour name, a hex colour specifier, RGB tuple, RGBA tuple or red value
          g: The green value (or alpha value if corr is a tuple and a is not specified.)
          b: The blue value
          a: The alpha value
          hsv: A tuple of 3 or 4 floats representing the HSV values of the colour.
          
        '''
        if hsv is not None:
            assert isinstance(hsv, tuple) and len(hsv) == 3 or len(hsv) == 4, \
                "hsv must be a tuple of 3 or 4 elements"
            assert all(isinstance(v, numbers.Number) for v in hsv), \
                'All entries must be numbers'
            assert corr is None and g is None and b is None, \
                "hsv and r, g and b cannot be specified together"
            rgb = colorsys.hsv_to_rgb(*hsv[:3])
            if len(hsv) == 4:
                assert a is None, \
                    'Alpha specified twice, once as a={a} and once as hsva={hsv}'
                a = hsv[3]        
        elif isinstance(corr, str):
            rgb = self.COLOUR_MAP.get(corr, None)
            if rgb is None and corr.startswith('#'):  # hex color
                rgb = self.parse_hex_color(corr)
            assert rgb is not None, f'Colour {corr} not found'
            if g is not None and a is None and len(rgb) == 3:
                # Assume g is alpha
                a , g = g, a
            assert g is None and b is None, \
                f'Colour name specified "{corr}" and also g={g} and b={b} not alloed.'
        elif isinstance(corr, Colour):
            rgb = corr.value
            assert g is None and b is None, 'Too many arguments'
        elif isinstance(corr, tuple) or isinstance(corr, list):
            if isinstance(corr, list):
                rgb = tuple(corr)
            else:
                rgb = corr
            # All entries should be numbers.
            assert all(isinstance(v, numbers.Number) for v in rgb), \
                'All entries must be numbers'
            if g is not None and a is None and len(rgb) == 3:
                # Assume g is alpha
                a , g = g, a
            assert len(rgb) >= 3, 'RGB tuple must have 3 or 4 elements'
            assert g is None and b is None, 'Too many arguments'
        
        # corr, g and b must be numeric and provide values between 0 and 1
        elif isinstance(corr, numbers.Number) \
            and isinstance(g, numbers.Number) \
            and isinstance(b, numbers.Number):
            rgb = (corr, g, b)
            
        if len(rgb) == 3:
            if a is None:
                a = 1.0
            else:
                assert isinstance(a, numbers.Number), \
                    f'Alpha must be a number, not {type(a)}'
            rgb = rgb + (a,)
        else:
            if len(rgb) == 4:
                assert a is None, \
                    f'alpha specified twice, once as a={a} and once as rgba=(...{rgb[3]})'
        # Validsate that all values are between 0 and 1
        assert all(0 <= v <= 1 for v in rgb), f'Colour values out of range - {rgb}'
        
        object.__setattr__(self, 'value', rgb)    
        assert len(self.value) == 4, 'RGBA tuple must have 4 elements'
    
    @classmethod
    def parse_hex_color(c, hex_color: str) -> tuple:
        '''Parse a hex color string into an RGB or RGBA tuple'''
        hex_color = hex_color.lstrip('#')
        length = len(hex_color)
        if length == 3 or length == 4:  # short form
            hex_color = ''.join([c*2 for c in hex_color])
            length = len(hex_color)
        
        # Check length.
        assert length == 6 or length == 8, f'Invalid hex color: {hex_color}'

        try:            
            rgb = tuple(int(hex_color[i:i+2], 16)/255 for i in range(0, 6, 2))
            if length == 8:  # alpha specified
                a = int(hex_color[6:8], 16)/255
                rgb += (a,)
        except ValueError as e:
            raise AssertionError(str(e))
        
        return rgb

    def alpha(self, a: float):
        '''Return a new colour with the same RGB values but with the specified alpha'''
        assert isinstance(a, numbers.Number), 'Alpha must be a number'
        return Colour(*self.value[:3], a)
    
    def red(self, r: float):
        '''Return a new colour with the same RGB values but with the specified red'''
        assert isinstance(r, numbers.Number), 'Red must be a number'
        return Colour(r, *self.value[1:])
    
    def green(self, g: float):
        '''Return a new colour with the same RGB values but with the specified green'''
        assert isinstance(g, numbers.Number), 'Green must be a number'
        return Colour(*self.value[:1], g, *self.value[2:])    
    
    def blue(self, b: float):
        '''Return a new colour with the same RGB values but with the specified blue'''
        assert isinstance(b, numbers.Number), 'Blue must be a number'
        return Colour(*self.value[:2], b, *self.value[3:])
    
    def blend(self, other, weight: float):
        '''Blend this colour with another colour'''
        assert isinstance(other, Colour), 'Other must be a colour'
        assert isinstance(weight, numbers.Number), 'Weight must be a number'
        assert 0 <= weight <= 1, 'Weight must be between 0 and 1'
        return Colour(*np.array(self.value) * (1 - weight) + np.array(other.value) * weight)     

    def to_hex(self):
        '''Return a hex string representation of this colour'''
        if self.value[3] >= 255 / 255.9999:
            return '#' + ''.join(f'{int(v*255.9999):02x}' for v in self.value[:3])
        return '#' + ''.join(f'{int(v*255.9999):02x}' for v in self.value)
    
    def to_hsv(self):
        '''Return a HSV representation of this colour'''
        r, g, b, a = self.value
        return colorsys.rgb_to_hsv(r, g, b) + (a,)
