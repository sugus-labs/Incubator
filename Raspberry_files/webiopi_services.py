#!/usr/bin/python

#   Copyright 2012 Eric Ptak - trouch.com
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import os
import sys
import time
import errno
import signal
import socket
import threading

import mimetypes as mime
import re
import base64
import codecs
import hashlib

import _webiopi.GPIO as GPIO

PYTHON_MAJOR = sys.version_info.major

if PYTHON_MAJOR >= 3:
    import http.server as BaseHTTPServer
else:
    import BaseHTTPServer

VERSION = '0.5.3'
SERVER_VERSION = "WebIOPi/Python%d/%s" % (PYTHON_MAJOR, VERSION)

FUNCTIONS = {
    "I2C0": {"enabled": False, "gpio": {0:"SDA", 1:"SCL"}},
    "I2C1": {"enabled": True, "gpio": {2:"SDA", 3:"SCL"}},
    "SPI0": {"enabled": False, "gpio": {7:"CE1", 8:"CE0", 9:"MISO", 10:"MOSI", 11:"SCLK"}},
    "UART0": {"enabled": True, "gpio": {14:"TX", 15:"RX"}}
}

MAPPING = [[], [], []]
MAPPING[1] = ["V33", "V50", 0, "V50", 1, "GND", 4, 14, "GND", 15, 17, 18, 21, "GND", 22, 23, "V33", 24, 10, "GND", 9, 25, 11, 8, "GND", 7]
MAPPING[2] = ["V33", "V50", 2, "V50", 3, "GND", 4, 14, "GND", 15, 17, 18, 27, "GND", 22, 23, "V33", 24, 10, "GND", 9, 25, 11, 8, "GND", 7]

M_PLAIN = "text/plain"
M_JSON  = "application/json"

__running__ = False
    
def runLoop(func=None):
    global __running__
    __running__ = True
    if func != None:
        while __running__:
            func()
    else:
        while __running__:
            time.sleep(1)

def __signalHandler__(sig, func=None):
    global __running__
    __running__ = False

def encodeAuth(login, password):
    abcd = "%s:%s" % (login, password)
    if PYTHON_MAJOR >= 3:
        b = base64.b64encode(abcd.encode())
    else:
        b = base64.b64encode(abcd)
    return hashlib.sha256(b).hexdigest()

def log(message):
    print("%s %s" % (SERVER_VERSION, message))

def warn(message):
    log("Warning - %s" % message)

def error(message):
    log("Error - %s" % message)

def getLocalIP():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 53))
            (host, p) = s.getsockname()
            s.close()
            return host 
        except (socket.error, e):
            return "localhost"

class Server():
    
    def __init__(self, port, context="webiopi", index="index.html", login=None, password=None, passwdfile=None):
        self.log_enabled = False
        self.handler = RESTHandler()
        self.host = getLocalIP()
        self.http_port = port

        self.context = context
        self.index = index
        self.auth = None
        
        if passwdfile != None:
            if os.path.exists(passwdfile):
                f = open(passwdfile)
                self.auth = f.read().strip(" \r\n")
                f.close()
                if len(self.auth) > 0:
                    log("Access protected using %s" % passwdfile)
                else:
                    log("Passwd file is empty : %s" % passwdfile)
            else:
                error("Passwd file not found : %s" % passwdfile)
            
        elif login != None or password != None:
            self.auth = encodeAuth(login, password)
            log("Access protected using login/password")
            
        if self.auth == None or len(self.auth) == 0:
            warn("Access unprotected")
            
        if not self.context.startswith("/"):
            self.context = "/" + self.context
        if not self.context.endswith("/"):
            self.context += "/"

        self.http_server = HTTPServer(self.host, self.http_port, self.context, self.index, self.handler, self.auth)
        self.http_server.log_enabled = self.log_enabled
        
    def addMacro(self, callback):
        self.handler.addMacro(callback)
        
    def stop(self):
        self.http_server.stop()

