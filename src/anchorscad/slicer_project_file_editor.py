'''
This module contains the SlicerProjectFileEditor class which is used to
create and edit slicer project files.

This is but a tool for the ultimate goal of creating a slicer project file
directly from the anchorscad model and also to create gcode files directly
by invoking the slicer as part of the fabricator process. 
'''

#
#  STILL INCOMPLETE. DO NOT USE.
#

import anchorscad as ad
from zipfile import ZipFile
import shutil
import os
from typing import Dict
import lxml.etree as etree 

from anchorscad.threemf_config import SERIALIZATION_SPEC as CONFIG_SPEC
from anchorscad.threemf_model import SERIALIZATION_SPEC as MODEL_SPEC


def parse_xml(xml_3mf_content) -> etree.ElementBase:
    '''Parse the XML content of a 3mf file and return the XML tree.'''
    xml_tree = etree.fromstring(xml_3mf_content)
    return xml_tree

@ad.datatree(repr=False, eq=False, order=False, unsafe_hash=False, frozen=False)
class SlicerModel:
    filename: str = ad.dtfield(doc='Name of the 3mf file')
    xml_3mf_content: str = ad.dtfield(doc='XML content of the 3mf file')
    xml_tree: etree.ElementBase = ad.dtfield(
        self_default=lambda s: parse_xml(s.xml_3mf_content), 
        doc='XML tree of the 3mf file')
    model: MODEL_SPEC.xml_type = ad.dtfield(
        self_default=lambda s: MODEL_SPEC.deserialize(s.xml_tree),
        doc='A Model object representing the 3mf file')
    
    def objects(self):
        '''Return the ids of the objects in this model file.'''
        ns = {'ns': self.xml_tree.nsmap[None]}
        return self.xml_tree.findall('.//ns:object', ns)


@ad.datatree
class SlicerMetadataConfig:
    filename: str = ad.dtfield(doc='Name of the metadata/settings.config file')
    content: str = ad.dtfield(doc='XML content of the metadata/settings.config file')
    xml_tree: etree.ElementBase = ad.dtfield(
        self_default=lambda s: parse_xml(s.content),
        doc='XML tree of the metadata/settings.config file')
    condig: CONFIG_SPEC.xml_type = ad.dtfield(
        self_default=lambda s: CONFIG_SPEC.deserialize(s.xml_tree),
        doc='A Condif object representing the 3mf file')
    
    def object_configs(self):
        '''Return the ids of the objects in this model file.'''
        ns = {'ns': self.xml_tree.nsmap[None]}
        return self.xml_tree.findall('.//ns:object', ns)


@ad.datatree
class SlicerProjectModel:
    metafiles: Dict[str, str] = ad.dtfield(default_factory=dict, doc='Dictionary of metafiles')
    model_files: Dict[str, SlicerModel] = ad.dtfield(default_factory=dict, doc='Dictionary of model by files')
    models_ids: Dict[str, SlicerModel] = ad.dtfield(default_factory=dict, doc='Dictionary of models by Id')
    metadata_config: SlicerMetadataConfig = ad.dtfield(None, doc='Name of the metadata/settings.config file')

    def add_model(self, filename, modelXml):
        with open('foo.xml', 'wb') as file:
            file.write(modelXml)
        model = SlicerModel(filename, modelXml)
        if filename in self.model_files:
            raise ValueError(f'File {filename} already exists in the slicer project')
        
        self.model_files[filename] = model
        objectids = tuple(o.get('id') for o in model.objects())
        print(f'filename={filename}, objectis = ' + ', '.join(objectids))
        for objectid in objectids:
            if objectid in self.models_ids:
                raise ValueError(f'Object id {objectid} already exists in the slicer project')
            self.models_ids[objectid] = model
            
    def add_metadata_settings_config(self, filename, content):
        '''Add a metadata/settings.config file to the slicer project.'''
        if self.metadata_config is not None:
            raise ValueError('The slicer project already has a metadata/settings.config file')

        self.metadata_config = SlicerMetadataConfig(filename, content)

    def write(self, output_file):
        '''Write the slicer project file to the output file.'''
        with ZipFile(output_file, 'w') as zipfile:
            for filename, content in self.metafiles.items():
                zipfile.writestr(filename, content)
            
            modelFilenames = {}
            for objectid, model in self.models.items():
                zipfile.writestr(filename, model.xml_3mf_content)


@ad.datatree(eq=False, order=False, unsafe_hash=False, frozen=False)
class SlicerProjectFileEditor:
    '''An interface for manipulating slicer project files using the 3mf format.
    '''
    template_file: str = ad.dtfield(doc='Path to the template file')
    output_file: str = ad.dtfield(doc='Path to the output file')

    model: SlicerProjectModel = ad.dtfield(
        default_factory=SlicerProjectModel, doc='Model of the slicer project file')
    
    def __post_init__(self):        
        # If the destination file is a folder, change it's name to use the basename
        # of the template file.
        if os.path.isdir(self.output_file):
            self.output_file = os.path.join(
                self.output_file, os.path.basename(self.template_file))

        with ZipFile(self.template_file, 'r') as zipfile:
        
            # Read all the 3mf files in the zip file and place them in the SliceProjectModel.
            for filename in zipfile.namelist():
                
                with zipfile.open(filename) as file:
                    content = file.read()
                    
                    
                    if self.is_model_file(filename):
                        
                        print(content.decode('utf-8'))
                        self.model.add_model(filename, content)
                        
                    else:
                        self.model.metafiles[filename] = content
                        
    def is_model_file(self, filename):
        _, suffix = os.path.splitext(filename)
        return suffix == '.model'
    
    def write(self):
        '''Write the slicer project file to the output file.'''
        with ZipFile(self.output_file, 'w') as zipfile:
            for filename, model in self.model.models.items():
                zipfile.writestr(filename, model.xml_3mf_content)
                        
def main():
    
    editor = SlicerProjectFileEditor(
        template_file='basic_4_model_orca.3mf', 
        output_file='basic_4_model_orca.3mf_gen.3mf')
    
    exit(0)
    editor.write()

if __name__ == '__main__':
    main()
