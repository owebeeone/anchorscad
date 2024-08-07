'''
Created on 4 Jan 2021

@author: gianni
'''

import copy
from collections import defaultdict
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json, config

from anchorscad import core, graph_model
from anchorscad import linear as l
import pythonopenscad as posc
from typing import Any, Hashable, Dict, List, Tuple, Set, Optional


class EmptyRenderStack(core.CoreEception):
    '''Before adding items to renderer a renderer.push must be called.'''
    
class UnpoppedItemsOnRenderStack(core.CoreEception):
    '''Before closing the renderer, all pushed frames must be pop()ed..'''
    
class PopCalledTooManyTimes(core.CoreEception):
    '''The render stack ran out of elements to pop..'''


@dataclass
class PartMaterialMapInstance:
    path: 'ShapePath'
    from_material: core.Material
    to_material: core.Material
    material_map: core.MaterialMap
    part: core.Part = None


@dataclass
class MaterialStats:
    '''A class that keeps track of the materials and parts used and where.'''
    material_map_list: List[PartMaterialMapInstance] = field(default_factory=list)
    
    # The final list of materials actually used in the model.
    model_materials: Set[core.Material] = field(default_factory=set)
    
    # The final list of parts actually used in the model.
    model_parts: Set[core.Part] = field(default_factory=set)
    
    # The final list of part-materials actually used in the model.
    model_part_martials: Set['PartMaterial'] = field(default_factory=dict)
    
    def add(self, 
            path, 
            from_material: core.Material, 
            to_material: core.Material, 
            material_map: core.MaterialMap, 
            part: core.Part):
        self.material_map_list.append(PartMaterialMapInstance(path, from_material, to_material, material_map, part))
        if part:
            self.model_parts.add(part)
    
    def has_material(self):
        '''Returns True if there is one ore more non None material in the model.'''
        if len(self.model_materials) > 1:
            return True
        if not self.model_materials:
            return False
        return None not in self.model_materials

    def has_part(self):
        '''Returns True if there is one or more non None part in the model.'''
        return bool(self.model_parts)
    
    def add_part_material(self, part_material: 'PartMaterial'):
        '''Adds a part-material to the model.'''
        self.model_part_martials.add(part_material)
        self.model_parts.add(part_material.part)
        self.model_materials.add(part_material.material)


@dataclass(frozen=True)
class PartMaterial:
    '''A part and material combination.'''
    part: Optional[core.Part]
    material: Optional[core.Material]

    def comparePriority(self, other: 'PartMaterial') -> int:
        '''Compares the priority of this part-material with another.
        A None part or material is considered to have the lowest priority.
        '''
        if self.part is None:
            if other.part is None:
                return 0
            return -1
        if other.part is None:
            return 1
        if self.part.priority != other.part.priority:
            return self.part.priority - other.part.priority
        
        if self.material is None:
            if other.material is None:
                return 0
            return -1
        if other.material is None:
            return 1
        return self.material.priority - other.material.priority
    

