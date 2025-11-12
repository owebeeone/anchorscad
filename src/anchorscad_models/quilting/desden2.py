import anchorscad as ad

INCH=25.4

@ad.datatree
class DresdenKitePathBuilder:
    
    n_points: int=ad.dtfield(16, 'Number of points')
    small_r: float=ad.dtfield(120, 'Radius of the small circle')
    small_r2: float=ad.dtfield(150, 'Radius of the inner small circle')
    large_r2: float=ad.dtfield(290, 'Radius of the inner large circle')
    large_r: float=ad.dtfield(340, 'Radius of the large circle')
    margin: float=ad.dtfield(0.25 * INCH, 'Margin')
    
    def build(self) -> ad.Maker:
        
        angle = ad.angle(360 / (2 * self.n_points))
        startr = ad.GVector((self.small_r, 0, 0))
        startr2 = ad.GVector((self.small_r2, 0, 0))
        endr2 = ad.GVector((self.large_r2, 0, 0))
        endr = ad.GVector((self.large_r, 0, 0))
        
        rot_up = angle.rotZ
        rot_down = (-angle).rotZ
        
        start_p = startr.A2
        start_upper_p = (rot_up * startr2).A2
        end_upper_p = (rot_up * endr2).A2
        end_p = endr.A2
        end_lower_p = (rot_down * endr2).A2
        small_lower_p = (rot_down * startr2).A2
        
    
        builder = ad.PathBuilder(
                path_modifier=ad.PathModifier(
                    offset=self.margin, 
                    join_type=ad.PathModifier.OFFSET_MITRE))
        with builder.construction() as cb:
            cb.move(start_p)
            cb.line((start_p + end_p) / 2, 'left')
            cb.line(end_p, 'right')
        
        path = (
            builder
            .move(start_p)
            .line(start_upper_p, 'small_upper')
            .line(end_upper_p, 'upper')
            .line(end_p, 'end_upper')
            .line(end_lower_p, 'end_lower')
            .line(small_lower_p, 'lower')
            .line(start_p, 'small_lower')
            .build()
        )

        return path



@ad.shape
@ad.datatree
class DresdenKite(ad.CompositeShape):
    path_node: ad.ShapeNode[DresdenKitePathBuilder] = ad.ShapeNode(DresdenKitePathBuilder)
    outer_path: ad.Path = ad.dtfield(self_default=lambda s: s.path_node().build())
    
    outer_h: float = ad.dtfield(3, 'Thickness')
    outer_extrude_node: ad.ShapeNode[ad.LinearExtrude] = ad.ShapeNode(ad.LinearExtrude, prefix='outer_')

    wall_size: float = ad.dtfield(15, 'Wall size')
    inner_path: ad.Path = ad.dtfield(self_default=lambda s: s.path_node(margin=-s.wall_size).build())
    inner_h: float = ad.dtfield(self_default=lambda s: s.outer_h + 2 * s.epsilon)
    inner_extrude_node: ad.ShapeNode[ad.LinearExtrude] = ad.ShapeNode(ad.LinearExtrude, prefix='inner_')
    epsilon: float = ad.dtfield(0.1, 'Epsilon')
    
    def build(self) -> ad.Maker:
        
        outer_shape = self.outer_extrude_node()
        maker = outer_shape.solid("dresden").at('right', 0, apply_offset=False)
        
        #inner_shape = self.inner_extrude_node()
        #maker.add_at(inner_shape.hole("inner").at('right', 0, apply_offset=False), post=ad.tranY(-self.epsilon))
        return maker
    

MAIN_DEFAULT=ad.ModuleDefault(all=True)    

if __name__ == '__main__':
    ad.anchorscad_main(False)