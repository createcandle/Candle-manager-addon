"""Candle manager API handler."""


import functools
import json
import socket
import os

try:
    from gateway_addon import APIHandler, APIResponse
    #print("Candle manager -> api_handler.py succesfully loaded APIHandler and APIResponse from gateway_addon")
except:
    print("Candle manager -> api_handler.py error. Import APIHandler and APIResponse from gateway_addon failed. Use at least WebThings Gateway version 0.10")

print = functools.partial(print, flush=True)


class CandleManagerAPIHandler(APIHandler):
    """ API handler."""

    def __init__(self, adapter, verbose=False):
        """Initialize the object."""
        #print("INSIDE API HANDLER INIT")
        try:
            manifest_fname = os.path.join(
                os.path.dirname(__file__),
                '..',
                'manifest.json'
            )
            self.adapter = adapter
            #print("ext: self.adapter = " + str(self.adapter))        

            with open(manifest_fname, 'rt') as f:
                manifest = json.load(f)

            #print("manifest['id'] = " + str(manifest['id']))
            APIHandler.__init__(self, manifest['id'])
            #APIHandler.__init__(self, "poultry")
            self.adapter.manager_proxy.add_api_handler(self)
            #if self.adapter.DEBUG:
            #    print("Created new API HANDLER: " + str(manifest['id']))
        except Exception as e:
            print("Failed to init UX extension API handler: " + str(e))
        
        

    def handle_request(self, request):
        """
        Handle a new API request for this handler.

        request -- APIRequest object
        """
        
        
        try:
            if self.adapter.DEBUG:
                print(">>>>>> INCOMING API REQUEST <<<<<<<<<")
                print(">>> REQUEST.PATH = " + str(request.path))
                print(">>> REQUEST.BODY = " + str(request.body))

            if request.path == '/full_lan_path':
                if self.adapter.DEBUG:
                    print("API call to full_lan_path")
                try:
        
                    
                        
                    
                    self.full_lan_path = "gateway.local:8686"
                        
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        try:
                            # doesn't even have to be reachable
                            s.connect(('192.126.199.199', 1))
                            lan_ip = s.getsockname()[0]
                        except:
                            print("Socket attempts to find IP failed: falling back to gateway.local")
                            lan_ip = 'gateway.local'
                        finally:
                            s.close()
                        
                        self.full_lan_path = str(lan_ip) + ":8686/"
                    except Exception as ex:
                        print("Error, unable to get local lan path: " + str(ex))        
        
        
        
                    if self.adapter.ssl_enabled:
                        self.full_lan_path = "https://" + self.full_lan_path
                    else:
                        self.full_lan_path = "http://" + self.full_lan_path
        
                    response = {'ssl_enabled':self.adapter.ssl_enabled, 'full_lan_path':self.full_lan_path}
                    if self.adapter.DEBUG:
                        print("Returning local path: " + str(response))
        
                    return APIResponse(
                      status=200,
                      content_type='application/json',
                      content=json.dumps(response),
                    )

                except Exception as ex:
                    print("Error returning local path data: " + str(ex))

            else:
                return APIResponse(
                  status=500,
                  content_type='application/json',
                  content=json.dumps({"state":"Error, invalid path"}),
                )

        except Exception as ex:
            print("Error responding to request: " + str(ex))

    
if __name__== "__main__":
    extension = CandleManagerAPIHandler(self, verbose=True)
    
    
    
    