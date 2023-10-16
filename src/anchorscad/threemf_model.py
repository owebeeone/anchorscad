'''
3mf XML xdatatree classes for the 3mf config file.
'''

from anchorscad.xdatatrees import xdatatree, xfield, Attribute, \
    Element, CamelSnakeConverter, SnakeCamelConverter, XmlSerializationSpec, \
    MetadataNameValue, ValueCollector, XmlNamespaces

from anchorscad import datatree, dtfield

from anchorscad.xdatatree_utils import TransformConverter

from typing import List, Tuple
import numpy as np


NAMESPACES=XmlNamespaces(
    xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
    xml="http://www.w3.org/XML/1998/namespace",
    slic3rpe="http://schemas.slic3r.org/3mf/2017/06",
    p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
)

DEFAULT_CONFIG=xfield(ename_transform=CamelSnakeConverter, ftype=Element)
DEFAULT_CONFIGX=DEFAULT_CONFIG(xmlns=NAMESPACES.xmlns)
DEFAULT_CONFIG2=xfield(
    ename_transform=SnakeCamelConverter,
    aname_transform=SnakeCamelConverter,
    ftype=Attribute)
DEFAULT_CONFIG2X=xfield(
    xmlns=NAMESPACES.xmlns,
    ename_transform=SnakeCamelConverter,
    aname_transform=SnakeCamelConverter,
    ftype=Attribute)


@xdatatree
class Component:
    XDATATREE_CONFIG=DEFAULT_CONFIGX(ftype=Attribute)
    path: str = xfield(xmlns=NAMESPACES.p, doc='Path of the component')
    objectid: str = xfield(xmlns=None, doc='Object id of the component')
    transform: TransformConverter = xfield(xmlns=None, doc='Transform of the component')
    uuid: str = xfield(xmlns=NAMESPACES.p, aname='UUID', doc='UUID of the component')

@xdatatree
class Components:
    XDATATREE_CONFIG=DEFAULT_CONFIGX
    components: List[Component] = xfield(ftype=Element, doc='List of components')
    
@xdatatree
class Vertex:
    x: float = xfield(ftype=Attribute, doc='X coordinate of the vertex')
    y: float = xfield(ftype=Attribute, doc='Y coordinate of the vertex')
    z: float = xfield(ftype=Attribute, doc='Z coordinate of the vertex')
    
    def get_array(self):
        return np.array([self.x, self.y, self.z])
    
@xdatatree
class Triangle:
    v1: int = xfield(ftype=Attribute, doc='V1 of the triangle')
    v2: int = xfield(ftype=Attribute, doc='V2 of the triangle')
    v3: int = xfield(ftype=Attribute, doc='V3 of the triangle')
    paint_color: str = xfield(ftype=Attribute, doc='paint_colors of the triangle')
    
    def get_array(self):
        return np.array([self.v1, self.v2, self.v3])
    
@datatree
class TriangesCustomConverter(ValueCollector):
    '''A custom converter for a field representing a list of Triange objects.
    This will represent the list of trianges as a numpy array and allow to serialize it
    back to a list of Triange objects.'''
    triangles: List[np.ndarray] = dtfield(default_factory=list, doc='List of vertices')
    paint_colors: List[str] = dtfield(default_factory=list, doc='List of paint colors')
    
    # This defines is used to read and write the values as xml element.
    CONTAINED_TYPE = Triangle
    
    def append(self, item: CONTAINED_TYPE):
        if not isinstance(item, self.CONTAINED_TYPE):
            raise ValueError(f'Item must be of type {self.CONTAINED_TYPE.__name__} but received {type(item).__name__}')
        self.triangles.append(item.get_array())
        self.paint_colors.append(item.paint_color)

    def get(self):
        return np.array(self.triangles), self.paint_colors
    
    @classmethod
    def to_contained_type(cls, triangles_paint_colors: Tuple[np.ndarray, List[str]]):
        return (cls.CONTAINED_TYPE(*x[0], paint_color=x[1]) for x in zip(*triangles_paint_colors))
    
@xdatatree
class Triangles:
    XDATATREE_CONFIG=DEFAULT_CONFIGX
    triangles_paint_colors: List[Tuple[Triangle, List[str]]] \
        = xfield(ftype=Element, ename='triangle', builder=TriangesCustomConverter,  doc='List of triangles')
    
    def __eq__(self, __value: object) -> bool:
        return np.array_equal(self.triangles_paint_colors[0], __value.triangles_paint_colors[0]) \
            and (self.triangles_paint_colors[1] == __value.triangles_paint_colors[1])



