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
import os
from typing import Dict
import lxml.etree as etree 
import argparse
from anchorscad.xdatatrees import XmlParserOptions

from anchorscad.threemf_config import SERIALIZATION_SPEC as CONFIG_SPEC
from anchorscad.threemf_model import SERIALIZATION_SPEC as MODEL_SPEC


@ad.datatree
class Options:
    '''Options for the SlicerProjectFileEditor.'''
    print_xml_unused: bool = ad.dtfield(doc='Print unknown attributes and elements to stderr')
    assert_xml_unused: bool = ad.dtfield(doc='Assert on unknown attributes and elements')
    recover_xml_errors: bool = ad.dtfield(doc='Recover from XML errors')
    recover_undeclared_namespace: bool = ad.dtfield(
        doc='Recover from undeclared XML namespace errors')
    
    xml_parser_options: XmlParserOptions = ad.dtfield(self_default=
        lambda s: XmlParserOptions(
            assert_unused_elements=s.assert_xml_unused,
            assert_unused_attributes=s.assert_xml_unused,
            print_unused_elements=s.print_xml_unused,
            print_unused_attributes=s.print_xml_unused,
            recover_undeclared_namespace=s.recover_undeclared_namespace
        ))


def parse_xml(xml_3mf_content, recover: bool) -> etree.ElementBase:
    '''Parse the XML content of a 3mf file and return the XML tree.'''
    parser = etree.XMLParser(recover=recover)
    xml_tree = etree.fromstring(xml_3mf_content, parser=parser)
    return xml_tree

@ad.datatree(repr=False, eq=False, order=False, unsafe_hash=False, frozen=False)
class SlicerModel:
    filename: str = ad.dtfield(doc='Name of the 3mf file')
    xml_3mf_content: str = ad.dtfield(doc='XML content of the 3mf file')
    xml_tree: etree.ElementBase = ad.dtfield(init=False, doc='XML tree of the 3mf file')
    model: MODEL_SPEC.xml_type = ad.dtfield(init=False,
        doc='A Model object representing the 3mf file')
    
    def deserialize(self, recover: bool=False, options: XmlParserOptions=None):
        '''Deserialize the 3mf file into a Model object.'''
        self.xml_tree = parse_xml(self.xml_3mf_content, recover)
        self.model = MODEL_SPEC.deserialize(self.xml_tree, options=options)
    
    def objects(self):
        '''Return the ids of the objects in this model file.'''
        ns = {'ns': self.xml_tree.nsmap[None]}
        return self.xml_tree.findall('.//ns:object', ns)


@ad.datatree
class SlicerMetadataConfig:
    filename: str = ad.dtfield(doc='Name of the metadata/settings.config file')
    content: str = ad.dtfield(doc='XML content of the metadata/settings.config file')
    xml_tree: etree.ElementBase = ad.dtfield(
        init=False,
        doc='XML tree of the metadata/settings.config file')
    config: CONFIG_SPEC.xml_type = ad.dtfield(
        init=False, doc='A Condif object representing the 3mf file')
    
    def deserialize(self, recover: bool=False, options: XmlParserOptions=None):
        '''Deserialize the 3mf file into a Model object.'''
        self.xml_tree = parse_xml(self.content, recover)
        self.config = CONFIG_SPEC.deserialize(self.xml_tree, options=options)
        
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

    def add_model(self, filename, modelXml, options: Options):
        # with open('foo.xml', 'wb') as file:
        #     file.write(modelXml)
        model = SlicerModel(filename, modelXml)
        model.deserialize(recover=options.recover_xml_errors, options=options.xml_parser_options)
        if filename in self.model_files:
            raise ValueError(f'File {filename} already exists in the slicer project')
        
        self.model_files[filename] = model
        objectids = tuple(o.get('id') for o in model.objects())
        print(f'filename={filename}, objectis = ' + ', '.join(objectids))
        for objectid in objectids:
            if objectid in self.models_ids:
                raise ValueError(f'Object id {objectid} already exists in the slicer project')
            self.models_ids[objectid] = model
            
    def add_metadata_settings_config(self, filename, content, options: Options):
        '''Add a metadata/settings.config file to the slicer project.'''
        if self.metadata_config is not None:
            raise ValueError('The slicer project already has a metadata/settings.config file')

        self.metadata_config = SlicerMetadataConfig(filename, content)
        
        self.metadata_config.deserialize(
            recover=options.recover_xml_errors, options=options.xml_parser_options)

    def write(self, output_file):
        '''Write the slicer project file to the output file.'''
        with ZipFile(output_file, 'w') as zipfile:
            for filename, content in self.metafiles.items():
                zipfile.writestr(filename, content)
            
            for objectid, model in self.models.items():
                zipfile.writestr(filename, model.xml_3mf_content)