class HTTPServer(BaseHTTPServer.HTTPServer, threading.Thread):
    def __init__(self, host, port, context, index, handler, auth=None):
        BaseHTTPServer.HTTPServer.__init__(self, ("", port), HTTPHandler)
        threading.Thread.__init__(self)

        self.docroot = "/usr/share/webiopi/htdocs"
        self.log_enabled = False
        self.host = host
        self.port = port
        self.context = context
        self.index = index
        self.handler = handler
        self.auth = auth

        self.start()
            
    def run(self):
        log("HTTP Server started at http://%s:%s%s" % (self.host, self.port, self.context))
        self.running = True
        try:
            self.serve_forever()
        except Exception as e:
            if self.running:
                error("%s" % e)
        log("HTTP Server stopped")

    def stop(self):
        self.running = False
        self.server_close()

class RESTHandler():
    def __init__(self):
        self.callbacks = {}

    def addMacro(self, callback):
        self.callbacks[callback.__name__] = callback

    def getJSON(self):
        json = "{"
        first = True
        for (alt, value) in FUNCTIONS.items():
            if not first:
                json += ", "
            json += '"%s": %d' % (alt, value["enabled"])
            first = False
        
        json += ', "GPIO":{\n'
        first = True
        for gpio in range(GPIO.GPIO_COUNT):
            if not first:
                json += ", \n"

            function = GPIO.getFunctionString(gpio)
            value = GPIO.input(gpio)
                    
            json += '"%d": {"function": "%s", "value": %d' % (gpio, function, value)
            if GPIO.getFunction(gpio) == GPIO.PWM:
                (type, value) = GPIO.getPulse(gpio).split(':')
                json  += ', "%s": %s' %  (type, value)
            json += '}'
            first = False
            
        json += "\n}}"
        return json

    def do_GET(self, relativePath):
        # JSON full state
        if relativePath == "*":
            return (200, self.getJSON(), M_JSON)
            
        # RPi header map
        elif relativePath == "map":
            json = "%s" % MAPPING[GPIO.BOARD_REVISION]
            json = json.replace("'", '"')
            return (200, json, M_JSON)

        # server version
        elif relativePath == "version":
            return (200, SERVER_VERSION, M_PLAIN)

        # board revision
        elif relativePath == "revision":
            revision = "%s" % GPIO.BOARD_REVISION
            return (200, revision, M_PLAIN)

         # get temperature
        elif relativePath == "TEMP":
            strPath="/home/pi/test/thermostate/lastTemp.txt"
            f = open(strPath)
            strText = f.read()
            return (200, strText, M_PLAIN)


        # Single GPIO getter
        elif relativePath.startswith("GPIO/"):
            (mode, s_gpio, operation) = relativePath.split("/")
            gpio = int(s_gpio)

            value = None
            if operation == "value":
                if GPIO.input(gpio):
                    value = "1"
                else:
                    value = "0"
    
            elif operation == "function":
                value = GPIO.getFunctionString(gpio)
    
            elif operation == "pwm":
                if GPIO.isPWMEnabled(gpio):
                    value = "enabled"
                else:
                    value = "disabled"
                
            elif operation == "pulse":
                value = GPIO.getPulse(gpio)
                
            else:
                return (404, operation + " Not Found", M_PLAIN)
                
            return (200, value, M_PLAIN)

        else:
            return (0, None, None)

    def do_POST(self, relativePath):
        if relativePath.startswith("EGG/"):
            (mode, s_gpio, operation, value) = relativePath.split("/")
            if s_gpio == "1":
                gpio = 7
            elif s_gpio == "2":
                gpio = 8
            elif s_gpio == "3":
                gpio = 9
            elif s_gpio == "4":
                gpio = 10
            elif s_gpio == "5":
                gpio = 11
            elif s_gpio == "6":
                gpio = 22
            elif s_gpio == "7":
                gpio = 23
            elif s_gpio == "8":
                gpio = 24
            else:
                gpio = 25

            if operation == "value":
                if value == "off":
                    GPIO.output(gpio, GPIO.LOW)
                elif value == "on":
                    GPIO.output(gpio, GPIO.HIGH)
                else:
                    return (400, "Bad Value", M_PLAIN)
    
                return (200, value, M_PLAIN)

            elif operation == "function":
                value = value.lower()
                if value == "in":
                    GPIO.setFunction(gpio, GPIO.IN)
                elif value == "out":
                    GPIO.setFunction(gpio, GPIO.OUT)
                elif value == "pwm":
                    GPIO.setFunction(gpio, GPIO.PWM)
                else:
                    return (400, "Bad Function", M_PLAIN)

                value = GPIO.getFunctionString(gpio)
                return (200, value, M_PLAIN)

            elif operation == "sequence":
                (period, sequence) = value.split(",")
                period = int(period)
                GPIO.outputSequence(gpio, period, sequence)
                return (200, sequence[-1], M_PLAIN)
                
            elif operation == "pwm":
                if value == "enable":
                    GPIO.enablePWM(gpio)
                elif value == "disable":
                    GPIO.disablePWM(gpio)
                
                if GPIO.isPWMEnabled(gpio):
                    result = "enabled"
                else:
                    result = "disabled"
                
                return (200, result, M_PLAIN)
                
            elif operation == "pulse":
                GPIO.pulse(gpio)
                return (200, "OK", M_PLAIN)
                
            elif operation == "pulseRatio":
                ratio = float(value)
                GPIO.pulseRatio(gpio, ratio)
                return (200, value, M_PLAIN)
                
            elif operation == "pulseAngle":
                angle = float(value)
                GPIO.pulseAngle(gpio, angle)
                return (200, value, M_PLAIN)
                
            else: # operation unknown
                return (404, operation + " Not Found", M_PLAIN)
                
        elif relativePath.startswith("macros/"):
            (mode, fname, value) = relativePath.split("/")
            if fname in self.callbacks:
                callback = self.callbacks[fname]

                if ',' in value:
                    args = value.split(',')
                    result = callback(*args)
                elif len(value) > 0:
                    result = callback(value)
                else:
                    result = callback()
                     
                response = ""
                if result:
                    response = "%s" % result
                return (200, response, M_PLAIN)
                    
            else:
                return (404, fname + " Not Found", M_PLAIN)

        elif operation == "saca17":
            GPIO.setFunction(17, GPIO.OUT)
        
        elif operation == "saca171":
            GPIO.output(17,GPIO.HIGH)

        elif operation == "saca170":
            GPIO.output(17,GPIO.LOW)

        elif operation == "saca21":
            GPIO.setFunction(21, GPIO.OUT)
        
        elif operation == "saca211":
            GPIO.output(21,GPIO.HIGH)

        elif operation == "saca210":
            GPIO.output(21,GPIO.LOW)

        elif relativePath.startswith("EGGSOFF"):
            GPIO.output(7, GPIO.LOW)
            GPIO.output(8, GPIO.LOW)
            GPIO.output(9, GPIO.LOW)
            GPIO.output(10, GPIO.LOW)
            GPIO.output(11, GPIO.LOW)
            GPIO.output(22, GPIO.LOW)
            GPIO.output(23, GPIO.LOW)
            GPIO.output(24, GPIO.LOW)
            GPIO.output(25, GPIO.LOW)
            return (200, "ALL EGGS OFF", M_PLAIN)

        elif relativePath.startswith("EGGSON"):
            GPIO.output(7, GPIO.HIGH)
            GPIO.output(8, GPIO.HIGH)
            GPIO.output(9, GPIO.HIGH)
            GPIO.output(10, GPIO.HIGH)
            GPIO.output(11, GPIO.HIGH)
            GPIO.output(22, GPIO.HIGH)
            GPIO.output(23, GPIO.HIGH)
            GPIO.output(24, GPIO.HIGH)
            GPIO.output(25, GPIO.HIGH)
            return (200, "ALL EGGS ON", M_PLAIN)
    

        else: # path unknowns
            return (0, None, None)


        
