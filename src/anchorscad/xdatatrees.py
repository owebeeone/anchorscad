'''
Provides annotations over datatrees to create xml deserializer/serializers 
to convert xml->datatree (python objects) and back i.e., datatree<->xml.

'''

from dataclasses import dataclass, MISSING, field, Field
from anchorscad import datatree, dtfield
from typing import Any, Optional, List, Dict, Tuple, Type
from types import FunctionType
import lxml.etree as etree
import inspect
import re
from itertools import chain
from copy import deepcopy
import sys


class TooManyValuesError(ValueError):
    '''Raised when multiple values are provided for a field that only allows one.'''

class UnspecifiedValue:
    def __bool__(self):
        return False
    
UNSPECIFIED=UnspecifiedValue()

# Validate parameters provided to xfield() passed into dtfield() and field() are valid.
_ALLOWED_XFIELD_PARAMS=\
    set(inspect.signature(field).parameters.keys()).union(
        inspect.signature(dtfield).parameters.keys())


# This field is used to store the default values for the fields.
XDATATREE_CONFIG_FIELD_NAME='XDATATREE_CONFIG'

# When parsing xml, this field is used to store the xml elements and attributes
# that were not used to populate the class.
XDATATREE_UNUSED_XML_ELEMENTS='xdatatree_unused_xml_elements'
XDATATREE_UNUSED_XML_ATTRIBUTES='xdatatree_unused_xml_attributes'

# When parsing xml, this field is used to store the parser spec for the class.
XDATATREE_PARSER_SPEC='XDATATREE_PARSER_SPEC'


class ValueCollector:
    '''Base type for collecting values for a field.'''
    
    def append(self, value):
        raise NotImplementedError('Abstract method, implement in subclass')
    
    def get(self):
        raise NotImplementedError('Abstract method, implement in subclass')

    @classmethod    
    def to_contained_type(self, value):
        raise NotImplementedError('Abstract method, implement in subclass')


class PythonNameToXmlNameProvider:
    '''Derives xml element and sttribute names by transforming the python class or field
    names. This allows for automatic naming consistency between the python and xml forms.'''
    @classmethod
    def to_xml(clz, name):
        raise NotImplementedError('Abstract method, implement in subclass')
    
    @classmethod
    def xml_name_selector(
            clz: 'PythonNameToXmlNameProvider', 
            xml_data_type: 'XmlDataType', 
            field_name : str, 
            class_name: str):
        '''Returns a name given the field name or the destination class name.
        This is the default implementation, it returns the field name if the
        xml_data_type is not an Element, otherwise it returns the class name.
        This is somewhat consistent with how XML element names being associated
        with the class of objects they represent.'''
        if isinstance(xml_data_type, _Element):
            return class_name
        return field_name


class CamelSnakeConverter(PythonNameToXmlNameProvider):
    '''A PythonNameToXmlNameProvider converts between camel case and snake case.
    This converter will transform python field and class names to corresponding
    xml element names and attribute names.
    '''
    @classmethod
    def to_xml(clz, name):
        '''This method overrides the superclass method to_xml.'''
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    @classmethod
    def from_xml(clz, name):
        '''This is just for completeness, it is not used by the xdatatree.'''
        components = name.split('_')
        return ''.join(x.title() for x in components)
    
class SnakeCamelConverter(PythonNameToXmlNameProvider):
    '''A PythonNameToXmlNameProvider converts between camel case and snake case.
    This converter will transform python field and class names to corresponding
    xml element names and attribute names.
    '''
    @classmethod
    def to_xml(clz, name):
        '''This is just for completeness, it is not used by the xdatatree.'''
        components = name.split('_')
        return ''.join(x.title() for x in components)
    
    @classmethod
    def from_xml(clz, name):
        '''This method overrides the superclass method to_xml.'''
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()



class XmlDataType:
    '''Base class for xml data types. e.g. Element, Attribute or Metadata.
    Thwse classes are instantiated by the xdatatree parser when it encounters an 
    attribute or an element that is mapped to the field. The ValueCollector class is 
    used to collect potentially multiple values for the field and to convert the values
    to the native python type of the field.'''
    @classmethod
    def xml_field_name_of(
        clz,
        container: Type, 
        field_types: List[Type], 
        python_field_name: str, 
        field_config: '_XFieldParams'):
        '''Return the xml field name for the python field name.'''
        raise NotImplementedError('Abstract method, implement in subclass')
    
    @classmethod
    def apply_collector_type(clz, parser_spec: 'XmlParserSpec', xml_field_spec: 'XmlFieldSpec'):
        ''''Should add the collector to the appropriate map entry fot this associated parser
        context'''
        raise NotImplementedError('Abstract method, implement in subclass')
    

@dataclass
class XmlFieldSpec:
    '''Each xdatatree field is associated with an XmlFieldSpec class. '''

    field_name: str
    xml_name: str    
    ftype: XmlDataType
    collector_type: ValueCollector

    def __post_init__(self):
        assert isinstance(self.field_name, str), 'field_name must be a string'
        assert isinstance(self.xml_name, str), 'xml_name must be a string'
        assert isinstance(self.ftype, XmlDataType), 'ftype must be a XmlDataType'
    
    def new_collector(self):
        return self.collector_type()
    
    def get_xml_name(self):
        return self.xml_name
    
    def get_field_name(self):
        return self.field_name
    

