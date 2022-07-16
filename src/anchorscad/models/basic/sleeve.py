'''
Created on 14 Jul 2022
@author: gianni
'''

import anchorscad as ad


@ad.shape
@ad.datatree
class Sleeve(ad.CompositeShape):
    '''
    Cylindrical sleeve
    '''
    h: float=ad.dtfield(1, 'Height of sleeve')   
    inside_r: float=ad.dtfield(10, 'Inner radius')
    outside_r: float=ad.dtfield(15, 'Outer radius')
    inside_cyl_cage_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cylinder, {'r': 'inside_r'}), init=False)
    outside_cyl_cage_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cylinder, 'h', {'r': 'outside_r'}), init=False)
    cage_of_node: ad.Node=ad.CageOfNode()
    start_degrees: float=ad.dtfield(0, 'Start angle of sleeve')
    end_degrees: float=ad.dtfield(360, 'End angle of sleeve')
    rotate_extrude_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.RotateExtrude, {}), init=False)
    epsilon: float=0.01 
     
    EXAMPLE_SHAPE_ARGS=ad.args(as_cage=False, h=10, fn=16, 
                               start_degrees=20, 
                               end_degrees=330)
    EXAMPLE_ANCHORS=(ad.surface_args('surface', 0),
                     ad.surface_args('inner_surface', 0),)

    def build(self) -> ad.Maker:

        assert self.outside_r > self.inside_r, (
            f'Inside radius ({self.inside_r}) must be smaller than outside ({self.outside_r}')
        maker = self.cage_of_node(
                self.outside_cyl_cage_node(), cage_name='outer').at('centre')
        
        maker.add(self.cage_of_node(
                self.inside_cyl_cage_node(
                    h=self.h + self.epsilon), cage_name='inner')
                    .colour((1, 0, 0, 0.4)).at('centre'))
        path = (ad.PathBuilder()
                .move((self.inside_r, 0))
                .line((self.inside_r, self.h / 2), name='upper_inner')
                .line((self.outside_r, self.h / 2), name='top_segment')
                .line((self.outside_r, 0), name='upper_outer')
                .line((self.outside_r, -self.h / 2), name='lower_outer')
                .line((self.inside_r, -self.h / 2), name='base_segment')
                .line((self.inside_r, 0), name='lower_inner')
                .build())
        sleeve_shape = self.rotate_extrude_node(
                path=path, 
                degrees=self.end_degrees - self.start_degrees)
        
        maker.add_at(sleeve_shape.solid('sleeve').at('top_segment', 1), 
                     'surface', degrees=self.start_degrees, rh=1,
                     post=ad.ROTX_90)
        return maker

    @ad.anchor('outer surface anchor')
    def surface(self, *args, **kwds):
        '''Inner surface anchor with corrected Z points away from surface.'''
        return ad.rotZ(-self.start_degrees) \
                * self.maker.at('outer', 'surface', *args, **kwds)


    @ad.anchor('inner surface anchor')
    def inner_surface(self, *args, **kwds):
        '''Inner surface anchor with corrected Z points away from surface.'''
        return ad.rotZ(-self.start_degrees) \
                * self.maker.at('inner', 'surface', *args, **kwds) * ad.ROTX_180

@ad.shape
@ad.datatree
class SleeveAndKeyway(ad.CompositeShape):
    '''
    Cylindrical sleeve
    '''
    h: float=ad.dtfield(1, 'Height of sleeve')   
    inside_r: float=ad.dtfield(10, 'Inner radius')
    outside_r: float=ad.dtfield(15, 'Outer radius')
    inside_cyl_cage_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cylinder, {'r': 'inside_r'}), init=False)
    outside_cyl_cage_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.Cylinder, 'h', {'r': 'outside_r'}), init=False)
    cage_of_node: ad.Node=ad.CageOfNode()
    start_degrees: float=ad.dtfield(0, 'Start angle of sleeve')
    end_degrees: float=ad.dtfield(360, 'End angle of sleeve')
    keyway_start_degrees: float=ad.dtfield(0, 'Start angle of keyway')
    keyway_end_degrees: float=ad.dtfield(0, 'End angle of keyway')
    linear_extrude_node: ad.Node=ad.dtfield(
            ad.ShapeNode(ad.LinearExtrude, 'h'), init=False)
    epsilon: float=0.01 
     
    EXAMPLE_SHAPE_ARGS=ad.args(as_cage=False, h=10, fn=16, 
                               start_degrees=20,
                               keyway_start_degrees=20,
                               keyway_end_degrees=80, 
                               end_degrees=330)
    EXAMPLE_ANCHORS=(ad.surface_args('surface', 0),
                     ad.surface_args('inner_surface', 0),)

    def build(self) -> ad.Maker:

        assert self.outside_r > self.inside_r, (
            f'Inside radius ({self.inside_r}) must be smaller than outside ({self.outside_r}')
        maker = self.cage_of_node(
                self.outside_cyl_cage_node(), cage_name='outer').at('centre')
        
        maker.add(self.cage_of_node(
                self.inside_cyl_cage_node(
                    h=self.h + self.epsilon), cage_name='inner')
                    .colour((1, 0, 0, 0.4)).at('centre'))
        
        to_end_angle = self.end_degrees - self.start_degrees
        keyway_to_end_angle = self.end_degrees - self.keyway_end_degrees
        keyway_start_angle = self.keyway_start_degrees - self.start_degrees
        
        inner_p = ad.GVector((self.inside_r, 0, 0))
        end_keyway_p = ad.rotZ(self.keyway_end_degrees - self.start_degrees) * inner_p

        path = (ad.PathBuilder()
                .move((self.outside_r, 0))
                .line((self.inside_r, 0), 'start_flat')
                .arc_centre_sweep((0, 0), keyway_start_angle, name='inside_arc_start')
                .line(end_keyway_p.A2, name='keyway')
                .arc_centre_sweep((0, 0), keyway_to_end_angle, name='inside_arc_end')
                .stroke(self.outside_r - self.inside_r, -90, name='end_flat')
                .arc_points_radius(
                        (self.outside_r, 0), 
                        self.outside_r,
                        to_end_angle,
                        name='outside_arc')
                .build())
        
        sleeve_shape = self.linear_extrude_node(path=path)
        
        maker.add_at(sleeve_shape.solid('sleeve')
                     .at('outside_arc', 1, post=ad.ROTX_270), 
                     'surface', degrees=self.start_degrees, rh=1,
                     post=ad.ROTX_90)
        return maker

    @ad.anchor('outer surface anchor')
    def surface(self, *args, **kwds):
        '''Inner surface anchor with corrected Z points away from surface.'''
        return ad.rotZ(-self.start_degrees) \
                * self.maker.at('outer', 'surface', *args, **kwds)


    @ad.anchor('inner surface anchor')
    def inner_surface(self, *args, **kwds):
        '''Inner surface anchor with corrected Z points away from surface.'''
        return ad.rotZ(-self.start_degrees) \
                * self.maker.at('inner', 'surface', *args, **kwds) * ad.ROTX_180




# Uncomment the line below to default to writing OpenSCAD files
# when anchorscad_main is run with no --write or --no-write options.
MAIN_DEFAULT=ad.ModuleDefault(True)

if __name__ == "__main__":
    ad.anchorscad_main()