@dataclass
class CombiningState:
    '''An intermediate state object containing part and material specific solids and holes.'''
    holes: List[Any] = field(default_factory=list)
    part_material_solid: List[Tuple[PartMaterial, List[Any]]] = field(default_factory=list)
    
    def __post_init__(self):
        assert isinstance(self.holes, list), 'Holes must be a list.'
        for part_material, solids in self.part_material_solid:
            assert isinstance(part_material, PartMaterial), 'part_material must be a PartMaterial.'
            assert solids is not None, 'Solids cannot be None.'
            assert isinstance(solids, list), 'Solids must be a list.'

    def set_holes(self, holes: List[Any]) -> None:
        self.holes = holes
        
    def has_holes(self) -> bool:
        return bool(self.holes)
        
    def add_part_material_solid(self, part_material: PartMaterial, *solids: Tuple[Any]) -> None:
        '''Adds a part, material and solid to the list of part material solids.'''
        self.part_material_solid.append((part_material, list(solids)))
        
    def flatten_solids(self) -> List[Any]:
        '''Returns a list of solids by removing all the part and material specifiers and returning the 
        flattened set of objects.'''
        if self.holes:
            raise Exception('Cannot convert to holes when there are holes.')
        
        # Flatten all the part_material_solid solids into a single list.
        solids = [solid for _, solids in self.part_material_solid for solid in solids]
        return solids
    
    def get_first_part_material(self) -> PartMaterial:
        '''Returns the first part and material in the part_material_solid list.'''
        if not self.part_material_solid:
            return None
        return self.part_material_solid[0][0]
    
    def has_one_or_no_parts_materials(self) -> bool:
        '''Returns True if there is only one part-material combination or none.'''
        return len(self.part_material_solid) <= 1
    
    def priority_ordered(self) -> List[Tuple[PartMaterial, List[Any]]]:
        '''Returns the part-material combinations ordered by priority.'''
        part_mat_dict = defaultdict(list)
        
        for part_material, solids in self.part_material_solid:
            part_mat_dict[part_material].extend(solids)
            
        part_mat_solids_list = list(part_mat_dict.items())
        list.sort(part_mat_solids_list, 
                  reverse=True, 
                  ????? need to fix this
                  key=lambda item: (
                      item[0][0].priority if item[0][0] else -float('inf'),
                      item[0][1].priority_sort_key() if item[0][1] else core.Material.default_priority_sort_key()
                  ))
        
        return [(part, material, solids) for (part, material), solids in part_mat_solids_list]
    
    def priority_cured(self, model) -> List[Tuple[PartMaterial, List[Any]]]:
        '''Returns a list of part_material_solids with the higher priority shapes removed from the
        lower priority shapes.'''
        part_mat_solids_list: List[Tuple[PartMaterial, List[Any]]] = self.priority_ordered()
        removal_list = []
        result = [part_mat_solids_list[0]]
        removal_next = list(result[0][2])
        removal_part_priority = result[0][0].priority if result[0][0] else -float('inf')
        removal_material_priority = result[0][1].priority if result[0][1] else core.DEFAULT_MATERIAL_PRIORITY
        for part_material, solids in part_mat_solids_list[1:]:
            if (part and part.priority != removal_part_priority) or (material.priority != removal_material_priority):
                removal_list = list(removal_next)
            
            if material.kind.physical:
                removal_next.extend(solids)
            
            if removal_list and material.kind.physical:
                if len(solids) > 1:
                    solids = [model.Union()(*solids)]
                solids = [model.Difference()(*solids, *removal_list)]
                solids[0].setMetadataName(f'priority_cured_{part}_{material}')
                
            result.append((part_material, solids))
                
        return result