@dataclass
class XmlObjectBuilder:
    '''Builds an object from an xml element.'''
    xml_node: etree.ElementBase
    result_dict: Dict[str, Any] = field(default_factory=dict)
    contains_unknown_elements: bool = field(default=False)
    contains_unknown_attributes: bool = field(default=False)
    
    def get_element_name(self):
        qname = etree.QName(self.xml_node.tag)
        return qname.localname
    
    def _add_entry(self, name: str, value: Any, container_factory: FunctionType):
        if not name in self.result_dict:
            if container_factory is None:
                self.result_dict[name] = value
            else:
                self.result_dict[name] = container_factory()
                self.result_dict[name].append(value)
        else:
            if container_factory is None:
                raise TooManyValuesError(
                    f'In element {self.get_element_name()}, '
                    f'multiple attributes named {name} exist, only one allowed.')
            else:
                try:
                    self.result_dict[name].append(value)
                except TooManyValuesError as e:
                    raise TooManyValuesError(
                        f'In element {self.get_element_name()}, '
                        f'multiple attributes named {name} exist, only one allowed.')
        
    
    def add_unknown_attribute(self, attribute_name: str, attribute_value: str):
        self._add_entry(
            XDATATREE_UNUSED_XML_ATTRIBUTES, (attribute_name, attribute_value), list)
        self.contains_unknown_attributes = True
    
    def add_unknown_element(self, xml_element: etree.ElementBase):
        self._add_entry(XDATATREE_UNUSED_XML_ELEMENTS, xml_element, list)
        self.contains_unknown_elements = True
    
    def add_value(self, field_spec: XmlFieldSpec, value: Any):
        self._add_entry(field_spec.field_name, value, field_spec.collector_type)
        
    # def build_object(self, field_spec: XmlFieldSpec):
    #     '''Build the object from the subelement_result.'''
    #     kwds = {}
    #     for name, value in self.result_dict.items():
    #         kwds[name] = value
        
    #     new_obj = field_spec.collector_type.CONTAINED_TYPE(**kwds)
    #     return new_obj
    
    def merge_status(self, sub_result: 'XmlObjectBuilder'):
        '''Merge the status of the sub_result into this result.'''
        self.contains_unknown_attributes = \
            self.contains_unknown_attributes or sub_result.contains_unknown_attributes
        self.contains_unknown_elements = \
            self.contains_unknown_elements or sub_result.contains_unknown_elements

@dataclass(frozen=True)
class XmlParserOptions:
    '''Options for deserializing.'''
    respect_namespace: bool = field(default=True)
    assert_unused_elements: bool = field(default=False)
    assert_unused_attributes: bool = field(default=False)
    print_unused_elements: bool = field(default=False)
    print_unused_attributes: bool = field(default=False)

DESERIALIZE_OPTIONS=XmlParserOptions()


