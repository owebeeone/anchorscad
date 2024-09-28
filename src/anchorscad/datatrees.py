'''
Created on 8 Dec 2021

@author: gianni

Wrapper over Python's dataclass that allows for the composition of classes
by injecting constructor parameters or function parameters into a datatree
annotated class with a Node type hint. The Node fields transform into factories
that use the injected fields as defaults to construct the class (or call the 
function). Field names can be mapped to different names, prefixed or suffixed 
or excluded. 

Example:

@datatree
class A:
    a: int=1
    b: int=2
    x: int=0

@datatree
class B:
    x: int=3
    a_node: Node=Node(A, 'a', {'b': 'c'}, 'x')
    
b = B(c=5)
a = b.a_node()

# The following are true

# The a field in B is mapped to the a field in A.
b.a == 1
a.a == 1

# The c field in B is mapped to the b field in A.
b.c == 5
a.b == 5

# The x field in B is mapped to the x field in A
# but the default value is now the value of the x 
# field in B.
a.x == 3

In the above example, the Node field a_node causes the fields of A to be
injected into B. The field 'a' is mapped to 'a' and the field 'b' is mapped
to 'c'. Hence B contains 4 fields (but only 3 parameters to the constructor
because by default Node fields are not included in the constructor parameters),
a_node, a, c and x. The a_node field is a factory that creates an instance of A
that has the 'a' init parameter default set to the value of the field 
'a' in B and the default value of the init parameter 'b' is set to the value 
of the field 'c' in B etc.

Datatree is particularly useful when composing a class from other classes or 
functions where the fields or constructor or function parameters 
become member fields of the composing class. Datatree will automate the
generation of these fields to become dataclass members. datatree will pull 
constructor field definitions of Node declarations and add annotations to 
the enclosed datatree class including any default values or other 
dataclasses.field properties. This is especially useful when constructing 
complex relationships that require a large number of parameters.
'''

from dataclasses import dataclass, field, Field, MISSING
from typing import List, Dict
from frozendict import frozendict
from sortedcollections import OrderedSet
from types import FunctionType
import inspect
import builtins
import re

FIELD_FIELD_NAMES = tuple(inspect.signature(field).parameters.keys())
DATATREE_SENTIENEL_NAME = '__datatree_nodes__'
OVERRIDE_FIELD_NAME = 'override'
METADATA_DOCS_NAME = 'dt_docs'


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
    
class _OrderedSet(OrderedSet):
    
    def union(self, other):
        result = _OrderedSet(self)
        for item in other:
            result.add(item)
        return result
    
    def intersection(self, other):
        result = _OrderedSet()
        for item in self:
            if item in other:
                result.add(item)
        return result


def _update_name_map(clz, name_map, from_name, to_value, description):
    '''Updates the given map but does not allow collision.'''
    if from_name in name_map:
        raise NameCollision(
            f'{description} {from_name} specified multiple times in {clz.__name__}')
    name_map[from_name] = to_value


def _update_name_multi_map(clz, name_map, from_name, to_value):
    '''Updates the given multi-valued map.'''
    if from_name in name_map:
        cur = name_map[from_name]
        name_map[from_name] = cur + (to_value,)
    name_map[from_name] = (to_value,)


def _dupes_and_allset(itr):
    '''Returns a tuple containing a set of duplicates and a set of all non 
    duplicated items in itr.'''
    seen = _OrderedSet()
    return _OrderedSet((x for x in itr if x in seen or seen.add(x))), seen


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


CLEANER_REGEX = re.compile('(\n?[ \t][ \t]+)+')


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


_Node = None  # Forward declaration for Node. This is set later.

