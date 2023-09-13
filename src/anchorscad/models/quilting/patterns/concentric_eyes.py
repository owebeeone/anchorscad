'''
A quilt pattern of concentric 'eye' shapes.


'''

import anchorscad as ad
import numpy as np
import anchorscad.models.quilting.patterns.pat_utils as pu



@ad.datatree
class ConcentricEyes(ad.CompositeShape):
    v: float = ad.dtfield(60, 'Vertical spacing')
    vt: np.array = ad.dtfield(default_factory=lambda : 1.9 * np.array((5, 40)), doc='Vertical spline vector')
    h: float = ad.dtfield(25, 'Horizontal spacing')
    ht: np.array = ad.dtfield(default_factory=lambda : np.array((0, 40)), doc='Horizontal spline vector')
    ch: float = ad.dtfield(30, 'centre horizontal dimension')
    cv: float = ad.dtfield(65, 'centre vertical dimension')
    huo: float = ad.dtfield(-6, 'Upper horizontal offset')
    hlo: float = ad.dtfield(-4, 'Lower horizontal offset')
    
    n: int = ad.dtfield(3, 'Number of concentric shapes')
    last_control_point: np.array = ad.dtfield(None, 'The last control point', init=False)
    
    def cp_scae_factor(self, i) -> float:
        return 0.1 + 0.7 * (i / self.n)
    
    def v_pos(self, i: int, side: bool, spin_dir: bool) -> float:
        s = 1 if side else -1
        sd = 1 if spin_dir else -1
        cp_scale = self.cp_scae_factor(i)
        return [
            cp_scale * self.vt * np.array((s, -sd)),
            np.array(
                ((0, (self.v * i + self.cv) * s))),
            cp_scale * self.vt * np.array((-s, -sd))]
    
    def h_pos(self, i: int, side: bool, spin_dir: bool) -> float:
        s = 1 if side else -1
        sd = 1 if spin_dir else -1
        cp_scale = 1 + self.cp_scae_factor(i)
        return [
            cp_scale * self.ht * np.array((-s, -sd)), 
            np.array(
                ((self.h * i + self.ch) * s, -s)), 
            cp_scale * self.ht * np.array((s, sd))]
    
    def range_for(self) -> range:
        return range(self.n, -1, -1)
    
    def range_for_rev(self) -> range:
        return range(self.n)
    
    def build_reverse(self, builder: ad.PathBuilder, sequence: tuple, trans: np.array) -> None:
        for i in self.range_for_rev():
            for func, side, spin_dir, offs in sequence:
                pos, tangent_from, tangent_to = func(i, side, spin_dir)
                pos = pos + offs + trans
                builder.line(pos + tangent_from).line(pos).line(pos + tangent_to)
                # if not self.last_control_point is None:
                #     builder.spline(
                #         (self.last_control_point, pos + tangent_from, pos))
                self.last_control_point = pos + tangent_to
        
        path = builder.build()
        
        return path
    
    
    def build_reverse(self, builder: ad.PathBuilder, plots: tuple, trans: np.array) -> None:

        for tangent_from, pos, tangent_to, offs in plots:
            pos = pos + offs + trans
            #builder.line(pos + tangent_from).line(pos).line(pos + tangent_to)
            if not self.last_control_point is None:
                builder.spline(
                    (self.last_control_point, pos + tangent_from, pos))
            self.last_control_point = pos + tangent_to
    
    def build_forward(self, builder: ad.PathBuilder, plots: tuple, trans: np.array) -> None:

        for tangent_to, pos, tangent_from, offs in plots:
            pos = pos + offs + trans
            #builder.line(pos + tangent_from).line(pos).line(pos + tangent_to)
            if not self.last_control_point is None:
                builder.spline(
                    (self.last_control_point, pos + tangent_from, pos))
            self.last_control_point = pos + tangent_to
        
        path = builder.build()
        
        return path
    
    def create_sequence(self, sequence) -> tuple:
        plots = []
        for i in self.range_for():
            for func, side, spin_dir, offs in sequence:
                entry = func(i, side, spin_dir)
                entry.append(offs)
                plots.append(entry)
                
        return plots
    
    
    def build(self) -> ad.Path:
        
        builder = ad.PathBuilder(multi=True)
        
        sequence = ((self.h_pos, True, True, np.array((0, 0))), 
                    (self.v_pos, False, False, np.array((self.hlo, 0))), 
                    (self.h_pos, False, False, np.array((0, 0))),
                    (self.v_pos, True, True, np.array((self.huo, 0))))
        
        sequence2 = ((self.h_pos, False, True, np.array((0, 0))), 
                    (self.v_pos, False,  False, np.array((self.hlo, 0))), 
                    (self.h_pos, True, False, np.array((0, 0))),
                    (self.v_pos, True, True, np.array((self.huo, 0))))
        

        func, side, spin_dir, offs = sequence[3]
        pos, tangent_to, tangent_from = func(self.n, side, spin_dir)
        self.last_control_point = pos + tangent_to + offs
        plots = self.create_sequence(sequence)
        plots2 = self.create_sequence(sequence2)
        
        rev_plots2 = list([x[2], x[1], x[0], x[3]] for x in reversed(plots2))
        rev_plots = list([x[2], x[1], x[0], x[3]] for x in reversed(plots))
        
        x_offs = np.array((105, 0))
        y_offs = np.array((0, 270))
        y_offs2 = np.array((0, 260))
        
        render_plots = plots[3:]
        render_rev_plots = rev_plots[:-1]
        
        #render_plots[-1][0] = (x_offs + y_offs * 0.7) * 0.7
        render_plots[-1][0] = (x_offs + y_offs * 0.5) * 0.7
        render_plots[-1][2] = render_plots[-1][0] * np.array((1, 0.9)) * -0.1
        render_rev_plots[0][2] = (x_offs * 1.1 + -y_offs * 0.7) *.4
        
        # start_v, start_pos, start_v2, x = render_rev_plots[-1]
        # pos = start_pos - x_offs + y_offs
        # self.last_control_point = pos + start_v
        # builder.move(start_pos - x_offs + y_offs)
        for y in range(3):
            start_v, start_pos, start_v2, x = render_rev_plots[-1]
            pos = start_pos - x_offs + y_offs + 2 * -y * y_offs2
            self.last_control_point = pos + start_v
            builder.move(start_pos - x_offs + y_offs + + 2 * -y * y_offs2)
            for x in range(5):
                self.build_forward(builder, render_plots, 2 * x * x_offs + 2 * -y * y_offs2)
                self.build_forward(builder, render_rev_plots, (2 * x + 1) * x_offs + (2 * -y) * y_offs2 + y_offs)
        # self.build_forward(builder, render_plots, np.array((0, 0)))
        # self.build_forward(builder, rev_plots, x_offs + y_offs)
        # self.build_forward(builder, render_plots, 2 * x_offs)
        # self.build_forward(builder, rev_plots, 3 * x_offs + y_offs)
        #self.build_reverse(builder, reversed(sequence), np.array((100, 200)))

        path = builder.build()
        
        return path
    
    
if __name__ == '__main__':
    pu.main(ConcentricEyes().build())