@dataclass
class XmlParserSpec:
    '''Specification for parsing an xml element.'''
    
    xml_element_specs: Dict[str, XmlFieldSpec] = field(default_factory=dict)
    xml_attribute_specs: Dict[str, XmlFieldSpec] = field(default_factory=dict)
    metadata_specs: Dict[str, XmlFieldSpec] = field(default_factory=dict)
    
    def add_element_spec(self, field_spec: XmlFieldSpec):
        self._check_collision_and_add(self.xml_element_specs, field_spec)
        
    def add_attribute_spec(self, attribute_spec: XmlFieldSpec):
        self._check_collision_and_add(self.xml_attribute_specs, attribute_spec)
        
    def add_metadata_spec(self, metadata_spec: XmlFieldSpec):
        self._check_collision_and_add(self.metadata_specs, metadata_spec)

    def _check_collision_and_add(self, specs, field_spec: XmlFieldSpec):
        xml_name = field_spec.get_xml_name()
        
        current_spec = specs.get(xml_name, None)
        if not current_spec is None:
            raise ValueError(
                f'In element {field_spec.get_field_name()}, '
                f'{field_spec.xml_name} is already defined as an attribute by '
                f'field {current_spec.get_field_name()}.')
        specs[xml_name] = field_spec
        
    def deserialize_subelement(self, xml_element: etree.ElementBase, options: XmlParserOptions):
        '''Parse the xml element and return a dictionary of values.'''
        result = XmlObjectBuilder(xml_element)
        
        for attr_name, attr_value in xml_element.items():
            field_spec = self.xml_attribute_specs.get(attr_name, None)
            
            if field_spec is None:
                result.add_unknown_attribute(attr_name, attr_value)
            else:
                result.add_value(field_spec, attr_value)
                
        
        for elem in xml_element.getchildren():
            field_spec = self.xml_element_specs.get(elem.tag, None)
            
            if field_spec is None:
                elem_qname = etree.QName(elem.tag)
                if elem_qname.localname == 'metadata':
                    metadata_name = elem.attrib.get('key', None)
                    if metadata_name:
                        metadata_value = elem.attrib.get('value', None)
                    else:
                        metadata_name = elem.attrib.get('name', None)
                        metadata_value = elem.text if elem.text else ''
                    
                    if metadata_name is None:
                        raise ValueError(
                            f'In element {result.get_element_name()}, '
                            f'metadata element {elem_qname.localname} is missing name attribute.')
                    
                    if metadata_value is None:
                        raise ValueError(
                            f'In element {result.get_element_name()}, '
                            f'metadata element {elem_qname.localname} is missing value attribute.')
                        
                    field_spec = self.metadata_specs.get(metadata_name, None)
                    if field_spec is None:
                        result.add_unknown_element(elem)
                    else:
                        # Have a metadata value
                        result.add_value(field_spec, metadata_value)
                else:
                    # An eleement that is not a metadata element and it's unknown.
                    result.add_unknown_element(elem)
            else:
                # A known element, recursively run the parser.
                contained_type = field_spec.collector_type.CONTAINED_TYPE
                parser_spec = getattr(contained_type, XDATATREE_PARSER_SPEC, None)
                value, sub_result = parser_spec.deserialize(
                    elem, field_spec.collector_type.CONTAINED_TYPE, options=options)
                
                result.add_value(field_spec, value)
                result.merge_status(sub_result)
                
        return result
    
    def deserialize(self, xml_element: etree.ElementBase, clz: type, options: XmlParserOptions=DESERIALIZE_OPTIONS):
        '''Parse the xml element and return an instance of clz.'''
        result = self.deserialize_subelement(xml_element, options)
        
        kwds = {}
        for name, value in result.result_dict.items():
            if isinstance(value, ValueCollector):
                value = value.get()

            kwds[name] = value
        
        new_obj = clz(**kwds)
        
        # Report unused elements and attributes. These are added to the xdatatree object
        # and will be rendered as is if the object is serialized back to xml although the
        # order is not preserved.
        if XDATATREE_UNUSED_XML_ATTRIBUTES in kwds:
            name = get_xml_path(xml_element)
            if options.assert_unused_attributes:
                raise ValueError(
                    f'In element {name}, '
                    f'unknown attributes found: {get_unused_xml_attribute_names(kwds)}')
            elif options.print_unused_attributes:
                print(
                    f'In element {name}, '
                    f'unknown attributes found: {get_unused_xml_attribute_names(kwds)}',
                    file=sys.stderr)
        if XDATATREE_UNUSED_XML_ELEMENTS in kwds:
            name = xml_element.getroottree().getpath(xml_element)
            if options.assert_unused_elements:
                raise ValueError(
                    f'In element {name}, '
                    f'unknown elements found: {get_unused_xml_element_names(kwds)}')
            elif options.print_unused_elements:
                print(
                    f'In element {name}, '
                    f'unknown elements found: {get_unused_xml_element_names(kwds)}',
                    file=sys.stderr)
        
        return new_obj, result
    
    
def make_xml_name_from(tag: str, nsmap: dict) -> str:
    qname = etree.QName(tag)
    if not qname.namespace:
        return qname.localname
    inverted_nsmap = {value: key for key, value in nsmap.items()}
    if qname.namespace in inverted_nsmap:
        nsname = inverted_nsmap[qname.namespace]
        if nsname:
            return f'{nsname}:{qname.localname}'
    return qname.localname


def get_xml_path(xml_element: etree.ElementBase) -> str:
    '''Return the xml path of the element.'''
    root = xml_element.getroottree().getroot()
    nsmap = root.nsmap
    path = [make_xml_name_from(xml_element.tag, nsmap)]
    while not xml_element is root:
        xml_element = xml_element.getparent()
        path.append(make_xml_name_from(xml_element.tag, nsmap))
    return '/'.join(reversed(path))

def get_unused_xml_element_names(kwds: dict) -> List[str]:
    '''Return a list of unused XML element names.'''
    return list((_describe_element(e) for e in kwds[XDATATREE_UNUSED_XML_ELEMENTS]))

def get_unused_xml_attribute_names(kwds: dict) -> List[str]:
    '''Return a list of unused XML attribute names.'''
    return list((a[0] for a in kwds[XDATATREE_UNUSED_XML_ATTRIBUTES]))

def _describe_element(e: etree.ElementBase) -> str:
    ename = etree.QName(e.tag).localname
    if ename == 'metadata':
        key = e.attrib.get('key', None)
        if key:
            return f'metadata(key="{key})"'
        name = e.attrib.get('name', None)
        if name:
            return f'metadata(name="{name})"'
        return 'metadata (no key or name)'
        

def deserialize(xml_element: etree.ElementBase, clz: type, options: XmlParserOptions=DESERIALIZE_OPTIONS):
    '''Parse the xml element and return an instance of clz.'''
    parser_spec = getattr(clz, XDATATREE_PARSER_SPEC, None)
    if parser_spec is None:
        raise ValueError(f'Class {clz.__name__} is not a xdatatree class.')
    
    return parser_spec.deserialize(xml_element, clz, options)


UNSPECIFIED_OR_NONE = (UNSPECIFIED, None)

