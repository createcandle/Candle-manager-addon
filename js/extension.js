(function() {
  class CandleManagerExtension extends window.Extension {
    constructor() {
      super('Candle-manager-addon');
      this.addMenuEntry('Candle manager');

      this.content = '';

      fetch(`/extensions/Candle-manager-addon/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
          this.content = text;
        })
        .catch((e) => console.error('Failed to fetch content:', e));

			this.view.innerHTML = this.content;
    }

    show() {
			//console.log("Candle manager received show command.");
			//console.log(this.content);
      this.view.innerHTML = this.content;
			document.getElementById('extension-Candle-manager-addon-iframe').src = "https://" + window.location.hostname + ":8686";
    }

		hide(){
	      //console.log("Candle manager received hide command");
				document.getElementById("extension-Candle-manager-addon-view").innerHTML = '';
		}
  }

  new CandleManagerExtension();

})();
