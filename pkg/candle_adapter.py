"""Candle adapter for Mozilla WebThings Gateway."""

import os
import sys
import time
from time import sleep
import asyncio
import logging
import urllib
import requests
#import urllib2
import json
import re
import subprocess
import threading
import serial #as ser
import serial.tools.list_ports as prtlst
from flask import Flask,Response, request,render_template,jsonify, url_for



from gateway_addon import Adapter, Device, Database

_TIMEOUT = 3

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.mozilla-iot', 'config'),
]

if 'MOZIOT_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['MOZIOT_HOME'], 'config'))


    
#def flaskThread():
#    app.run()


#global current_serial_devices, previous_serial_devices
#current_serial_devices = {}
#previous_serial_devices = {}



'''
def enumerate_serial_devices():
    return set([item for item in list_ports.comports()])

def check_new_devices(old_devices):
    devices = enumerate_serial_devices()
    added = devices.difference(old_devices)
    removed = old_devices.difference(devices)
    if added:
        print('added: {}'.format(added))
    if removed:
        print('removed: {}'.format(removed))
    return devices

#old_devices = enumerate_serial_devices()
'''




#
# ADAPTER
#

class CandleAdapter(Adapter):
    """Adapter for Candle"""

    def __init__(self, verbose=True):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        print("initialising adapter from class")
        self.adding_via_timer = False
        self.pairing = False
        self.name = self.__class__.__name__
        Adapter.__init__(self, 'candle-adapter', 'candle-adapter', verbose=verbose)
        #print("Adapter ID = " + self.get_id())
        
        print("paths:" + str(_CONFIG_PATHS))
        
        for path in _CONFIG_PATHS:
            if os.path.isdir(path):
                self.persistence_file_path = os.path.join(
                    path,
                    'candle-adapter-persistence.json'
                )
        
        self.add_on_path = os.path.join(os.path.expanduser('~'), '.mozilla-iot', 'addons','Candle-manager-addon')
        print("self.add_on_path = " + str(self.add_on_path))
        
        self.DEBUG = False
        self.DEVELOPMENT = True
        
        self.json_sketches_url = ""
        self.simple_password = ""
        self.arduino_type = "nano"
        
        # Get the user's settings
        self.add_from_config()
        
        
        
        
        # Scan sources directory
        self.sources = []
        #self.cwd = str(os.getcwd())
        try:
            self.scan_source_dir()
        except:
            print("Failed to scan sources")
        
        
        
        
        # Download/update sketches
        print("self.json_sketches_url = " + str(self.json_sketches_url))
        if self.json_sketches_url.startswith("http") and self.json_sketches_url.endswith(".json"):
            try:
                response = requests.get(self.json_sketches_url, allow_redirects=True) # was True
                
                #print("response.status_code = " + str(response.status_code))
                #print("response.encoding = " + str(response.encoding))
                #print("Got response")
                #print("response: " + str(response))
                json_sketches_data = json.loads(response.content.decode('utf-8'))
                if self.DEBUG:
                    print(str(json_sketches_data["sketch_urls"]))
                for sketch_url in json_sketches_data["sketch_urls"]:
                    self.download_source(sketch_url)
            except Exception as e:
                print("Failed to download sketches from JSON file: " + str(e))
                
        elif self.json_sketches_url.startswith("http") and self.json_sketches_url.endswith(".ino"):
            self.download_source(self.json_sketches_url)
        


        # Update the Arduino CLI:
        if self.update_arduino_cli():
            print("Succesfully updated Arduino CLI index and AVR")
        else:
            print("Error: failed to update Arduino CLI")
            
            
        # Get JSON list of already installer Arduino libraries
        print("CHECKING ALREADY INSTALLED LIBRARIES")
        self.required_libraries = []
        self.installed_libraries = []
        try:
            #command = self.add_on_path + '/arduino-cli lib list --all --format=json' # perhaps use os.path.join(self.add_on_path, 'arduino-cli') + 'lib list --all --format=json' ?
            command = os.path.join(self.add_on_path, 'arduino-cli') + ' lib list --all --format=json'
            installed_libraries_response = json.loads(run_command_json(command))

            for lib_object in installed_libraries_response['libraries']:
                print(lib_object['library']['Properties']['name'])
                self.installed_libraries.append(lib_object['library']['Properties']['name'])
        except:
            print("failed to check libraries")
            
        # Pre-compile the cleaner code
        self.cleaner_pre_compiled = False
        try:
            hex_filename = "Candle_cleaner.arduino.avr." + self.arduino_type + ".hex"
            #cleaner_hex_path = self.add_on_path + "/code/Candle_cleaner/Candle_cleaner.arduino.avr." + self.arduino_type + ".hex"
            cleaner_hex_path = os.path.join(self.add_on_path, 'code','Candle_cleaner',hex_filename)
            print("cleaner_hex_path = " + str(cleaner_hex_path))
            if os.path.isfile(cleaner_hex_path):
                print("HEX file already existed, so no need to pre-compile the Candle Cleaner")
                self.cleaner_pre_compiled = True
            elif "Candle_cleaner" in self.sources:
                if self.DEBUG:
                    print("Candle Cleaner was found at index " + str(self.sources.index("Candle_cleaner")))
                test_result = self.compile(self.sources.index("Candle_cleaner"))
                if self.DEBUG:
                    print("Pre-compile result:" + str(test_result))
                if test_result["success"] == True:
                    print("Succesfully pre-compiled the cleaner code")
                    self.cleaner_pre_compiled = True
            else:
                print("Candle Cleaner was missing from the source directory")
        except Exception as e:
            print("Failed to pre-compile test code: " + str(e))



        # USB scanning variables
        self.previous_serial_devices = []
        self.last_added_serial_port = ""
        self.scan_usb_ports()

        # Create the Candle thing
        device = CandleDevice(self)
        self.handle_device_added(device)


        # Arduino CLI
        self.upload_status = "Preparing"
        self.bootloader = ":cpu=atmega328"
        
        
        # Flask webserver
        self.port = 8686
        print(str(__name__))
        
        # Disable outputting to console
        #if not self.DEBUG:
        #    log = logging.getLogger('werkzeug')
        #    log.setLevel(logging.ERROR)
        
        app = Flask(__name__)
        app = Flask(__name__, root_path= os.path.join(self.add_on_path, 'pkg') )
        
        @app.route('/') # The home page
        def index():
            return render_template('index.html')
            
        @app.route('/source') # Returns a list of all available source code in the source folder
        def app_scan_source_dir():
            d = self.scan_source_dir()
            return jsonify(d)   
            
        @app.route('/scanUSB') # Returns newly plugged in USB serial devices
        def app_scanUSB():
            return jsonify( self.scan_usb_ports() )  
            
        @app.route('/extract/<source_id>') # Returns a list of all available source code in the source folder
        def app_extract_settings(source_id):
            if self.DEBUG:
                print("source ID to extract: " + str(source_id))
            d = self.change_settings(source_id, False, None) # False here indicates it should only scan for variables.
            return jsonify(d) 
            
        @app.route('/generate_code/<source_id>', methods=['POST']) # Generates source code from the new settings
        def app_generate_code(source_id):
            
            data = request.get_json()
            if self.DEBUG:
                print("received new settings json:" + str(data))
            
            d = self.change_settings(source_id, True, data)
            return jsonify(d)
            
        @app.route('/check_libraries/<source_id>') # Check if all required libraries are installed
        def app_check_libraries(source_id):
            d = self.check_libraries(source_id)
            return jsonify(d)
            
        @app.route('/compile/<source_id>') # Compile the code
        def app_compile(source_id):
            d = self.compile(source_id)
            return jsonify(d)
            
        @app.route('/test_upload/<source_id>') # Do a test upload, and see if the correct bootloader is set.
        def app_test_upload(source_id): # It doesn't actually use the source_id.
            
            d = self.test_upload(source_id)
            return jsonify(d)
        
        
        @app.route('/upload/<source_id>') # Returns a list of all available source code in the source folder
        def app_upload(source_id):
            
            d = self.upload(source_id, self.bootloader)
            return jsonify(d)
            
            
        @app.route('/serial-output')
        def app_serial_output():
            
            try:
                self.open_serial_port.close()
            except:
                pass
            
            def inner2():
                if self.last_added_serial_port == "":
                    yield "No serial port found"
                try:
                    if self.DEBUG:
                        print("Opening serial port")
                    self.open_serial_port = serial.Serial(self.last_added_serial_port, 115200, timeout=1)
                    self.open_serial_port.flushInput()
                except:
                    print("Could not open serial port")
            
                countdown_counter = 60
                while countdown_counter > 0:
                    if self.DEBUG:
                        print("countdown_counter = " + str(countdown_counter))
                    try:
                        ser_bytes = self.open_serial_port.readline()
                        decoded_bytes = ser_bytes.decode("utf-8") # float(ser_bytes[0:len(ser_bytes)-2].decode("utf-8"))
                        if len(decoded_bytes) > 0:
                            decoded_bytes += "<br/>"
                        if self.DEBUG:
                            print(str(decoded_bytes))
                        yield decoded_bytes
                        
                    except:
                        print("Could not read from the serial port")
                        break
                    
                    countdown_counter -= 1
                    sleep(.1)
                    
                print("Closing serial port")
                self.open_serial_port.close()
                
            return Response(inner2(), mimetype='text/html')  # text/html is required for most browsers to show th$
            
        
        @app.route('/stop_listening') # If it's still open, close the serial port.
        def app_stop_listening():
            try:
                self.open_serial_port.close()
            except:
                pass
            return '{"success":True}'
            
            
        # Used to aid development
        @app.context_processor
        def override_url_for():
            return dict(url_for=dated_url_for)
            
        def dated_url_for(endpoint, **values):
            if endpoint == 'static':
                filename = values.get('filename', None)
                if filename:
                    file_path = os.path.join(app.root_path,
                                         endpoint, filename)
                    values['q'] = int(os.stat(file_path).st_mtime)
            return url_for(endpoint, **values)
        
        #template_folder = os.path.join(self.add_on_path, 'pkg', 'templates')
        #static_folder = os.path.join(self.add_on_path, 'pkg', 'static')
        
        
        #app.run(host="0.0.0.0", port=self.port, use_reloader=False, template_folder=template_folder, static_folder=static_folder)
        app.run(host="0.0.0.0", port=self.port, use_reloader=False)
        #threading.Thread(target=app.run).start()


    def update_arduino_cli(self):
        success = False
        index_updated = False
        
        # Updating Arduino CLI index
        try:
            command = self.add_on_path + '/arduino-cli core update-index'
            for line in run_command(command):
                if self.DEBUG:
                    print(line)
                if line.startswith('Command failed'):
                    print("CLI update index failed")
                elif line.startswith('Command success'):
                    if self.DEBUG:
                        print("CLI update index success")
                    index_updated = True
                time.sleep(.1)
        except:
            print("Error sending Arduino CLI update index command")
            
        # Downloading latest version of AVR for Arduino CLI, which allows it to work with the Arduino Nano, Uno and Mega
        if index_updated:
            try:
                command = self.add_on_path + '/arduino-cli core install arduino:avr'
                for line in run_command(command):
                    if self.DEBUG:
                        print(line)
                    if line.startswith('Command failed'):
                        print("CLI update AVR failed")
                    elif line.startswith('Command success'):
                        if self.DEBUG:
                            print("CLI update AVR success")
                        success = True
                    time.sleep(.1)
            except:
                print("Error sending Arduino CLI update AVR command")
        return success



    def download_source(self, sketch_url):
        print("downloading sketch at " + str(sketch_url))
        pattern = '^http.*\/([\w\-]*)\.ino'  # Extract file name (without .ino)
        matched = re.match(pattern, sketch_url)
        #print("matched?:" + str(matched))
        if matched:
            if matched.group(1) != None:
                target_filename = str(matched.group(1))
                if self.DEBUG:
                    print("Sketch file name: " + target_filename)
                target_dir = os.path.join(self.add_on_path, "source", target_filename)
                target_file = os.path.join(target_dir, target_filename + ".ino")
                
                if self.DEBUG:
                    print("target_dir  = " + str(target_dir))
                    print("target_file = " + str(target_file))
                
                attempts = 0
                while attempts < 3:
                
                    # Download file
                    try:
                        response = requests.get(sketch_url, allow_redirects=True)
                    except Exception as e:
                        print("could not download: " + str(e))
                        attempts += 1
                        continue
                        
                    # Create directory
                    try:
                        if not os.path.exists(target_dir):
                            os.mkdir(target_dir)
                    except Exception as e:
                        print("problem creating directory: " + str(e))
                        attempts += 1
                        continue
                        
                    # Store file
                    try:
                        f = open( target_file, 'w' )
                        #open('google.ico', 'wb').write(response.content)
                        f.write( response.content.decode('utf-8') )
                        f.close()
                        break
                    except Exception as e:
                        attempts += 1
                        print("Error writing to file: " + str(e))
        
        
        

    def scan_usb_ports(self): # Scans for USB serial devices
        current_serial_devices = []
        result = {"state":"stable"}
        
            
        ports = prtlst.comports()
        for port in ports:
            if 'USB' in port[1]: #check 'USB' string in device description
                #if self.DEBUG:
                #    print("port: " + str(port[0]))
                #    print("usb device description: " + str(port[1]))
                if str(port[0]) not in current_serial_devices:
                    current_serial_devices.append(str(port[0]))
                    if str(port[0]) not in self.previous_serial_devices:
                        self.last_added_serial_port = str(port[0])
                        #if self.DEVELOPMENT:
                        #    self.last_added_serial_port = '/dev/ttyUSB1' # Overrides the port to use during development of this add-on.
                        print("New USB device added: " + self.last_added_serial_port)
                        result["state"] = "added"
        
        #print("Current USB devices: " + str(current_serial_devices))
        
        if len(self.previous_serial_devices) > len(current_serial_devices):
            print("A USB device was removed")
            result["state"] = "removed"
            
        self.previous_serial_devices = current_serial_devices
        
        return result



    def scan_source_dir(self):
        print("Scanning source file directory")
        
        print(self.add_on_path)
        file_list = []
        for dentry in os.scandir(self.add_on_path + "/source"):
            if not dentry.name.startswith('.') and dentry.is_dir():
                file_list.append(dentry.name)
        self.sources = file_list
        return file_list



    # This function is dual use. if generate_new_code is set to False it will scan arduino code and extract the settings. if generate_new_code is set to True is will create new arduino code with updated settings that it received from the clientside.
    def change_settings(self, source_id, generate_new_code=False, new_values_list=[]):
        state = 0 # extracting the comment
        explanation = ""
        print("generate_new_code: " + str(generate_new_code))
        if generate_new_code:
            print("Creating new code from new desired settings:" + str(new_values_list))
        else:
            print("Extracting settings from .ino file")

        result = {}
        settings = []
        required_libraries = []
        lines = []
        new_code = ""
        settings_counter = 0
        source_name = str(self.sources[int(source_id)])
        path = str(self.add_on_path) + "/source/" + source_name  + "/" + source_name + ".ino"
        print(path)
        file = open(path, 'r')
        lines = file.readlines()
        file.close()
        
        for line in lines:
            #print(line)
            
            # This part deals with the header text
            if state == 0:
                new_code += str(line) #+ "\n" # if generate_new_code is set to true, this will create the code with the updated settings.
                if "* SETTINGS */" not in line:
                    if line.find('*') > -1 and line.find('*') < 3: # Remove the * that precedes lines in the comment
                        line = re.sub(r'.*\*', '', line)
                        explanation += str(line) #+ "\n"
                else:
                    state = 1
                    print("Done with explanation")
                    result["explanation"] = explanation
                    continue
                    
            # This part deals with the part of the Arduino code that contains the settings
            if state == 1:
                title = ""
                comment = ""
                if "/* END OF SETTINGS" not in line:
                    if line == '\n':
                        new_code += str(line)
                        continue
                        
                    elif "MY_ENCRYPTION_SIMPLE_PASSWD" in line or "MY_SECURITY_SIMPLE_PASSWD" in line or "MY_SIGNING_SIMPLE_PASSWD" in line:
                        
                        if generate_new_code:
                            try:
                                # REPLACING PASSWORD
                                pattern = '^#define\s\w+SIMPLE_PASSWD\s\"([\w\.\*\#\@\(\)\!\ˆ\%\&\$\-]+)\"'
                                matched = re.match(pattern, line)
                                if matched and matched.group(1) != None:
                                        
                                    line = line.replace(str(matched.group(1)),self.simple_password, 1)
                                    print("updated line:" + str(line))
                                    new_code += str(line) #+ "\n"
                                    continue
                            except:
                                print('Unable to merge password while generating new code')
                                continue
                        else:
                            continue
                            
                        
                    else:
                        
                        
                        try:
                            # NORMAL VARIABLE
                            pattern = '\w+\s\w+\[?[0-9]*?\]?\s?\=\s?\"?([\w\+\!\@\#\$\%\ˆ\&\*\(\)\.\,\-]*)\"?\;\s*\/?\/?\s?(.*)'
                            matched = re.match(pattern, line)
                            #print("matched?:" + str(matched))
                            if matched:
                                if matched.group(2) != None:
                                    sentences = split_sentences(matched.group(2))
                                    title = sentences[0]
                                    sentences.pop(0)
                                    
                                    try:
                                        comment = ''.join(sentences) #str(matched.group(2).split('.', 1)[1])
                                    except:
                                        pass
                                else:
                                    continue # if a setting does not have a comment it cannot be used.
                                    
                                if generate_new_code and settings_counter < len(new_values_list):
                                    line = line.replace(str(matched.group(1)), str(new_values_list[settings_counter]), 1)
                                    print("updated line:" + str(line))
                                    new_code += str(line) #+ "\n"
                                    
                                else:
                                    settings.append({"type":"text" ,"value":matched.group(1), "title":title ,"comment":comment}) # moet nog een ID nummer in ofzo, anders krijg je dubbele
                                
                                
                                settings_counter += 1 # This is used to keep track of the ID of the settings line we are modifying.
                                continue
                        except:
                            print('normal variable error')
                            continue
                            
                            
                        try:
                            # COMPLEX DEFINE WITH A STRING VALUE INSIDE ""
                            pattern = '^#define\s\w+\s\"?([\w\.\*\#\@\(\)\!\ˆ\%\&\$\-]+)\"?\s*\/?\/?\s?(.*)'
                            matched = re.match(pattern, line)
                            if matched:
                                if matched.group(2) != None:
                                    sentences = split_sentences(matched.group(2))
                                    title = sentences[0]
                                    sentences.pop(0)
                                    
                                    try:
                                        comment = ''.join(sentences) #str(matched.group(2).split('.', 1)[1])
                                    except:
                                        pass
                                else:
                                    continue # if a setting does not have a comment it cannot be used.
                                    
                                if generate_new_code and settings_counter < len(new_values_list):
                                    line = line.replace(str(matched.group(1)),str(new_values_list[settings_counter]), 1)
                                    print("updated line:" + str(line))
                                    new_code += str(line) #+ "\n"
                                    
                                settings.append({"type":"text" ,"value":matched.group(1), "title":title ,"comment":comment})
                                
                                settings_counter += 1
                                continue
                        except:
                            print('complex define error')
                            continue
                            
                        
                        try:
                            # A TOGGLE DEFINE
                            pattern = '^(\/\/)?\s?#define\s\w+\s*\/?\/?\s?(.*)' #define DOOR1_SELF_LOCKING                          #Self locking? Should door number one automatically re-lock itself after a short amount of time?
                            matched = re.match(pattern, line)
                            if matched:
                                #print("toggle define match line:" + line)
                                #print("- Slashes?: " + str(matched.group(1)))
                                #print("- comment = " + str(matched.group(2)))
                                #print("checkbox matched.group(1) = " + str(matched.group(1)))
                                toggle_state = 0 if str(matched.group(1)) == "//" else 1
                                '''
                                if matched.group(2) != None:
                                    title = str(matched.group(2).split('.', 1)[0])
                                    #if len(matched.group(2).split('.', 1)) > 1:
                                    try:
                                        comment = str(matched.group(2).split('.', 1)[1])
                                    except:
                                        pass
                                '''
                                if matched.group(2) != None:
                                    sentences = split_sentences(matched.group(2))
                                    title = sentences[0]
                                    sentences.pop(0)
                                    
                                    try:
                                        comment = ''.join(sentences) #str(matched.group(2).split('.', 1)[1])
                                    except:
                                        pass
                                else:
                                    continue # if a setting does not have a comment it cannot be used.
                                    
                                
                                if generate_new_code and settings_counter < len(new_values_list):
                                    #print("MODIFYING TOGGLE")
                                    #print("new_values_list[settings_counter] = " + str(new_values_list[settings_counter]))
                                    #print(line)
                                    if toggle_state == 1 and new_values_list[settings_counter] == 0:
                                        #print("should be off, so should add //")
                                        line = "//" + line
                                        
                                    if toggle_state == 0 and new_values_list[settings_counter] == 1:
                                        #print("should be on, so removing //")
                                        line = re.sub("^\s?\/\/", "", line) # remove // from beginning of the line
                                        
                                    print("updated line:" + str(line))
                                    new_code += str(line) #+ "\n"
                                    
                                settings.append({"type":"checkbox" ,"value":toggle_state, "title":title ,"comment":comment})
                                #settings.append({"checkbox":toggle_state,"comment":comment})
                                
                                settings_counter += 1
                                continue
                        except:
                            print('checkbox error')
                            continue
                            
                            
                else:           # found END OF SETTINGS in the line
                    state = 2
                    print("Done with settings")
                    new_code += str(line) #+ "\n"
                    if not generate_new_code:
                        print("Breaking early")
                        break # No point in getting the rest of the code if this is not a 'generate code' run.
                    continue
            

            # This part of the code deals with the rest of the Arduino code. It scans for libraries to install.
            if state == 2:
                new_code += str(line) #+ "\n"
                
        
        if state == 0: # If we are still at state 0, then the code did not conform the the standard, as no settings part was found.
            explanation = "This is just to inform you that the Arduino Code did not conform to the Candle standard - it did not contain an explanation part or a settings part. Hence, there are no settings for you to change.\n\nYou can try to upload it anyway, \"as is\", and it should probably work just fine."
        
        if generate_new_code:
            
            # We go over the Arduino and extract a list of libraries it requires.
            for line in lines:    
                library_name = ""
                try:
                    # EXTRACTING LIBRARY NAME
                    pattern = '^\s*#include\s(\"|\<)(avr)?\/?(\w+)\.?h?(\"|\>)?\s*\/?\/?\s?(\"([A-Za-z0-9+\s-]*)\")?'
                    matched = re.match(pattern, line, re.I)
                    if matched:
                        if str(matched.group(2)) == "avr" or str(matched.group(2)) == "AVR":
                            if self.DEBUG:
                                print("avr, so skipping")
                            continue # AVR libraries should already be installed
                        if matched.group(3) != None:
                            library_name = matched.group(3)
                            try:
                                if matched.group(6) != None:
                                    library_name = matched.group(6)
                            except:
                                pass
                            print("library name:" + str(library_name))
                        if library_name is not "" and library_name is not None:
                            if library_name not in self.installed_libraries and library_name not in self.required_libraries:
                                print("->Not installed yet")
                                self.required_libraries.append(str(library_name))
                            else:
                                print("-library already installed, skipping.")
                        else:
                            print("Library name was empty")
                except:
                    print('library name scraping error')
            
            
            print("done scanning libraries")
            
            if settings_counter == len(new_values_list):
                print("settings_counter == len(new_values_list)")
                result["success"] = True
                result["code"] = new_code
                #print(new_code)
                
                source_name = str(self.sources[int(source_id)])
                path = str(self.add_on_path) + "/code/" + source_name
                if not os.path.exists(path):
                    print("created new directory: " + path)
                    os.makedirs(path)
                path += "/" + source_name + ".ino"
                if self.DEBUG:
                    print("path to store new code file:" + str(path))
                try:
                    text_file = open(path, "w")
                    text_file.write(new_code)
                    text_file.close()
                    print("Saved the new code")
                except:
                    print("Failed to save the new code to a file")
                
            else:
                print("Updating the settings code to the new values failed")
                result["code_created"] = False
                
                
        else:
            result["settings"] = settings
        
        return result



    def check_libraries(self, source_id):
        print("Checking for missing libraries")
        result = {"success":False,"message":"Downloading required libraries failed"}
        errors = []
        
        if len(self.required_libraries) == 0:
            result["success"] = True
            result["message"] = "No new libraries required."
        else:
            for library_name in self.required_libraries:
                print("DOWNLOADING: " + str(library_name))
                command = self.add_on_path + '/arduino-cli lib install "' + str(library_name) + '"'
                for line in run_command(command):
                    if self.DEBUG:
                        print(line)
                    if line.startswith( 'Error' ):
                        if not self.DEBUG:
                            print(line)
                        errors.append(line)
                    if line.startswith('Command success'):
                        result["message"] = "Compiled succesfully. Next step is actual upload."
                        result["success"] = True
                    time.sleep(.1)
        result["errors"] = errors
        return result
    
    
    
    def compile(self, source_id):
        print("Compiling")
        result = {"success":False, "message":"Compiling failed"}
        errors = []
        source_name = str(self.sources[int(source_id)])
        path = str(self.add_on_path) + "/code/" + source_name  #+ "/" + source_name + ".ino"
        
        if not os.path.isdir(path):
            result["success"] = False
            result["message"] = "Error: cannot find the file to upload."
            return result
        
        
        command = self.add_on_path + '/arduino-cli compile -v --fqbn arduino:avr:' + self.arduino_type + ' ' + str(path)
        for line in run_command(command):
            #line = line.decode('utf-8')
            if self.DEBUG:
                print(line)
            if line.startswith( 'Error' ) and not line.startswith( 'Error: exit status 1' ):
                if not self.DEBUG:
                    print(line)
                errors.append(line)
            if line.startswith('Command failed'):
                result["message"] = "Compiling failed"
            elif line.startswith('Command success'):
                result["message"] = "Compiled succesfully."
                result["success"] = True
            #elif line.startswith('Global variables use'):
            #    result["message"] = "Compiled succesfully."
            #    result["success"] = True

            time.sleep(.1)
            
        
        #result["success"] = True
        #result["message"] = "Finished compiling"
        result["errors"] = errors
        return result



    def test_upload(self,source_id):
        print("Doing a test upload of the Candle Cleaner")
        result = {"success":False,"message":"Test failed"}
        errors = []
        
        if "Candle_cleaner" in self.sources:
            test_result = self.upload(self.sources.index("Candle_cleaner"), self.bootloader)
            if self.DEBUG:
                print("first test result:" + str(test_result))
                print("success:" + str(test_result["success"]))
            if test_result["success"] is True:
                print("Worked on the first try")
                result["success"] = True
                sleep(15) # Allow the cleaner to do it's work.
            elif "Error syncing up with the Arduino" in test_result["errors"]:
                print("sync error was spotted in error list")
                self.bootloader = ':cpu=atmega328old' if self.bootloader == ':cpu=atmega328' else ':cpu=atmega328'
                print("new bootloader value: " + str(self.bootloader))
                test_result = self.upload(self.sources.index("Candle_cleaner"), self.bootloader)
                if self.DEBUG:
                    print("second test result:" + str(test_result))
                if test_result["success"]:
                    result["success"] = True
                    sleep(15) # Allow the cleaner to do it's work.
                else:
                    errors.append("Error syncing. Tried both the old and new bootloader.")
        else:
            errors.append("The Candle Cleaner code, which is used to test, was not found on your system.")
            
        result["errors"] = errors
        return result
        



    def upload(self, source_id, bootloader=""):
        print("Uploading")
        if self.DEBUG:
            print("bootloader parameter = " + str(bootloader))
        result = {"success":False,"message":"Upload failed"}
        errors = []
        source_name = str(self.sources[int(source_id)])
        if self.DEBUG:
            print("Code name: " + str(source_name))
        path = str(self.add_on_path) + "/code/" + source_name  #+ "/" + source_name + ".ino"
        
        command = self.add_on_path + '/arduino-cli upload -p ' + str(self.last_added_serial_port) + ' --fqbn arduino:avr:' + self.arduino_type + str(bootloader) + ' ' + str(path)
        if self.DEBUG:
            print("Arduino CLI command = " + str(command))
        for line in run_command(command):
            #line = line.decode('utf-8')
            if self.DEBUG:
                print(line)
            if line.startswith( 'Error' ) and not line.startswith( 'Error: exit status 1' ) and not line.startswith( 'Error during upload' ):
                if not self.DEBUG:
                    print(line)
                    
                if "getsync() attemp" in line:
                    errors.append("Error syncing up with the Arduino")
                else:
                    errors.append(line)
            #if line.startswith('Command failed'):
            #    result["message"] = "Upload failed"
            #elif line.startswith('Command success'):
            if line.startswith('Command success'):
                result["message"] = "Uploaded succesfully."
                result["success"] = True
            time.sleep(.1)

        result["errors"] = errors
        return result



    def unload(self):
        print("Shutting down adapter")
        try:
            pass
        except:
            print("Unable to cleanly close the add-on")



    def add_from_config(self):
        """Attempt to add all configured devices."""
        database = Database('Candle-manager')
        if not database.open():
            return

        config = database.load_config()
        database.close()

        if not config:
            return
        
        if 'Sketches' in config:
            self.json_sketches_url = config['Sketches']
        
        if 'Password' in config:
            self.simple_password = config['Password']
        
        if 'Arduino type' in config:
            if config['Arduino type'] == "Arduino Nano":
                self.arduino_type == "nano"
            if config['Arduino type'] == "Arduino Uno":
                self.arduino_type == "uno"
            if config['Arduino type'] == "Arduino Mega":
                self.arduino_type == "mega"








