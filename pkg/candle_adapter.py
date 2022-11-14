"""Candle adapter for Candle Controller / WebThings Gateway."""


import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
import time
from time import sleep
#from datetime import datetime, timedelta
#import traceback
#import asyncio
import logging
import urllib
import requests
import socket
import string
import secrets
#import urllib2
import json
import re
import subprocess
#from subprocess import STDOUT, check_output
import threading
#from threading import Timer
import serial #as ser
import serial.tools.list_ports as prtlst
from flask import Flask,Response,request,render_template,jsonify,url_for


from gateway_addon import Adapter, Device, Database


try:
    #from gateway_addon import APIHandler, APIResponse
    from .api_handler import * #CandleManagerAPIHandler
    print("CandleManagerAPIHandler imported.")
except:
    print("Unable to load CandleManagerAPIHandler (which is used for UI extention)")




_TIMEOUT = 3

_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))




#
# ADAPTER
#

class CandleAdapter(Adapter):
    """Adapter for Candle"""

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        print("initialising adapter from class")
        self.adding_via_timer = False
        self.pairing = False
        self.name = self.__class__.__name__
        self.addon_name = 'Candle-manager-addon'
        Adapter.__init__(self, self.addon_name, self.addon_name, verbose=verbose)
        #print("Adapter ID = " + self.get_id())
        
        print("paths:" + str(_CONFIG_PATHS))
        
        #for path in _CONFIG_PATHS:
        #    if os.path.isdir(path):
        #        self.persistence_file_path = os.path.join(
        #            path,
        #            'candle-adapter-persistence.json'
        #        )
        
        
        #self.persistence_path = os.path.join(os.path.expanduser('~'), '.webthings', 'addons','data',self.adapter_name)
        #if not os.path.exists(directory):
        #    os.makedirs(directory)
        #self.persistence_file = os.path.join(self.persistence_path,'persistence.json')
        
        
        self.addon_path =  os.path.join(self.user_profile['addonsDir'], self.addon_name)
        self.data_path = os.path.join(self.user_profile['dataDir'], self.addon_name)
        self.code_path = os.path.join(self.data_path, 'code')
        self.source_path = os.path.join(self.data_path, 'source')
     
        
        if not os.path.exists(self.code_path):
            os.makedirs(self.code_path)
        if not os.path.exists(self.source_path):
            os.makedirs(self.source_path)

        if sys.platform == 'darwin':
            self.arduino_cli_path = os.path.join(self.addon_path, 'arduino-cli', 'darwin-x64')
        elif sys.platform == 'linux':
            machine = os.uname().machine
            print("machine = " + str(machine))
            if machine == 'aarch64' or machine == 'arm64':
                self.arduino_cli_path = os.path.join(self.addon_path, 'arduino-cli', 'linux-arm64')
            elif machine.startswith('armv7'):
                self.arduino_cli_path = os.path.join(self.addon_path, 'arduino-cli', 'linux-armv7')
            elif machine.startswith('armv6'):
                self.arduino_cli_path = os.path.join(self.addon_path, 'arduino-cli', 'linux-armv6')
            elif machine == 'x86_64':
                self.arduino_cli_path = os.path.join(self.addon_path, 'arduino-cli', 'linux-x64')
            else:
                self.arduino_cli_path = os.path.join(self.addon_path, 'arduino-cli', 'linux-armv6')
            #else:
            #    print('Unknown platform!')
            #    self.arduino_cli_path = None
     
        self.arduino_cli_path = os.path.join(self.arduino_cli_path, 'arduino-cli')
        os.system("sudo chmod +x " + str(self.arduino_cli_path))
        
        self.DEBUG = True
        self.DEVELOPMENT = False
        
        self.port = 8686
        self.ssl_certificate_detected = False
        self.json_sketches_url = ""
        self.simple_password = ""
        self.arduino_type = "nano"
        self.advanced_interface = False
        #self.initial_usb_port_scan_finished = False
        self.last_updated = time.time()  
	    #self.last_update_sketches_time = time.time()
        self.update_interval = 86400 # a day
        self.create_candle_manager_thing = False
        self.installed_libraries = set()
        self.busy_downloading_libraries = False
        self.initial_update_done = False
        
        # Get the user's settings
        self.add_from_config()
        
        # Output some debug data
        try:
            if self.DEBUG:
                print("self.addon_path = " + str(self.addon_path))
                print("self.code_path = " + str(self.code_path))
                print("os.uname().machine = " + str(os.uname().machine))
                print("self.arduino_cli_path = " + str(self.arduino_cli_path))
                print("Gateway version: " + self.gateway_version)
                
            self.gateway_version_array = self.gateway_version.split(".")
            
        except:
            print("self.gateway_version did not exist")
        
        
        
        # Detect if SSL is enabled
        ssl_folder = os.path.join(self.user_profile['baseDir'], 'ssl')
        self.certificate_path = os.path.join(ssl_folder, 'certificate.pem')
        self.privatekey_path = os.path.join(ssl_folder, 'privatekey.pem')
        
        if self.DEBUG:
            print("certificate_path = " + str(self.certificate_path))
        
        if os.path.isfile(self.certificate_path):
            if self.DEBUG:
                print("spotted a SSL certificate file, assuming SSL/Tunnel is enabled")
            #self.ssl_certificate_detected = True # TODO: tmeporarily disabled https for the flask server. Might give better user experience.
        else:
            if self.DEBUG:
                print("did not spot ssl certificate file, assuming SSL/Tunnel is disabled")
        
        self.full_lan_path = "candle.local:8686"
        try:
            lan_ip = get_ip()
            self.full_lan_path = str(lan_ip) + ":8686/"
        except Exception as ex:
            print("Error, unable to get local lan path: " + str(ex))

        if self.ssl_certificate_detected:
            self.full_lan_path = "https://" + self.full_lan_path
        else:
            self.full_lan_path = "http://" + self.full_lan_path

        if self.DEBUG:
            print("Path to Candle manager server = " + str(self.full_lan_path))
        
        
        # Create the Candle thing
        if self.create_candle_manager_thing is True:
            try:
                #if self.gateway_version_array[0] == "0" and int(self.gateway_version_array[1]) < 10: # temporarily disabled, since users were having issues if they used the proxy service.
                device = CandleDevice(self)
                self.handle_device_added(device)
                #if self.DEBUG:
                print("Created the Candle Manager thing")

                #self.create_candle_device = self.get_device('candle-device') # Or should it use the human readable name?
                self.create_candle_device = self.get_device('candle-device') # Or should it use the human readable name?
                if self.DEBUG:
                    print("self.create_candle_device = " + str(self.create_candle_device))
                if str(self.create_candle_device) != 'None':
                    self.create_candle_device.connected_notify(False)
                    if self.DEBUG:
                        print("-Set Create Candle thing status set to 'not connected'.")
                else:
                    print("Warning: Create Candle thing does not exist.")
            except:
                print("Error: unable to set the Create Candle thing status to 'not connected'.")

        


        
        
        
        # Scan sources directory
        self.sources = []
        #self.cwd = str(os.getcwd())
        try:
            self.scan_source_dir()
        except Exception as e:
            print("Failed to scan sources directory: " + str(e))
        
        
        if self.DEBUG:
            print("Starting the initial update")
        try:
            t = threading.Thread(target=self.initial_update)
            t.daemon = True
            t.start()
        except:
            print("Error starting the initial update thread")
        
        
        # USB scanning variables
        self.previous_serial_devices = set()
        #self.last_added_serial_port = ""
        try:
            if self.DEBUG:
                print("Making initial scan of USB ports")
            self.scan_usb_ports()
        except:
            print("Error during initial scan of usb ports")
        
        #self.last_added_serial_port = "" # Making sure we don't start with any device selected as the device to upload to.
        self.open_serial_ports = []
        
        # Arduino CLI
        self.upload_status = "Preparing"
        self.bootloader = ":cpu=atmega328"
        
        # Now we can set the thing to connected, since Flask will launch pretty quickly.
        try:
            if self.create_candle_manager_thing is True and self.gateway_version_array[0] == "0" and int(self.gateway_version_array[1]) < 10:
                self.create_candle_device.connected_notify(True)
                if self.DEBUG:
                    print("Set the Create Candle device to 'connected' state." + str(self.create_candle_device))
        except Exception as ex:
            print("Warning, could not set the Candle Manager thing to 'connected' state: " + str(ex))
        
        
        
        #
        # THE NEW WAY
        #
        
        try:
            self.extension = CandleManagerAPIHandler(self, verbose=True)
            #self.manager_proxy.add_api_handler(self.extension)
            print("Extension API handler initiated")
        except Exception as e:
            print("Failed to start API handler (this only works on gateway version 0.10 or higher). Error: " + str(e))
        
        
        #
        #  THE OLD WAY, CREATING A FLASK WEBSERVER
        #
        
        try:
            # Flask webserver
            if self.DEBUG:
                print("Preparing a Flask webserver called " + str(__name__))

            #Disable outputting Flask messages to console
            #if not self.DEVELOPMENT:
            #    flask_log = logging.getLogger('werkzeug')
            #    flask_log.setLevel(logging.ERROR)

            app = Flask(__name__, root_path= os.path.join(self.addon_path, 'pkg') )

            @app.route('/') # The home page
            def index():
                return render_template('index.html')


            @app.route('/init') # Returns intitial variables to the Candle Manager browser tab, such as whether to show advances features.
            def app_init():
                d = self.init()
                return jsonify(d)   

            @app.route('/update_sketches', methods=['POST']) # Download the latest version of the sketches.
            def app_update_sketches():
                data = request.get_json()
                if self.DEBUG:
                    print("URL to download sketch(es) from:" + str(data))
                d = self.update_sketches(str(data))
                return jsonify(d)

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

            @app.route('/test_upload/<source_id>', methods=['POST']) # Do a test upload, and see if the correct bootloader is set.
            def app_test_upload(source_id): # It doesn't actually use the source_id.
                data = request.get_json()
                if self.DEBUG:
                    print("Port to test upload to:" + str(data))
                d = self.test_upload(source_id,data)
                return jsonify(d)

            @app.route('/upload/<source_id>', methods=['POST']) # Uploads the sketch to the Arduino
            def app_upload(source_id):
                data = request.get_json()
                if self.DEBUG:
                    print("Port to upload to:" + str(data))
                d = self.upload(source_id, data, self.bootloader)
                return jsonify(d)

            @app.route('/serial_output', methods=['POST'])
            def app_serial_output():
                data = request.get_json()
                if self.DEBUG:
                    print("Port to listen to:" + str(data))
                d = self.serial_output(data)
                return jsonify(d)

            @app.route('/serial_close', methods=['POST']) # If it's still open, close the serial port.
            def app_serial_close():
                data = request.get_json()
                if self.DEBUG:
                    print("Port to close:" + str(data))
                d = self.close_serial_port(data)
                return jsonify(d)

            @app.route('/close_tab') # If it's still open, close the serial port.
            def app_close_tab():
                if self.DEBUG:
                    print("Closing Candle Manager browser tab")
                d = self.close_tab()
                return jsonify(d)


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
            
            if self.ssl_certificate_detected:
                print("Running Flask as https")
                app.run(host='0.0.0.0', debug=True, use_reloader=False, port=self.port, ssl_context=(self.certificate_path, self.privatekey_path) )
            else:
                print("Running Flask as http")
                app.run(host="0.0.0.0", port=self.port, use_reloader=False)
            
            #threading.Thread(target=app.run).start()
        except Exception as e:
            print("Flask error: " + str(e))
        

    #def handle_device_saved(self, device_id, device):
    #    print("Candle adapter: handle_device_saved is being called")




    def initial_update(self):
        
        # Download/update sketches
        try:
            self.update_sketches(self.json_sketches_url)
        except:
            print("Failed to update sketches during add-on start (no internet connection?).")

        # Update the Arduino CLI:
        try:
            if self.update_arduino_cli():
                if self.DEBUG:
                    print("Succesfully updated Arduino CLI index and AVR")
                
            else:
                print("Warning: could not check for updates for the Arduino CLI (no internet connection?)")
        except Exception as e:
            print("Failed to download sketches from JSON file: " + str(e))

            
        try:
            # Get JSON list of already installed Arduino libraries        
            print("Looking for already installed libraries")
            self.required_libraries = set(["MySensors", "SSD1306Ascii", "SSD1306AsciiAvrI2c", "DallasTemperature", "OneWire", "Grove - Barometer Sensor BME280", "SoftwareSerial"]) # some hardcoded libraries that are required
        
            self.check_installed_arduino_libraries()

            # Pre-download the required libraries
            self.check_libraries(0)
        except Exception as e:
            print("Failed to check required libraries during inital update: " + str(e))
            
        
        # Pre-compile the cleaner code
        self.cleaner_pre_compiled = False
        try:
            #hex_filename = "Candle_cleaner.arduino.avr." + str(self.arduino_type) + ".hex"
            #cleaner_hex_path = self.addon_path + "/code/Candle_cleaner/Candle_cleaner.arduino.avr." + self.arduino_type + ".hex"
            cleaner_hex_path = os.path.join(self.data_path,'code','Candle_cleaner','build','arduino.avr.' + str(self.arduino_type),'Candle_cleaner.ino.with_bootloader.hex')
            if self.DEBUG:
                print("cleaner_hex_path = " + str(cleaner_hex_path))
            
            
            
            if os.path.isfile(cleaner_hex_path):
                if self.DEBUG:
                    print("HEX file already existed, so no need to pre-compile the Candle Cleaner")
                self.cleaner_pre_compiled = True
            elif "Candle_cleaner" in self.sources:
                if self.DEBUG:
                    print("Candle Cleaner was found at index " + str(self.sources.index("Candle_cleaner")))
                    
                # Create the CandleCleaner code
                self.change_settings(self.sources.index("Candle_cleaner"), True, [2] )
                   
                # Then compile it
                test_result = self.compile(self.sources.index("Candle_cleaner"))
                if self.DEBUG:
                    print("Pre-compile result:" + str(test_result))
                if test_result["success"] == True:
                    print("Succesfully pre-compiled the cleaner code")
                    self.cleaner_pre_compiled = True
                else:
                    print("Error: failed to pre-compile the candle cleaner")
            else:
                print("Candle Cleaner was missing from the source directory")
        
        except Exception as e:
            print("initial pre-compilation failed: " + str(e))
        
        if self.DEBUG:
            print("initial update complete")
        self.initial_update_done = True



    def update_arduino_cli(self):
        success = False
        index_updated = False
        
        # Updating Arduino CLI index
        try:
            command = self.arduino_cli_path + ' core update-index'
            if self.DEBUG:
                print("ARDUINO UPDATE COMMAND = " + str(command))
            
            #bla = run_command(command).splitlines()
            #print("bla = " + str(bla))
            command_output = run_command(command, 120)
            if command_output != None:
                for line in run_command(command).splitlines():
                    #if self.DEBUG:
                    print(line)
                    if line.startswith('Command failed'):
                        print("Error: CLI update index failed")
                        print("- PROBLEMATIC ARDUINO UPDATE COMMAND WAS: " + str(command))
                    elif line.startswith('Command success'):
                        if self.DEBUG:
                            print("CLI update index success")
                        index_updated = True
            else:
                print("Error: Arduino core update command timed out. Do you have a (slow) internet connection?")
                #time.sleep(.1)
        except Exception as e:
            print("Error sending Arduino CLI update index command: " + str(e))
            
        # Downloading latest version of AVR for Arduino CLI, which allows it to work with the Arduino Nano, Uno and Mega
        if index_updated:
            try:
                command = self.arduino_cli_path + ' core install arduino:avr'
                command_output = run_command(command,120)
                if command_output != None:
                    for line in run_command(command,120).splitlines():
                        if self.DEBUG:
                            print(line)
                        if line.startswith('Command failed'):
                            print("CLI update AVR failed")
                        elif line.startswith('Command success'):
                            if self.DEBUG:
                                print("CLI update AVR success")
                            success = True
                else:
                    print("Error: Arduino AVR download command timed out. Do you have a (slow) internet connection?")
                        #time.sleep(.1)
            except Exception as e:
                print("Error sending Arduino CLI update AVR command: " + str(e))
        return success


    def check_installed_arduino_libraries(self):
        try:
            #command = self.arduino_cli_path + ' lib list --all --format=json' # perhaps use os.path.join(self.addon_path, 'arduino-cli') + 'lib list --all --format=json' ?
            command = self.arduino_cli_path + ' lib list --all --format=json'
            print("check_installed_arduino_libraries command = " + str(command))
            command_output = run_command_json(command,120) # Sets a time limit for how long the command can take.
            if self.DEBUG:
                print("Installed arduino libs command_output: " + str(command_output))
                
            if command_output != None and command_output != "":
                if self.DEBUG:
                    print("Installed libraries according to Arduino CLI: " + str(command_output))
                    
                installed_libraries_response = json.loads(command_output)
                if self.DEBUG:
                    print("installed_libraries_response = " + str(installed_libraries_response))
                #for lib_object in installed_libraries_response['libraries']:
                for lib_object in installed_libraries_response:
                    try:
                        if self.DEBUG:
                            print("Found library: " + str(lib_object['library']['name']))
                        self.installed_libraries.add(str(lib_object['library']['name']))
                    except Exception as e:
                        print("Warning: could not add a library to list of installed libraries: " + str(e))
            else:
                print("Erro: Unable to check installed Arduino libraries")
        except Exception as e:
            print("Failed to check libraries: " + str(e))
    

    # Checks whether to download a list of files from a json, or just a single file.
    def update_sketches(self, sketches_url="https://raw.githubusercontent.com/createcandle/candle_source_code_list/master/candle_source_code_list.json"):
        result = {"success":False}
    
		# Check if this wasn't already done recently.
			
		#if time.time() - self.last_update_sketches_time > 60: # Try an update every 60 seconds at most. To avoid overload when multiple users active (e.g. in a workshop, while debug is on.)
		#    self.last_update_sketches_time = time.time()
			
        try:
            print("received sketches_url = " + str(sketches_url))
            if sketches_url.startswith("http") and sketches_url.endswith(".json"):

                response = requests.get(sketches_url, allow_redirects=True) # was True
                json_sketches_data = json.loads(response.content.decode('utf-8'))
                if self.DEBUG:
                    print(str(json_sketches_data["sketch_urls"]))
                for sketch_url in json_sketches_data["sketch_urls"]:
                    self.download_source(sketch_url)
            
            elif sketches_url.startswith("http") and sketches_url.endswith(".ino"):
                self.download_source(sketches_url)
    
            result["success"] = True
        
        except Exception as e:
            print("Failed to download sketches from JSON file: " + str(e))
    
		#else: # The update was already done recently.
		#	result["success"] = True
        
        self.scan_source_dir()

        return result
		
    
    # Downloads a single file
    def download_source(self, sketch_url):
        
        if self.DEBUG:
            print("downloading sketch at " + str(sketch_url))
						
        source_dir = os.path.basename(os.path.normpath( os.path.dirname(sketch_url) ))
        source_file = os.path.basename(sketch_url)

        target_dir = os.path.join(self.source_path, source_dir)
        target_file = os.path.join(target_dir, source_file)
      
        if self.DEBUG:
            print("source_dir = " + str(source_dir))
            print("source_file = " + str(source_file))
            print("target_dir = " + str(target_dir))
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

            # Create directory if it doesn't exist yet
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
                f.write( response.content.decode('utf-8') )
                f.close()
                break
            except Exception as e:
                attempts += 1
                print("Error writing to file: " + str(e))




    def scan_usb_ports(self): # Scans for USB serial devices
        current_serial_devices = set()
        result = {"state":"stable","port_id":[]}
        
        #if self.initial_usb_port_scan_finished == False: # To avoid any open window asking for newly attached devices even though the initial scan isn't done yet.
        #    print("Initial scan of USB parts isn't done yet")
        #    return result
        
        try:    
            ports = prtlst.comports()
            for port in ports:
                if 'USB' in port[1] or 'Arduino' in port[1]: #check 'USB' string in device description
                    #if self.DEBUG:
                    #    print("port: " + str(port[0]))
                    #    print("usb device description: " + str(port[1]))
                    if str(port[0]) not in current_serial_devices:
                        current_serial_devices.add(str(port[0]))
                        if str(port[0]) not in self.previous_serial_devices:
                            print("New device plugged into port " + str(port[0]))
                            result["new_port_id"] = str(port[0])
                            result["state"] = "added"


            #print("Current USB devices: " + str(current_serial_devices))

            if len(self.previous_serial_devices) > len(current_serial_devices):
                try:
                    removed = self.previous_serial_devices - current_serial_devices
                    print("removed list = " + str(removed))
                    result["removed_port_ids"] = list(removed)
                    
                except:
                    print("Too many USB devices removed at once (whoa)")
                
                print("A USB device was removed")
                result["state"] = "removed"
        
        except Exception as e:
            print("Error getting serial ports list: " + str(e))
            

        self.previous_serial_devices = current_serial_devices
        #if self.initial_usb_port_scan_finished == False:
        #    if self.DEBUG:
        #        print("Initial scan of USB ports complete")
        #    self.initial_usb_port_scan_finished = True
        #return {"state":"added","new_port_id":'/dev/ttyUSB1'} # emulate a new device being added, useful during development
        return result



    def init(self):
        print("Running init for new Candle Manager tab")

        result_message = "Updated succesfully"
        
        
        if self.initial_update_done == False:
            result = {"success":False,"message":"busy"}
            return result
            
        try:
            self.scan_usb_ports()
            print("1. Finished USB scan")

            self.check_installed_arduino_libraries()
            print("2. Updated list of already install Arduino libraries")
        except Exception as e:
            print("Failure during init: " + str(e))
                    
        # Check if we already updated recently.
        now = time.time()
        #print("now: " + str(now))
        #print("last updated: " + str(self.last_updated))
        #then = time.mktime(self.last_updated.timetuple())
        if (now - self.last_updated) > self.update_interval:
            self.last_updated = now
            print("Will check for updates.")
            # more than 24 hours passed
        
            try:
                self.update_sketches()
                print("3. Updated sketches")
                self.update_arduino_cli()
                print("4. Updated Arduino CLI")
                
                #self.last_updated = time.time() # remember the time we last updated

            except Exception as e:
                print("Error while attempting init update: " + str(e))
                result_message = "Something went wrong during updating."
        else:
            print("Already updated quite recently.")
                
        result = {"success":True, "advanced_interface":self.advanced_interface, "message":result_message,"sketches_url":self.json_sketches_url}
        return result


    def scan_source_dir(self):
        print("Scanning source file directory")
        
        try:
            if self.DEBUG:
                print("Scanning " + str(self.source_path))
            file_list = []
            for dentry in os.scandir(self.source_path):
                if not dentry.name.startswith('.') and dentry.is_dir():
                    file_list.append(dentry.name)
            self.sources = file_list
            return file_list
        
        except Exception as e:
            print("Error scanning source directory: " + str(e))


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
        lines = []
        new_code = ""
        settings_counter = 0
        source_name = str(self.sources[int(source_id)])
        #path = str(self.addon_path) + "/source/" + source_name  + "/" + source_name + ".ino"
        
        path = os.path.join(self.source_path, source_name, source_name + '.ino')
        print("change_settings source path: " + str(path))
        file = open(path, 'r')
        lines = file.readlines()
        file.close()
        
        for line in lines:
            
            # The first part extracts the header text from the code.
            if state == 0: # state 0 is when the code is analysed, state 1 is when new settings are being updated in the code.
                try:
                    new_code += str(line) #+ "\n" # if generate_new_code is set to true, this will create the code with the updated settings.
                    if "* SETTINGS */" not in line:
                        if line.find('*') > -1 and line.find('*') < 3: # Remove the * that precedes lines in the comment
                            line = re.sub(r'.*\*', '', line)
                            explanation += str(line) #+ "\n"
                    else:
                        state = 1
                        result["explanation"] = explanation
                        continue
                except Exception as e:
                    print("Error extracting header text: " + str(e))
                    
            # This part deals with the part of the Arduino code that contains the settings. State 2 is when things get updated in the code.
            if state == 1:
                title = ""
                comment = ""
                if "/* END OF SETTINGS" not in line:
                    if line == '\n':
                        new_code += str(line)
                        settings.append({"type":"hr" ,"value":1, "title":"" ,"comment":""})
                        continue
                        
                    elif "MY_ENCRYPTION_SIMPLE_PASSWD" in line or "MY_SECURITY_SIMPLE_PASSWD" in line or "MY_SIGNING_SIMPLE_PASSWD" in line:
                        try:
                            # REPLACING PASSWORD
                            pattern = '^#define\s\w+SIMPLE_PASSWD\s\"([\w\.\*\#\@\(\)\!\ˆ\%\&\$\-]+)\"'
                            matched = re.match(pattern, line)
                            if matched and matched.group(1) != None:
                                if self.DEBUG:
                                    print("found security line")
                                if str(self.simple_password) == "":
                                    print("WARNING - Password was empty, so not adding encryption feature to final code")
                                    continue # If the password has been set to "", then the user doesn't want security. Skip adding the security line to the code.
                                line = line.replace(str(matched.group(1)),self.simple_password, 1)
                                if self.DEBUG:
                                    print("Added encryption password to code.")
                                new_code += str(line) #+ "\n"
                                continue
                        except:
                            print('Unable to merge password while generating new code')
                            continue
                            
                    
                        
                        
                    else:
                        
                        
                        try:
                            # A TOGGLE DEFINE
                            pattern = '^\s*(\/\/)?\s?#define\s\w+\s*\/\/\s?([\w\"\_\-\+\s\(\)]*[\.\s|\?\s])(.*)'
                            matched = re.match(pattern, line)
                            if matched:

                                toggle_state = 0 if str(matched.group(1)) == "//" else 1
    
                                if matched.group(2) != None:
                                    title = str(matched.group(2)).strip( '.' )
                                else:
                                    continue # if a setting does not at the very least have a title it cannot be used.
                                if matched.group(3) != None:
                                    comment = str(matched.group(3))
                                
                                if generate_new_code and settings_counter < len(new_values_list):
                                    
                                    if toggle_state == 1 and new_values_list[settings_counter] == 0:
                                        if self.DEBUG:
                                            print("should be off, so should add //")
                                        line = "//" + line
                                        
                                        # A shortcut to try and anticipate which bootloader to try first.
                                        if "RF-Nano" in title:
                                            self.bootloader = ":cpu=atmega328old"
                                        
                                    if toggle_state == 0 and new_values_list[settings_counter] == 1:
                                        if self.DEBUG:
                                            print("should be on, so removing //")
                                        line = re.sub("^\s?\/\/", "", line) # remove // from beginning of the line
                                        
                                        # A shortcut to try and anticipate which bootloader to try first.
                                        if "RF-Nano" in title:
                                            self.bootloader = ":cpu=atmega328"
                                        
                                    if self.DEBUG:
                                        print("updated line:" + str(line))
                                    new_code += str(line) #+ "\n"
                                    
                                settings.append({"type":"checkbox" ,"value":toggle_state, "title":title ,"comment":comment})
                                
                                settings_counter += 1
                                continue
                        except:
                            print('checkbox error')
                            continue
                        
                        
                        if line.startswith("//"): # The line starts with // and it's not a toggle define (since that would have been caught by the code above), so we should skip this line.
                            continue
                        
                        
                        try:
                            # NORMAL VARIABLE
                            pattern = '\w+\s\w+\[?[0-9]*?\]?\s?\=\s?\"?([\w\+\!\@\#\$\%\ˆ\&\*\(\)\.\,\-]*)\"?\;\s*\/?\/?\s?([\w\"\_\-\+\#\s\(\)]*[\.\s|\?\s])(.*)'
                            matched = re.match(pattern, line)
                            #print("matched?:" + str(matched))
                            if matched:
                                if matched.group(2) != None:
                                    title = str(matched.group(2)).strip( '.' )
                                else:
                                    continue # if a setting does not at the very least have a title it cannot be used.
                                if matched.group(3) != None:
                                    comment = str(matched.group(3))

                                if generate_new_code and settings_counter < len(new_values_list):
                                    line = line.replace(str(matched.group(1)), str(new_values_list[settings_counter]), 1)
                                    if self.DEBUG:
                                        print("updated line:" + str(line))
                                    new_code += str(line) #+ "\n"
                                    
                                else:
                                    settings.append({"type":"text" ,"value":str(matched.group(1)), "title":title ,"comment":comment})
                                
                                settings_counter += 1 # This is used to keep track of the ID of the settings line we are modifying.
                                continue
                        except:
                            print('normal variable error')
                            continue
                            
                            
                        try:
                            # COMPLEX DEFINE WITH A STRING VALUE INSIDE ""
                            pattern = '^#define\s\w+\s+\"?([\w\.\*\#\@\(\)\!\ˆ\%\&\$\-]*)\"?\s*\/?\/?\s?([\w\"\_\-\+\s\(\)]*[\.\s|\?\s])(.*)'
                            matched = re.match(pattern, line)
                            if matched:
                                if matched.group(2) != None:
                                    title = str(matched.group(2)).strip( '.' )
                                else:
                                    continue # if a setting does not at the very least have a title it cannot be used.
                                if matched.group(3) != None:
                                    comment = str(matched.group(3))
                                    
                                if generate_new_code and settings_counter < len(new_values_list):
                                    line = line.replace(str(matched.group(1)),str(new_values_list[settings_counter]), 1)
                                    if self.DEBUG:
                                        print("updated complex define line:" + str(line))
                                    new_code += str(line) #+ "\n"
                                    
                                settings.append({"type":"text" ,"value":str(matched.group(1)), "title":title ,"comment":comment})
                                
                                settings_counter += 1
                                continue
                        except:
                            print('complex define error')
                            continue
                            
                        
                        
                            
                            
                else:           # found END OF SETTINGS in the line
                    state = 2
                    print("Done with settings")
                    new_code += str(line) #+ "\n"
                    if not generate_new_code:
                        print("Breaking early, since there is no need to scan all the Arduino code yet.")
                        if self.DEBUG:
                            print(str(settings))
                        break # No point in getting the rest of the code if this is not a 'generate code' run.
                    continue
            

            # This part of the code deals with the rest of the Arduino code. It scans for libraries to install.
            if state == 2:
                
                if "MY_ENCRYPTION_SIMPLE_PASSWD" in line or "MY_SECURITY_SIMPLE_PASSWD" in line or "MY_SIGNING_SIMPLE_PASSWD" in line:
                    try:
                        # REPLACING PASSWORD
                        pattern = '^#define\s\w+SIMPLE_PASSWD\s\"([\w\.\*\#\@\(\)\!\ˆ\%\&\$\-]+)\"'
                        matched = re.match(pattern, line)
                        if matched and matched.group(1) != None:
                            print("found security line")
                            if str(self.simple_password) == "":
                                print("Password was empty, so not adding security line to final code")
                                continue # If the password has been set to "", then the user doesn't want security. Skip adding the security line to the code.
                            line = line.replace(str(matched.group(1)),self.simple_password, 1)
                            print("updated security line:" + str(line))
                            new_code += str(line) #+ "\n"
                            continue
                    except:
                        print('Unable to merge password while generating new code')
                        continue
                        
                        
                else:
                    new_code += str(line)
                
        
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
                                print("avr (built-in), so skipping")
                            continue # AVR libraries should already be installed
                        if matched.group(3) != None:
                            library_name = str(matched.group(3))
                            try:
                                if matched.group(6) != None:
                                    library_name = str(matched.group(6))
                            except:
                                pass
                            print("library name:" + str(library_name))
                        if library_name != "" and library_name != None:
                            if library_name not in self.installed_libraries and library_name not in self.required_libraries:
                                
                                
                                #for installed_library_name in self.installed_libraries:
                                #    if installed_library_name in library_name:
                                #        print("Library is an expanded name of an already installed library, skipping.")
                                #        continue
                                
                                print("->Not installed yet")
                                self.required_libraries.add(str(library_name))
                            else:
                                print("-Library is already installed, skipping.")
                        else:
                            print("Library name was empty")
                except:
                    print('library name scraping error')
            
            
            print("done scanning libraries")
            print("The code has this number of settings: " + str(settings_counter))
            
            if settings_counter == len(new_values_list):
                #print("settings_counter == len(new_values_list)")
                result["success"] = True
                result["code"] = new_code
                #print(new_code)
                
                source_name = str(self.sources[int(source_id)])
                path = os.path.join(self.code_path, source_name)
                
                if not os.path.exists(path):
                    print("created new directory: " + path)
                    os.makedirs(path)
                #path += "/" + source_name + ".ino"
                path = os.path.join(path, source_name + ".ino")
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



    def check_libraries(self, source_id): # Source_ID isn't really used here.
        if self.DEBUG:
            print("Checking for missing libraries, and installing if required.")
        result = {"success":False,"message":"Downloading required libraries failed"}
        errors = []
        try:
            if len(self.required_libraries) == 0:
                result["success"] = True
                result["message"] = "No new libraries required."
                if self.DEBUG:
                    print("No new Arduino libraries required")
            else:
                for library_name in self.required_libraries:
                    if str(library_name) not in self.installed_libraries:
                        print("Downloading Arduino library: " + str(library_name))
                        command = self.arduino_cli_path + ' lib install "' + str(library_name) + '"'
                        print("library install command: " + str(command))
                        try:
                            compile_output = run_command(command)
                            for line in compile_output.splitlines():
                                if self.DEBUG:
                                    print(line)
                                if line.startswith( 'Error' ):
                                    print(line)
                                    errors.append(line)
                                    # Perhaps the proces should be broken off here.
                                elif line.startswith('Command success'):
                                    result["message"] = "Installed library succesfully. Next step is actual upload."
                                    result["success"] = True
                                #time.sleep(.1)
                        except Exception as e:
                            print("Exception while trying to install new required library: " + str(e))
                            
        except Exception as e:
            print("Exception while trying to download new required libraries: " + str(e))
        
        self.required_libraries.clear() # remove all required library names from the set, ready for the next round.
        
        result["errors"] = errors
        return result
    
    
    def compile(self, source_id):
        
        result = {"success":False, "message":"Compiling failed"}
        errors = []
        
        try:
            source_name = str(self.sources[int(source_id)])
            if self.DEBUG:
                print("Compiling: " + str(source_name))
            #path = str(self.addon_path) + "/code/" + source_name  #+ "/" + source_name + ".ino"
            path = os.path.join(self.code_path, source_name) # ,'build'
            build_path = os.path.join(self.code_path, source_name ,'build')
            
            if not os.path.isdir(path):
                result["success"] = False
                result["message"] = "Error: source directory does not exist."
                return result

            command = self.arduino_cli_path + ' compile -e -v --fqbn arduino:avr:' + str(self.arduino_type) + ' --build-path ' + str(build_path) + " " + str(path)
            if self.DEBUG:
                print("compile command = " + str(command))
            
            compile_output = run_command(command)
            if compile_output != None:
                for line in compile_output.splitlines():
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

                #time.sleep(.1)
        except Exception as e:
            print("Error during compiling: " + str(e))

        result["errors"] = errors
        return result



    def test_upload(self, source_id, port_id):
        
        result = {"success":False,"message":"Testing"}
        errors = []
        if str(port_id) == "":
            
            print("Error: no port_id set")
            result = {"success":False,"message":"No port_id set"}
            return result

        
        # If we are uploading the Candle receiver, then we skip the test upload. This is because if th MySensors plugin is already installed, it will interfere.
        #try:
        #    source_name = str(self.sources[int(source_id)])
        #    if source_name == "Candle_receiver":
        #        print("Skipping test upload of Candle Receiver")
        #        result["success"] = True # pretend the test went ok, and skip it.
        #        return result
        #        
        #except Exception as ex:
        #    print("Error while trying to skip test upload for the Candle Receiver: "  + str(ex))
            
        
        print("Doing a test upload of the Candle Cleaner")
        print("Initial bootloader value: " + str(self.bootloader))
        
        
        try:
            if "Candle_cleaner" in self.sources:
                if self.DEBUG:
                    print("Candle_cleaner seems to exist, will do test upload")
                test_result = self.upload(self.sources.index("Candle_cleaner"), str(port_id), self.bootloader)
                if self.DEBUG:
                    print("first test result:" + str(test_result))
                    print("success:" + str(test_result["success"]))
                if test_result["success"] is True:
                    print("Test upload succeeded on the first try")
                    result["success"] = True
                #elif "Error syncing up with the Arduino" in test_result["errors"]:
                else:
                    print("sync error was spotted in error list")
                    self.bootloader = ':cpu=atmega328old' if self.bootloader == ':cpu=atmega328' else ':cpu=atmega328'
                    print("new bootloader value: " + str(self.bootloader))
                    try:
                        test_result = self.upload(self.sources.index("Candle_cleaner"), str(port_id), self.bootloader)
                        if self.DEBUG:
                            print("second test result:" + str(test_result))
                        if test_result["success"]:
                            result["success"] = True
                        else:
                            errors.append("Error syncing. Tried both the old and new bootloader.")
                    except Exception as e:
                        errors.append("Exception during second upload attempt. Tried both the old and new bootloader.")
                        
            else:
                errors.append("The Candle Cleaner code, which is used to test, was not found on your system.")
        except Exception as e:
            print("Error during test upload phase: " + str(e))

        result["errors"] = errors
        return result


    def upload(self, source_id, port_id, bootloader=""):
        if self.DEBUG:
            print("Uploading")
        if self.DEBUG:
            print("bootloader parameter = " + str(bootloader))
        result = {"success":False,"message":"Upload failed"}
        
        if str(port_id) == "":
            print("Error: no port_id set")
            result = {"success":False,"message":"Upload failed, no port_id set"}
            return result
        
        try:
            self.close_serial_port(str(port_id))
        except Exception as ex:
            if self.DEBUG:
                print("unable to close serial port (this is not an issue): " + str(ex))
            
        errors = []
        try:
            source_name = str(self.sources[int(source_id)])
            if self.DEBUG:
                print("Code name: " + str(source_name))
            #path = str(self.addon_path) + "/code/" + source_name  #+ "/" + source_name + ".ino"
            path = os.path.join(self.code_path, source_name, 'build','arduino.avr.' + str(self.arduino_type)) # e.g. build/arduino.avr.nano/
            if self.DEBUG:
                print("path to upload from: " + str(path))
            
            command = str(self.arduino_cli_path) + ' upload -p ' + str(port_id) + ' --fqbn arduino:avr:' + self.arduino_type + str(bootloader) + ' --input-dir ' + str(path)
            if self.DEBUG:
                print("Arduino CLI upload command = " + str(command))
                
            for line in run_command(command).splitlines():
                if line.startswith( 'Error' ) and not line.startswith( 'Error: exit status 1' ) and not line.startswith( 'Error during upload' ):
                    #if not self.DEBUG:
                    print(line)

                    if "getsync() attemp" in line:
                        errors.append("Error syncing up with the Arduino")
                    else:
                        errors.append(line)
                if line.startswith('Command success'):
                    result["message"] = "Uploaded succesfully."
                    result["success"] = True
                #time.sleep(.1)
        except Exception as e:
            print("Error during upload process: " + str(e))
                
        result["errors"] = errors
        return result


    def serial_output(self, port_id):

        #print("received port id for serial output: " + str(port_id))
        if str(port_id) == "":
            if self.DEBUG:
                print("No port_id received")
            return
        new_lines = ""
        result = {}
        port_exists = False
        port_is_open = False
        some_dict = {}
        current_serial_object = None
        
        try:
            # Check if the port has already been created
            for key in self.open_serial_ports:
                if port_id in key:
                    if self.DEBUG:
                        print("Serial port existed in serial port list")
                    #print(str(key))
                    port_exists = True
                    key[port_id]['countdown'] = 3 # reset countdown.
                    current_serial_object = key[port_id]['port_object']
                    if current_serial_object.isOpen():
                        port_is_open = True
                    else:
                        current_serial_object.open()
                        port_is_open = True
                        if self.DEBUG:
                            print("re-opened port")
        except Exception as e:
            print("Error while checking if serial port object already existed: " + str(e))
            
        # Create the port if it does not exist    
        if port_exists == False and port_is_open == False:
            if self.DEBUG:
                print("Opening new serial port")
            try:
                new_port = serial.Serial(port_id, 115200, timeout=1)
                current_serial_object = new_port
                port_exists = True
                port_is_open = True  
                if self.DEBUG:
                    print("port opened: " + str(new_port))
                try:
                    port_item = {port_id:{'port_object':new_port, "countdown":3}} # Countdown may be used later to self-close the ports after a while. But it may not be necessary.
                    self.open_serial_ports.append(port_item)
                    #current_serial_object = port_item[port_id]['port_object']
                except Exception as e:
                    print("Failed to append serial port object to port object list: " + str(e))
                
            except Exception as e:
                print("Failed to create serial port object: " + str(e))


        if port_exists == True and port_is_open == True:
            try:
                while( current_serial_object.inWaiting() > 0 ):
                    ser_bytes = current_serial_object.readline()
                    decoded_bytes = ser_bytes.decode("utf-8") # float(ser_bytes[0:len(ser_bytes)-2].decode("utf-8")) # Use ASCII instead?
                    if len(decoded_bytes) > 0:
                        decoded_bytes += "<br/>"
                        #if self.DEBUG:
                        print("New serial line: " + str(decoded_bytes))
                        new_lines += str(decoded_bytes)
                        #if len(new_lines) > 500:
                        #    print("Huge amount of serial data")
                        #    break
            except Exception as e:
                print("Could not read from the serial port: " + str(e))

        result["new_lines"] = new_lines
        
        return result
    


    def close_serial_port(self, port_id):
        result = {'success':True}
        print("port id to close: " + str(port_id))
        try:
            for key in self.open_serial_ports:
                if port_id in key:
                    current_serial_object = key[port_id]['port_object']
                    if current_serial_object.isOpen():
                        print("Port was open, closing...")
                        current_serial_object.close()
        except Exception as e:
            print("Error closing port:" + str(e))
            result['success'] = False
        return result



    def close_tab(self):
        result = {'success':True}
        print("Rebooting gateway in order to close a browser tab while in fullscreen..")
        try:
            os.system('sudo reboot now') # Pretty hardcore way of closing a tab, but it's the only way of do this while in fullscreen.
        except Exception as e:
            print("Error closing tab:" + str(e))
            result['success'] = False
        return result



    def unload(self):
        print("Shutting down adapter")
        try:
            for port_name in self.previous_serial_devices:
                self.close_serial_port(str(port_name))
        except:
            print("Unable to cleanly close the add-on")



    def add_from_config(self):
        """Attempt to add all configured devices."""
        try:
            database = Database('Candle-manager-addon')
            if not database.open():
                return
            
            config = database.load_config()
            database.close()
            
            if not config:
                print("Error: no settings found for Candle Manager.")
                return
            
            #print("Loading settings for Candle manager Config: " + str(config))
            
            
        
            # Debug
            try:
                if 'Debug' in config:
                    self.DEBUG = bool(config['Debug'])
                    if self.DEBUG:
                        print("Debugging is set to: " + str(self.DEBUG))
                else:
                    print("Debugging preference was not in the database?")
                    self.DEBUG = False
                
            except:
                print("Error loading debugging preference")
            
            
            # Sketches URL
            try:
                if 'Sketches' in config:
                    self.json_sketches_url = str(config['Sketches'])
                    print("-Sketch URL found in settings")
                else:
                    print("-No Arduino sketch(es) URL found in the code.")
            except:
                print("Error loading sketches URL from preference")
            
            
            # Password
            try:
                if 'Password' in config:
                    print("-Password found in settings")
                    self.simple_password = str(config['Password'])
                
                    if self.simple_password == "changeme":
                        try:
                            #alphabet = string.ascii_letters + string.digits
                            #better_password = ''.join(secrets.choice(alphabet) for i in range(8))
                        
                            #try:
                                # Try to generate an even better password.
                            alphabet = string.ascii_letters + string.digits
                            while True:
                                better_password = ''.join(secrets.choice(alphabet) for i in range(8))
                                if (any(c.islower() for c in better_password)
                                        and any(c.isupper() for c in better_password)
                                        and sum(c.isdigit() for c in better_password) >= 2):
                                    break
                            #except:
                                #pass
                            
                        
                            #print("Generated a better password")
                            #print(str(better_password))
                            config['Password'] = better_password
                    
                            # Store the better password.
                            print("Storing overridden settings")
                            try:
                                database = Database('Candle-manager-addon')
                                if not database.open():
                                    print("Error, could not open settings database to store better password.")
                                    #return
                                else:
                                    database.save_config(config)
                                    database.close()
                                    print("-The password was changeme, so a better password was generated and stored in settings.")
                        
                            except:
                                print("Error! Failed to store better password in database.")
                        except Exception as e:
                            print("Error generating better password: " + str(e))

                else:
                    print("-No Password found in settings")
            except:
                print("Error loading encryption password from preference")
            

            # Arduino type
            try:
                if 'Arduino type' in config:
                    if str(config['Arduino type']) == "Arduino Nano":
                        self.arduino_type == "nano"
                    if str(config['Arduino type']) == "Arduino Uno":
                        self.arduino_type == "uno"
                    if str(config['Arduino type']) == "Arduino Mega":
                        self.arduino_type == "mega"
                    print("-Arduino type found in settings")
            except:
                print("Error loading Arduino type from preference")
                
            # Advanced
            try:
                if 'Advanced' in config:
                    self.advanced_interface = bool(config['Advanced'])
                    self.create_candle_manager_thing = True
            except:
                print("Error loading advanced preference")
            
                
                
        except:
            print("Error loading configuration")






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
        self.adapter = adapter
        self.name = 'Candle manager'
        self.title = 'Candle manager'
        self.description = 'Candle manager'
        
        try:
            
            self.links = [
                {
                    "rel": "alternate",
                    "mediaType": "text/html",
                    "href": self.adapter.full_lan_path
                }
            ]
            Device.__init__(self, adapter, 'candle-device')
        
            self.links = [
                {
                    "rel": "alternate",
                    "mediaType": "text/html",
                    "href": self.adapter.full_lan_path
                }
            ]


        except Exception as e:
            print("Error generating Candle Manager Thing: " + str(e))





#
#  HELPER FUNCTIONS
#

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever



def run_command(cmd, timeout_seconds=60):
    try:
        
        p = subprocess.run(cmd, timeout=timeout_seconds, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        if p.returncode == 0:
            return p.stdout  + '\n' + "Command success" #.decode('utf-8')
            #yield("Command success")
        else:
            if p.stderr:
                return "Run command error: " + str(p.stderr)  + '\n' + "Command failed"   #.decode('utf-8'))

    except Exception as e:
        print("Error running Arduino CLI command: "  + str(e))
        
        
        
def run_command_json(cmd, timeout_seconds=60):
    try:
        
        result = subprocess.run(cmd, timeout=timeout_seconds, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

        if result.returncode == 0:
            return result.stdout #.decode('utf-8')
        else:
            if result.stderr:
                return "Error: " + str(result.stderr)  #.decode('utf-8'))
 
    except Exception as e:
        print("Error running Arduino JSON CLI command: "  + str(e))
        
        
        
def split_sentences(st):
    sentences = re.split(r'[.?!]\s*', st)
    if sentences[-1]:
        return sentences
    else:
        return sentences[:-1]
        


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = 'candle.local'
    finally:
        s.close()
    return IP
    
    