@datatree(frozen=True)
class _XFieldParams:
    '''Stores parameters for fields. These parameters include all those
    provided by datatrees.dtfield which also includes all the parameters
    provided by dataclasses.field.
    
    The xdatatree field specifier, function xfield (see below) creates instances
    of this class. Upon the xdatatree decorator processing this class, it will
    replace all instances of the this class with instances of the dataclasses
    Field class. The xdatatree specific parameters will be added to 
    dataclasses.field metadata.
    
    This class is composable, in that it's __call__ method can be used to
    create new instances of this class with the same parameters as the original
    but with some parameters overridden.
    
    '''
    
    ftype: Optional[XmlDataType] = UNSPECIFIED
    exmlns: Optional[str] = UNSPECIFIED
    ename_transform: Optional[PythonNameToXmlNameProvider] = UNSPECIFIED
    ename: Optional[str] = UNSPECIFIED
    axmlns: Optional[str] = UNSPECIFIED
    aname_transform: Optional[PythonNameToXmlNameProvider] = UNSPECIFIED
    aname: Optional[str] = UNSPECIFIED
    exclude: Optional[bool] = UNSPECIFIED
    other_params: dict = UNSPECIFIED  # Other parameters to pass to datatrees.dtfield
    builder: Type[ValueCollector] = UNSPECIFIED
    
    def __post_init__(self):
        assert self.ftype in UNSPECIFIED_OR_NONE or isinstance(self.ftype, XmlDataType), \
            f'ftype must be an instance of XmlDataType, Attribute, Element or Metadata'
        assert self.ename in UNSPECIFIED_OR_NONE or isinstance(self.ename, str), \
            f'ename must be a string'
        assert self.exmlns in UNSPECIFIED_OR_NONE or isinstance(self.exmlns, str), \
            f'exmlns must be a string'
        assert self.ename_transform in UNSPECIFIED_OR_NONE  \
            or isinstance(self.ename_transform, PythonNameToXmlNameProvider) \
            or issubclass(self.ename_transform, PythonNameToXmlNameProvider), \
            f'ename_transform must be an instance of KeyOrNameConverter'
        assert self.aname in UNSPECIFIED_OR_NONE or isinstance(self.aname, str), \
            f'aname must be a string'
        assert self.axmlns in UNSPECIFIED_OR_NONE or isinstance(self.axmlns, str), \
            f'axmlns must be a string'
        assert self.aname_transform in UNSPECIFIED_OR_NONE  \
            or isinstance(self.aname_transform, PythonNameToXmlNameProvider) \
            or issubclass(self.aname_transform, PythonNameToXmlNameProvider), \
            f'aname_transform must be an instance of KeyOrNameConverter'
        assert self.exclude in UNSPECIFIED_OR_NONE or isinstance(self.exclude, bool), \
            f'exclude must be a bool'
        assert self.other_params in UNSPECIFIED_OR_NONE or isinstance(self.other_params, dict), \
            f'other_params must be a dict'
        if not self.other_params is UNSPECIFIED:
            invalid_params = set(self.other_params.keys()).difference(_ALLOWED_XFIELD_PARAMS)
            assert not invalid_params, f'_XFieldParams Invalid other_params {invalid_params}'
        assert self.builder in UNSPECIFIED_OR_NONE or issubclass(self.builder, ValueCollector), \
            f'builder {self.builder} must be a subclass of ValueCollector'
    
    def __call__(self, 
                 ftype: 'XmlDataType' = UNSPECIFIED, 
                 xmlns: Optional[str] = UNSPECIFIED,
                 exmlns: Optional[str] = UNSPECIFIED,
                 ename_transform: PythonNameToXmlNameProvider = UNSPECIFIED,
                 ename: str = UNSPECIFIED,
                 axmlns: Optional[str] = UNSPECIFIED,
                 aname_transform: PythonNameToXmlNameProvider = UNSPECIFIED,
                 aname: str = UNSPECIFIED,
                 exclude: bool = UNSPECIFIED,
                 builder: Type[ValueCollector] = UNSPECIFIED,
                 **kwds: Any) -> Any:
        '''Create a new instance of this class with the passed in values
        overriding the values in this instance.'''
        
        if not xmlns is UNSPECIFIED:
            if exmlns is UNSPECIFIED:
                exmlns = xmlns
            if axmlns is UNSPECIFIED:
                axmlns = xmlns

        if ftype is UNSPECIFIED:
            ftype = self.ftype
            
        if exmlns is UNSPECIFIED:
            exmlns = self.exmlns
        
        if ename_transform is UNSPECIFIED:
            if ename is UNSPECIFIED:
                ename_transform = self.ename_transform
                ename = self.ename
            else:
                ename_transform = UNSPECIFIED
                ename = ename
        else:
            if ename is UNSPECIFIED:
                ename_transform = ename_transform
                ename = UNSPECIFIED
            else:
                raise ValueError('Cannot specify both ename and ename_transform')
            
        if axmlns is UNSPECIFIED:
            axmlns = self.axmlns
            
        if aname_transform is UNSPECIFIED:
            if aname is UNSPECIFIED:
                aname_transform = self.aname_transform
                aname = self.aname
            else:
                aname_transform = UNSPECIFIED
                aname = aname
        else:
            if aname is UNSPECIFIED:
                aname_transform = aname_transform
                aname = UNSPECIFIED
            else:
                raise ValueError('Cannot specify both aname and aname_transform')
        
        if ftype is UNSPECIFIED:
            ftype = self.ftype
            
        if exclude is UNSPECIFIED:
            exclude = self.exclude
            
        if builder is UNSPECIFIED:
            builder = self.builder
        
        other_params = kwds
        if not other_params:
            other_params = self.other_params
        elif not self.other_params is UNSPECIFIED:
            # Override individual entries in self.other_params with kwds.
            other_params = {**self.other_params, **other_params}
            
        return _XFieldParams(
            ftype=ftype, 
            exmlns=exmlns,
            ename_transform=ename_transform,
            ename=ename,
            axmlns=axmlns,
            aname_transform=aname_transform,
            aname=aname,
            exclude=exclude,
            builder=builder,
            other_params=other_params)
        
    def apply(self, other: Optional['_XFieldParams']) -> '_XFieldParams':
        '''Create a new instance of this class with the passed in _XFieldParams
        overriding the values in this instance.'''
        if other is UNSPECIFIED:
            return self
        
        # Use the () operator...
        return self(
            ftype=other.ftype, 
            exmlns=other.exmlns,
            ename_transform=other.ename_transform,
            ename=other.ename,
            axmlns=other.axmlns,
            aname_transform=other.aname_transform,
            aname=other.aname,
            exclude=other.exclude,
            builder=other.builder,
            **other.other_params)
        
    def is_default_specified(self):
        '''Return true if any of the ways to specify a default value are specified.'''
        return not (self.other_params.get('default', UNSPECIFIED) is UNSPECIFIED
            and self.other_params.get('default_factory', UNSPECIFIED) is UNSPECIFIED
            and self.other_params.get('self_default', UNSPECIFIED) is UNSPECIFIED)
    
    def fieldof(self):
        '''Return a dataclasses.Field instance for this field.'''

        if not self.is_default_specified():
            # No default value specified, use the default value of the ftype.
            return dtfield(default=None, **self.other_params)

        return dtfield(**self.other_params)
        
