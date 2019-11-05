"""Example API handler."""


import functools
import json
import os

try:
    from gateway_addon import APIHandler, APIResponse
    print("Candle manager -> api_handler.py succesfully loaded APIHandler and APIResponse from gateway_addon")
except:
    print("Candle manager -> api_handler.py error. Import APIHandler and APIResponse from gateway_addon failed. Use at least WebThings Gateway version 0.10")

print = functools.partial(print, flush=True)


class CandleManagerAPIHandler(APIHandler):
    """Example API handler."""

    def __init__(self, adapter, verbose=False):
        """Initialize the object."""
        print("INSIDE API HANDLER INIT")
        try:
            manifest_fname = os.path.join(
                os.path.dirname(__file__),
                '..',
                'manifest.json'
            )            
            self.adapter = adapter
            print("ext: self.adapter = " + str(self.adapter))

            with open(manifest_fname, 'rt') as f:
                manifest = json.load(f)

            APIHandler.__init__(self, manifest['id'])
            self.adapter.manager_proxy.add_api_handler(self)
        
            print("Created new API HANDLER: " + str(manifest['id']))
        except Exception as e:
            print("Failed to init UX extension API handler: " + str(e))
        
        

    def handle_request(self, request):
        """
        Handle a new API request for this handler.

        request -- APIRequest object
        """
        
        try:
            print(">>>>>> INCOMING API REQUEST <<<<<<<<<")
            print(">>> REQUEST.PATH = " + str(request.path))
            print(">>> REQUEST.BODY = " + str(request.body))
        
        
            if request.method != 'POST' or request.path != '/example-api':
                return APIResponse(status=404)

            # echo back the body
            return APIResponse(
              status=200,
              content_type='application/json',
              content=json.dumps(request.body),
            )
        except Exception as e:
            print("Failed to handle UX extension API request: " + str(e))
        