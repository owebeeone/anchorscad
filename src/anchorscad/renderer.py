'''
Created on 4 Jan 2021

@author: gianni
'''

import copy
from collections import defaultdict
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json, config

from anchorscad import core, graph_model
import anchorscad_lib.linear as l
import pythonopenscad as posc
from typing import Any, Hashable, Dict, List, Tuple, Set, Optional, Union
from functools import total_ordering

import re


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

# Define the global replacements for the float format to make it a valid identifier.
_FLOAT_FORMAT_REPLACEMENTS = {'.': '_', '-': 'm'}

# Define the module global for maximum decimal places
_MAX_FLOAT_ID_CHARS = 3

def _make_identifier_from_tuple(names: Tuple[str, ...]) -> str:
    '''Returns a sanitized identifier for the given string.'''
    return '_'.join(core.sanitize_name(name) for name in names)

@total_ordering
@dataclass(frozen=True)
class PartMaterial:
    '''A part and material combination.'''
    part: Optional[core.Part]
    material: Optional[core.Material]
    
    
    def get_part(self) -> core.Part:
        '''Returns the part or the default part if None.'''
        return self.part if self.part else core.DEFAULT_PART
    
    def get_material(self) -> core.Material:
        '''Returns the material or the default material if None.'''
        return self.material if self.material else core.DEFAULT_EXAMPLE_MATERIAL

    def get_priority_key(self) -> Tuple[core.Part, core.Material]:
        '''Returns the part and material as a tuple.'''
        part = self.get_part()
        material = self.get_material()
        return (part.priority, part.name, material.priority, material.name)
    
    def get_part_material_name(self) -> Tuple[str, str]:
        '''Returns the part and material names as a tuple.'''
        return (self.get_part().name, self.get_material().name)
    
    def same_part_material_name(self, other: 'PartMaterial') -> bool:
        '''Returns True if the part and material names are the same.'''
        return self.get_part_material_name() == other.get_part_material_name()
        
    def __gt__(self, other: 'PartMaterial') -> bool:
        if not isinstance(other, PartMaterial):
            return NotImplemented
        return self.get_priority_key() > other.get_priority_key()
    
    def __eq__(self, other: 'PartMaterial') -> bool:
        if not isinstance(other, PartMaterial):
            return NotImplemented
        return self.get_priority_key() == other.get_priority_key()
    
    def get_material_key(self) -> Tuple[int, str]:
        '''Returns the material key.'''
        return (self.get_material().priority, self.get_material().name)
    
    def make_identifier(self) -> str:
        '''Returns an identifier for the part-material combination including the priority.
        
        These identifiers are used to create names for the part-material openscad modules. 
        They are not guarenteed to be unique but are designed to be recognizable as a part-material
        combination. If the names used for material and parts are not valid identifiers, then the
        identifier will be <part_name>_<part_priority>_<material_name>_<material_priority>. If the
        name is not a valid identifier, then a hash of the non-identifier part is appended to the
        part name with the invalid characters replaced with underscores.
        '''


        def format_priority(f) -> str:
            # format the priority as a string with a maximum of _MAX_FLOAT_ID_CHARS characters.
            formatted = f'{f:.{_MAX_FLOAT_ID_CHARS}f}'
            formatted = re.sub(r'\.?0+$', '', formatted)
            formatted = re.sub(r'[.-]', lambda m: _FLOAT_FORMAT_REPLACEMENTS[m.group()], formatted)
            return formatted
        
        part = self.get_part()
        p_pri_formatted = format_priority(part.priority)
        p_sanitized = core.sanitize_name(part.name)
        
        material = self.get_material()
        m_pri_formatted = format_priority(material.priority)
        m_sanitized = core.sanitize_name(material.name)
        
        return f'{p_sanitized}_{p_pri_formatted}_{m_sanitized}_{m_pri_formatted}'
    
    def description(self) -> str:
        '''Returns a description of the PartMaterial.'''
        part = self.get_part()
        material = self.get_material()
        part_defined = f'{part.name} {part.priority}' if self.part else f'undef-{part.name}'
        material_defined = f'{material.name} {material.priority}' \
                           if self.material else f'undef-{material.name}'
        if not material.kind.physical:
            material_defined = material_defined + ' non-physical'
        
        return f'PartMaterial {part_defined} - {material_defined}'