DEFAULT_XFIELD_PARAMS=_XFieldParams()

@datatree(frozen=True)
class XmlFieldSpecifier:
    element_name: Optional[str] = dtfield(None, doc='The name of the xml element or none if an attribute')
    attribute_name: Optional[str] = dtfield(None, doc='The name of the xml attribute or none if an element')
    metadata_name: Optional[str] = dtfield(None, doc='The name of the metadata name an attribute')
    metadata_value: Optional[str] = dtfield(None, doc='The name of the metadata value an attribute')

    @classmethod
    def metadata(clz, metadata_attribute_name_name: str, metadata_attribute_value_name: str):
        '''Return a new XmlFieldSpecifier with the metadata name and value set.'''
        return XmlFieldSpecifier(
            element_name='metadata',
            attribute_name=None,
            metadata_name=metadata_attribute_name_name,
            metadata_value=metadata_attribute_value_name)
    
def _select_name_from_spec(
        xml_data_type: XmlDataType,
        transform: PythonNameToXmlNameProvider, 
        python_type: str, 
        python_field_name: str):
    '''Return the name selected by the transform.'''
    if transform in UNSPECIFIED_OR_NONE:
        return python_field_name
    
    selected_name = transform.xml_name_selector(
        xml_data_type, python_field_name, python_type.__name__)

    return transform.to_xml(selected_name)

class _Attribute(XmlDataType):
    '''The type for XML attribute'''
    def xml_field_name_of(
            self,
            container: Type, 
            field_types: List[Type], 
            python_field_name: str,
            field_config: _XFieldParams):
        # The name has been specified, no transform is required.
        if not field_config.aname in UNSPECIFIED_OR_NONE:
            return field_config.aname, field_config.axmlns
        
        # attribute names are based on the python field name.
        if field_config.aname_transform in UNSPECIFIED_OR_NONE:
            return python_field_name, field_config.axmlns

        return _select_name_from_spec(
            self,
            field_config.aname_transform,
            field_types[0],
            python_field_name), field_config.axmlns
    
    @classmethod
    def apply_collector_type(
        clz, parser_spec: XmlParserSpec, xml_field_spec: XmlFieldSpec):
        parser_spec.add_attribute_spec(xml_field_spec)
        
    
    def serialize(self, xml_node: etree.ElementBase, name: str, value: Any):
        '''Place the attribute value in the xml_node.'''
        if value is None:
            return
        xml_node.set(name, str(value))


