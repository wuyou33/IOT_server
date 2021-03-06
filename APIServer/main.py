#
# main.py - Entry point for the application
# Copyright 2016 Oscar Blanco.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#

from http.server import BaseHTTPRequestHandler, HTTPServer
from Parser import Parser
import xmltodict
import requests
import time
import json
import socket

hostName = ""
hostPort = 9001
server_ip = "localhost"
server_port = 8081

class APIServer(BaseHTTPRequestHandler):
    def do_ALL(self):
        network = self.headers.get('Network-token')
        if not network:
            self.send_response(401)
            self.send_header("Content-Length", 0)
            self.end_headers()
            return
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_ip, server_port))
        s.send(bytes("ID: " + network + "\n", 'utf-8'))
        try:
            s.setblocking(1)
            s.settimeout(0.01)
            while s.recv(1): # flush buffer
                pass
        except:
            pass
            
        s.send(bytes(self.command + " " + self.path + " " + self.request_version + '\r\n', 'utf-8'))
        
        if self.headers.get('content-length'):
            s.send(bytes('Content-Length: ' + self.headers.get('content-length') + '\r\n', 'utf-8'))
            
        if self.headers.get('content-type'):
            s.send(bytes('Content-Type: ' + self.headers.get('content-type') + '\r\n', 'utf-8'))
            
        s.send(bytes('\r\n', 'utf-8'))
        #s.send(bytes(str(self.headers), 'utf-8'))
        length = self.headers.get('Content-length')
        if length:
            s.send(self.rfile.read(int(length)))
            
        parser = Parser()
        s.setblocking(1)
        s.settimeout(10) # 10s timeout
        while not parser.end():
            try:
                data = s.recv(1)
            except:
                break
            
            if not data:
                break
            parser.parse(data.decode("utf-8"))
            #print(data.decode("utf-8"))
        
        s.close()
        
        if not parser.statusCode:
            self.send_response(504) # gateway timeout
            self.send_header("Content-Length", 0)
            self.end_headers()
            return
            
        self.send_response(parser.statusCode)
        for header in parser.headers:
            self.send_header(header[0], header[1])
        
        if not "Access-Control-Allow-Methods" in parser.headers:
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        
        if not "Access-Control-Allow-Origin" in [x[0] for x in parser.headers]:
            self.send_header("Access-Control-Allow-Origin", "*")
            
        if not "Access-Control-Allow-Headers" in parser.headers:
            self.send_header("Access-Control-Allow-Headers", "network-token")
        
        self.end_headers()
        self.wfile.write(bytes(parser.body, 'utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Content-Length", 0)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "network-token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.end_headers()
    
    do_GET = do_ALL
    do_HEAD = do_ALL
    do_POST = do_ALL
    do_PUT = do_ALL
    do_DELETE = do_ALL
    

myServer = HTTPServer((hostName, hostPort), APIServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