def dtfield(default=MISSING, doc=None, self_default=None, init=MISSING, **kwargs):
    '''Like dataclasses.field but also supports doc parameter.
    Args:
      default: The default value for the field.
      doc: A docstring associated with the field.
      self_default: A default factory taking a self parameter. 
      Includes all fields allowed by dataclasses.field().
    '''
    metadata = kwargs.pop('metadata', {})
    metadata[METADATA_DOCS_NAME] = FieldMetadata(doc)
    if self_default:
        if default is not MISSING:
            raise SpecifiedMultipleDefaults(
                'Cannot specify default and self_default.')
        default = BindingDefault(self_default)
        
    if init is MISSING:
        # Don't make self_default and Node fields init by self_default.
        types = (_Node, BindingDefault) if _Node is not None else BindingDefault
        init = not isinstance(default, types)

    return field(**kwargs, default=default, metadata=metadata, init=init)


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
    clz_or_func: type = dtfield(
        doc='A class or function for parameter binding.')
    use_defaults: bool = dtfield(
        doc='Allows use of defaults otherwise defaults should be '
            'specified elsewhere.')
    suffix: str = dtfield(
        doc='Suffix to apply to injected field names.')
    prefix: str = dtfield(
        doc='Prefix to apply to injected field names.')
    expose_all: bool = dtfield(
        doc='Forces the mapping of all fields even if the expose_spec '
            ' excluded the class or function parameter name.')
    init_signature: tuple = field(default=None, repr=False)
    expose_map: dict = field(default=None, repr=False)
    expose_rev_map: dict = field(default=None, repr=False)
    node_doc: str = dtfield(None, doc='Field documentation.')

    # The default value for the preserve init parameter. Derived classes can override.
    # This allows for application specific Node types that have a set of
    # field names that should be preserved from prefix and suffix mapping.
    DEFAULT_PRESERVE_SET = frozendict()
    # The default value for the expose_if_avail init parameter. Derived classes can override.
    # Similar to DEFAULT_PRESERVE_SET, allows for application specific Node type.
    DEFAULT_EXPOSE_IF_AVAIL = frozendict()

    ALT_DEFAULT_ALLOW_SET = None

    def __init__(self,
                 clz_or_func,
                 *expose_spec,
                 use_defaults=True,
                 suffix='',
                 prefix='',
                 expose_all=None,
                 expose_if_avail=None,
                 preserve=None,
                 exclude=(),
                 node_doc: str = None):
        '''Args:
            clz_or_func: A class or function for parameter binding.
            *expose_spec: A list of names and dictionaries for mapping. If these
              are specified, only these fields are mapped unless expose_all is
              set.
            use_defaults: Allows use of defaults otherwise defaults should be
              specified elsewhere.
            suffix: Suffix to apply to injected field names not otherwise mapped.
            prefix: Prefix to apply to injected field names not otherwise mapped.
            expose_all: Forces the mapping of all fields even if the expose_spec
              excluded the class or function parameter name.
            expose_if_avail: The set of field to expose if they're available.
            preserve: A set of names that are not prefixed or suffixed.
            exclude: A set of field names to exclude otherwise would be included by expose_all.
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
        maps_specified = tuple(
            f for f in expose_spec if not isinstance(f, str))
        fields_in_maps = tuple(f for m in maps_specified for f in m.keys())
        dupes, all_specified = _dupes_and_allset(
            fields_specified + fields_in_maps)
        if dupes:
            raise NameCollision(
                f'Field names have multiple specifiers {dupes!r}')

        params = self.init_signature.parameters
        init_fields = _OrderedSet(params.keys())
        if self.expose_all:
            # Add all the fields not already specified.
            all_fields = _OrderedSet(name
                             for name in init_fields
                             if name != OVERRIDE_FIELD_NAME and name not in exclude)
            fields_specified = _OrderedSet(fields_specified).union(
                all_fields - all_specified)

        elif expose_if_avail:
            all_fields = _OrderedSet(name
                             for name in init_fields
                             if name != OVERRIDE_FIELD_NAME)
            fields_specified = _OrderedSet(fields_specified).union(
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
                if from_id not in init_fields:
                    raise MappedFieldNameNotFound(
                        f'Field name "{from_id}" is not an '
                        f'{clz_or_func.__name__}.__init__ parameter name')
                _update_name_map(
                    clz_or_func, expose_dict, from_id, to_id, 'Field name')
                anno_detail = self.make_anno_detail(
                    from_id, clz_or_func.__dataclass_fields__[from_id], clz_or_func.__annotations__)
                _update_name_multi_map(
                    clz_or_func, expose_rev_dict, to_id, anno_detail)

            for map_specified in maps_specified:
                # The dictionary has a set of from:to pairs.
                for from_id, to_id in map_specified.items():
                    if from_id not in init_fields:
                        raise MappedFieldNameNotFound(
                            f'Field name "{from_id}" mapped to "{to_id}" '
                            f'is not an {clz_or_func.__name__}.__init__ parameter name')
                    _update_name_map(
                        clz_or_func, expose_dict, from_id, to_id, 'Field name')
                    anno_detail = self.make_anno_detail(
                        from_id, clz_or_func.__dataclass_fields__[from_id], clz_or_func.__annotations__)
                    _update_name_multi_map(
                        clz_or_func, expose_rev_dict, to_id, anno_detail)
        else:  # Not a dataclass type, can be a function.

            for from_id in fields_specified:
                to_id = prefix + from_id + suffix
                if from_id not in init_fields:
                    raise MappedFieldNameNotFound(
                        f'Field name "{from_id}" is not an '
                        f'{clz_or_func.__name__}.__init__ parameter name')
                _update_name_map(
                    clz_or_func, expose_dict, from_id, to_id, 'Field name')
                anno_detail = AnnotationDetails.from_init_param(
                    from_id, params)
                _update_name_multi_map(
                    clz_or_func, expose_rev_dict, to_id, anno_detail)

            for map_specified in maps_specified:
                # The dictionary has a set of from:to pairs.
                for from_id, to_id in map_specified.items():
                    if from_id not in init_fields:
                        raise MappedFieldNameNotFound(
                            f'Field name "{from_id}" mapped to "{to_id}" '
                            f'is not an {clz_or_func.__name__}.__init__ parameter name')
                    _update_name_map(
                        clz_or_func, expose_dict, from_id, to_id, 'Field name')
                    anno_detail = AnnotationDetails.from_init_param(
                        from_id, params)
                    _update_name_multi_map(
                        clz_or_func, expose_rev_dict, to_id, anno_detail)

        _field_assign(self, 'expose_map', frozendict(expose_dict))
        _field_assign(self, 'expose_rev_map', frozendict(expose_rev_dict))

    def make_anno_detail(self, from_id, dataclass_field, annotations):
        if from_id in annotations:
            return AnnotationDetails(dataclass_field, annotations[from_id])
        return AnnotationDetails(dataclass_field, dataclass_field.type)

    def get_rev_map(self):
        return self.expose_rev_map
    
    def get_map(self):
        return self.expose_map


def _make_dataclass_field(field_obj, use_default, node_doc):
    '''Creates a dataclasses Field for the given parameters.
    Args:
      field_obj: the current Field object.
      use_default: If True, the default of the Field is used otherwise the 
          default is excluded.
      node_doc: The docstring for the wrapping Node field.
    '''
    value_map = dict((name, getattr(field_obj, name))
                     for name in FIELD_FIELD_NAMES)

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


@dataclass
class InjectedFieldInfo:
    '''The source of an injected field.'''
    node_field_name: str
    node_name: str
    node: Node


@dataclass
class InjectedFieldDetails:
    '''Details of an injected field and its bindings.'''
    field_name: str
    sources: List[InjectedFieldInfo]=field(default_factory=list, init=False)
    

@dataclass
class InjectedFields:
    '''Details of the injected fields and their bindings.'''
    clz: type
    injections: Dict[str, InjectedFieldDetails]=\
                field(default_factory=dict, init=False)
    
    def _add(self, field_name: str, details: InjectedFieldInfo):
        '''Adds an instance of an injected field.'''
        if not field_name:
            return
        ifd = self.injections.get(field_name, None)
        if not ifd:
            ifd = InjectedFieldDetails(field_name)
            self.injections[field_name] = ifd
        else:
            pass
        ifd.sources.append(details)
        
    def __str__(self) -> str:
        info = []
        field_names = sorted(self.injections.keys())
        for field_name in field_names:
            details = self.injections[field_name]
            info.append(f'{field_name}:')
            for source in details.sources:
                node = source.node
                node_field_name = source.node_field_name
                info.append(f'    {node_field_name}: {node.clz_or_func!r}')
        return '\n'.join(info)

    def _deep_info_helper(
            self, node: Node, field_name: str, prefix: str, info: list):
        prefix += '    '
        level = get_injected_fields(node.clz_or_func.clz_or_func)
        if field_name in level.injections:
            for source in level.injections[field_name].sources:
                info.append(f'{prefix}{source.node_field_name}: {source.node.clz_or_func!r}')
                self._deep_info_helper(source.node, source.node_field_name, prefix, info)


    def deep_str(self) -> str:
        '''Returns a string representation of the injected fields and their
        bindings including the deeper levels of the injected fields.'''
        info = []
        field_names = sorted(self.injections.keys())
        for field_name in field_names:
            details = self.injections[field_name]
            info.append(f'{field_name}: {self.clz.__name__}')
            prefix = '    '
            for source in details.sources:
                node = source.node
                node_field_name = source.node_field_name
                info.append(f'{prefix}{node_field_name}: {node.clz_or_func!r}')
                self._deep_info_helper(
                    source.node, source.node_field_name, prefix, info)
                
        return '\n'.join(info)

    def generate_html_page(self, url_generator) -> str:
        import html
        def _html_row(field_name, details, is_nested):
            rows = ''
            for source in details.sources:
                link = url_generator(source.node.clz_or_func)
                nested_table_content = ''
                if hasattr(source.node.clz_or_func, 'clz_or_func'):
                    next_level = get_injected_fields(source.node.clz_or_func.clz_or_func)
                    if source.node_field_name in next_level.injections:
                        nested_table_content = _html_row(source.node_field_name, next_level.injections[source.node_field_name], True)
                rows += ("""
                <tr>
                """
                +
                ('<td>&nbsp;</td>' if is_nested else f"""    <td>{field_name}</td>
                """)
                +
                f"""    <td>{source.node_field_name}</td>
                    <td><a href='{link}'>{source.node.clz_or_func!r}</a></td>
                </tr>
                """)
                if nested_table_content:
                    rows += f"""
                    <tr>
                        <td colspan='3'>
                            <table>{nested_table_content}</table>
                        </td>
                    </tr>
                    """
            return rows

        docstring = inspect.getdoc(self.clz)
        if docstring:
            class_docstring = '<p>' + html.escape(docstring).replace('\n', '<br/>') + '</p>'
        else:
            class_docstring = ''

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Datatree Injected Fields for {self.clz.__name__}</title>
            <style>
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <h1>Datatree Injected Fields for {self.clz.__name__}</h1>
            {class_docstring}
            <table>
                <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Node Field Name</th>
                        <th>Node Class/Func</th>
                    </tr>
                </thead>
                <tbody>
        """
        for field_name in sorted(self.injections.keys()):
            details = self.injections[field_name]
            html_content += _html_row(field_name, details, False)

        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        return html_content
    
    def __bool__(self) -> bool:
        return bool(self.injections)


def _get_injected_fields(clz) -> InjectedFields:
    nodes = getattr(clz, DATATREE_SENTIENEL_NAME, {})
    injected_fields = InjectedFields(clz)
    
    for node_name, node in nodes.items():
        if not isinstance(node, Node):
            continue
        for field_name, injected_name in node.get_map().items():
            injected_fields._add(
                injected_name,
                InjectedFieldInfo(field_name, node_name, node)
            )
    return injected_fields

# Cache the injected fields for each class.
_INJECTED_FIELDS_CACHE = {}

def get_injected_fields(clz) -> InjectedFields:
    '''Returns information about the injected fields for the given class.
    This can be used to find how fields are injected and bound. In particular,
    a number of Node fields can inject the same field name. This will also 
    provide all the Node fields will bind to a field.
    Args:
      clz: The class to inspect.
    '''
    result = _INJECTED_FIELDS_CACHE.get(clz, None)
    if result is None:
        result = _get_injected_fields(clz)
        _INJECTED_FIELDS_CACHE[clz] = result
    return result

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
            field_params = {'default':anno_default, 'compare':False}            
            if isinstance(anno_default, Node):
                # By default don't make Node parameters initializer fields.
                field_params['init'] = False
            setattr(clz, name, field(**field_params))

        if isinstance(anno_default, Node):
            nodes[name] = anno_default
            rev_map = anno_default.get_rev_map()
            # Add the fields from the Node specification.
            for rev_map_name, anno_detail_tuple in rev_map.items():
                if rev_map_name is None:
                    continue  # Skip fields mapped to None, these are not injected.
                anno_detail = anno_detail_tuple[0]
                if rev_map_name not in new_annos:
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
            if name not in nodes:
                nodes[name] = val

    setattr(clz, DATATREE_SENTIENEL_NAME, nodes)
    return clz

_Node = Node

@dataclass(frozen=True, repr=False)
class BoundNode:
    '''The result of binding a Node to a class instance. Once a datatree 
    object is created, all Node fields become BoundNode fields.'''
    parent: object = field(compare=False)
    name: str
    node: Node = field(compare=False)
    instance_node: object = field(repr=False)
    chained_node: object = field(default=None, repr=False, compare=False)

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
        passed_bind = node.node.init_signature.bind_partial(
            *args, **kwds).arguments
        ovrde = (node.parent.override.get_override(node.name)
                 if hasattr(node.parent, 'override') and node.parent.override
                 else MISSING)
        if ovrde is not MISSING:
            ovrde_bind = ovrde.bind_signature(
                node.node.init_signature)

            for k, v in passed_bind.items():
                if k not in ovrde_bind:
                    ovrde_bind[k] = v

            if ovrde.clazz:
                clz_or_func = ovrde.clazz
        else:
            ovrde_bind = passed_bind

        alt_default_allow_set = node.node.ALT_DEFAULT_ALLOW_SET
        # Pull any values left from the parent or, as a final resort,
        # the alt_defaults object.
        for fr, to in node.node.expose_map.items():
            if fr not in ovrde_bind:
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
    items: tuple = None


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
    clazz: type = None

    def bind_signature(self, signature):
        return signature.bind_partial(*self.arg, **self.kwds).arguments


def dtargs(*arg, clazz=None, **kwds):
    return Args(arg, kwds, clazz=clazz)


def _initialize_node_instances(clz, instance):
    '''Post dataclass initialization binding of nodes to instance.'''
    nodes = getattr(clz, DATATREE_SENTIENEL_NAME)

    bindings = []
    for name, node in nodes.items():
        # The cur-value may contain args specifically for this node.
        cur_value = getattr(instance, name)
        if isinstance(cur_value, BoundNode):
            field_value = cur_value.chain(instance, node)
        elif isinstance(cur_value, Node):
            field_value = BoundNode(instance, name, node, cur_value)
        elif isinstance(cur_value, BindingDefault):
            # Evaluate the default value after all BoundNode initializations.
            bindings.append((name, cur_value))
            continue
        else:
            # Parent node has passed something other than a Node or a chained BoundNode.
            # Assume they just want to have it called.
            continue
        _field_assign(instance, name, field_value)

    # Evaluate any default values after all BoundNode initializations.
    # This allows binding functions to reference any Node fields as
    # long as the Node fields do not use bindings that not evaluated yet.
    for name, cur_value in bindings:
        field_value = cur_value.self_default(instance)
        _field_assign(instance, name, field_value)


# Provide dataclass compatiability post python 3.8.
# Default values for the dataclass function post Python 3.8.
_POST_38_DEFAULTS = dtargs(match_args=True, kw_only=False, slots=False).kwds


def _process_datatree(clz, init, repr, eq, order, unsafe_hash, frozen,
                      match_args, kw_only, slots, chain_post_init, provide_override_field):

    if OVERRIDE_FIELD_NAME in clz.__annotations__:
        if clz.__annotations__[OVERRIDE_FIELD_NAME] != Overrides:
            raise ReservedFieldNameException(
                f'Reserved field name {OVERRIDE_FIELD_NAME} used by class '
                f'{clz.__name__}')
    if provide_override_field:
        clz.__annotations__[OVERRIDE_FIELD_NAME] = Overrides
        setattr(clz, OVERRIDE_FIELD_NAME, field(default=None, repr=False))

    post_init_chain = dict()
    if chain_post_init:
        # Collect all the __post_init__ functions being inherited and place
        # them in a tuple of functions to call.
        for bclz in clz.__mro__[1:-1]:
            if hasattr(bclz, '__post_init_chain__'):
                post_init_chain.update(
                    dict().fromkeys(bclz.__post_init_chain__))

            if hasattr(bclz, '__post_init__'):
                post_init_func = getattr(bclz, '__post_init__')
                if not hasattr(post_init_func, '__is_datatree_override_post_init__'):
                    post_init_chain[post_init_func] = None

    if hasattr(clz, '__post_init__'):
        post_init_func = getattr(clz, '__post_init__')
        if not hasattr(post_init_func, '__is_datatree_override_post_init__'):
            if post_init_func not in post_init_chain:
                post_init_chain[post_init_func] = None

    clz.__post_init_chain__ = tuple(post_init_chain.keys())
    clz.__initialize_node_instances_done__ = False

    def override_post_init(self):  # TODO: Add support for InitVars.
        if not self.__initialize_node_instances_done__:
            _field_assign(self,
                          '__initialize_node_instances_done__',
                          True)
            _initialize_node_instances(clz, self)
            
            for post_init_func in reversed(self.__post_init_chain__):
                post_init_func(self)
    
    override_post_init.__is_datatree_override_post_init__ = True
    clz.__post_init__ = override_post_init

    _apply_node_fields(clz)

    values_post_38 = dtargs(match_args=match_args,
                            kw_only=kw_only, slots=slots).kwds
    values_post_38_differ = dict(
        ((k, v) for k, v in values_post_38.items() if v != _POST_38_DEFAULTS[k]))

    dataclass(clz, init=init, repr=repr, eq=eq, order=order,
              unsafe_hash=unsafe_hash, frozen=frozen, **values_post_38_differ)

    return clz


def datatree(clz=None, /, *, init=True, repr=True, eq=True, order=False,
             unsafe_hash=False, frozen=False, match_args=True,
             kw_only=False, slots=False, chain_post_init=False,
             provide_override_field=True):
    '''Python decorator similar to dataclasses.dataclass providing parameter injection,
    injection, binding and overrides for parameters deeper inside a tree of objects.
    Args:
        clz: The class to decorate.
        init: If True, a __init__ method will be generated.
        repr: If True, a __repr__ method will be generated.
        eq: If True, __eq__ and __ne__ methods will be generated.
        order: If True, __lt__, __le__, __gt__, and __ge__ methods will be generated.
        unsafe_hash: If True, a __hash__ method will be generated.
        frozen: If True, the class is made immutable.
        match_args: If True, the generated __init__ method will accept only the parameters
            that are defined in the class.
        kw_only: If True, the generated __init__ method will accept only keyword arguments.
        slots: If True, the class will be a slots class.
        chain_post_init: If True, the __post_init__ method will chain the post init methods
            of the base classes.
        provide_override_field: If True, the class will provide an override field that can be
            used to provide overrides for the Node fields
    '''

    def wrap(clz):
        return _process_datatree(
            clz, init, repr, eq, order, unsafe_hash, frozen, match_args, kw_only, 
            slots, chain_post_init, provide_override_field)

    # See if we're being called as @datatree or @datatree().
    if clz is None:
        # We're called with parens.
        return wrap

    # We're called as @datatree without parens.
    return wrap(clz)