Attribute=_Attribute()
        
    
class _Element(XmlDataType):
    '''The type for XML element'''
    
    def xml_field_name_of(
            self,
            container: Type, 
            field_types: List[Type], 
            python_field_name: str,
            field_config: _XFieldParams):
        # attribute names are based on the python field name.
        if not field_config.ename in UNSPECIFIED_OR_NONE:
            return field_config.ename, field_config.exmlns
        
        # attribute names are based on the python field name.
        if field_config.ename_transform in UNSPECIFIED_OR_NONE:
            return python_field_name, field_config.exmlns

        return _select_name_from_spec(
            self,
            field_config.ename_transform,
            field_types[0],
            python_field_name), field_config.exmlns
    
    @classmethod
    def apply_collector_type(
        clz, parser_spec: XmlParserSpec, xml_field_spec: XmlFieldSpec):
        parser_spec.add_element_spec(xml_field_spec)
        
        
    def serialize(self, xml_node: etree.ElementBase, name: str, value: Any):
        '''Place the element value in the xml_node.'''
        if isinstance(value, list) or inspect.isgenerator(value):
            for item in value:
                child = etree.SubElement(xml_node, name)
                _serialize(child, item)
        else:
            if value is None:
                return
            child = etree.SubElement(xml_node, name)
            _serialize(child, value)


Element=_Element()

@dataclass
class _Metadata(XmlDataType):
    '''The type for metadata elements containing "name" and "value" attributes.'''
    is_name_value: bool = field(default=True)
 
    def xml_field_name_of(
            self,
            container: Type, 
            field_types: List[Type], 
            python_field_name: str,
            field_config: _XFieldParams):
        xml_name, xmlns = Attribute.xml_field_name_of(
            container, field_types, python_field_name, field_config)
        # Metadata does not use the namespaces.
        return xml_name, None

    @classmethod 
    def apply_collector_type(
        clz, parser_spec: XmlParserSpec, xml_field_spec: XmlFieldSpec):
        parser_spec.add_metadata_spec(xml_field_spec)
        
    def serialize(self, xml_node: etree.ElementBase, name: str, value: Any):
        '''Place the metadata value in the xml_node.'''
        if value is None:
            return
        
        value_str = value if isinstance(value, str) else str(value)
        if self.is_name_value:
            etree.SubElement(xml_node, 'metadata', name=name).text = value_str
        else:
            etree.SubElement(xml_node, 'metadata', key=name, value=value_str)

Metadata=_Metadata(is_name_value=False)
MetadataNameValue=_Metadata(is_name_value=True)


def _serialize(xml_node: etree.ElementBase, xdatatree_object: Any):
    '''Serialize an xdatatree to an xml node.'''
    if xdatatree_object is None:
        return
    
    parser_spec = xdatatree_object.XDATATREE_PARSER_SPEC
    
    all_values = chain(
        parser_spec.xml_attribute_specs.items(),
        parser_spec.metadata_specs.items(),
        parser_spec.xml_element_specs.items())
        
    for xml_name, field_spec in all_values:
        field_name = field_spec.field_name
        collector_type = field_spec.collector_type
        value = getattr(xdatatree_object, field_name)
        value = collector_type.to_contained_type(value)
        field_spec.ftype.serialize(xml_node, xml_name, value)
    
    if xdatatree_object.xdatatree_unused_xml_attributes:
        for name, value in xdatatree_object.xdatatree_unused_xml_attributes:
            xml_node.set(name, value)
    
    if xdatatree_object.xdatatree_unused_xml_elements:
        for elem in xdatatree_object.xdatatree_unused_xml_elements:
            elem = deepcopy(elem)
            xml_node.append(elem)
        
    
    return xml_node

def serialize(xdatatree_object: Any, name: str, namespaces: Optional[Dict[str, str]] = None):
    '''Serialize an xdatatree to a new xml node with the given name.'''
    
    xml_node = etree.Element(name, nsmap=namespaces) if namespaces else etree.Element(name)
    
    return _serialize(xml_node, xdatatree_object)


def xfield(ftype: 'XmlDataType' = UNSPECIFIED, 
           xmlns: Optional[str] = UNSPECIFIED,
           exmlns: Optional[str] = UNSPECIFIED,
           ename_transform: PythonNameToXmlNameProvider = UNSPECIFIED,
           ename: str = UNSPECIFIED,
           axmlns: Optional[str] = UNSPECIFIED,
           aname_transform: PythonNameToXmlNameProvider = UNSPECIFIED,
           aname: str = UNSPECIFIED,
           exclude: bool = UNSPECIFIED,
           builder: Type[ValueCollector] = UNSPECIFIED,
           **kwargs) -> _XFieldParams:
    '''Like datatrees.dtfield but also supports annotations for xml parsing.
    Args:
      ftype: The type of the xml data. One of Attribute, Element or Metadata.
      ename: Optional, the name of the xml element.
      ename_transform: The transform to apply to the class name.
    '''
    # Validate the parameters.
    invalid_params = set(kwargs.keys()).difference(_ALLOWED_XFIELD_PARAMS)
    assert not invalid_params, f'xfield Invalid parameters {invalid_params}'

    if not xmlns is UNSPECIFIED:
        if exmlns is UNSPECIFIED:
            exmlns = xmlns
        if axmlns is UNSPECIFIED:
            axmlns = xmlns

    return _XFieldParams(
            ftype=ftype, 
            exmlns=exmlns,
            ename_transform=ename_transform,
            ename=ename,
            axmlns=axmlns,
            aname_transform=aname_transform,
            aname=aname,
            exclude=exclude,
            builder=builder,
            other_params=kwargs)


