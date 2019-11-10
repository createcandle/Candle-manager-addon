(function() {
  class CandleManagerExtension extends window.Extension {
    constructor() {
      super('Candle-manager-addon');
      this.addMenuEntry('Candle manager');

      this.content = '';
			//this.empty = '';
	  	//console.log("HELLO THERE CANDLE FANS");
	  	//console.log( ${this.id} );
	  
	  	//fetch(`/extensions/${this.id}/views/content.html`)
      fetch(`/extensions/Candle-manager-addon/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
          this.content = text;
        })
        .catch((e) => console.error('Failed to fetch content:', e));
				
	
			this.view.innerHTML = this.content;
	
    }

    show() {
			console.log("Candle manager received show command.");
			//console.log(this.content);
      this.view.innerHTML = this.content;
	  	//waitForElementToDisplay("#extension-Candle-manager-addon-iframe",100);

	  /*
      const key =
        document.getElementById('extension-Candle-manager-addon-form-key');
      const value =
        document.getElementById('extension-Candle-manager-addon-form-value');
      const submit =
        document.getElementById('extension-Candle-manager-addon-form-submit');
      const pre =
        document.getElementById('extension-Candle-manager-addon-response-data');

      submit.addEventListener('click', () => {
        fetch(`/extensions/${this.id}/api/example-api?samplekey=samplevalue`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            Authorization: `Bearer ${window.API.jwt}`,
          },
          body: JSON.stringify({[key.value]: value.value}),
        }).then((res) => {
          return res.json();
        }).then((body) => {
          pre.innerText = JSON.stringify(body, null, 2);
        }).catch((e) => {
          pre.innerText = e.toString();
        });
      });
	  */
	  
    }
		hide(){
	      console.log("Candle manager received hide command");
		}
  }

  new CandleManagerExtension();
  console.log("Initialising Candle Manager add-on");
  candleManagerCheckLoop(500); // the main function that loads of unloads the iframe.
  //var current_hostname = window.location.hostname;
  //var flask_base = "http://" + current_hostname + ":8686";
  //console.log(flask_base);
  
  function resizeIframe(obj) {
    obj.style.height = obj.contentWindow.document.body.scrollHeight + 'px';
  }
  
  function candleManagerCheckLoop(time){
  	var candle_manager_section = document.getElementById("extension-Candle-manager-addon-view");
		var style = window.getComputedStyle(candle_manager_section);
    if ( typeof this.loaded == 'undefined' ) {
        // It has not... perform the initialization
        this.loaded = false;
    }

		//var ready_to_load = true;
		if( style.display === 'none' ){
			// If the Candle Manager view is actually visible
		  console.log("Unloading the Candle manager.");
		  //document.getElementById('extension-Candle-manager-addon-iframe').src = "about:blank";
			candle_manager_section.innerHTML = '';
			this.loaded = false;
		}
		else{
			//console.log("Candle manager is visible");
			if(this.loaded == false){
				console.log("Loading the Candle Manager iframe");
				document.getElementById('extension-Candle-manager-addon-iframe').src = "http://" + window.location.hostname + ":8686";
				this.loaded = true;
			}
		}
		
    setTimeout(function() {
      candleManagerCheckLoop(time);
    }, time);
		
  }
	
  
  
/*
  function defer(method) {
      if (window.jQuery) {
          method();
      } else {
          setTimeout(function() { defer(method) }, 50);
      }
  }
*/
  
//  defer(function(){
//	  jQuery.getScript("/extensions/Candle-manager-addon/js/wizard.jquery.js")
//	  jQuery.getScript("/extensions/Candle-manager-addon/js/main.js") 
//  });
  
})();
