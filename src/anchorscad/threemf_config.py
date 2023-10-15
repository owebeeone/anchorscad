'''
3mf XML xdatatree classes for the 3mf config file.
'''

from anchorscad.xdatatrees import xdatatree, xfield, Attribute, Metadata, \
    Element, CamelSnakeConverter, XmlSerializationSpec
    
from anchorscad.xdatatree_utils import MatrixConverter, \
    TransformConverter, VectorConverter

from typing import List

'''Create a default config for all xdatatree annotationed classes.'''
DEFAULT_CONFIG=xfield(ename_transform=CamelSnakeConverter, ftype=Element)

@xdatatree
class MeshStat:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Attribute)
    edges_fixed: int = xfield(doc='Number of fixed edges')
    degenerate_facets: int = xfield(doc='Number of degenerate facets')
    facets_removed: int = xfield(doc='Number of facets removed')
    facets_reversed: int = xfield(doc='Number of facets reversed')
    backwards_edges: int = xfield(doc='Number of backwards edges')


@xdatatree
class Part:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Metadata)
    id: str = xfield(ftype=Attribute, doc='Id of the part')
    subtype: str = xfield(ftype=Attribute, doc='Subtype of the part')
    name: str = xfield(ftype=Metadata, doc='Name of the part')
    matrix: MatrixConverter = xfield(ftype=Metadata, doc='Frame of ref of the object')
    source_file: str
    source_object_id: str
    source_volume_id: str
    source_offset_x: float
    source_offset_y: float
    source_offset_z: float
    mesh_stat: MeshStat= xfield(ftype=Element, doc='Mesh statistics of the part')


@xdatatree
class Object:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Attribute)
    id: int = xfield(ftype=Attribute, doc='Id of the object')
    name: str = xfield(ftype=Metadata, doc='Name of the object')
    extruder: str = xfield(ftype=Metadata, doc='Name of the object')
    parts: List[Part] = xfield(ftype=Element, doc='List of parts')

@xdatatree
class ModelInstance:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Metadata)
    object_id: str
    instance_id: str
    identify_id: str

@xdatatree
class Plate:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Metadata)
    plater_id: str
    plater_name: str
    locked: bool
    thumbnail_file: str
    top_file: str
    pick_file: str
    model_instances: List[ModelInstance] = xfield(
        ename='model_instance', ftype=Element, doc='instances of models on the plate')

@xdatatree
class AssembleItem:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Attribute)
    object_id: str
    instance_id: str
    transform: TransformConverter
    offset: VectorConverter
    
@xdatatree
class Assemble:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Element)
    assemble_items: List[AssembleItem] = xfield(ename='assemble_item', doc='List of assemble items') 

@xdatatree
class Config:
    XDATATREE_CONFIG=DEFAULT_CONFIG
    objects: List[Object] = xfield(ename='object', doc='List of objects')
    plate: Plate
    assemble: Assemble


SERIALIZATION_SPEC = XmlSerializationSpec(Config, 'config')