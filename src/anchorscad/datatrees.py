'''
Created on 8 Dec 2021

@author: gianni

Wrapper over Python's dataclass adding support for a docstring for each 
field and 'Node' fields where fields can be injected into a class 
definition from constructor parameters and bound when nodes are invoked. 

This is particularly useful when composing a class from other classes or 
functions where the fields or constructor or function parameters 
become member fields of the composing class. datatree will automate the
generation of these fields to become dataclass members. datatree will pull 
constructor field definitions of Node declarations and add annotations to 
the enclosed datatree class including any default values or other 
dataclasses.field properties. This is especially useful when constructing 
complex relationships that require a large number of parameters.
'''

from dataclasses import dataclass, field, Field, MISSING
from frozendict import frozendict
from types import FunctionType
import inspect
import builtins
import re

FIELD_FIELD_NAMES=tuple(inspect.signature(field).parameters.keys())
DATATREE_SENTIENEL_NAME='__datatree_nodes__'
OVERRIDE_FIELD_NAME='override'
METADATA_DOCS_NAME='dt_docs'

class ReservedFieldNameException(Exception):
    f'''The name '{OVERRIDE_FIELD_NAME}' is reserved for use by datatree.'''
    
class NameCollision(Exception):
    '''The requested name is already specified.'''
    
class ExpectedDataclassObject(Exception):
    '''Node requires the given object to be dataclass decorated.'''

class MappedFieldNameNotFound(Exception):
    '''Field name specified is not found in the given class.'''    
    
class DataclassAlreadyApplied(Exception):
    '''The function called in intended to be called before the dataclass decorator.'''
    
class IllegalMetadataClass(Exception):
    '''Classes inheriting FieldMetadataBase must override get_doc.'''
    
class SpecifiedMultipleDefaults(Exception):
    '''Attempting to specify default and self_default parameters.'''


def _update_name_map(clz, map, from_name, to_value, description):
    '''Updates the given map but does not allow collision.'''
    if from_name in map:
        raise NameCollision(
            f'{description} {from_name} specified multiple times in {clz.__name__}')
    map[from_name] = to_value

def _dupes_and_allset(itr):
    '''Returns a tuple containing a set of duplicates and a set of all non 
    duplicated items in itr.'''
    seen = set()
    return set((x for x in itr if x in seen or seen.add(x))), seen

@dataclass
class AnnotationDetails:
    '''A dataclass/annotation pair.'''
    field: object
    anno_type: type
    
    @classmethod
    def from_init_param(cls, name, inspect_params):
        '''Creates an AnnotationDetails from a name and inspect.Signature.parameters'''
        param = inspect_params[name]
        
        anno = param.annotation()
        if anno is inspect._empty:
            anno = object
            
        default = param.default
        
        if default is inspect._empty:
            default = MISSING
        
        this_field = field(default=default)
        return AnnotationDetails(this_field, anno)
        

def _field_assign(obj, name, value):
    '''Field assignment that works on frozen objects.'''
    builtins.object.__setattr__(obj, name, value)


class FieldMetadataBase:
    '''Datatree metadata object.'''
    def get_doc(self):
        raise IllegalMetadataClass(
            f'Class must override get_doc() {self.__class__.__name__}')
    

@dataclass(frozen=True)
class FieldMetadata(FieldMetadataBase):
    '''Provides a docstring for a field.'''
    doc: str
    
    def get_doc(self):
        '''Returns the docstring.'''
        return self.doc


@dataclass(frozen=True)
class NodeFieldMetadata(FieldMetadataBase):
    '''Provides a docstring for a Node field.'''
    node_doc: str
    field_metadata: FieldMetadata
    
    def get_doc(self):
        return f'{self.node_doc}: {self.field_metadata.get_doc()}'

CLEANER_REGEX=re.compile('(\n?[ \t][ \t]+)+')

