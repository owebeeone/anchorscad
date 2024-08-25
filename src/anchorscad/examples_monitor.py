'''Anchorscad local files monitor.

Run this script from the root of the Anchorscad project directory to monitor
files in the examples_out directory. This is where files are written when
examples are run.

This script will serve the files in the examples_out directory and will
provide a web page that will load a selected file and will poll for changes
so you don't need to remember to reload the html page when the file changes.

This is intended to be used when developing examples so you can see the
changes as you make them.

'''


import http.server
import os
import sys
import socketserver
import datetime
import time
import urllib.parse
import json
import socket


# The HTML to return for the index page.
# Includes a frame that will load a selected file and a script that will
# keep checking for updates to the file and reload the frame if it has
# a 200 response.
INDEX_HTML = '''\
<!DOCTYPE html>
<html>
<head>
    <title>Anchorscad Monitor {filename}</title>
    <style>
        #myFrame {{
            width: calc(95vw - 20px); /* 5% smaller than the window width */
            height: calc(100vh - 20px); /* clipped by the window */
            border: none;
        }}
    </style>
</head>
<body>
    <h1>Monitor for {filename}</h1>
    <iframe src="{filename}" id="myFrame"></iframe>
    <script>
        var checkFrameDocUpdatedTimeoutId = null;
        var lastModifiedStr = null;
    
        function updateFrame() {{
            var frame = document.getElementById("myFrame");
            frame.src = "{filename}";
        }}

        function checkFrameDocUpdated() {{
            var frame = document.getElementById("myFrame");
            if (lastModifiedStr == null) {{
                var lastModified = frame.contentWindow.document.lastModified;
                var doc = frame.contentWindow.document;
                // Reformat the date to match the If-Modified-Since header.
                // Which is "%a, %d %b %Y %H:%M:%S GMT" instead of 
                // e.g. "Thu, 21 Sep 2023 21:36:12 GMT"
                // from the local time provided e.g. "09/22/2023 07:36:12"
                var lastModifiedDateTime = new Date(lastModified);
                lastModifiedStr = lastModifiedDateTime.toUTCString();
            }}
            var headers = {{ "Poll-For-Changes-For": "10" }};
            // Send the request with the If-Modified-Since header.
            if (lastModifiedStr) {{
                headers["If-Modified-Since"] = lastModifiedStr;
            }}
            fetch(
                "{filename}", 
                {{ 
                    method: "GET",
                    headers: headers           
                }})
                .then(function(response) {{
                    if (response.status !== 304) {{
                        lastModifiedStr = response.headers.get("Last-Modified");
                        updateFrame();
                    }} else {{
                        scheduleCheckFrameDocUpdated();
                    }}
                }})
                .catch(function(error) {{
                    console.error("Error:", error);
                    scheduleCheckFrameDocUpdated();
                }}
            );
        }}
        
        function scheduleCheckFrameDocUpdated() {{
            if (checkFrameDocUpdatedTimeoutId) {{
                clearTimeout(checkFrameDocUpdatedTimeoutId);
            }}
            // Wait a fraction of a second before checking again.
            checkFrameDocUpdatedTimeoutId = setTimeout(checkFrameDocUpdated, 100);
        }}
        var frame = document.getElementById("myFrame");
        frame.onload = function() {{ scheduleCheckFrameDocUpdated(); }};
    </script>
</body>
</html>
'''

HTML_LISINGS_PAGE = '''\
<!DOCTYPE html>
<html>
<head>
    <title>File Listing for {directory}</title>
</head>
<body>
    <h1>File Listings</h1>
    <table>
        <tr>
            <th>File Name</th>
            <th>Last Modified</th>
        </tr>
        <script>
            var file_list = {file_list_json_str};
            
            for (var i = 0; i < file_list.length; i++) {{
                var file = file_list[i];
                document.write('<tr>');
                document.write('<td><a href="' + file.url + '" target="_blank">' + file.name + '</a></td>');
                document.write('<td>' + file.last_modified + '</td>');
                document.write('</tr>');
            }}
        </script>
    </table>
</body>
</html>
'''

