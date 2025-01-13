'''
A quilt pattern of concentric 'eye' shapes.


'''

import anchorscad as ad
import numpy as np
import anchorscad_models.quilting.patterns.pat_utils as pu



@ad.datatree
class ConcentricEyes(ad.CompositeShape):
    v: float = ad.dtfield(60, 'Vertical spacing')
    vt: np.array = ad.dtfield(default_factory=lambda : 1.9 * np.array((5, 40)), doc='Vertical spline vector')
    h: float = ad.dtfield(25, 'Horizontal spacing')
    ht: np.array = ad.dtfield(default_factory=lambda : np.array((0, 40)), doc='Horizontal spline vector')
    ch: float = ad.dtfield(29, 'centre horizontal dimension')
    cv: float = ad.dtfield(65, 'centre vertical dimension')
    huo: float = ad.dtfield(-3, 'Upper horizontal offset')
    hlo: float = ad.dtfield(7, 'Lower horizontal offset')
    
    n: int = ad.dtfield(3, 'Number of concentric shapes')
    last_control_point: np.array = ad.dtfield(None, 'The last control point', init=False)
    
    def cp_scale_factor(self, i) -> float:
        return 0.1 + 0.7 * (i / self.n)
    
    def v_pos(self, i: int, side: bool, spin_dir: bool, size_offset, sequence_num) -> float:
        s = 1 if side else -1
        sd = 1 if spin_dir else -1
        cp_scale = self.cp_scale_factor(i)
        factor = size_offset + sequence_num
        return [
            cp_scale * self.vt * np.array((s, -sd)),
            np.array(
                ((0, (self.v * factor + self.cv) * s))),
            cp_scale * self.vt * np.array((-s, -sd))]
    
    def h_pos(self, i: int, side: bool, spin_dir: bool, size_offset, sequence_num) -> float:
        s = 1 if side else -1
        sd = 1 if spin_dir else -1
        cp_scale = 1 + self.cp_scale_factor(i)
        factor = size_offset + sequence_num
        return [
            cp_scale * self.ht * np.array((-s, -sd)), 
            np.array(
                ((self.h * factor + self.ch) * s, -s)), 
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
    
    def create_sequence(self, sequence, size_offset, seq_factor) -> tuple:
        plots = []
        sequence_num = self.n * len(sequence)
        for i in self.range_for():
            for func, side, spin_dir, offs in sequence:
                entry = func(i, side, spin_dir, size_offset, sequence_num * seq_factor)
                entry.append(offs)
                plots.append(entry)
                sequence_num -= 1
                
        return plots
    
    
    def build(self) -> ad.Path:
        
        builder = ad.PathBuilder(multi=True)
        
        sequence = ((self.h_pos, True, True, np.array((0, 0))), 
                    (self.v_pos, False, False, np.array((self.hlo - 6, 0))), 
                    (self.h_pos, False, False, np.array((0, 0))),
                    (self.v_pos, True, True, np.array((self.huo + 0, 0))))
        
        sequencex = ((self.v_pos, False, False, np.array((self.hlo + 1, 0))), 
                    (self.h_pos, False, False, np.array((0, 0))),
                    (self.v_pos, True, True, np.array((self.huo + 10, 0))),
                    (self.h_pos, True, True, np.array((0, 0))), 
                    )
        
        sequence2 = ((self.h_pos, False, True, np.array((0, 0))), 
                    (self.v_pos, False,  False, np.array((self.hlo, 0))), 
                    (self.h_pos, True, False, np.array((0, 0))),
                    (self.v_pos, True, True, np.array((self.huo, 0))))
        

        func, side, spin_dir, offs = sequence[3]
        pos, tangent_to, tangent_from = func(self.n, side, spin_dir, 0, 0.3)
        self.last_control_point = pos + tangent_to + offs
        
        plots = self.create_sequence(sequence, .9, 0.25)
        
        self.v += 6
        plotsx = self.create_sequence(sequencex, 1.33, 0.25)
        plots2 = self.create_sequence(sequence2, 1, 0.25)
        
        rev_plots2 = list([x[2], x[1], x[0], x[3]] for x in reversed(plots2))
        rev_plots = list([x[2], x[1], x[0], x[3]] for x in reversed(plots))
        rev_plotsx = list([x[2], x[1], x[0], x[3]] for x in reversed(plotsx))
        
        x_offs = np.array((120, 0))
        y_offs = np.array((0, 310))
        y_offs2 = np.array((0, 305))
        #y_offs2 = y_offs
        # x_offs = np.array((140, 0))
        # y_offs = np.array((0, 300))
        # y_offs2 = np.array((0, 290))
        
        render_plots = plots[:-1][3:]
        render_rev_plots = rev_plotsx[:-4]
        
        render_plots[-1][0] = (x_offs * 0 + y_offs * 0.5) * 0.61
        #render_plots[-1][2] = render_plots[-1][0] * np.array((1, 0.9)) * -0.1
        render_rev_plots[0][2] = (x_offs * 0. + -y_offs * 0.5) *.7

        for y in range(2):
            start_v, start_pos, start_v2, x = render_rev_plots[-1]
            pos = start_pos - x_offs + y_offs + 2 * -y * y_offs2
            self.last_control_point = pos + start_v
            builder.move(start_pos - x_offs + y_offs + + 2 * -y * y_offs2)
            for x in range(5):
                self.build_forward(builder, render_plots, 2 * x * x_offs + 2 * -y * y_offs2)
                self.build_forward(builder, render_rev_plots, (2 * x + 1) * x_offs + (2 * -y) * y_offs2 + y_offs)

        path = builder.build()
        
        return path
    
    
if __name__ == '__main__':
    pu.main(ConcentricEyes().build())