def _get_abbreviated_source(func, max_size=75):
    '''Returns stripped abbreviated source of a function (or lambda).'''
    src = inspect.getsource(func).strip()
    # Remove interspersed white space chunks.
    src = ' '.join(s.strip() for s in CLEANER_REGEX.split(src) if s.strip())
    return (src[:max_size] + '...') if len(src) > (3 + max_size) else src


@dataclass(frozen=True, repr=False)
class BindingDefault:
    '''Like the dataclass field default_factory parameter but called after 
    the regular __init__ function is finished and with the class instance 
    (self) as the first parameter.'''
    self_default: FunctionType

    def __repr__(self):
        return (f'{self.__class__.__name__}'
                f'({_get_abbreviated_source(self.self_default)})')


def field_docs(obj, field_name):
    '''Return the documentation for a field. Returns None if not provided.'''
    metadata = obj.__dataclass_fields__[field_name].metadata
    
    if not metadata:
        return None
    
    doc_metadata = metadata.get(METADATA_DOCS_NAME, None)
    if doc_metadata is None:
        return None
    
    return doc_metadata.get_doc()

def dtfield(default=MISSING, doc=None, self_default=None, **kwargs):
    '''Like dataclasses.field but also supports doc parameter.
    Args:
      default: The default value for the field.
      doc: A docstring associated with the field.
      self_default: A default factory taking a self parameter. 
      Includes all fields allowed by dataclasses.field().
    '''
    metadata = kwargs.get('metadata', {})
    metadata[METADATA_DOCS_NAME] = FieldMetadata(doc)
    if self_default:
        if not default is MISSING:
            raise SpecifiedMultipleDefaults(
                'Cannot specify default and self_default.')
        default=BindingDefault(self_default)
    
    return field(**kwargs, default=default, metadata=metadata)


@dataclass(frozen=True, repr=False)
class _ClzOrFuncWrapper:
    clz_or_func: type
    
    def __repr__(self):
        return self.clz_or_func.__name__
    

