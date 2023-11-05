'''
Code for the Merlin1846 model was posted to Reddit by 
u/Merlin1846 on 2023-11-3 on r/openscad on reddit.com.

@author: gianni 
'''

import anchorscad as ad

POSTED_CODE='''
hole_depth=2;
hole_diameter=15.5;
holes=8;
r=100;
outer_spacing=3;
thickness=10;
donut=true;

difference() {
cylinder(h=thickness, r = r);
r2 = r - (hole_diameter / 2) - outer_spacing;
for (i=[0:360/holes:360])
  translate([r2 * sin(i), r2 * cos(i), thickness- hole_depth]) cylinder(hole_depth, d=hole_diameter);
  
cylinder(thickness, r=r-(outer_spacing * 2)-hole_diameter);
}

'''

@ad.shape
@ad.datatree
class Merlin1846(ad.CompositeShape):
    '''
    Anchorscad model duplicating the model posted by Merlin1846.
    '''
    hole_depth: float=2
    hole_diameter: float=15.5
    holes: int=8
    radius: float=100
    outer_spacing: float=3
    thickness: float=10
    donut: bool=True
    
    # Maps a cylinder onto the Merlin1846 fields.
    cylinder_node: ad.Node=ad.dtfield(
        ad.ShapeNode(
            ad.Cylinder, 
            {'r': 'radius', 'h': 'thickness'}, 
            expose_all=True, 
            prefix='cylinder_'))

    # Creates the radius of the holes.    
    r2: float=ad.dtfield(
        self_default=lambda s: s.hole_diameter / 2)
    
    # Maps the "hole" cyclinder onto the Merlin1846 fields.
    hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(
            ad.Cylinder, 
            {'r': 'r2', 'h': 'hole_depth'}, 
            expose_all=True, 
            prefix='hole_'))

    # Radius of cylinder that locates the holes on the main cylinder.    
    cage_r: float=ad.dtfield(
        self_default=lambda s: s.radius - s.outer_spacing - s.r2)

    # Maps the "cage" cylinder onto the Merlin1846 fields.
    locator_cage_node: ad.Node=ad.dtfield(
        ad.ShapeNode(
            ad.Cylinder, 
            {'r': 'cage_r', 'h': 'thickness'}, 
            expose_all=True, 
            prefix='cage_'))
    
    # An "epsilon" value to avoid aliasing problems.
    epsilon: float=0.01
    
    # Radius of the centre hole.
    centre_hole_r: float = ad.dtfield(
        self_default=lambda s: s.radius - 2 * (s.outer_spacing + s.r2))
    # Depth of the centre hole - slightly deeper than the main cylinder 
    # to avoid aliasing problems.
    centre_hole_h: float = ad.dtfield(
        self_default=lambda s: s.thickness + s.epsilon)
    
    # Maps the "centre_hole" cylinder onto the Merlin1846 fields.
    centre_hole_node: ad.Node=ad.dtfield(
        ad.ShapeNode(
            ad.Cylinder,
            prefix='centre_hole_',
            expose_all=True))
    
    fn: int=64 # Number of facets for the shapes.

    def build(self) -> ad.Maker:
        
        # This is for locating the holes on the main cylinder.
        maker = self.locator_cage_node().cage('cage').at('base')
        
        # This adds the main cylinder onto the cage.
        maker.add_at(self.cylinder_node().solid('cylinder').at('base'), 'base')
        
        # Place the big centre hole.
        maker.add_at(self.centre_hole_node().hole('centre_hole').at('centre'), 'centre')
        
        # Place the holes around the main cylinder.
        hole_shape = self.hole_node()
        for i in range(self.holes):
            hole_maker = hole_shape.hole(('hole', i)).at('top')
            maker.add_at(
                hole_maker,
                'surface', rh=1, degrees=i * 360 / self.holes, 
                post=ad.ROTX_270 * ad.tranZ(self.epsilon))

        return maker



# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(all=True)

if __name__ == "__main__":
    ad.anchorscad_main()
