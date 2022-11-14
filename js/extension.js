(function() {
  class CandleManagerExtension extends window.Extension {
    constructor() {
      super('Candle-manager-addon');
      this.addMenuEntry('Candle manager');

      this.content = '<p style="color:white;font-family:arial,sans-serif; margin:4rem auto"><strong>Failed to load Candle Manager add-on</strong><br/><br/>- The gateway did not respond. Perhaps it crashed? You could try rebooting it.<br/><br/>- You can try to reload this page.</p>';
      
      this.debug = false;
      
      fetch(`/extensions/Candle-manager-addon/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
          this.content = text;
		  //console.log("fetch done");
		  if( document.location.href.endsWith("andle-manager-addon") ){
		  	this.show();
		  }
		  
        })
        .catch((e) => console.error('Failed to fetch content:', e));
			
	  this.view.innerHTML = this.content;
			
      this.warning_needed = true;
            
	  var attachFuncEvent = "message";
      var attachFunc = window.addEventListener ;
      if (! window.addEventListener) {
          attachFunc = window.attachEvent;
          attachFuncEvent = "onmessage";
      }

      attachFunc(attachFuncEvent, function(event) {
          if (event.data ==  'iframeIsDone') { // iframe has succesfully loaded the Candle manager callback
			  console.log("Candle manager loaded in iframe succesfully");
              this.warning_needed = false;
			  const ssl_frame_warning = document.getElementById('extension-Candle-manager-addon-ssl-frame-warning');
			  if(ssl_frame_warning != null){
				  ssl_frame_warning.parentNode.removeChild(ssl_frame_warning); // remove the warning if the Candle manager loaded succesfully
			  }
          }
      });

    }

    show() {
			//console.log("Candle manager received show command.");
			//console.log(this.content);
      	  	this.view.innerHTML = this.content;
			//console.log(this.content);
			
			const iframe_el = document.getElementById('extension-Candle-manager-addon-iframe');
			//var full_lan_path = "http://gateway.local:8686"
			
            //console.log("window.location.protocol: ", window.location.protocol);
			
			var http_local_address = window.location.protocol + '//' + window.location.hostname + ':8686'; // this is only used as a backup guess for where the flask server may be
            
            /*
			//var the_protocol = "https://";
			if (window.location.protocol == 'http:'){
				// If the connection is unsecured, we assume it's a local lan connection, and can simply load the Candle Manager into the iframe. Perhaps a more thorough check would be if `mozilla-iot` is in the URL bar string.
				//the_protocol = "http://";
                if(iframe_el != null){
                    iframe_el.src = http_local_address;
                }
				
			}
			else{
			    console.log("Candle manager: seems to be a HTTPS connection");
            }
            */
			
			var https_in_url = 0;
			if (location.protocol == 'https:'){
				https_in_url = 1
			}
			
			
			// If the user is using https and/or the tunneling feature, find out what the actual local IP address is from the controller.
	      	
            //console.log("https_in_url : ", https_in_url );
			
			window.API.postJson(
		        `/extensions/${this.id}/api/full_lan_path`,
		        {'ssl':https_in_url,'hostname':window.location.hostname}
		      ).then((body) => {
						//full_lan_path = body['full_lan_path'];
						//if( 'https://' + window.location.hostname + ':8686' != body['full_lan_path'] ){
						//	document.getElementById('extension-Candle-manager-addon-iframe').src = 'data:text/html,\'<p style="color:white;font-family:arial,sans-serif; margin:4rem auto"><strong>The manager cannot be displayed (yet)</strong><br/><br/> - It might still be starting up. You can try reloading the page in a few seconds.<br/><br/>- Alternatively, you can try to visit <a target="_blank" href="' + body['full_lan_path'] + '">directly</a>. There you may have to create a security exception.</p>\'';
						//}
                        
                        
                        this.debug = body['debug'];
                        
                        if(this.debug){
    						console.log("Candle manager full_lan_path API response:");
    						console.log(body);
                        }
                        
                        
                        var flask_protocol = 'http';
                        if( body['ssl_certificate_detected'] ){
                            flask_protocol = 'https';
                        }
                        
                        
						if(document.getElementById('extension-Candle-manager-addon-iframe') != null){
                            if(this.debug){
                                console.log("candle manager debug: setting iframe to:", flask_protocol + "://" + body['full_lan_path']);
                            }
						    document.getElementById('extension-Candle-manager-addon-iframe').src = flask_protocol + "://" + body['full_lan_path'];
						}
                        else{
                            console.log('error, candle manager iframe_el was null while trying to set candle manager iframe to : ', flask_protocol + "://" + body['full_lan_path']);
                        }
                        
						//iframe_el.src = ;
						document.getElementById('extension-Candle-manager-addon-support-link').href = flask_protocol + "://" + body['full_lan_path'];
						//console.log(body['full_lan_path']);
						//console.log(body['ssl_enabled']);
						
						
						setTimeout(function() {
							//console.log("timeout is now");
                            if(this.warning_needed){
    							try {
    							    document.getElementById('extension-Candle-manager-addon-ssl-frame-warning').classList.remove("extension-Candle-manager-addon-hidden");
    							}
    							catch(err) {
                                    if(this.debug){
                                        console.log("debug: candle manager timeout error: ", err);
                                    }
    							}
                            }
							else{
							    console.log("candle manager: iframe loaded succesfully, no need to show warning");
							}
						}, 3000);
						
		      }).catch((e) => {
		        		if(this.debug){
                            console.log("Error calling API, will try backup option. Error was: ", e);
                        }
						if(document.getElementById('extension-Candle-manager-addon-iframe') != null){
						    document.getElementById('extension-Candle-manager-addon-iframe').src = http_local_address;
						}
                        else{
                            console.log('error, iframe_el was null while trying to set candle manager iframe to backup address: ', http_local_address);
                        }
                        
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