@dataclass(frozen=True)
class Node:
    '''A specifier for a datatree node. This specifies how fields
    from a class initializer (or function) is translated from fields in the
    composition class.
    '''
    clz_or_func: type=dtfield(
        doc='A class or function for parameter binding.')
    use_defaults: bool=dtfield(
        doc='Allows use of defaults otherwise defaults should be '
            'specified elsewhere.')
    suffix: str=dtfield(
        doc='Suffix to apply to injected field names.')
    prefix: str=dtfield(
        doc='Prefix to apply to injected field names.')
    expose_all: bool=dtfield(
        doc='Forces the mapping of all fields even if the expose_spec '
            ' excluded the class or function parameter name.')
    init_signature: tuple=field(repr=False)
    expose_map: dict=field(repr=False)
    expose_rev_map: dict=field(repr=False)
    node_doc: str=dtfield(None,
        doc='Field documentation.')
    
    # The default value for the preserve init parameter. Derived classes can override.
    # This allows for application specific Node types that have a set of
    # field names that should be preserved from prefix and suffix mapping.
    DEFAULT_PRESERVE_SET=frozendict()
    # The default value for the expose_if_avail init parameter. Derived classes can override.
    # Similar to DEFAULT_PRESERVE_SET, allows for application specific Node type.
    DEFAULT_EXPOSE_IF_AVAIL=frozendict()
    
    ALT_DEFAULT_ALLOW_SET=None
    
    def __init__(self, 
                 clz_or_func, 
                 *expose_spec, 
                 use_defaults=True, 
                 suffix='', 
                 prefix='', 
                 expose_all=None,
                 expose_if_avail=None,
                 preserve=None,
                 node_doc: str=None):
        '''Args:
            clz_or_func: A class or function for parameter binding.
            *expose_spec: A list of names and dictionaries for mapping. If these
              are specified, only these fields are mapped unless expose_all is
              set.
            use_defaults: Allows use of defaults otherwise defaults should be
              specified elsewhere.
            suffix: Suffix to apply to injected field names.
            prefix: Prefix to apply to injected field names.
            expose_all: Forces the mapping of all fields even if the expose_spec
              excluded the class or function parameter name.
            expose_if_avail: The set of field to expose if they're available.
            preserve: A set of names that are not prefixed or suffixed.
            node_doc: Documentation for the node field.
        '''
        _field_assign(self, 'clz_or_func', _ClzOrFuncWrapper(clz_or_func))
        _field_assign(self, 'use_defaults', use_defaults)
        expose_all = not expose_spec if expose_all is None else expose_all
        _field_assign(self, 'expose_all', expose_all)
        _field_assign(self, 'suffix', suffix)
        _field_assign(self, 'prefix', prefix)
        _field_assign(self, 'init_signature', inspect.signature(clz_or_func))
        _field_assign(self, 'node_doc', node_doc)
        
        if preserve is None:
            preserve = self.DEFAULT_PRESERVE_SET
            
        if expose_if_avail is None:
            expose_if_avail = self.DEFAULT_EXPOSE_IF_AVAIL
        
        fields_specified = tuple(f for f in expose_spec if isinstance(f, str))
        maps_specified = tuple(f for f in expose_spec if not isinstance(f, str))
        fields_in_maps = tuple(f for m in maps_specified for f in m.keys())
        dupes, all_specified = _dupes_and_allset(fields_specified + fields_in_maps) 
        if dupes:
            raise NameCollision(f'Field names have multiple specifiers {dupes!r}')
        
        params = self.init_signature.parameters
        init_fields = set(params.keys())
        if self.expose_all:
            # Add all the fields not already specified.
            all_fields = set(name 
                             for name in init_fields
                             if name != OVERRIDE_FIELD_NAME)
            fields_specified = set(fields_specified).union(all_fields - all_specified)
        elif expose_if_avail:
            all_fields = set(name 
                             for name in init_fields
                             if name != OVERRIDE_FIELD_NAME)
            fields_specified = set(fields_specified).union(
                all_fields.intersection(expose_if_avail) - all_specified)
        expose_dict = {}
        expose_rev_dict = {}
        
        # If we have a dataclass decorated class, use the __dataclass_fields__
        # to fill in this class,
        if hasattr(clz_or_func, '__dataclass_fields__'):
            for from_id in fields_specified:
                if from_id in preserve:
                    to_id = from_id
                else:
                    to_id = prefix + from_id + suffix
                if not from_id in init_fields:
                    raise MappedFieldNameNotFound(
                        f'Field name "{from_id}" is not an '
                        f'{clz_or_func.__name__}.__init__ parameter name')
                _update_name_map(
                    clz_or_func, expose_dict, from_id, to_id, 'Field name')
                anno_detail = self.make_anno_detail(
                        from_id, clz_or_func.__dataclass_fields__[from_id], clz_or_func.__annotations__)
                _update_name_map(
                    clz_or_func, expose_rev_dict, to_id, anno_detail, 
                    'Mapped field name')
                
            for map_specified in maps_specified:
                # The dictionary has a set of from:to pairs.
                for from_id, to_id in map_specified.items():
                    if not from_id in init_fields:
                        raise MappedFieldNameNotFound(
                            f'Field name "{from_id}" mapped to "{to_id}" '
                            f'is not an {clz_or_func.__name__}.__init__ parameter name')
                    _update_name_map(
                        clz_or_func, expose_dict, from_id, to_id, 'Field name')
                    anno_detail = self.make_anno_detail(
                        from_id, clz_or_func.__dataclass_fields__[from_id], clz_or_func.__annotations__)
                    _update_name_map(
                        clz_or_func, expose_rev_dict, to_id, anno_detail,
                        'Mapped field name')
        else:  # Not a dataclass type, can be a function.
            
            for from_id in fields_specified:
                to_id = prefix + from_id + suffix
                if not from_id in init_fields:
                    raise MappedFieldNameNotFound(
                        f'Field name "{from_id}" is not an '
                        f'{clz_or_func.__name__}.__init__ parameter name')
                _update_name_map(
                    clz_or_func, expose_dict, from_id, to_id, 'Field name')
                anno_detail = AnnotationDetails.from_init_param(from_id, params)
                _update_name_map(
                    clz_or_func, expose_rev_dict, to_id, anno_detail, 
                    'Mapped field name')
                
            for map_specified in maps_specified:
                # The dictionary has a set of from:to pairs.
                for from_id, to_id in map_specified.items():
                    if not from_id in init_fields:
                        raise MappedFieldNameNotFound(
                            f'Field name "{from_id}" mapped to "{to_id}" '
                            f'is not an {clz_or_func.__name__}.__init__ parameter name')
                    _update_name_map(
                        clz_or_func, expose_dict, from_id, to_id, 'Field name')
                    anno_detail = AnnotationDetails.from_init_param(from_id, params)
                    _update_name_map(
                        clz_or_func, expose_rev_dict, to_id, anno_detail,
                        'Mapped field name')
            
        _field_assign(self, 'expose_map', frozendict(expose_dict))
        _field_assign(self, 'expose_rev_map', frozendict(frozendict(expose_rev_dict)))
        
    def make_anno_detail(self, from_id, dataclass_field, annotations):
        if from_id in annotations:
            return AnnotationDetails(dataclass_field, annotations[from_id])
        return AnnotationDetails(dataclass_field, dataclass_field.type)
        
    def get_rev_map(self):
        return self.expose_rev_map

    
