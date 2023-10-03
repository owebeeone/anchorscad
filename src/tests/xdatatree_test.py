from anchorscad.xdatatrees import xdatatree, xfield, Attribute, Metadata,\
    Element, KeyOrNameConverter, deserialize

from typing import List
import re
import lxml.etree as etree 


from unittest import TestCase, main


class CamelSnakeConverter(KeyOrNameConverter):
    '''A "key transform", converts between camel case and snake case.
    This converter will convert keys corresponding to xml element names to the
    xml equivalent. For example, the key 'sourceFile' will be converted to
    the xml element name 'source_file'.
    '''
    @classmethod
    def to_xml(clz, name):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    @classmethod
    def from_xml(clz, name):
        components = name.split('_')
        return ''.join(x.title() for x in components)


'''Create a default config for all xdatatree annotationed classes.'''
DEFAULT_CONFIG=xfield(ename_transform=CamelSnakeConverter, ftype=Element)

@xdatatree
class Part:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Metadata)
    id: str = xfield(ftype=Attribute, doc='Id of the part')
    subtype: str = xfield(ftype=Attribute, doc='Subtype of the part')
    source_file: str
    source_object_id: str
    source_volume_id: str
    source_offset_x: float
    source_offset_y: float
    source_offset_z: float
    
@xdatatree
class Object:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Attribute)
    id: int = xfield(ftype=Attribute, doc='Id of the object')
    name: str = xfield(ftype=Metadata, aname='name', doc='Name of the object')
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
    transform: str
    offset: str
    
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
        config = deserialize(xml_tree, Config)

        self.assertEqual(len(config.objects), 4)


if __name__ == "__main__":
    main()