@ad.datatree(eq=False, order=False, unsafe_hash=False, frozen=False)
class SlicerProjectFileEditor:
    '''An interface for manipulating slicer project files using the 3mf format.
    '''
    template_file: str = ad.dtfield(doc='Path to the template file')
    output_file: str = ad.dtfield(doc='Path to the output file')
    options: Options = ad.dtfield(doc='Options for the SlicerProjectFileEditor')

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
                        self.model.add_model(filename, content, self.options)
                        
                    elif self.is_config_file(filename):
                        self.model.add_metadata_settings_config(filename, content, self.options)
                        
                    else:
                        self.model.metafiles[filename] = content

    def is_model_file(self, filename):
        _, suffix = os.path.splitext(filename)
        return suffix == '.model'
    
    
    def is_config_file(self, filename):
        return filename in (
            'Metadata/model_settings.config',
            'Metadata/Slic3r_PE_model.config')
    
    def write(self):
        '''Write the slicer project file to the output file.'''
        with ZipFile(self.output_file, 'w') as zipfile:
            for filename, model in self.model.models.items():
                zipfile.writestr(filename, model.xml_3mf_content)


def arg_parser():
    '''
    Parses the command line arguments. It accepts a 3mf file as input and a 3mf file as output.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Path to the input 3mf file')
    parser.add_argument('output_file', help='Path to the output 3mf file')
    
    parser.add_argument('--print-xml-unused', action='store_true', 
                        help='Print unknown attributes and elements to stderr')
    parser.add_argument('--noprint-xml-unused', action='store_false', dest='print_xml_unused', 
                        help='Don\'t print unknown attributes and elements')
    parser.set_defaults(print_xml_unused=True)
    
    parser.add_argument('--assert-xml-unused', action='store_true', 
                        help='Assert on unknown attributes and elements')
    parser.add_argument('--noassert-xml-unused', action='store_false', dest='assert_xml_unused', 
                        help='Do not assert on unknown attributes and elements')
    parser.set_defaults(assert_xml_unused=True)
    
    parser.add_argument('--recover-xml-errors', action='store_true', 
                        help='Recover from XML errors')
    parser.add_argument('--norecover-xml-errors', action='store_false', dest='recover_xml_errors', 
                        help='Fail on XML errors')
    parser.set_defaults(recover_xml_errors=True)
    
    parser.add_argument('--recover-undeclared-namespace', action='store_true', 
                        help='Recover from XML errors')
    parser.add_argument('--norecover-undeclared-namespace', action='store_false', 
                        dest='recover_undeclared_namespace', 
                        help='Fail on XML undeclared namespace errors')
    parser.set_defaults(recover_undeclared_namespace=False)
    
    return parser
    
           
def main():
    
    args = arg_parser().parse_args()
    
    options = Options(
        args.print_xml_unused, 
        args.assert_xml_unused, 
        args.recover_xml_errors,
        args.recover_undeclared_namespace)
    
    # Ensure the input file exists.
    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f'Input file \'{args.input_file}\' does not exist.')

    # Check if the input file has a .3mf extension
    if not args.input_file.endswith('.3mf'):
        raise ValueError(f'Input file (\'{args.input_file}\')  must have a .3mf extension.')
    
    # Ensure the output file does not exist.
    if os.path.exists(args.output_file):
        raise FileExistsError(f'output file \'{args.output_file}\' exists already.')
    
    # Check if the input file has a .3mf extension
    if not args.output_file.endswith('.3mf'):
        raise ValueError(f'Output file (\'{args.output_file}\') must have a .3mf extension.')
    
    editor = SlicerProjectFileEditor(
        template_file=args.input_file, 
        output_file=args.output_file,
        options=options)
    
    exit(0)
    editor.write()

if __name__ == '__main__':
    
    #import sys;sys.argv = [sys.argv[0], 'basic_4_model_orca.3mf', 'basic_4_model_orca.3mf_gen1.3mf']
    #import sys; sys.argv = [sys.argv[0], "--assert-xml-unused", "--recover-xml-errors", "test3mfs/end-caps.3mf", "test3mfs/jnk.3mf"]
    main()