def _make_dataclass_field(field_obj, use_default, node_doc):
    '''Creates a dataclasses Field for the given parameters.
    Args:
      field_obj: the current Field object.
      use_default: If True, the default of the Field is used otherwise the 
          default is excluded.
      node_doc: The docstring for the wrapping Node field.
    '''
    value_map = dict((name, getattr(field_obj, name)) for name in FIELD_FIELD_NAMES)
    
    # Fix docs in the metadata.
    metadata = value_map.get('metadata', None)
    metadata_docs = (None 
                     if metadata is None 
                     else metadata.get(METADATA_DOCS_NAME, None))
    if metadata_docs:
        new_metadata = {METADATA_DOCS_NAME: 
                        NodeFieldMetadata(node_doc, metadata_docs)}
        new_metadata.update(
            (k, v) for k, v in metadata.items() if k != METADATA_DOCS_NAME)
        value_map['metadata'] = new_metadata
    
    default_val = value_map['default']
    if isinstance(default_val, Node):
        return field(**value_map), default_val

    if not use_default:
        value_map.pop('default', None)
        value_map.pop('default_factory', None)
    return field(**value_map), None

def _apply_node_fields(clz):
    '''Adds new fields from Node annotations.'''
    annotations = clz.__annotations__
    new_annos = {}  # New set of annos to build.
    
    # The order in which items are added to the new_annos dictionary is important.
    # Here we maintain the same order of the original with the new exposed fields
    # interspersed between the Node annotated fields.
    nodes = {}
    for name, anno in annotations.items():
        new_annos[name] = anno
        if not hasattr(clz, name):
            continue
        anno_default = getattr(clz, name)
        if isinstance(anno_default, Field):
            anno_default = anno_default.default
        else:
            # By default don't compare node fields as they don't add
            # any value.
            setattr(clz, name, field(default=anno_default, compare=False))
        if isinstance(anno_default, Node):
            nodes[name] = anno_default
            rev_map = anno_default.get_rev_map()
            for rev_map_name, anno_detail in rev_map.items():
                if not rev_map_name in new_annos:
                    new_annos[rev_map_name] = anno_detail.anno_type
                    if not hasattr(clz, rev_map_name):
                        field_default, node_default = _make_dataclass_field(
                            anno_detail.field, 
                            anno_default.use_defaults, 
                            anno_default.node_doc)
                        setattr(clz, rev_map_name, field_default)
                        if node_default:
                            nodes[rev_map_name] = node_default
        elif isinstance(anno_default, BindingDefault):
            nodes[name] = anno_default

    clz.__annotations__ = new_annos
    
    for bclz in clz.__mro__[-1:0:-1]:
        bnodes = getattr(bclz, DATATREE_SENTIENEL_NAME, {})
        for name, val in bnodes.items():
            if not name in nodes:
                nodes[name] = val
    
    setattr(clz, DATATREE_SENTIENEL_NAME, nodes)
    return clz