@dataclass
class Container():
    '''A container for solids, holes and heads as the model is being rendered.'''
    mode: core._Mode
    model: Any
    shape_name: Hashable
    part_material_solids: Dict[PartMaterial, List[Any]] = field(default_factory=dict, init=False, repr=False)
    heads: List[Any] = field(default_factory=list, init=False, repr=False)
    holes: List[Any] = field(default_factory=list, init=False, repr=False)
    
        
    def _get_or_create_part_material_solid_container(self, part_material: PartMaterial):
        '''Returns the container for the given part and material, creating it if necessary.'''
        key = part_material
        if key in self.part_material_solids:
            return self.part_material_solids[key]
        result = []
        self.part_material_solids[key] = result
        return result    
        
    def _container_extend(self, part_material: PartMaterial, solids: List[Any]):
        '''Extends a part-material container with the given solids.'''
        if part_material in self.part_material_solids:
            self.part_material_solids[part_material].extend(solids)
        else:
            self.part_material_solids[part_material] = list(solids)
        
    def _extend_part_material_solids(self, part_material_solids: List[Tuple[PartMaterial, List[Any]]]):
        '''Extends the current part material solids with the given part material solids.'''
        for part_material, solids in part_material_solids:
            self._container_extend(part_material, solids)
    
    def _apply_name(self, obj: List[Any]):
        '''Applies the shape name to the given objects.'''
        if self.shape_name:
            for o in obj:
                o.setMetadataName(self.shape_name)
                    
    def _apply_combining_state(self, combining_state: CombiningState):
        '''Applies the combining state to this container.'''
        self._extend_part_material_solids(combining_state.part_material_solid)
        self.holes.extend(combining_state.holes)

    def add_solid(self, *obj, part: Optional[core.Part], material: Optional[core.Material]):
        container = self._get_or_create_part_material_solid_container(
            PartMaterial(part, material))
        self._apply_name(obj)
        container.extend(obj)
        
    def add_hole(self, *obj):
        container = self.holes
        self._apply_name(obj)
        container.extend(obj)
        
    def add_head(self, *obj):
        container = self.heads
        self._apply_name(obj)
        container.extend(obj)
        
    def _combine_solids_and_holes(self) -> CombiningState:
        '''Combines solids and holes into a single list of solids.
        Heads and holes (if any) are applied to each solid and the new list of solids is
        provided as the [CombiningState] result.'''
        holes = self.holes
        part_material_solid = list(self.part_material_solids.items()) 
        
        force_container = self.mode.has_operator_container or True
        
        # Combining solids and holes causes the result to have no holes.
        result = CombiningState()
        
        if not part_material_solid:
            # No solids, hence nothing to combine. Holes are "consumed" here since
            # turning only holes into a solid is a no-op.
            return result
        
        while part_material_solid:
            
            part_material, solids = part_material_solid.pop()
            
            if not solids:
                continue  # Skip empty solids.
            
            try:
                len(solids)
            except:
                print(f'Error: solids is not a list: {solids}')
                solids = [solids]
            
            if len(solids) == 1 and not force_container:
                solid_obj = solids[0]
            else:
                solid_obj = self.createNamedModeContainer(
                    '_combine_solids_and_holes')(*solids)
                
            if holes:
                result_node = self.model.Difference()(solid_obj, *holes)
                result_node.setMetadataName('_combine_solids_and_holes')
            else:
                result_node = solid_obj
            result.add_part_material_solid(part_material, result_node)
        
        return result
    
    def _combine_heads(self, make_copy: bool=False) -> Tuple[Any, Any]:
        '''Combines heads into a single head chain but also provides the tail
        object so that solids or holes can be apppended.'''

        heads = copy.deepcopy(self.heads) if make_copy else self.heads
        
        top_head = None
        last_head = None
        if heads:
            top_head = heads[0]
            last_head = heads[-1]
            for i in range(len(heads)-1):
                heads[i].append(heads[i + 1])
                
        return top_head, last_head
    
    def build_combine(self) -> CombiningState:
        '''Combines solids and holes if any and returns the representative list of objects.'''

        result = self._combine_solids_and_holes()

        # If there are no heads, then we can return the combined solids and holes.
        if not self.heads:
            return result
        
        assert not result.has_holes(), 'There should be no holes at this point.'
        
        # There are heads, so we need to combine them with the combined solids and holes.
        result_part_material_solids = []
        part_material_solids = result.part_material_solid
        while part_material_solids:
            
            part, material, solids = part_material_solids.pop()
            
            top_head, last_head = self._combine_heads(make_copy=bool(part_material_solids))
            
            if isinstance(last_head, self.model.Difference):
                print('last_head is a difference')

            last_head.append(*solids)
            
            result_part_material_solids.append((part, material, [top_head]))
            
        result.part_material_solid = result_part_material_solids
        return result
    
    def build_composite(self) -> CombiningState:
        '''Heads (if any) are applied to holes and solids as separate objects. 
        The result is a list of solids and holes that are not combined. (holes are preserved))'''
        
        # A List[Tuple[Tuple[Optional[Part], core.Material], List[Any]]] is a list of part-material solids pairs.
        part_material_solid = list(self.part_material_solids.items()) 
        
        if not self.heads:
            return CombiningState(holes=self.holes, part_material_solid=[(part, material, solids) for (part, material), solids in part_material_solid])
        
        if self.holes:
            if not part_material_solid:
                # No solids, hence we can return just the holes.
                top_head, tail_head = self._combine_heads(make_copy=False)
                tail_head.append(*self.holes)
                
                return CombiningState(holes=[top_head])
            
            top_head, tail_head = self._combine_heads(make_copy=True)
            tail_head.append(*self.holes)
            
            result = CombiningState(holes=[top_head])
        else:
            result = CombiningState()
        
        # Applies heads to the part material solids for each part-material combination.
        while part_material_solid:
            
            part_material, solids = part_material_solid.pop()
            has_more = bool(part_material_solid)  # True if there are more part-material combinations.
            
            heads_front, heads_tail = self._combine_heads(make_copy=has_more)
            
            heads_tail.append(*solids)
            
            result.add_part_material_solid(part_material, heads_front)
            
        return result
        
    def createNamedUnion(self, name) -> Any:
        result = self.model.Union()
        result.setMetadataName(f'{self.shape_name} : {name}')
        return result
    
    def createNamedModeContainer(self, name) -> Any:
        result = self.mode.make_container(self.model)
        result.setMetadataName(f'{self.shape_name} : {name}')
        return result
    
    def get_or_create_first_head(self) -> Any:
        '''Returns the first head or creates one if there are no heads.
        This is used to add modifiers to the first head.'''
        heads = self.heads
        if not heads:
            head = self.createNamedUnion('get_or_create_first_head')
            self.add_head(head)
        return heads[0]
    
    def close(self, mode, parent_container):
        '''Closes the container and adds it to the parent container.'''
        if mode.mode == core.ModeShapeFrame.SOLID.mode:
            self.propagate(mode, parent_container)
        elif mode.mode == core.ModeShapeFrame.HOLE.mode:
            combining_state = self.build_combine()
            # All solids of all materials become holes.
            holes = combining_state.flatten_solids()
            parent_container.add_hole(*holes)
        elif mode.mode == core.ModeShapeFrame.COMPOSITE.mode:
            combining_state = self.build_composite()
            parent_container._apply_combining_state(combining_state)
        elif mode.mode == core.ModeShapeFrame.CAGE.mode:
            pass  # Cage drops everything
        elif mode.mode == core.ModeShapeFrame.INTERSECT.mode:
            self.propagate(mode, parent_container)
        elif mode.mode == core.ModeShapeFrame.HULL.mode:
            self.propagate(mode, parent_container)
        elif mode.mode == core.ModeShapeFrame.MINKOWSKI.mode:
            self.propagate(mode, parent_container)
        
    def propagate(self, mode, parent_container):
        combining_state = self.build_combine()
        parent_container._apply_combining_state(combining_state)


