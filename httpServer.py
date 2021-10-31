from threading import Thread
from http.server import HTTPServer,BaseHTTPRequestHandler
from jinja2 import Template
import sys
import json,os
from pathlib import Path
import mimetypes
import zlib
from Logger import Logger

def handler(Master):
    class SimpleHandler(BaseHTTPRequestHandler):
        nonlocal Master
        logger = Master
       
        def json(self):
            "return json dict or empty dict"
            if self.headers['Content-Length']:
                return json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode())
            return {} 

        def abort404(self):
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write('<h1>PAGE NOT FOUND.</h1>'.encode())

        def sendData(self,data,header,cache=True):
            self.send_response(200)
            self.send_header("Content-type", header)
            # FIXME: remove dev testing.
            if (sys.argv[-1] != '-dev'):
                if cache:
                    self.send_header("Cache-Control","public, max-age=432000")
            self.end_headers()
            self.wfile.write(data)

        def sendCSS(self,css):
            self.sendData(css,'text/css')
        def sendHTML(self,html):
            self.sendData(html,'text/html')
        def sendJS(self,js):
            self.sendData(js,'application/javascript')
        def sendMAP(self,js):
            self.sendData(js,'application/json')

        def do_GET(self):
            """Respond to a GET request."""
            # display LED flash.
            # self.logger.main.peripheral.led.show('wifi',[50,1],1,)
            path = self.path.strip('/') or 'index.html'
            self.sendFileOr404(path)
            

        def sendFileOr404(self,filePath,mode='html'):
            header = mimetypes.guess_type(filePath)[0] or 'application/json'
            if self.logger.resources.get(filePath,None):
                data = self.logger.resources.get(filePath)
                return self.sendData(data,header)
            return self.abort404()

    return SimpleHandler
 

class HttpServerModule(Thread,Logger):
    """
    A simple http server, servering some pages.
    """
    def __init__(self,main):
        self.main = main
        super().__init__()
        Logger.__init__(self,'http',fileHandler = self.main.fileHandler)
        self.initialize()

    def initialize(self,**kwargs):

        # load all resources from templates folder to self.resources        
        self.resources = {}
        for root,_,files in os.walk('./html'):
            for file in files:
                fp = os.path.join(root,file)
                relative_path = str(Path(fp).relative_to('./html'))
                with open(fp,'rb') as f:
                    self.resources[relative_path] = f.read()
        self.debug(f"Loaded {len(self.resources)} resources. {list(self.resources.keys())}")
        
    def run(self):        
        self.httpServer = None
        try:
            serverAddress = ('localhost',88)
            self.httpServer = HTTPServer(serverAddress,handler(self)) 
            self.debug(f"Started HttpServer on: {serverAddress[0]}:{serverAddress[1]}")
            self.httpServer.serve_forever() 
        except PermissionError:            
            self.error(f"Started HttpServer on: {serverAddress[0]}:{serverAddress[1]} Permission error")
        except Exception as e:
            self.error(f"Start HttpServer on {serverAddress[0]}:{serverAddress[1]} error: {e}")
        # release binding socket.
        if self.httpServer:
            self.httpServer.socket.close()
            self.debug(f"<{self.__class__.__name__}> stopped.")
    
