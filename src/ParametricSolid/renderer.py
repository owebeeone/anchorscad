'''
Created on 4 Jan 2021

@author: gianni
'''

import copy
from dataclasses import dataclass
from pygments.lexers import graph

from ParametricSolid import core, graph_model
from ParametricSolid import linear as l
import pythonopenscad as posc


class EmptyRenderStack(core.CoreEception):
    '''Before adding items to renderer a renderer.push must be called.'''
    
class UnpoppedItemsOnRenderStack(core.CoreEception):
    '''Before closing the renderer, all pushed frames must be pop()ed..'''
    
class PopCalledTooManyTimes(core.CoreEception):
    '''The render stack ran out of elements to pop..'''

HEAD_CONTAINER=1
SOLID_CONTAINER=2
HOLE_CONTAINER=3

class Container():
    def __init__(self, mode, model, shape_name):
        self.mode = mode
        self.model = model
        self.shape_name = shape_name
        self.containers = {}
        
    def _get_or_create_container(self, container_id):
        if container_id in self.containers:
            return self.containers[container_id]
        result = []
        self.containers[container_id] = result
        return result
        
        
    def _get_container(self, container_id):
        return self.containers.get(container_id, None)
    
    def _apply_name(self, obj):
        if self.shape_name:
            for o in obj:
                o.setMetadataName(self.shape_name)

    def add_solid(self, *obj):
        container = self._get_or_create_container(SOLID_CONTAINER)
        self._apply_name(obj)
        container.extend(obj)
        
    def add_hole(self, *obj):
        container = self._get_or_create_container(HOLE_CONTAINER)
        self._apply_name(obj)
        container.extend(obj)
        
    def add_head(self, *obj):
        container = self._get_or_create_container(HEAD_CONTAINER)
        self._apply_name(obj)
        container.extend(obj)
        
    def _combine_solids_and_holes(self):
        holes = self._get_container(HOLE_CONTAINER)
        solids = self._get_container(SOLID_CONTAINER)
        
        force_container = self.mode.has_operator_container or True
        
        if holes:
            if not solids:
                solid_obj = self.createNamedModeContainer(
                    '_combine_solids_and_holes')
            elif len(solids) == 1 and not force_container:
                solid_obj = solids[0]
            else:
                solid_obj = self.createNamedModeContainer(
                    '_combine_solids_and_holes')(*solids)
            
            result = self.model.Difference()(solid_obj, *holes)
            result.setMetadataName('_combine_solids_and_holes')
            return [result]
        
        # No holes.
        if solids:
            if force_container:
                return [self.createNamedModeContainer(
                    '_combine_solids_and_holes')(*solids)]
            else:
                return solids
        return []
    
    def _combine_heads(self, heads):
        
        top_head = None
        last_head = None
        if heads:
            top_head = heads[0]
            last_head = heads[-1]
            for i in range(len(heads)-1):
                heads[i].append(heads[i + 1])
                
        return top_head, last_head
    
    def build_combine(self):
        '''Combines solids and holes if any and returns the representative list of objects.'''
        top_head, last_head = self._combine_heads(heads=self._get_container(HEAD_CONTAINER))

        if not top_head:
            return self._combine_solids_and_holes()
        
        last_head.append(*self._combine_solids_and_holes())
        return [top_head]
    
    def build_composite(self):
        '''Returns a list of solids and holes.'''
        
        holes = self._get_or_create_container(HOLE_CONTAINER)
        solids = self._get_or_create_container(SOLID_CONTAINER)    
        
        head_copies = [None, None]
        
        heads = self._get_container(HEAD_CONTAINER)
        if heads:
            if holes and solids:
                head_copies[0] = self._combine_heads(copy.deepcopy(heads))
                head_copies[0][1].append(*solids)
                head_copies[1] = self._combine_heads(heads)
                head_copies[1][1].append(*holes)
            elif holes:
                head_copies[1] = self._combine_heads(heads)
                head_copies[1][1].append(*holes)
            elif solids:
                head_copies[0] = self._combine_heads(heads)
                head_copies[0][1].append(*solids)
            else:
                return [], []
   
            return [
                    head_copies[0][0] 
                      if head_copies[0] 
                      else self.createNamedUnion('build_composite')],  [
                    head_copies[1][0] 
                      if head_copies[1] 
                      else self.createNamedUnion('build_composite')]
        else:
            return solids, holes
        
    def createNamedUnion(self, name):
        result = self.model.Union()
        result.setMetadataName(f'{self.shape_name} : {name}')
        return result
    
    def createNamedModeContainer(self, name):
        result = self.mode.make_container(self.model)
        result.setMetadataName(f'{self.shape_name} : {name}')
        return result
    
    def get_or_create_first_head(self):
        heads = self._get_or_create_container(HEAD_CONTAINER)
        if not heads:
            head = self.createNamedUnion('get_or_create_first_head')
            self.add_head(head)
        return heads[0]
    
    def close(self, mode, parent_container):
        if mode.mode == core.ModeShapeFrame.SOLID.mode:
            self.propagate(mode, parent_container)
        elif mode.mode == core.ModeShapeFrame.HOLE.mode:
            holes = self.build_combine()
            parent_container.add_hole(*holes)
        elif mode.mode == core.ModeShapeFrame.COMPOSITE.mode:
            solids, holes = self.build_composite()
            parent_container.add_solid(*solids)
            parent_container.add_hole(*holes)
        elif mode.mode == core.ModeShapeFrame.CAGE.mode:
            pass
        elif mode.mode == core.ModeShapeFrame.INTERSECT.mode:
            self.propagate(mode, parent_container)
        elif mode.mode == core.ModeShapeFrame.HULL.mode:
            self.propagate(mode, parent_container)
        elif mode.mode == core.ModeShapeFrame.MINKOWSKI.mode:
            self.propagate(mode, parent_container)
        
    def propagate(self, mode, parent_container):
        solids = self.build_combine()
        parent_container.add_solid(*solids)
        
            