#
# DEVICE
#
class CandleDevice(Device):
    """Candle device type."""

    def __init__(self, adapter):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        """
        self.name = 'Create Candle'
        
        '''
        self.events = [
            {
                name: 'added',
                metadata: {
                    description: 'A device was added',
                    type: 'string',
                }
            }
        ]
        '''
        self.links = [
            {
                "rel": "alternate",
                "mediaType": "text/html",
                "href": "http://gateway.local:8686/"
            }
        ]
        Device.__init__(self, adapter, 'candle-device')
        
        self.adapter = adapter

        self.description = 'Create Candle'



    def as_dict(self):
        """
        Get the device state as a dictionary.
        Returns the state as a dictionary.
        """
        properties = {k: v.as_dict() for k, v in self.properties.items()}
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            '@context': self._context,
            '@type': self._type,
            'description': self.description,
            'properties': properties,
            'actions': self.actions,
            'events': self.events,
            'links': self.links,
            'baseHref': self.base_href,
            'pin': {
                'required': self.pin_required,
                'pattern': self.pin_pattern,
            },
            'credentialsRequired': self.credentials_required,
        }

    def as_thing(self):
        """
        Return the device state as a Thing Description.
        Returns the state as a dictionary.
        """
        thing = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            '@context': self._context,
            '@type': self._type,
            'properties': self.get_property_descriptions(),
            'links': self.links,
            'baseHref': self.base_href,
            'pin': {
                'required': self.pin_required,
                'pattern': self.pin_regex,
            },
            'credentialsRequired': self.credentials_required,
        }

        if self.description:
            thing['description'] = self.description

        return thing






def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever


def run_command(command):
    try:
        p = subprocess.Popen(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
        # Read stdout from subprocess until the buffer is empty !
        for bline in iter(p.stdout.readline, b''):
            line = bline.decode('ASCII') #decodedLine = lines.decode('ISO-8859-1')
            if line: # Don't print blank lines
                yield line
        # This ensures the process has completed, AND sets the 'returncode' attr
        while p.poll() is None:                                                                                                                                        
            sleep(.1) #Don't waste CPU-cycles
        # Empty STDERR buffer
        err = p.stderr.read()
        if p.returncode == 0:
            yield("Command success")
        else:
            # The run_command() function is responsible for logging STDERR 
            #print("len(err) = " + str(len(err)))
            if len(err) > 1:
                yield("Error: " + str(err.decode('utf-8')))
            yield("Command failed")
            #return false
    except:
        print("Error running Arduino CLI command")
        
def run_command_json(cmd):
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE)
        process.wait()
        data, err = process.communicate()
        if process.returncode is 0:
            return data.decode('utf-8')
        else:
            return "Error: " + str(err.decode('utf-8'))
            #print("Error exit code:", err.decode('utf-8'))
    except:
        print("Error running Arduino CLI command")
        
def split_sentences(st):
    sentences = re.split(r'[.?!]\s*', st)
    if sentences[-1]:
        return sentences
    else:
        return sentences[:-1]
        