def get_file_list(directory):

    file_list = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            last_modified_time = os.path.getmtime(file_path)
            last_modified_time_datetime = datetime.datetime.fromtimestamp(last_modified_time)
            last_modified_time_str = last_modified_time_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
            file_list.append({
                "name": filename,
                "url": f'/monitor?file={filename}',
                "last_modified": last_modified_time_str,
                "last_modified_time" : last_modified_time
            })
    
    # Sort the list by last_modified_time. Most recent first.
    file_list.sort(key=lambda file: file["last_modified_time"], reverse=True)
    return file_list

def get_file_list_html(directory, file_list):
    file_list_json_str = json.dumps(file_list)
    return HTML_LISINGS_PAGE.format(
        directory=directory,
        file_list_json_str=file_list_json_str)


class Handler(http.server.SimpleHTTPRequestHandler):
    
    MAX_WAIT_SECS = 100
    POLL_TIME_SECS = 0.2
    DIRECTORY=None

    def do_GET(self):
        #time.sleep(5)
        parsed_url = urllib.parse.urlparse(self.path)
        
        file_path = parsed_url.path
        
        if file_path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            
            html_str = get_file_list_html(
                self.DIRECTORY,
                get_file_list(self.DIRECTORY))
            self.wfile.write(html_str.encode("utf-8"))
            return
        
        elif file_path == "/monitor":
            filenames = urllib.parse.parse_qs(parsed_url.query).get('file', [None])
            if filenames:
                file_path = f"/{filenames[0]}"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(INDEX_HTML.format(filename=file_path).encode("utf-8"))
            else:
                # Malformed request.
                self.send_response(400)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Bad Request - expected a file name in the 'file' query parameter")
            
        try:
            file_path = self.DIRECTORY + "/" + file_path
            last_modified_time = os.path.getmtime(file_path)
            if_modified_since = self.headers.get("If-Modified-Since")
            wait_secs_str = None
            
            if if_modified_since:
                
                wait_secs_str = self.headers.get("Poll-For-Changes-For")
            
            if wait_secs_str:
                
                wait_secs = float(wait_secs_str)
                # Only wait if the file has been modified since the timestamp
                # and the wait time is not too long.
                if if_modified_since and wait_secs > 0 and wait_secs <= self.MAX_WAIT_SECS:
                    # Convert the time stamp to a datetime object.
                    if_modified_since_datetime = datetime.datetime.strptime(if_modified_since, "%a, %d %b %Y %H:%M:%S GMT")
                    
                    # Convert the datetime object to a timestamp.
                    if_modified_since_timestamp = if_modified_since_datetime.timestamp()

                    # Wait until the file has been modified since the timestamp or we have waited long enough.
                    # too long.
                    start_time = time.time()    
                    while int(last_modified_time) <= if_modified_since_timestamp:
                        time.sleep(self.POLL_TIME_SECS)
                        last_modified_time = os.path.getmtime(file_path)
                        if time.time() - start_time > wait_secs:
                            break
                        
                    # If we have waited long enough, return a 304 response.
                    if int(last_modified_time) <= if_modified_since_timestamp:
                        last_modified_time_datetime = datetime.datetime.fromtimestamp(last_modified_time)
                        last_modified_time_str = last_modified_time_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
                        self.send_header("Last-Modified", last_modified_time_str)
                        self.send_response(304)
                        self.end_headers()
                        return
                
            with open(file_path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                last_modified_time_datetime = datetime.datetime.fromtimestamp(last_modified_time)
                last_modified_time_str = last_modified_time_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
                self.send_header("Last-Modified", last_modified_time_str)
                self.end_headers()
                self.copyfile(f, self.wfile)

        except FileNotFoundError:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"File not found")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""

    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.last_modified_time = 0


def find_free_port(start_port=8080):
    port = start_port
    while True:
        try:
            # Create a socket object
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Set the socket option to reuse the address
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # Try binding the socket to the port
                sock.bind(('localhost', port))
                return port
            
        except OSError:
            # If the port is already in use, increment the port number and try again
            port += 1


def main():
    
    args = sys.argv[1:]
    directory = args[0] if args else "examples_out"
    port = find_free_port(8080)
    
    # Patch the Handler class to use the directory.
    class HandlerForDir(Handler):
        DIRECTORY=directory
    
    server = ThreadedHTTPServer(('localhost', port), HandlerForDir)
    print('Starting server, use <Ctrl-C> to stop')
    print(f'Monitoring directory: {directory}')
    print(f'Open http://localhost:{port}/')
    server.serve_forever()


if __name__ == '__main__':
    main()