@dataclass
class PartMarterialResolver:
    '''Computes the final part and material combinations for a given set of part-materials.
    
    Takes a set of part-materials and their associated objects and resolves them into a
    set of models that are combined with the higher priority part-materials removed from 
    the lower priority part-materials. 
    
    A model for each part is created as well as a model for all the parts combined.
    Materials that are designated as not physical are only placed in the combined 
    output file and they do not interact with the physical parts. These will be emitted
    as separate objects in the combined output file even if the material names are the
    same.
    '''
    
    part_material_object: List[Tuple[PartMaterial, List[Any]]]  # A map of part-materials to objects.
    holes: List[Any] # A list of holes to be applied to the solids.
    model: Any = posc # The model API to use for the output.
    
    resolved_part_materials: Dict[str, Dict[str, Any]] = field(default=None, init=False)
    
        
    part_models: Dict[str, Any] = field(default=None, init=False)
    all_parts_model: Any = field(default=None, init=False)
    
    identifier_map: Dict[str, int] = field(default_factory=dict, init=False)
        
    
    def __post_init__(self):
        self.part_models, self.all_parts_model, self.resolved_part_materials, _ = \
            self._resolve_part_materials()
        
    def unique_identifier(self, key: Union[PartMaterial, Tuple[str, ...]], suffix: str=None) -> str:
        '''Returns a unique identifier for the part-material-priority combination.'''
        id: str = key.make_identifier() \
            if isinstance(key, PartMaterial) else _make_identifier_from_tuple(key)
        uid = id if not suffix else f'{id}_{suffix}'
        
        # Ensure the identifier is unique. While used to evade potential name clashes
        # with suffixed identifiers. i.e. keep suffxing until a unique identifier is found.
        # It's very unlikely that this will be needed but it ensures that the identifier
        # is unique. This means every generated identifier will be in the map as well.
        while uid in self.identifier_map:
            self.identifier_map[uid] += 1
            uid = f'{id}_{self.identifier_map[uid]}'
        else:
            self.identifier_map[uid] = 0
        return uid
    
    def _make_part_material_module(
            self, part_material: PartMaterial, objs: List[Any], suffix: str=None) -> Any:
        '''Returns a module for the part-material combination.'''
        suffix = suffix if part_material.get_material().kind.physical \
                        else f'non_physical{"_" + suffix if suffix else ""}'
        o = self.model.Module(self.unique_identifier(part_material, suffix=suffix))(*objs)
        o.setMetadataName(part_material.description())
        return o
        
    def _resolve_part_materials(self) -> \
        Tuple[Dict[str, Any], 
              Any, 
              Dict[Tuple[str, str], Dict[str, List[Any]]], 
              Dict[Tuple[str, str, str], List[Any]]]:
        '''Resolves the part-materials into a set of models.'''
        # Sort the part_material_object_map by priority.
        physical_list: List[Tuple[PartMaterial, Any]] = \
            list((k, self._make_part_material_module(k, v)) 
                 for k, v in self.part_material_object
                 if k.get_material().kind.physical)
        
        non_physical_list: List[Tuple[PartMaterial, Any]] = \
            list((k, self._make_part_material_module(k, v, suffix='non_physical')) 
                 for k, v in self.part_material_object
                 if not k.get_material().kind.physical)
            
        physical_list.sort(reverse=True, key=lambda item: item[0])
        
        # Non physical objects are only placed in the combined output file.
        non_physical_list.sort(reverse=True, key=lambda item: item[0])

        # Objects that have been resolved with higher priority materials removed
        # from the lower priority materials.
        cured_negative_map: Dict[PartMaterial, List[Any]] = defaultdict(list)
        
        cured_map: Dict[PartMaterial, Any] = dict()
        
        for i in range(len(physical_list)):
            part_material, obj = physical_list[i]
            cure_list = []
            cured_negative_map[part_material].append(cure_list)
            
            for j in range(i):
                part_material_j, obj_j = physical_list[j]
                if not part_material_j.same_part_material_name(part_material):
                    cure_list.append(obj_j)
            
            if cure_list or self.holes:
                if len(cure_list) + len(self.holes) > 1:
                    cure_item = self.model.Union()(*cure_list, *self.holes)
                    cure_item.setMetadataName(f'cured {part_material}')
                else:
                    cure_item = cure_list[0] if len(cure_list) > 0 else self.holes[0]
                # Create a new object with the higher priority materials removed.
                cured_result = self._make_part_material_module(
                    part_material, 
                    [self.model.Difference()(obj, cure_item)],
                    suffix='cured')
            else:
                # Nothing to remove here.
                cured_result = obj
            cured_map[part_material] = cured_result
            
        # Assemble the final models. One for each part and one for all the parts
        # combined with non physical parts added.
        
        parts: Dict[Tuple[str, str], Dict[str, List[Any]]] = defaultdict(lambda: defaultdict(list))
        all_parts: Dict[Tuple[str, str, str], List[Any]] = defaultdict(list)
        
        # Collect the physical parts.
        for part_material, obj in cured_map.items():
            parts[(part_material.get_part().name, 'physical')] \
                 [part_material.get_material().name].append(obj)
            all_parts[part_material.get_part_material_name() + ('physical',)].append(obj)
            
        non_physical_map: Dict[str, List[Any]] = defaultdict(list)
        
        for part_material, obj in non_physical_list:
            non_physical_map[(part_material.get_part().name, 'non_physical')].append(obj)
            all_parts[part_material.get_part_material_name() + ('non_physical',)].append(obj)
        
        part_models: Dict[str, Any] = dict()
        for k, v in parts.items():
            # The generated identifier is only informational, no need to uniqueify it.
            part_models[k] = self._create_final_model(_make_identifier_from_tuple(k), v)
        
        all_parts_model: Any = self._create_final_model('all_parts', all_parts)
        
        return part_models, all_parts_model, parts, all_parts
        
    def _create_final_model(
        self, part_name: str, objects: Dict[Tuple[str, ...], List[Any]]) -> Any:
        '''Creates a final model for the given part name and objects.'''
        
        lazy_union = posc.LazyUnion()
        lazy_union.setMetadataName(str(part_name))
        
        for k, v in objects.items():
            if len(v) > 1:
                id = self.unique_identifier(k)
                lazy_union.append(posc.Module(id)(*v))
            else:
                lazy_union.append(v[0])
        
        return lazy_union
        
            
    


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
    
    def generate_models(self, model) -> PartMarterialResolver:
        '''Generates the part-material models for the part-material solids.'''        
        return PartMarterialResolver(self.part_material_solid, self.holes, model)


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
            except:  # noqa: E722
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
            
            part_material, solids = part_material_solids.pop()
            
            top_head, last_head = self._combine_heads(make_copy=bool(part_material_solids))

            last_head.append(*solids)
            
            result_part_material_solids.append((part_material, [top_head]))
            
        result.part_material_solid = result_part_material_solids
        return result
    
    def build_composite(self) -> CombiningState:
        '''Heads (if any) are applied to holes and solids as separate objects. 
        The result is a list of solids and holes that are not combined. (holes are preserved))'''
        
        # A List[Tuple[Tuple[Optional[Part], core.Material], List[Any]]] is a list of part-material solids pairs.
        part_material_solid = list(self.part_material_solids.items()) 
        
        if not self.heads:
            return CombiningState(holes=self.holes, 
                                  part_material_solid=[
                                      (part_material, solids) 
                                      for part_material, solids in part_material_solid])
        
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
    shape_path: Tuple[graph_model.Node, ...] = field(metadata=config(
        encoder=lambda shape_path: tuple(str(v.label) for v in shape_path)))
    
    def __post_init__(self):
        if not isinstance(self.shape_path, tuple):
            raise ValueError('shape_path must be a tuple.')
        for n in self.shape_path:
            assert isinstance(n, graph_model.Node), 'shape_path must be a tuple of Nodes.'
    
    def to_path(self) -> Tuple[str, ...]:
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
    mapped_attributes: core.ModelAttributes = None

    def get_from_material(self):
        if self.attributes:
            return self.attributes.material
        return None
    
    def get_material(self):
        if self.mapped_attributes:
            return self.mapped_attributes.material
        return None
    
    def get_part(self):
        if self.mapped_attributes:
            return self.mapped_attributes.part
        return None
    
    def get_attributes_map(self):
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
        
    def map_attributes(self, merged_attrs: core.ModelAttributes) -> core.ModelAttributes:
        '''Maps the attributes if there is a material_map set.'''
        if merged_attrs.material_map:
            return merged_attrs.material_map.map_attributes(merged_attrs)
        return merged_attrs        

    def push(self, 
             mode: core.ModeShapeFrame, 
             reference_frame: l.GMatrix, 
             attributes: core.ModelAttributes,
             shape_name: Hashable=None,
             graph_node: graph_model.Node=None):
        '''Pushes a new context onto the stack. The context is an accumulation of the current state'''
        last_attrs = self.get_last_attributes()
        last_mapped_attributes = self.get_last_mapped_attributes()
        
        merged_attrs = last_attrs.merge(attributes)
        diff_attrs = last_attrs.diff(merged_attrs)
        
        container = Container(mode, model=self.model, shape_name=shape_name)
        
        if diff_attrs.is_empty():
            mapped_attributes = last_mapped_attributes
            diff_mapped_attrs = core.EMPTY_ATTRS
        else:
            # The mapping function can use on any of the attributes to map any values.
            mapped_attributes = self.map_attributes(merged_attrs)
            diff_mapped_attrs = last_mapped_attributes.diff(mapped_attributes)
        
        entry = ContextEntry(container, mode, reference_frame, merged_attrs, graph_node, mapped_attributes)

        self.stack.append(entry)
        
        if reference_frame:
            if reference_frame != l.IDENTITY:
                container.add_head(self.model.Multmatrix(reference_frame.A))
            
        if diff_mapped_attrs.colour:
            container.add_head(self.model.Color(c=diff_mapped_attrs.colour.value))
            
        if diff_mapped_attrs.disable:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.DISABLE)
        if diff_mapped_attrs.show_only:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.SHOW_ONLY)
        if diff_mapped_attrs.debug:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.DEBUG)
        if diff_mapped_attrs.transparent:
            head = container.get_or_create_first_head()
            head.add_modifier(self.model.TRANSPARENT)
        
            
    def pop(self) -> PartMarterialResolver:
        last : ContextEntry = self.stack.pop()
        if self.stack:
            last.container.close(last.mode, self.stack[-1].container)
            return None
        else:
            combining_state = last.container.build_combine()

            resolved_models: PartMarterialResolver = combining_state.generate_models(self.model)

            return resolved_models
            
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
            if attrs is not None:
                return attrs
        return core.EMPTY_ATTRS
    
    def get_last_mapped_attributes(self) -> core.ModelAttributes:
        '''Returns the last part-material-colour in the stack or an empty one.'''
        if self.stack:
            mapped_attributes: core.ModelAttributes = self.stack[-1].mapped_attributes
            if mapped_attributes is not None:
                return mapped_attributes
        return core.EMPTY_ATTRS
        
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
        material_map = last_context.get_attributes_map()
                
        self.renderer.material_stats.add(
            self.get_current_graph_path(), material, material, material_map, part)
        
        last_context.container.add_solid(*obj, part=part, material=material)


