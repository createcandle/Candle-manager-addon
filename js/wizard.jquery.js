(function ( $ ) {

    function getActiveStep() {
        return $("ol.extension-Candle-manager-addon-wizard li.extension-Candle-manager-addon-active");
    }


    var methods = {

        init : function (options) {

        },

        nextStep : function () {
            var active = getActiveStep();
            var index = $(active).index();
            var numSteps = $("ol.extension-Candle-manager-addon-wizard li").length;
            if (index < numSteps - 1) {
                $(active).removeClass("extension-Candle-manager-addon-active");
                $(active).addClass("extension-Candle-manager-addon-done");
                $(active).next().addClass("extension-Candle-manager-addon-active");
            }
        },

        previousStep : function () {
            var active = getActiveStep();
            var index = $(active).index();
            if (index > 0) {
                $(active).removeClass("extension-Candle-manager-addon-active");
                $(active).prev().removeClass("extension-Candle-manager-addon-done");
                $(active).prev().addClass("extension-Candle-manager-addon-active");
            }
        }
    };

    $.fn.wizard = function(methodOrOptions) {

        if ( methods[methodOrOptions] ) {
            return methods[ methodOrOptions ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof methodOrOptions === 'object' || ! methodOrOptions ) {
            // Default to "init"
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  methodOrOptions + ' does not exist on jQuery.tooltip' );
        }
    };

}(jQuery));