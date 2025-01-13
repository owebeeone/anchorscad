'''
Created on 31 Dec 2021

@author: gianni
'''
import unittest

import anchorscad.graph_model as graph_model
import pathlib as pl


class TestDirectedGraph(unittest.TestCase):

    def setUp(self):
        
        graph_model._num = 0  # reset the node counter for hatchling runs
        dg = graph_model.DirectedGraph()
        
        na = dg.new_node('a')
        nb = dg.new_node('b')
        nc = dg.new_node('c')
        nd = dg.new_node('d')
        
        dg.add_edge(na, nb)
        dg.add_edge(na, nc)
        dg.add_edge(nb, nd)
        dg.add_edge(nc, nd)
        
        self.dg = dg
        
        self.filename = 'test_graph.dot'
        
        self.unlink_file(self.filename)
        self.unlink_file(self.filename + '.svg')
    
    def unlink_file(self, filename):
        try: 
            pl.Path(filename).unlink()
        except:
            pass #ignoring if file does not exist

    def test_simple_graph(self):
        
        self.assertEqual(self.dg.dump('foo'), 
                'digraph foo {\n'
                '    a_1 [label="a"];\n'
                '    b_2 [label="b"];\n'
                '    c_3 [label="c"];\n'
                '    d_4 [label="d"];\n'
                '    a_1 -> b_2;\n'
                '    a_1 -> c_3;\n'
                '    b_2 -> d_4;\n'
                '    c_3 -> d_4;\n'
                '}\n')
        
    def test_write_svg(self):
        
        self.dg.write_svg(self.filename)
        self.assertTrue(pl.Path(self.filename).resolve().is_file())  
        self.assertTrue(pl.Path(self.filename + '.svg').resolve().is_file())        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    