@dataclass
class Renderer():
    '''Provides renderer machinery for anchorscad. Renders to PythonOpenScad models.'''
    context: Context
    result: PartMarterialResolver 
    graph: graph_model.DirectedGraph
    paths: ShapePathDict
    material_stats: MaterialStats
    model: Any = posc
    
    def __init__(self, initial_frame: l.GMatrix=None, initial_attrs: core.ModelAttributes=None):
        self.context = Context(self)
        self.result = None
        self.graph = graph_model.DirectedGraph()
        self.paths = ShapePathDict()
        self.material_stats = MaterialStats()
        root_node = self.graph.new_node('root') 
        # Push an item on the stack that will collect the final objects.
        self.context.push(core.ModeShapeFrame.SOLID, initial_frame, initial_attrs, None, root_node)
        
    def close(self) -> PartMarterialResolver:
        count = len(self.context.stack)
        if count != 1:
            raise UnpoppedItemsOnRenderStack(
                f'{count - 1} items remain on the render stack.')
        part_material_resolver : PartMarterialResolver = self.context.pop()
        self.result = part_material_resolver
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
        
    def make_result(self, 
                    shape: core.Shape, 
                    resolver: PartMarterialResolver) -> 'RenderResult':
        return RenderResult(
            shape, 
            resolver.all_parts_model, 
            self.graph, 
            self.paths, 
            self.material_stats,
            resolver.part_models
            )


@dataclass(frozen=True)
class RenderResult():
    '''A result of rendering.'''
    shape: core.Shape  # The AnchorScad Shape that was rendered.
    rendered_shape: Any  # The resulting POSC shape.
    graph: graph_model.DirectedGraph  # The graph of the rendered shape.
    paths: dict  # A dictionary of Path to list of anchors in the graph.
    material_stats: MaterialStats  # Mapped material stats.
    parts: Dict[str, Any] # The individual parts of the shape.
    
    
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
    renderer.close()
    return renderer.make_result(shape, renderer.result)

