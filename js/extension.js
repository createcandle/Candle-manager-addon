(function() {
  class CandleManagerExtension extends window.Extension {
    constructor() {
      super('Candle-manager-addon');
      this.addMenuEntry('Candle manager');

      this.content = '';
	  //console.log("HELLO THERE CANDLE FANS");
	  //console.log( ${this.id} );
	  
	  //fetch(`/extensions/${this.id}/views/content.html`)
      fetch(`/extensions/Candle-manager-addon/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
          this.content = text;
        })
        .catch((e) => console.error('Failed to fetch content:', e));
    }

    show() {
      this.view.innerHTML = this.content;

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
  }

  new CandleManagerExtension();
  console.log("HELLO THERE, I AM NORMAL JS");
  
  //var current_hostname = window.location.hostname;
  //var flask_base = "http://" + current_hostname + ":8686";
  //console.log(flask_base);
  
  function resizeIframe(obj) {
      obj.style.height = obj.contentWindow.document.body.scrollHeight + 'px';
    }
  
  
  function waitForElementToDisplay(selector, time) {
  	if(document.querySelector(selector)!=null) {
	  document.getElementById('extension-Candle-manager-addon-iframe').src = "http://" + window.location.hostname + ":8686";
	  document.getElementById('extension-Candle-manager-addon-iframe').style.height = document.getElementById('extension-Candle-manager-addon-iframe').contentWindow.document.body.scrollHeight + 'px';
      return;
    }
    else {
      setTimeout(function() {
        waitForElementToDisplay(selector, time);
      }, time);
    }
  }
  waitForElementToDisplay("#extension-Candle-manager-addon-iframe",100);
  
  
  
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
