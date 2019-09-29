"""Example API handler."""

from gateway_addon import APIHandler, APIResponse
import json
import os


class CandleManagerAPIHandler(APIHandler):
    """Example API handler."""

    def __init__(self, adapter, verbose=False):
        """Initialize the object."""
        print("INSIDE API HANDLER INIT")
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
        
        print(">>>>>> Created new API HANDLER: " + str(manifest['id']) + " <<<<<<<<<")


    def handle_request(self, request):
        """
        Handle a new API request for this handler.

        request -- APIRequest object
        """
        
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