@dataclass_json
@dataclass(frozen=True)
class ShapePath:
    shape_path: tuple = field(metadata=config(
        encoder=lambda shape_path: tuple(str(v.label) for v in shape_path)))
    
    def to_path(self):
        return tuple(v.label for v in self.shape_path)
    
    def __str__(self):
        return f'{self.to_path()}'
    
@dataclass_json
@dataclass
class ShapePathCollection:
    
    anchor_paths: list = field(default_factory=list)
    
    def append(self, path):
        self.anchor_paths.append(path)


@dataclass
class ShapePathDict:
    
    paths: dict = field(default_factory=lambda: defaultdict(ShapePathCollection))
    
    def add(self, path, anchor_path):
        self.paths[path].append(anchor_path)


@dataclass(frozen=True)
class ContextEntry():
    container: Container
    mode: core.ModeShapeFrame
    reference_frame: l.GMatrix
    attributes: core.ModelAttributes = None
    graph_node: object = None
    mapped_part_material_colour: core.PartMaterialColour = None

    def get_material(self):
        if self.mapped_part_material_colour:
            return self.mapped_part_material_colour.material
        return None
    
    def get_part(self):
        if self.mapped_part_material_colour:
            return self.mapped_part_material_colour.part
        return None
    
    def get_material_map(self.):
        if self.attributes:
            return self.attributes.material_map
        return None