def _get_field_type(annotated_type):
    '''Return the container type and the field types for the annotated type.'''
    if hasattr(annotated_type, '__origin__') and hasattr(annotated_type, '__args__'):
        # This is a typing type.
        field_types = annotated_type.__args__
        container = annotated_type.__origin__
    else:
        container = None
        field_types = (annotated_type,)
        
    return container, field_types


def get_xml_field_name(
    clz: Type, python_field_name: str, field_annotation: Type, field_config: _XFieldParams):
    '''Return the xml field name for the python field name.'''

    ftype = field_config.ftype
    if ftype is UNSPECIFIED:
        # If the field type is missing, then the field is not an xml field.
        return None
    
    container, field_types = _get_field_type(field_annotation)
    
    xml_field_name, xmlns = ftype.xml_field_name_of(
        container, field_types, python_field_name, field_config)
    
    if xmlns in (None, UNSPECIFIED):
        return xml_field_name
    
    return etree.QName(xmlns, xml_field_name).text


def _get_field_as_params(current_field_value: Field) \
        -> Tuple[Dict[str, Any], Optional[_XFieldParams]]:
    '''
    Return the field as a dictionary of parameters and if the default value
    is a _XFieldParams, that as well.
    '''
    
    if new_default_value is UNSPECIFIED:
        new_default_value = None
    
    all_values = (
        (fname, getattr(current_field_value, fname, MISSING)) 
            for fname in _ALLOWED_XFIELD_PARAMS)
    
    curr_values = dict((k, v) for k, v in all_values if not v is MISSING)
    
    default_value = curr_values.get('default', UNSPECIFIED)
    if isinstance(default_value, _XFieldParams):
        del curr_values['default']
        default_value = UNSPECIFIED
        
    return curr_values, default_value


def _get_collector_type(annotation: Any) -> Tuple[type, bool]:
    if hasattr(annotation, '__origin__') and hasattr(annotation, '__args__'):
        # Assume it's a typing module annotation specifier.
        container_type = annotation.__origin__
        contained_types = annotation.__args__
        
        if container_type is list:
            @dataclass
            class ListCollector(ValueCollector):
                CONTAINED_TYPE=contained_types[0] # The type of the items.
                value: annotation = field(default_factory=container_type)
                    
                def append(self, item: CONTAINED_TYPE):
                    # Perform conversion.
                    if not isinstance(item, self.CONTAINED_TYPE):
                        item = self.CONTAINED_TYPE(item)
                    self.value.append(item)
                    
                def get(self):
                    return self.value
                
                @classmethod
                def to_contained_type(cls, value: List[CONTAINED_TYPE]):
                    return value
                
            return ListCollector
                
        elif container_type is tuple:
            @dataclass
            class TupleCollector(ValueCollector):
                CONTAINED_TYPE=contained_types[0]
                value: List[contained_types[0]] = field(default_factory=list)
                    
                def append(self, item: CONTAINED_TYPE):
                    # Perform conversion.
                    if not isinstance(item, self.CONTAINED_TYPE):
                        item = self.CONTAINED_TYPE(item)
                    
                    self.value.append(item)
                    
                def get(self):
                    return tuple(self.value)
                
                @classmethod
                def to_contained_type(cls, value: Tuple[CONTAINED_TYPE]):
                    return value
                
            return TupleCollector
        
    else:
        @dataclass
        class SingleValueCollector(ValueCollector):
            CONTAINED_TYPE=annotation
            value: annotation = UNSPECIFIED
                
            def append(self, item: CONTAINED_TYPE):
                # Perform conversion.
                if not isinstance(item, self.CONTAINED_TYPE):
                    item = self.CONTAINED_TYPE(item)
                    
                if not self.value is UNSPECIFIED:
                    raise TooManyValuesError(
                        f'Cannot speficy multiple values for')
                self.value = item
                
            def get(self):
                return self.value
            
                
            @classmethod
            def to_contained_type(cls, value: CONTAINED_TYPE):
                return value
            
        return SingleValueCollector
        
def _diagnostic_name_of_ftype(ftype: XmlDataType):
    '''Provides a diagnostic name for the ftype.'''
    name = getattr(ftype, '__name__', None)
    if name:
        return name
    
    return repr(ftype)

