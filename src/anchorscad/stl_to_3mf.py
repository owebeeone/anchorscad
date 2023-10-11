
import os
from stl.mesh import Mesh
import numpy as np
from anchorscad.colours import Colour
from dataclasses import dataclass, field
from typing import List, Tuple
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from collections import OrderedDict
import sys
from argparse import ArgumentParser
import pythonopenscad as posc

def dedupe_verticies(v0: np.ndarray, v1: np.ndarray, v2: np.ndarray):
    '''Dedupe vertices in a set of triangles. Returns a tuple of the deduped vertices and 
    tri_map. tri_map is a 2D array of indices that maps the indices of the original triangles'''
      
    tris_count = len(v0)
    assert len(v1) == tris_count and len(v2) == tris_count, \
        'All vertex arrays must be the same length.'
    
    vertices = np.vstack((v0, v1, v2))
    unique_vertices, tri_map = np.unique(vertices, axis=0, return_inverse=True)
    
    triangles = tri_map.reshape((tris_count, 3), order='F')
    
    return unique_vertices, triangles


XML_ATTRS=OrderedDict({
    'unit': 'millimeter', 
    'xml:lang': "en-US",
    'xmlns:m': "http://schemas.microsoft.com/3dmanufacturing/material/2015/02",
    'xmlns': "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
    'xmlns:ad': 'http://schemas.anchorscad.com/3dmanufacturing/2023/01/core'
})

@dataclass(frozen=True)
class ColourGroup:
    id: str
    colour: Colour = Colour('red')
    
    def export_colour(self, resources):
        colour_group = ET.SubElement(resources, 'm:colorgroup', id=self.id)
        return ET.SubElement(colour_group, 'm:color', color=self.colour.to_hex())

@dataclass
class Model:
    model_id: str
    pid: str
    vertices: np.ndarray
    triangles: np.ndarray
    colour_group: ColourGroup = None
    
    def export_colour(self, colour_group):
        return ET.SubElement(colour_group, 'm:color', color=self.colour.to_hex())
    
    def export_object(self, resources):
        obj = ET.SubElement(resources, 'object', id=self.model_id, type='model', pid=self.pid)

        # Create the mesh element
        mesh = ET.SubElement(obj, 'mesh')

        # Create the vertices element
        vertices_elem = ET.SubElement(mesh, 'vertices')
        for v in self.vertices:
            ET.SubElement(vertices_elem, 'vertex', x=str(v[0]), y=str(v[1]), z=str(v[2]))

        # Create the triangles element
        triangles_elem = ET.SubElement(mesh, 'triangles')
        for t in self.triangles:
            ET.SubElement(triangles_elem, 'triangle', v1=str(t[0]), v2=str(t[1]), v3=str(t[2]))
            
    def export_build(self, build):
        return ET.SubElement(build, 'item', objectid=self.model_id, transform='1 0 0 0 1 0 0 0 1 0 0 0')

    def export_scad(self):
        return posc.Polyhedron(points=self.vertices, faces=self.triangles)
            

def generate_pretty_xml(root, do_pretty=True):
    
    if do_pretty:
        ET.indent(root)
        
    xml_string = ET.tostring(
            root, 
            encoding='utf-8', 
            method='xml', 
            xml_declaration=True
        ).decode()

    return xml_string


@dataclass
class ModelGroup:
    models: List[Model] = field(default_factory=list)
 
    def generate_xml(self):
    
        root = ET.Element('model', attrib=XML_ATTRS)
        
        ET.SubElement(root, 'metadata', name='ad:tool', value='AnchorScad stl_to_3mf')

        # Create the resources element
        resources = ET.SubElement(root, 'resources')
        
        
        colour_groups = {m.colour_group for m in self.models}
        
        for cg in colour_groups:
            cg.export_colour(resources)
            
        for model in self.models:
            model.export_object(resources)
            
        build = ET.SubElement(root, 'build')
        for model in self.models:
            model.export_build(build)

        return generate_pretty_xml(root, False)
    
    def generate_scad(self):
        '''Returns a list of pythonopenscad Polyhedron objects, one for each model.'''
        scad_models = []
        for model in self.models:
            scad_models.append(model.export_scad())
        return scad_models
            
    
    def add_new_model_by_tris(self, model_id, vertices, triangles, colour_group):
        self.models.append(Model(model_id, colour_group.id, vertices, triangles, colour_group))