@dataclass
class Context():
    renderer: 'Renderer' = field(repr=False)
    stack: List[ContextEntry] = field(default_factory=list, init=False)
    model: Any = field(init=False)
    
    def __post_init__(self):
        self.model = self.renderer.model
        
    def map_part_material_colour(self, merged_attrs: core.ModelAttributes) -> core.PartMaterialColour:
        '''Maps the part, material and colour using the material map if available otherwise returns the
        original part, material and colour.'''
        if merged_attrs.material_map:
            return merged_attrs.material_map.map_part_material_colour(
                merged_attrs.part, merged_attrs.material, merged_attrs.colour, merged_attrs)
        return core.PartMaterialColour(merged_attrs.part, merged_attrs.material, merged_attrs.colour)        

    def push(self, 
             mode: core.ModeShapeFrame, 
             reference_frame: l.GMatrix, 
             attributes: core.ModelAttributes,
             shape_name: Hashable=None,
             graph_node: graph_model.Node=None):
        '''Pushes a new context onto the stack. The context is an accumulation of the current state'''
        last_attrs = self.get_last_attributes()
        last_part_material_colour = self.get_last_part_material_colour()
        
        merged_attrs = last_attrs.merge(attributes)
        diff_attrs = last_attrs.diff(merged_attrs)
        
        container = Container(mode, model=self.model, shape_name=shape_name)
        
        if not diff_attrs.is_empty():
            # The mapping function can depend on any of the attributes.
            part_material_colour = self.map_part_material_colour(merged_attrs)
        else:
            part_material_colour = last_part_material_colour
        
        entry = ContextEntry(container, mode, reference_frame, merged_attrs, graph_node, part_material_colour)

        self.stack.append(entry)
        
        if reference_frame:
            if reference_frame != l.IDENTITY:
                container.add_head(self.model.Multmatrix(reference_frame.m.A))
            
        if part_material_colour.colour != last_part_material_colour:
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
        last : ContextEntry = self.stack.pop()
        if self.stack:
            last.container.close(last.mode, self.stack[-1].container)
            return None
        else:
            combining_state = last.container.build_combine()
            # If we have only one material then we can keep legacy mode, one object models.
            if combining_state.has_one_or_no_materials():
                objs = combining_state.flatten_solids()
                if not objs:
                    self.renderer.material_stats.model_materials.add(None)
                    return self.createNamedUnion(last.mode, 'pop')
                
                self.renderer.material_stats.add_part_material(combining_state.get_first_part_material())
                if len(objs) > 1:
                    return self.createNamedUnion(last.mode, 'pop').append(*objs)
                return objs[0]
            else:
                # Create a LazyUnion to combine the material solids.
                lazy_union = self.model.LazyUnion()
                # assert None not in combining_state.material_solid, \
                #     'None material in material_solid.' ### None check ###
                material_solids = combining_state.priority_cured(self.model)
                for material, solids in material_solids:
                    self.renderer.material_stats.model_materials.add(material)
                    mat_container = self.createNamedUnion(last.mode, f'pop - {material}').append(*solids)
                    lazy_union.append(mat_container)
                    
                return lazy_union
            
    def get_current_graph_node(self):
        if self.stack:
            return self.stack[-1].graph_node
        return None
    
    def get_current_graph_path(self) -> ShapePath:
        return ShapePath(tuple((entry.graph_node for entry in self.stack)))
        
    def createNamedUnion(self, mode: core.ModeShapeFrame, name: str):
        result = self.model.Union()
        mode_str = f':{mode.mode}' if mode.mode else ''
        result.setMetadataName(f'{name}{mode_str}')
        return result
    
    def get_last_attributes(self) -> core.ModelAttributes:
        '''Returns the last attributes in the stack or an empty one.'''
        if self.stack:
            attrs = self.stack[-1].attributes
            if not attrs is None:
                return attrs
        return core.EMPTY_ATTRS
    
    def get_last_part_material_colour(self) -> core.PartMaterialColour:
        '''Returns the last part-material-colour in the stack or an empty one.'''
        if self.stack:
            mapped_part_material_colour: core.PartMaterialColour = \
                self.stack[-1].mapped_part_material_colour
            if not mapped_part_material_colour is None:
                return mapped_part_material_colour
        return core.EMPTY_PART_MATERIAL_COLOUR
        
    def get_last_container(self):
        if not self.stack:
            raise EmptyRenderStack('renderer stack is empty.')
        return self.stack[-1].container
    
    def add_solid(self, *obj):
        '''Adds a solid into the current context. The Part and Material is taken from the 
        current attributes.'''
        if not self.stack:
            raise EmptyRenderStack('renderer stack is empty.')
        
        last_context: ContextEntry = self.stack[-1]
        
        part = last_context.get_part()
        material = last_context.get_material()
        material_map = last_context.get_material_map()
                
        self.renderer.material_stats.add(
            self.get_current_graph_path(), material, material, material_map, part)
        
        last_context.container.add_solid(*obj, part=part, material=material)