@dataclass(frozen=True)
class ContextEntry():
    
    container: Container
    mode: core.ModeShapeFrame
    reference_frame: l.GMatrix
    attributes: core.ModelAttributes = None
    graph_node: object = None

class Context():

    def __init__(self, renderer):
        self.stack = [] # A stack of ContextEntry
        self.renderer = renderer
        self.model = renderer.model
        
    def push(self, 
             mode: core.ModeShapeFrame, 
             reference_frame: l.GMatrix, 
             attributes: core.ModelAttributes,
             shape_name: str=None,
             graph_node: object=None):
        container = Container(
            mode, model=self.model, shape_name=shape_name)
        last_attrs = self.get_last_attributes()
        merged_attrs = last_attrs.merge(attributes)
        diff_attrs = last_attrs.diff(merged_attrs)
        
        entry = ContextEntry(container, mode, reference_frame, merged_attrs, graph_node)

        self.stack.append(entry)
        
        if reference_frame:
            if reference_frame != l.IDENTITY:
                container.add_head(self.model.Multmatrix(reference_frame.m.A))
            
        if diff_attrs.colour:
            container.add_head(self.model.Color(c=diff_attrs.colour.value))
            
        if diff_attrs.disable:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.DISABLE)
        if diff_attrs.show_only:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.SHOW_ONLY)
        if diff_attrs.debug:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.DEBUG)
        if diff_attrs.transparent:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.TRANSPARENT)
        
            
    def pop(self):
        last = self.stack[-1]
        del self.stack[-1]
        if self.stack:
            last.container.close(last.mode, self.stack[-1].container)
            return None
        else:
            objs = last.container.build_combine()
            if not objs:
                return self.createNamedUnion(last.mode, 'pop')
            if len(objs) > 1:
                return self.createNamedUnion(last.mode, 'pop').append(*objs)
            return objs[0]
            
    def get_current_graph_node(self):
        if self.stack:
            return self.stack[-1].graph_node
        return None
        
    def createNamedUnion(self, mode, name):
        result = self.model.Union()
        result.setMetadataName(name)
        return result
    
    def get_last_attributes(self):
        if self.stack:
            attrs = self.stack[-1].attributes
            if not attrs is None:
                return attrs
        return core.EMPTY_ATTRS
        
    
    def get_last_container(self):
        if not self.stack:
            raise EmptyRenderStack('renderer stack is empty.')
        return self.stack[-1].container
        
class Renderer():
    '''Provides renderer machinery for ParametricSolid. Renders to PythonOpenScad models.'''
    model = posc
    
    def __init__(self, initial_frame=None, initial_attrs=None):
        self.context = Context(self)
        self.result = None
        self.graph = graph_model.DirectedGraph()
        root_node = self.graph.new_node('root') 
        # Push an item on the stack that will collect the final objects.
        self.context.push(core.ModeShapeFrame.SOLID, initial_frame, initial_attrs, None, root_node)
        
    def close(self):
        count = len(self.context.stack)
        if count != 1:
            raise UnpoppedItemsOnRenderStack(
                f'{count - 1} items remain on the render stack.')
        self.result = self.context.pop()
        self.context = Context(self) # Prepare for the next object just in case.
        return self.result

    def push(self, mode, reference_frame, attributes, shape_name, clazz_name=None):
        graph_node = self.graph.new_node(shape_name, clazz_name)
        self.graph.add_edge(self.context.get_current_graph_node(), graph_node)
        self.context.push(mode, reference_frame, attributes, shape_name, graph_node)

    def pop(self):
        self.context.pop()
        # The last item on the stack is for office us only.
        if len(self.context.stack) < 1:
            raise PopCalledTooManyTimes('pop() called more times than push() - stack underrun.')
        
    def get_current_attributes(self):
        return self.context.get_last_attributes()
        
    def add(self, *obj):
        self.context.get_last_container().add_solid(*obj)


def render_graph(shape, initial_frame=None, initial_attrs=None):
    '''Renders a shape and returns the model root object.'''
    renderer = Renderer(initial_frame, initial_attrs)
    shape.render(renderer)
    return renderer.close(), renderer.graph

def render(shape, initial_frame=None, initial_attrs=None):
    '''Renders a shape and returns the model root object.'''
    return render_graph(shape, initial_frame, initial_attrs)[0]