@dataclass(frozen=True, repr=False)
class BoundNode:
    '''The result of binding a Node to a class instance. Once a datatree 
    object is created, all Node fields become BoundNode fields.'''
    parent: object
    name: str
    node: Node=field(compare=False)
    instance_node: object=field(repr=False)
    chained_node: object=field(default=None, repr=False)
    
    def chain(self, new_parent, node):
        return BoundNode(new_parent, self.name, self.node, node, self)

    def __call__(self, *args, **kwds):
        return self._invoke(self, self.node.clz_or_func.clz_or_func, args, kwds)

    def call_with(self, clz_or_func, *args, **kwds):
        return self._invoke(self, clz_or_func, args, kwds)
    
    def call_with_alt_defaults(self, clz_or_func, *args, alt_defaults=None, **kwds):
        return self._invoke(self, clz_or_func, args, kwds, alt_defaults)
        
    @classmethod
    def _invoke(cls, node, clz_or_func, args, kwds, alt_defaults=None):
        # Resolve parameter values.
        # Priority order:
        # 1. Override (if any)
        # 2. Passed in parameters
        # 3. Parent field values
        passed_bind = node.node.init_signature.bind_partial(*args, **kwds).arguments
        ovrde = (node.parent.override.get_override(node.name)
                 if node.parent.override
                 else MISSING)
        if not ovrde is MISSING:
            ovrde_bind = ovrde.bind_signature(
                node.node.init_signature)
            
            for k, v in passed_bind.items():
                if not k in ovrde_bind:
                    ovrde_bind[k] = v
            
            if ovrde.clazz:
                clz_or_func = ovrde.clazz 
        else:
            ovrde_bind = passed_bind
        
        alt_default_allow_set = node.node.ALT_DEFAULT_ALLOW_SET
        # Pull any values left from the parent or, as a final resort,
        # the alt_defaults object.
        for fr, to in node.node.expose_map.items():
            if not fr in ovrde_bind:
                val = getattr(node.parent, to)
                if (val is None
                    and ((alt_default_allow_set is None)
                         or (fr in alt_default_allow_set))
                    and hasattr(alt_defaults, to)):
                        # Pull the attribute from alt_defaults if
                        # its available and otherwise we have None.
                        val = getattr(alt_defaults, to)
                ovrde_bind[fr] = val
        
        return clz_or_func(**ovrde_bind)
    
    def __repr__(self):
        return f'BoundNode(node={repr(self.node)})'

    
@dataclass
class Exposures:
    items: tuple=None

    
class Overrides:
    
    def __init__(self, kwds):
        self.kwds = kwds
    
    def get_override(self, name):
        return self.kwds.get(name, MISSING)
    
def override(**kwds):
    return Overrides(kwds)


@dataclass
class Args:
    arg: tuple
    kwds: dict
    clazz: type=None
    
    def bind_signature(self, signature):
        return signature.bind_partial(*self.arg, **self.kwds).arguments

    
def dtargs(*arg, clazz=None, **kwds):
    return Args(arg, kwds, clazz=clazz)