def _process_field(
    clz: type,
    field_name: str, 
    field_annotation: Any,
    class_config: _XFieldParams,
    parser_spec: XmlParserSpec) -> Field:
    '''Process a field annotation. If the structure is a Field, then the
    user has applied the dtfield or field value directly to the field so we
    need to apply a default value to the field.
    '''
    
    field_config = class_config
    default_value = getattr(clz, field_name, UNSPECIFIED)
    
    if isinstance(default_value, _XFieldParams):
        # User has applied the xfield value directly to the field.
        field_config = field_config.apply(default_value)
        default_value = UNSPECIFIED
    elif isinstance(default_value, Field):
        
        dc_field_params, field_default = _get_field_as_params(default_value)
        field_config = field_config(**dc_field_params)
        default_value = UNSPECIFIED
        
        if isinstance(field_default, _XFieldParams):
            # Field contained an xfield value.
            field_config = field_config.apply(field_default) 
        
    if not field_config.is_default_specified():
        field_config = field_config(default=None)
    
    if field_config.builder in UNSPECIFIED_OR_NONE:
        collector_type = _get_collector_type(field_annotation)
    else:
        collector_type = field_config.builder
    
    ftype = field_config.ftype
    
    assert isinstance(ftype, XmlDataType), \
        f'ftype for field {field_name}, is {_diagnostic_name_of_ftype(ftype)}, ' \
        f'expected an instance of XmlDataType, Attribute, Element or Metadata.'
        
    xml_name = get_xml_field_name(clz, field_name, field_annotation, field_config)
    
    if not xml_name:
        # This field is not specified as an xml field.
        return
    
    field_spec = XmlFieldSpec(
        field_name=field_name,
        xml_name=xml_name,
        ftype=ftype,
        collector_type=collector_type)
    
    ftype.apply_collector_type(parser_spec, field_spec)

    setattr(clz, field_name, field_config.fieldof())


def _process_xdatatree(clz, init, repr, eq, order, unsafe_hash, frozen,
                       match_args, kw_only, slots, chain_post_init):

    # Get the default config for the fields in this class.
    default_config = getattr(clz, XDATATREE_CONFIG_FIELD_NAME, DEFAULT_XFIELD_PARAMS)
    
    xml_parser_spec = XmlParserSpec()
    
    # Process the fields. This will populate the xml_parser_spec.
    for field_name, field_annotation in clz.__annotations__.items():
        if field_name in (XDATATREE_UNUSED_XML_ATTRIBUTES, XDATATREE_UNUSED_XML_ELEMENTS):
            # don't process these fields.
            assert field_annotation is None, \
                f'Field named "{field_name}" has been specified as a ' \
                f'"{_diagnostic_name_of_ftype(field_name)}". No specification allowed.'
            continue
        _process_field(clz, field_name, field_annotation, default_config, xml_parser_spec)
    
    # Create fields for storing the unidentified xml elements and attributes.
    setattr(clz, XDATATREE_UNUSED_XML_ATTRIBUTES, None)
    clz.__annotations__[XDATATREE_UNUSED_XML_ATTRIBUTES] = None
    setattr(clz, XDATATREE_UNUSED_XML_ELEMENTS, None)
    clz.__annotations__[XDATATREE_UNUSED_XML_ELEMENTS] = None

    setattr(clz, XDATATREE_PARSER_SPEC, xml_parser_spec)

    return datatree(clz, init=init, repr=repr, eq=eq, order=order,
                    unsafe_hash=unsafe_hash, frozen=frozen, 
                    match_args=match_args, kw_only=kw_only, slots=slots, 
                    chain_post_init=chain_post_init)

def xdatatree(clz=None, /, *, init=True, repr=True, eq=True, order=False,
             unsafe_hash=False, frozen=False, match_args=True,
             kw_only=False, slots=False, chain_post_init=False):
    '''Python decorator similar to datatrees.datatree providing parameter injection,
    injection, binding and overrides for parameters deeper inside a tree of objects.
    '''

    def wrap(clz):
        return _process_xdatatree(
            clz, init, repr, eq, order, unsafe_hash, frozen, match_args, 
            kw_only, slots, chain_post_init)

    # See if we're being called as @datatree or @datatree().
    if clz is None:
        # We're called with parens.
        return wrap

    # We're called as @datatree without parens.
    return wrap(clz)


class XmlNamespaces:
    '''Provides a container for the XML namespace mappings.'''
    def __init__(self, xml="http://www.w3.org/XML/1998/namespace", **kwargs):
        self.xml = xml
        self._keys = kwargs.keys()
        self.__dict__.update(kwargs)
        
    def to_nsmap(self):
        '''Returns a dictionary of namespace definitions suitable for lxml.etree.Element.'''
        kvs = ((k, getattr(self, k)) for k in self._keys)
        nsmap = {k: getattr(self, k) for k, v in kvs if v is not None}
        nsmap[None] = self.xml
        return nsmap
    

@datatree(frozen=True)
class XmlSerializationSpec:
    '''Specifies the configuration for XML serialization and deserialization
    for a specific xdatatree annotated class.'''
    xml_type: Type = dtfield(doc='The xdatatee annotated class for the top level element.')
    xml_node_name: str = dtfield(doc='The name of the root element.')
    xml_namespaces: XmlNamespaces = dtfield(None, doc='The namespaces for the xml document.')
    options: XmlParserOptions = dtfield(DESERIALIZE_OPTIONS, doc='The options for the deserializer.')
    
    def serialize(self, xdatatree_obj):
        nsmap = self.xml_namespaces.to_nsmap() if self.xml_namespaces else None
        return serialize(xdatatree_obj, self.xml_node_name, nsmap)
    
    def deserialize(self, xml_node: etree.ElementBase, options: XmlParserOptions=None):
        if options is None:
            options = self.options
        return deserialize(xml_node, self.xml_type, options=options)
