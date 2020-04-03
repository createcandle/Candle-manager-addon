(function() {
  class CandleManagerExtension extends window.Extension {
    constructor() {
      super('Candle-manager-addon');
      this.addMenuEntry('Candle manager');

      this.content = '<p style="color:white;font-family:arial,sans-serif; margin:4rem auto"><strong>Failed to load Candle Manager add-on</strong><br/><br/>- The gateway did not respond. Perhaps it crashed? You could try rebooting it.<br/><br/>- You can try to reload this webpage.</p>';
			
      fetch(`/extensions/Candle-manager-addon/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
          this.content = text;
        })
        .catch((e) => console.error('Failed to fetch content:', e));
			
	  this.view.innerHTML = this.content;
			
	  var attachFuncEvent = "message";
	          var attachFunc = window.addEventListener ;
	          if (! window.addEventListener) {
	              attachFunc = window.attachEvent;
	              attachFuncEvent = "onmessage";
	          }

	          attachFunc(attachFuncEvent, function(event) {
	              if (event.data ==  'iframeIsDone') { // iframe has succesfully loaded the Candle manager callback
					  //console.log("Candle manager loaded in iframe succesfully");
					  var ssl_frame_warning = document.getElementById('extension-Candle-manager-addon-ssl-frame-warning');
					  ssl_frame_warning.parentNode.removeChild(ssl_frame_warning); // remove the warning if the Candle manager loaded succesfully
	              }
	          });
			
    }

    show() {
			console.log("Candle manager received show command.");
			//console.log(this.content);
      	  	this.view.innerHTML = this.content;
			
			
			//var full_lan_path = "http://gateway.local:8686"
			
			
			/*			
			var the_protocol = "https://";
			if (location.protocol == 'http:'){
				// If the connection is unsecured, we assume it's a local lan connection, and can simply load the Candle Manager into the iframe. Perhaps a more thorough check would be if `mozilla-iot` is in the URL bar string.
				//the_protocol = "http://";
				document.getElementById('extension-Candle-manager-addon-iframe').src = 'http://' + window.location.hostname + ':8686';
			}
			else{
			*/
				// If the user is using https and/or the tunneling feature, find out what the actual local IP address is from the controller.
	      	window.API.postJson(
		        `/extensions/${this.id}/api/full_lan_path`,
		        {'ssl':1,'hostname':window.location.hostname} // Not currently used
		      ).then((body) => {
						//full_lan_path = body['full_lan_path'];
						console.log("API response:");
						//console.log(body);
						//if( 'https://' + window.location.hostname + ':8686' != body['full_lan_path'] ){
						//	document.getElementById('extension-Candle-manager-addon-iframe').src = 'data:text/html,\'<p style="color:white;font-family:arial,sans-serif; margin:4rem auto"><strong>The manager cannot be displayed (yet)</strong><br/><br/> - It might still be starting up. You can try reloading the page in a few seconds.<br/><br/>- Alternatively, you can try to visit <a target="_blank" href="' + body['full_lan_path'] + '">directly</a>. There you may have to create a security exception.</p>\'';
						//}
						document.getElementById('extension-Candle-manager-addon-iframe').src = body['full_lan_path'];
						document.getElementById('extension-Candle-manager-addon-support-link').href = body['full_lan_path'];
						//console.log(body['full_lan_path']);
						//console.log(body['ssl_enabled']);
						
						
						setTimeout(function() {
							console.log("timeout is now");
							try {
							  document.getElementById('extension-Candle-manager-addon-ssl-frame-warning').classList.remove("extension-Candle-manager-addon-hidden");
							}
							catch(err) {
							  //
							}
						}, 3000);
						
		      }).catch((e) => {
						var error_string = e.toString();
		        		console.log("Error calling API, will try backup option");
						console.log(error_string);
						document.getElementById('extension-Candle-manager-addon-iframe').src = "https://gateway.local:8686";
		      });
			//}
    }


		hide(){
	      //console.log("Candle manager received hide command");
				document.getElementById('extension-Candle-manager-addon-iframe').src = "";
				//document.getElementById("extension-Candle-manager-addon-view").innerHTML = '';
		}
  }

  new CandleManagerExtension();
  
})();
