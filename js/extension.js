(function() {
  class CandleManagerExtension extends window.Extension {
    constructor() {
      super('Candle-manager-addon');
      this.addMenuEntry('Candle manager');

      this.content = '';
	  //console.log("HELLO THERE CANDLE FANS");
	  //console.log( ${this.id} );
      fetch(`/extensions/${this.id}/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
          this.content = text;
        })
        .catch((e) => console.error('Failed to fetch content:', e));
    }

    show() {
      this.view.innerHTML = this.content;

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
    }
  }

  new CandleManagerExtension();
})();