@datatree
class VerticesCustomConverter(ValueCollector):
    '''A custom converter for a field representing a list of Vertex objects.
    This will represent the list of vertices as a numpy array and allow to serialize it
    back to a list of Vertex objects.'''
    vertices: List[np.ndarray] = dtfield(default_factory=list, doc='List of vertices')
    
    # This defines the type used to read and write the values as xml element.
    CONTAINED_TYPE = Vertex
    
    def append(self, item: CONTAINED_TYPE):
        if not isinstance(item, self.CONTAINED_TYPE):
            raise ValueError(f'Item must be of type {self.CONTAINED_TYPE.__name__} but received {type(item).__name__}')
        self.vertices.append(item.get_array())

    def get(self):
        return np.array(self.vertices)
    
    @classmethod
    def to_contained_type(cls, vertices: np.ndarray):
        return (cls.CONTAINED_TYPE(*x) for x in vertices)


@xdatatree
class Vertices:
    XDATATREE_CONFIG=DEFAULT_CONFIGX
    vertices: np.ndarray = xfield(
        ftype=Element, 
        ename='vertex', 
        builder=VerticesCustomConverter, 
        doc='List of vertices')
    
    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Vertices):
            return False
        return np.array_equal(self.vertices, __value.vertices)

@xdatatree
class Mesh:
    XDATATREE_CONFIG=DEFAULT_CONFIGX
    vertices: Vertices = xfield(ftype=Element, doc='List of vertices')
    triangles: Triangles = xfield(ftype=Element, doc='List of triangles')

@xdatatree
class Object:
    XDATATREE_CONFIG=DEFAULT_CONFIGX
    id: int = xfield(ftype=Attribute, xmlns=None, doc='Id of the object')
    uuid: str = xfield(ftype=Attribute, xmlns=NAMESPACES.p, doc='Uuid of the object')
    type: str = xfield(ftype=Attribute, xmlns=None, doc='Type of the object')
    components: List[Components] = xfield(ftype=Element, doc='List of components')
    mesh: Mesh = xfield(ftype=Element, doc='Mesh of the object')

@xdatatree
class Resources:
    XDATATREE_CONFIG=DEFAULT_CONFIGX
    objects: List[Object] = DEFAULT_CONFIG(ename='object', doc='List of objects')

@xdatatree
class Item:
    XDATATREE_CONFIG=DEFAULT_CONFIGX(ftype=Attribute, xmlns=None)
    objectid: str = xfield(doc='Object id of the item')
    uuid: str = xfield(xmlns=NAMESPACES.p, doc='Uuid of the item')
    transform: TransformConverter = xfield(doc='Transform of the item')
    printable: bool = xfield(doc='Printable of the item')

@xdatatree
class Build:
    XDATATREE_CONFIG=DEFAULT_CONFIGX
    uuid: str = xfield(ftype=Attribute, xmlns=NAMESPACES.p, doc='Uuid of the build')
    items: List[Item] = xfield(doc='List of items')

@xdatatree
class Model:
    XDATATREE_CONFIG=DEFAULT_CONFIG2X(ftype=MetadataNameValue)
    unit: str = xfield(ftype=Attribute, aname='unit', xmlns=None, doc='Unit of the model')
    lang: str = DEFAULT_CONFIG(ftype=Attribute, aname='lang', xmlns=NAMESPACES.xml, doc='Language of the model')
    requiredextensions: str = DEFAULT_CONFIG(ftype=Attribute, aname='requiredextensions', xmlns=None, doc='Required extensions')
    application: str = xfield(doc='Application creating this model')
    x3mf_content: str = xfield(aname='BambuStudio:3mfVersion', doc='BambuStudio:3mfVersion')
    copyright: str = xfield(aname='Copyright', doc='The copyright string')
    copyRight: str = xfield(aname='CopyRight', doc='The copyRight string')
    license_terms: str = xfield(doc='The licence terms')
    creation_date: str = xfield(doc='The creation date')
    description: str = xfield(doc='The description string')
    designer: str = xfield(doc='The designer string')
    designer_cover: str = xfield(doc='The designer cover string')
    designer_user_id: str = xfield(doc='The designer user id string')
    license: str = xfield(doc='The license string')
    modification_date: str = xfield(doc='The modification date')
    origin: str = xfield(doc='The origin string')
    title: str = xfield(doc='The title string')
    rating: str = xfield(doc='The title string')
    slic3rpe_version_3mf: str = xfield(aname='slic3rpe:Version3mf', doc='The slic3rpe version 3mf')
    resources: Resources = xfield(ftype=Element, ename='resources', doc='The resources')
    build: Build = DEFAULT_CONFIGX(ftype=Element, doc='The build')


SERIALIZATION_SPEC = XmlSerializationSpec(Model, 'model', NAMESPACES)