def _initialize_node_instances(clz, instance):
    '''Post dataclass initialization binding of nodes to instance.'''
    nodes = getattr(clz, DATATREE_SENTIENEL_NAME)
    
    for name, node in nodes.items():
        # The cur-value may contain args specifically for this node.
        cur_value = getattr(instance, name)
        if isinstance(cur_value, BoundNode):
            field_value = cur_value.chain(instance, node)
        elif isinstance(cur_value, Node):
            field_value = BoundNode(instance, name, node, cur_value)
        elif isinstance(cur_value, BindingDefault):
            field_value = cur_value.self_default(instance)
        else:
            # Parent node has passed something other than a Node or a chained BoundNode.
            # Assume they just want to have it called.
            continue
        setattr(instance, name, field_value)

# Provide dataclass compatiability post python 3.8.
# Default values for the dataclass function post Python 3.8.
_POST_38_DEFAULTS=dtargs(match_args=True, kw_only=False, slots=False).kwds

def _process_datatree(clz, init, repr, eq, order, unsafe_hash, frozen,
                   match_args, kw_only, slots, chain_post_init):

    if OVERRIDE_FIELD_NAME in clz.__annotations__:
        if clz.__annotations__['override'] != Overrides:
            raise ReservedFieldNameException(
                f'Reserved field name {OVERRIDE_FIELD_NAME} used by class '
                f'{clz.__name__}')
    clz.__annotations__['override'] = Overrides
    setattr(clz, OVERRIDE_FIELD_NAME, field(default=None, repr=False))
    
    post_init_chain = dict()
    if chain_post_init:
        # Collect all the __post_init__ functions being inherited and place
        # them in a tuple of functions to call.
        for bclz in clz.__mro__[1:-1]:
            if hasattr(bclz, '__post_init_chain__'):
                post_init_chain.update(dict().fromkeys(bclz.__post_init_chain__))

            if hasattr(bclz, '__post_init__'):
                post_init_func = getattr(bclz, '__post_init__')
                if not hasattr(post_init_func, '__is_datatree_override_post_init__'):
                    post_init_chain[post_init_func] = None

    if hasattr(clz, '__post_init__'):
        post_init_func = getattr(clz, '__post_init__')
        if not hasattr(post_init_func, '__is_datatree_override_post_init__'):
            if not post_init_func in post_init_chain:
                post_init_chain[post_init_func] = None
    
    clz.__post_init_chain__ = tuple(post_init_chain.keys())
    clz.__initialize_node_instances_done__ = False
        
    def override_post_init(self):
        if not self.__initialize_node_instances_done__:
            _field_assign(self,
                          '__initialize_node_instances_done__',
                          True)
            _initialize_node_instances(clz, self)
        for post_init_func in self.__post_init_chain__:
            post_init_func(self)
    override_post_init.__is_datatree_override_post_init__ = True
    clz.__post_init__ = override_post_init

    _apply_node_fields(clz)
    
    values_post_38 = dtargs(match_args=match_args, kw_only=kw_only, slots=slots).kwds
    values_post_38_differ = dict(
        ((k, v) for k, v in values_post_38.items() if v != _POST_38_DEFAULTS[k]))
        
    dataclass(clz, init=init, repr=repr, eq=eq, order=order,
              unsafe_hash=unsafe_hash, frozen=frozen, **values_post_38_differ)

    return clz


def datatree(clz=None, /, *, init=True, repr=True, eq=True, order=False,
              unsafe_hash=False, frozen=False, match_args=True,
              kw_only=False, slots=False, chain_post_init=False):
    '''Python decorator similar to dataclasses.dataclass providing parameter injection,
    binding and overrides for parameters deeper inside a tree of objects.
    '''
    
    def wrap(clz):
        return _process_datatree(clz, init, repr, eq, order, unsafe_hash,
                              frozen, match_args, kw_only, slots, chain_post_init)

    # See if we're being called as @datatree or @datatree().
    if clz is None:
        # We're called with parens.
        return wrap

    # We're called as @datatree without parens.
    return wrap(clz)