class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if self.server.log_enabled:
            log(format % args)

    def version_string(self):
        return SERVER_VERSION + ' ' + self.sys_version
    
    def checkAuthentication(self):
        if self.server.auth == None or len(self.server.auth) == 0:
            return True
        
        authHeader = self.headers.get('Authorization')
        if authHeader == None:
            return False
        
        if not authHeader.startswith("Basic "):
            return False
        
        auth = authHeader.replace("Basic ", "")
        if PYTHON_MAJOR >= 3:
            hash = hashlib.sha256(auth.encode()).hexdigest()
        else:
            hash = hashlib.sha256(auth).hexdigest()
            
        if hash == self.server.auth:
            return True
        return False

    def requestAuthentication(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="webiopi"')
        self.end_headers();
    
    def sendResponse(self, code, body=None, type="text/plain"):
        if code >= 400:
            if body != None:
                self.send_error(code, body)
            else:
                self.send_error(code)
        else:
            self.send_response(code)
            self.send_header("Content-type", type);
            self.end_headers();
            self.wfile.write(body.encode())
            
    def serveFile(self, relativePath):
        if relativePath == "":
            relativePath = self.server.index
                        
        realPath = relativePath;
        
        if not os.path.exists(realPath):
            realPath = self.server.docroot + os.sep + relativePath
            
        if not os.path.exists(realPath):
            return self.sendResponse(404, "Not Found")

        realPath = os.path.realpath(realPath)
        
        if realPath.endswith(".py"):
            return self.sendResponse(403, "Not Authorized")
        
        if not (realPath.startswith(self.server.docroot) or realPath.startswith(os.getcwd())):
            return self.sendResponse(403, "Not Authorized")
            
        if os.path.isdir(realPath):
            realPath += os.sep + self.server.index;
            if not os.path.exists(realPath):
                return self.sendResponse(403, "Not Authorized")
            
        (type, encoding) = mime.guess_type(realPath)
        f = codecs.open(realPath, encoding="utf-8")
        data = f.read()
        f.close()
        self.send_response(200)
        self.send_header("Content-type", type);
#            self.send_header("Content-length", os.path.getsize(realPath))
        self.end_headers()
        self.wfile.write(data.encode(encoding="utf-8"))
        
    def processRequest(self):
        if not self.checkAuthentication():
            return self.requestAuthentication()
        
        relativePath = self.path.replace(self.server.context, "/")
        if relativePath.startswith("/"):
            relativePath = relativePath[1:];

        try:
            result = (None, None, None)
            if self.command == "GET":
                result = self.server.handler.do_GET(relativePath)
            elif self.command == "POST":
                result = self.server.handler.do_POST(relativePath)
            else:
                result = (405, None, None)
                
            (code, body, type) = result
            
            if code > 0:
                self.sendResponse(code, body, type)
            else:
                if self.command == "GET":
                    self.serveFile(relativePath)
                else:
                    self.sendResponse(404)

        except (GPIO.InvalidDirectionException, GPIO.InvalidChannelException, GPIO.SetupException) as e:
            self.sendResponse(403, "%s" % e)
        except Exception as e:
            self.sendResponse(500)
            raise e
            
    def do_GET(self):
        self.processRequest()

    def do_POST(self):
        self.processRequest()

def main(argv):
    port = 8000
    passwdfile = "/etc/webiopi/passwd"

    if len(argv)  == 2:
        port = int(argv[1])
    
    server = Server(port=port, passwdfile=passwdfile)
    runLoop()
    server.stop()

signal.signal(signal.SIGINT, __signalHandler__)
signal.signal(signal.SIGTERM, __signalHandler__)

if __name__ == "__main__":
    main(sys.argv)