'''
Created on 31 Dec 2021

@author: gianni
'''
import html
from dataclasses import dataclass, field
import re

try:
    import graphviz
    _graphviz_imported = True
except:  # noqa: E722
    _graphviz_imported = False
    
_num = 0

def _num_gen():
    global _num
    _num += 1
    return str(_num)
    

@dataclass
class Node:
    label: str
    clazz_name: str=None
    ident: str=field(default_factory=_num_gen)
    parent: object=None
    
    def __repr__(self):
        return f'{self.get_id()} [label="{self.get_label()}"];'
    
    def get_label(self):
        lbl = str(self.label)
        return re.escape(lbl)
    
    def get_clazz_name(self):
        if not self.clazz_name:
            return None
        return re.escape(self.clazz_name)
    
    def get_id(self):
        label = self.label
        if isinstance(label, tuple):
            label = label[0]
        if isinstance(label, str) and label.isidentifier():
            return f'{label}_{self.ident}'
        return self.ident
    
    def set_parent(self, parent):
        self.parent = parent
        
    def get_path(self):
        if not self.parent:
            return ()
        return self.parent.get_path() + (self.label,)
    
    def get_path_str(self):
        return re.escape(str(self.get_path()))
        
@dataclass
class Edge:
    start: Node
    end: Node
        
    def __repr__(self):
        return f'{self.start.get_id()} -> {self.end.get_id()};'
    
    
@dataclass
class DirectedGraph:
    '''
    classdocs
    '''

    nodes: list=field(default_factory=lambda:list())
    edges: list=field(default_factory=lambda:list())
    
    def new_node(self, label, clazz_name=None) -> Node:
        node = Node(label, clazz_name)
        self.nodes.append(node)
        return node
    
    def add_edge(self, start, end):
        self.edges.append(Edge(start, end))
        end.set_parent(start)
    
    def get_last_node(self):
        return self.nodes[-1]
        
    def __repr__(self):
        return self.dump('D')
        
    def dump(self, name):
        nodes_str = '\n'.join(f'    {n}' for n in self.nodes)
        edges_str = '\n'.join(f'    {e}' for e in self.edges)
        return '\n'.join((f'digraph {name} {{', 
                          nodes_str,
                          edges_str,
                          '}\n')) 
    
    def write(self, filename, name='D'):
        '''Writes the GraphViz syntax to the given file name.
        Args:
            filename: The filename to create.
        '''
        with open(filename, 'w') as fp:
            fp.write(self.dump(name))  
            
    def write_svg(self, filename, name='D'):  
        '''Writes an SVG and DOT files to the given file name.
        Args:
            filename: The DOT filename to create, with SVG created
            by appending ".svg" to this filename.
        '''
        if not _graphviz_imported:
            raise Exception('Unable to generate SVG file. '
                            'GraphViz must be installed. '
                            'To install, run "pip3 install graphviz" in shell. ')
        dot = graphviz.Digraph(
            name=name,
            graph_attr=(('rankdir', 'LR'),))
        for node in self.nodes:
            label = node.get_label()
            tip = node.get_clazz_name()
            tipd = {'tooltip': tip} if tip else {}
            escape_path = html.escape(node.get_path_str())
            url=f'javascript:s=&quot;{escape_path}\\n{tip}&quot;; console.log(s); alert(s);'
            dot.node(node.get_id(), label, href=url, **tipd)
        for edge in self.edges:
            dot.edge(edge.start.get_id(), edge.end.get_id())
        
        dot.render(filename, format='svg')
    
    
    
    
    

