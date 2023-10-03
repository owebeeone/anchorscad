from anchorscad.xdatatrees import xdatatree, xfield, Attribute, Metadata,\
    Element, CamelSnakeConverter, deserialize

from anchorscad import GMatrix, GVector, datatree, dtfield

from typing import List
import re
import lxml.etree as etree 
import numpy as np

from unittest import TestCase, main


'''Create a default config for all xdatatree annotationed classes.'''
DEFAULT_CONFIG=xfield(ename_transform=CamelSnakeConverter, ftype=Element)


class FullDeserializeChecker:
    '''Mixin class that checks if all XML elements and attributes are used.'''
    def __post_init__(self):
        assert self.xdatatree_unused_xml_elements is None, 'Unused XML elements found'
        assert self.xdatatree_unused_xml_attributes is None, 'Unused XML attributes found'


@datatree
class MatrixConverter:
    '''Convert a string like "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1" to a GMatrix
    and back.'''
    matrix: GMatrix = dtfield(doc='The matrix as a GMatrix')

    def __init__(self, matrix_str: str):
        nparray = np.array([float(x) for x in re.split(r'\s+', matrix_str)])
        self.matrix = GMatrix(nparray.reshape((4, 4)))
    
    def __str__(self):
        return ' '.join([str(x) for x in self.matrix.A.flatten()])

@datatree
class TransformConverter:
    '''Convert a string like "1 0 0 0 1 0 0 0 1 40 40 10" to a GMatrix
    and back.'''
    matrix: GMatrix = dtfield(doc='The matrix as a GMatrix')

    def __init__(self, matrix_str: str):
        nparray = np.array([float(x) for x in re.split(r'\s+', matrix_str)])
        self.matrix = GMatrix(nparray.reshape((3, 4), order='F'))
    
    def __str__(self):
        nparray = self.matrix.A[0:3].reshape((1, 12), order='F')
        return ' '.join([str(x) for x in nparray])
    
@datatree
class VectorConverter:
    '''Convert a string like "1 2 3" to a GVector and back.'''
    vector: GVector = xfield(ftype=Metadata, doc='The vector as a numpy array')

    def __init__(self, vector_str: str):
        self.vector = GVector([float(x) for x in re.split(r'\s+', vector_str)])
    
    def __str__(self):
        return ' '.join([str(x) for x in self.vector.A[0:3]])


@xdatatree
class MeshStat(FullDeserializeChecker):
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Attribute)
    edges_fixed: int = xfield(doc='Number of fixed edges')
    degenerate_facets: int = xfield(doc='Number of degenerate facets')
    facets_removed: int = xfield(doc='Number of facets removed')
    facets_reversed: int = xfield(doc='Number of facets reversed')
    backwards_edges: int = xfield(doc='Number of backwards edges')

@xdatatree
class Part(FullDeserializeChecker):
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
class Object(FullDeserializeChecker):
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Attribute)
    id: int = xfield(ftype=Attribute, doc='Id of the object')
    name: str = xfield(ftype=Metadata, doc='Name of the object')
    extruder: str = xfield(ftype=Metadata, doc='Name of the object')
    parts: List[Part] = xfield(ftype=Element, doc='List of parts')

@xdatatree
class ModelInstance(FullDeserializeChecker):
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Metadata)
    object_id: str
    instance_id: str
    identify_id: str

@xdatatree
class Plate(FullDeserializeChecker):
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
class AssembleItem(FullDeserializeChecker):
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Attribute)
    object_id: str
    instance_id: str
    transform: TransformConverter
    offset: VectorConverter
    
@xdatatree
class Assemble(FullDeserializeChecker):
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Element)
    assemble_items: List[AssembleItem] = xfield(ename='assemble_item', doc='List of assemble items') 


@xdatatree
class Config(FullDeserializeChecker):
    XDATATREE_CONFIG=DEFAULT_CONFIG
    objects: List[Object] = xfield(ename='object', doc='List of objects')
    plate: Plate
    assemble: Assemble


XML_DATA = '''\
<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="OpenSCAD Model"/>
    <metadata key="extruder" value="2"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="OpenSCAD Model"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="basic_4_model.3mf"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="40"/>
      <metadata key="source_offset_y" value="40"/>
      <metadata key="source_offset_z" value="10"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <object id="4">
    <metadata key="name" value="OpenSCAD Model"/>
    <metadata key="extruder" value="1"/>
    <part id="3" subtype="normal_part">
      <metadata key="name" value="OpenSCAD Model"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="basic_4_model.3mf"/>
      <metadata key="source_object_id" value="1"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="-20"/>
      <metadata key="source_offset_y" value="40"/>
      <metadata key="source_offset_z" value="10"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <object id="6">
    <metadata key="name" value="OpenSCAD Model"/>
    <metadata key="extruder" value="3"/>
    <part id="5" subtype="normal_part">
      <metadata key="name" value="OpenSCAD Model"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="basic_4_model.3mf"/>
      <metadata key="source_object_id" value="2"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="-20"/>
      <metadata key="source_offset_y" value="-20"/>
      <metadata key="source_offset_z" value="10"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <object id="8">
    <metadata key="name" value="OpenSCAD Model"/>
    <metadata key="extruder" value="4"/>
    <part id="7" subtype="normal_part">
      <metadata key="name" value="OpenSCAD Model"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="basic_4_model.3mf"/>
      <metadata key="source_object_id" value="3"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="40"/>
      <metadata key="source_offset_y" value="-20"/>
      <metadata key="source_offset_z" value="10"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>
    <metadata key="top_file" value="Metadata/top_1.png"/>
    <metadata key="pick_file" value="Metadata/pick_1.png"/>
    <model_instance>
      <metadata key="object_id" value="2"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="463"/>
    </model_instance>
    <model_instance>
      <metadata key="object_id" value="4"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="483"/>
    </model_instance>
    <model_instance>
      <metadata key="object_id" value="6"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="503"/>
    </model_instance>
    <model_instance>
      <metadata key="object_id" value="8"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="523"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="2" instance_id="0" transform="1 0 0 0 1 0 0 0 1 40 40 10" offset="0 0 0" />
   <assemble_item object_id="4" instance_id="0" transform="1 0 0 0 1 0 0 0 1 -20 40 10" offset="0 0 0" />
   <assemble_item object_id="6" instance_id="0" transform="1 0 0 0 1 0 0 0 1 -20 -20 10" offset="0 0 0" />
   <assemble_item object_id="8" instance_id="0" transform="1 0 0 0 1 0 0 0 1 40 -20 10" offset="0 0 0" />
  </assemble>
</config>
'''


class ExtrudeTest(TestCase):

    def getXml(self):
         return etree.fromstring(XML_DATA.encode('utf-8'))
    
    def testXfieldFtypeResolution(self):
        conf = DEFAULT_CONFIG
        conf2 = xfield(ename='object', doc='List of objects')
        conf3 = conf.apply(conf2)

        self.assertEqual(conf3.ftype, Element)
        self.assertEqual(conf3.ename, 'object')
    
    def testXfield(self):
        conf = xfield(ftype=Attribute)
        conf2 = xfield(ename='object', doc='List of objects')
        conf3 = conf.apply(conf2)

        self.assertEqual(conf3.ftype, Attribute)
        self.assertEqual(conf3.ename, 'object')


    def testDeserialize(self):
        xml_tree = self.getXml()
        config, status = deserialize(xml_tree, Config)

        self.assertEqual(status.contains_unknown_elements, False)
        self.assertEqual(status.contains_unknown_attributes, False)

        self.assertEqual(len(config.objects), 4)


if __name__ == "__main__":
    main()