@dataclass
class Renderer():
    '''Provides renderer machinery for anchorscad. Renders to PythonOpenScad models.'''
    model = posc
    context: Context
    result: CombiningState 
    graph: graph_model.DirectedGraph
    paths: ShapePathDict
    material_stats: MaterialStats
    
    def __init__(self, initial_frame: l.GMatrix=None, initial_attrs: core.ModelAttributes=None):
        self.context = Context(self)
        self.result = None
        self.graph = graph_model.DirectedGraph()
        self.paths = ShapePathDict()
        self.material_stats = MaterialStats()
        root_node = self.graph.new_node('root') 
        # Push an item on the stack that will collect the final objects.
        self.context.push(core.ModeShapeFrame.SOLID, initial_frame, initial_attrs, None, root_node)
        
    def close(self):
        count = len(self.context.stack)
        if count != 1:
            raise UnpoppedItemsOnRenderStack(
                f'{count - 1} items remain on the render stack.')
        combining_state = self.context.pop()
        self.result = combining_state
        self.context = Context(self) # Prepare for the next object just in case.
        return self.result

    def push(self, 
             mode: core._Mode, 
             reference_frame: l.GMatrix, 
             attributes: core.ModelAttributes, 
             shape_name: Hashable, 
             clazz_name: str=None):
        graph_node = self.graph.new_node(shape_name, clazz_name)
        self.graph.add_edge(self.context.get_current_graph_node(), graph_node)
        self.context.push(mode, reference_frame, attributes, shape_name, graph_node)

    def pop(self):
        self.context.pop()
        # The last item on the stack is for office use only.
        if len(self.context.stack) < 1:
            raise PopCalledTooManyTimes('pop() called more times than push() - stack underrun.')
        
    def get_current_attributes(self):
        return self.context.get_last_attributes()
        
    def add(self, *obj):
        self.context.add_solid(*obj)
        
    def add_path(self, path):
        '''Adds a Path to the set of paths used to render the model.'''
        self.paths.add(path, self.context.get_current_graph_path())
        
    def make_result(self, shape: core.Shape, result_object: Any) -> 'RenderResult':
        return RenderResult(shape, result_object, self.graph, self.paths, self.material_stats)


@dataclass(frozen=True)
class RenderResult():
    '''A result of rendering.'''
    shape: core.Shape  # The AnchorScad Shape that was rendered.
    rendered_shape: object  # The resulting POSC shape.
    graph: graph_model.DirectedGraph  # The graph of the rendered shape.
    paths: dict  # A dictionary of Path to list of anchors in the graph.
    material_stats: MaterialStats  # Mapped material stats.
    
    
def render(shape, 
           initial_frame: l.GMatrix=None, 
           initial_attrs: core.ModelAttributes=None) -> RenderResult:
    '''Renders a shape and returns a RenderResult.
    args:
        shape: The shape to render.
        initial_frame: The initial reference frame.
        initial_attrs: The initial attributes.
    '''
    renderer = Renderer(initial_frame, initial_attrs)
    shape.render(renderer)
    return renderer.make_result(shape, renderer.close())

