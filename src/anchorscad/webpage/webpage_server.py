'''
Serves a webpage to view the content of a direcroty of generated resources
from running anchorscad_runner.py.

Author: gianni
'''

import sys
import os
import filecmp
import argparse
import re
import argparse
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Optional, List, Tuple, Dict
import numpy as np
from PIL import Image, ImageChops

import http.server
import socketserver
from urllib.parse import unquote
import mimetypes



@dataclass
class ServerConfig:
    generated_dir: str = '.'
    host: str = 'localhost'
    port: Optional[int] = None
    
    
def find_index_html():
    '''Find the index.html file in the same directory as this module.'''
    current_dir = os.path.dirname(__file__)
    index_path = os.path.join(current_dir, 'generated_viewer.html')
    if os.path.exists(index_path):
        return index_path
    return None


def find_js_files(pathname):
    # Strip the /scripts/ prefix 
    prefix = '/scripts/'
    if pathname.startswith(prefix):
        pathname = pathname[len(prefix):]
    else:
        return None
    current_dir = os.path.dirname(__file__)
    script_path = os.path.join(current_dir, pathname)
    if os.path.exists(script_path):
        return script_path
    return None

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    '''Custom HTTP request handler that serves files from the specified directories and 
    diff output directory.'''
    def __init__(self, *args, **kwargs):
        self.server_conf = kwargs.pop('server_conf', {})
        self.generated_dir = self.server_conf.generated_dir
        super().__init__(*args, **kwargs)

    def send_file(self, file_path, content_type: Optional[str]=None):
        '''Send the file named with the appropriate content type. If the content type is not
        provided, it is guessed from the file extension.'''
        with open(file_path, 'rb') as file:
            self.send_response(200)
            if content_type is None:
                content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(file.read())

    def do_GET(self):
        url_path = unquote(self.path)
        
        if url_path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            index_html = find_index_html()
            if index_html is None:
                self.send_response(200)
                self.wfile.write(b"<!DOCTYPE html><html><body><h1>Index not found</h1></body></html>")
                return
            with open(index_html, 'rb') as file:
                self.send_response(200)
                self.wfile.write(file.read())
            return
        
        script_file = find_js_files(url_path)
        if script_file:
            self.send_file(script_file)
            return
        
        if url_path == '/status.json':
            json_path = os.path.join(self.generated_dir, "status.json")
            if os.path.exists(json_path):
                self.send_file(json_path, 'application/json')
                return
            else:
                self.send_response(404)
                self.end_headers()
                return
        
        resource_path = url_path[1:] if url_path.startswith('/') else url_path
        
        resource_path = os.path.join(self.generated_dir, resource_path)

        if resource_path and os.path.exists(resource_path):
            self.send_file(resource_path)
            return
        self.send_response(404)
        self.end_headers()
        
    
    def xlog_message(self, format, *args):
        # Suppress logging
        return


def start_server(server_conf: ServerConfig):
    def handler(*args, **kwargs): MyHttpRequestHandler(*args, server_conf=server_conf, **kwargs)
    
    host = server_conf.host
    port = server_conf.port

    if port is None:
        port = 4600
        while True:
            try:
                with socketserver.TCPServer((host, port), handler) as httpd:
                    print(f"Serving at: http://{host}:{port}")
                    httpd.serve_forever()
            except OSError:
                port += 1
                continue
            break
    else:
        with socketserver.TCPServer((host, port), handler) as httpd:
            print(f"Serving at: http://{host}:{port}")
            httpd.serve_forever()
    
def add_boolean_optional_argument(
    parser: argparse.ArgumentParser, name: str, dest: str=None, help: str=None, default: bool=False):
    if not dest:
        dest = name.replace('-', '_')
    parser.add_argument(
        f'--{name}', 
        dest=dest,
        action='store_true',
        help=help)
    parser.add_argument(
        f'--no-{name}', 
        dest=dest,
        action=argparse.BooleanOptionalAction,
        help=f"Do not {help[0].lower() + help[1:]}")
    
    parser.set_defaults(**{dest:default})

def main():
    parser = argparse.ArgumentParser(
        description='Compare contents of 2 directories for files with given suffix.')
    parser.add_argument('--generated_dir', type=str, default=None, help='Anchorscad generated directory')

    
    parser.add_argument(
        '--host', 
        type=str, 
        default="localhost",
        help="The local host address to start the server on.")
    
    parser.add_argument(
        '--port', 
        type=str, 
        default=None,
        help="The local host address to start the server on.")

    args = parser.parse_args()
    start_server(args)

    return 0

if __name__ == '__main__':
    # args = ['--generated_dir', 'generated-dev-fobm-pmc']
    # sys.argv = [sys.argv[0]] + args
    exit(main())