@dataclass
class ColourGroupGenerator:
    
    current_id: int = 0
    colours: Tuple[Colour] = (
            Colour('purple'), 
            Colour('green'),
            Colour('orange'),
            Colour('yellow'),
            Colour('blue'),
            Colour('red'), 
            Colour('darkred'),
        )
    
    def get_colour(self, id):
        id = id + 1
        colour_list = []
        while id > 0:
            current_count = len(colour_list)
            divider = (len(self.colours) - current_count)
            index = current_count + id % divider
            id = id // divider
            colour_list.append(self.colours[index])
            
        # blend the colours in the list
        colour = colour_list[0]
        for i, c in enumerate(colour_list[1:]):
            colour = colour.blend(c, 1 / (i + 1))
            
        return colour
    
    def get_next_colour(self):
        id = self.current_id
        self.current_id += 1
        return self.get_colour(id)
    
    def get_colour_group(self, id):
        colour = self.get_colour(id)
        cg = ColourGroup(f'm{self.current_id}', colour)
        return cg
    
    def get_next_colour_group(self):
        colour = self.get_next_colour()
        cg = ColourGroup(f'm{self.current_id}', colour)
        return cg


def stl_to_model_group(stl_files):
    models = ModelGroup()
    colour_genny = ColourGroupGenerator()
    
    for i, stl_file in enumerate(stl_files):
        # Load the STL file.
        stl_mesh = Mesh.from_file(stl_file)
        
        # Create a model ID from the stl file name, removing everything but the base name.
        stl_base_name = os.path.basename(stl_file)
        
        # Dedupe the verticies and get the tri_map.
        verticies, trimap = dedupe_verticies(stl_mesh.v0, stl_mesh.v1, stl_mesh.v2)
        
        models.add_new_model_by_tris(
            f'{i}', verticies, trimap, colour_genny.get_next_colour_group())
        
    return models

CONTENT_TYPES = '''\
<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
	<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
	<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
</Types>'''

RELS = '''\
<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
	<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" />
</Relationships>
'''
    

def stl_to_3mf(stl_files, output_file):
    '''Convert a list of STL files to a 3MF file.'''
    
    models = stl_to_model_group(stl_files) 
    
    xmlstr = models.generate_xml()
    
    with ZipFile(output_file, 'w') as zipfile:
        zipfile.writestr('_rels/.rels', RELS)
        zipfile.writestr('[Content_Types].xml', CONTENT_TYPES)
        zipfile.writestr('3D/3dmodel.model', xmlstr)
        
    return 0

def stl_to_scad(stl_files, output_file):
    
    models = stl_to_model_group(stl_files) 
    
    with open(output_file, 'w') as scad_file:
        for i in range(len(models.models)):
            scad_file.write(f'M{i}();\n')
            
        for i, model in enumerate(models.generate_scad()):
            scad_file.write(f'module M{i}() ' + '{\n')
            model.dump(scad_file)
            scad_file.write('\n}\n')
    

def main():
    parser = ArgumentParser(description='Convert a list of STL files to a 3MF file.')
    parser.add_argument('stl_files', nargs='+', help='List of STL files')
    parser.add_argument('output_file', help='Output 3MF file')

    args = parser.parse_args()

    stl_files = args.stl_files
    output_file = args.output_file
    
    # Get the file extension of the output file
    file_extension = os.path.splitext(output_file)[1]
    
    if file_extension == '.3mf':
        status = stl_to_3mf(stl_files, output_file)
    elif file_extension == '.scad':
        status = stl_to_scad(stl_files, output_file)
    else:
        print("Invalid output file extension. Supported extensions are .3mf and .scad.")
        status = 1

    exit(status)

if __name__ == '__main__':
    main()
