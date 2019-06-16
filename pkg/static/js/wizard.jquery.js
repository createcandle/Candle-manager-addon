(function ( $ ) {

    function getActiveStep() {
        return $("ol.wizard li.active");
    }


    var methods = {

        init : function (options) {

        },

        nextStep : function () {
            var active = getActiveStep();
            var index = $(active).index();
            var numSteps = $("ol.wizard li").length;
            if (index < numSteps - 1) {
                $(active).removeClass("active");
                $(active).addClass("done");
                $(active).next().addClass("active");
            }
        },

        previousStep : function () {
            var active = getActiveStep();
            var index = $(active).index();
            if (index > 0) {
                $(active).removeClass("active");
                $(active).prev().removeClass("done");
                $(active).prev().addClass("active");
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