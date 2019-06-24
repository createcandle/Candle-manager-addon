
var current_step = 1;
var source_id = -1;
var new_port_id = "";
var doing_serial_check = false

$(document).ready(function(){
	console.log("document ready");
    
    //var el = $("ol.wizard.numeric");
    
    $('#step3 button.back').on('click', function () {
        $("ol.wizard.numeric").wizard('previousStep');
        show_step(2);
    });

    $('#step3 button.next').on('click', function () {
        return_new_settings()
    });

    $('#step4 button.show.code').on('click', function () {
        console.log("button clicked to toggle code display")
        $('#new-code').toggleClass( 'hidden' );
    });
    
    $('#step5 button.next').on('click', function () {
        $("ol.wizard.numeric").wizard('nextStep');
        new_port_id = "";   // Reset some variables
        source_id = -1;     // Reset some variables
        show_step(6);
        serial_close();
    });

    $('#skip-to-check').on('click', function () {
        show_step(5);
        $('#upload-progress').addClass('progress_complete');
        show_step(5);
        show_serial_debug();

    });
    
    
    $('button.restart').on('click', function () {
        location.reload();
    });
    
    // Ask if a USB device has been plugged in.
    init_interface();
    //setTimeout(poll_USB, 1000);
    setInterval(poll_USB, 1000);
});



function show_step(step_number){
    current_step = step_number;
    $("#content > div").removeClass("active");
    $("#content > #step" + step_number).addClass("active");
}

function init_interface(){
    $.getJSON( "/init_interface", function( data ) {
        console.log(data);
        if ( data.advanced == 1 ){
            $('.advanced').show(); // Show all the advanced interface elements.
        }
        /*
        var items = [];
        $.each( data, function( key, value ) {
            //console.log("at item:" + key);
            items.push( "<li id=source" + key + " data-source-id=" + key + ">" + value + "</li>" );
        });
        */
    });

}


function poll_USB(){
    // make Ajax call here, inside the callback call:
    $.getJSON("/scanUSB",function(json){
        
        if(json.state != undefined){
            if ( json.state == "stable" ) {
                console.log("No change in connected USB devices")// No change in the number of attached USB devices.
            }
            else if ( json.state == "added" && json.new_port_id != undefined ){
                
                console.log("New USB device connected at " + json.new_port_id)
                if(current_step == 1){
                    console.log("json.new_port_id = " + json.new_port_id);
                    new_port_id = json.new_port_id;
                    $('.new-port-id').text(new_port_id);
                    generate_sources_list();
                }
                //else{
                //    location.reload();
                //}
            }
            else if ( json.state == "removed" && json.removed_port_ids != undefined){
                console.log("USB device removed!")
                if( json.removed_port_ids.indexOf(new_port_id) >= 0) { // If the current port is in the list of removed ports.
                    console.log("The targeted USB serial device is no longer available");
                    location.reload();
                }
            }
            else{
                console.error("Error checking USB status");
            }
        }
        //setTimeout(poll_USB, 1000);
    });
}



function generate_sources_list(){
    console.log("Generating sources list");
        
    $.getJSON( "/source", function( data ) {
        console.log(data);
        var items = [];
        $.each( data, function( key, value ) {
            //console.log("at item:" + key);
            items.push( "<li id=source" + key + " data-source-id=" + key + ">" + value + "</li>" );
        });
        
        $( "<ul/>", {
            "id": "sources-list",
            "class":"list",
            html: items.join( "" )
        }).appendTo( "#sources-container" );
        
        $( "#sources-list > li" ).each(function(index){
            $(this).string_to_color(["background-color"], $(this).text());
        });
        
        $("#sources-list > li").click(function(){
            //returnValue = ;
            console.log("clicked on " + $(this).text() );
            $('#settings_device_name').text( $(this).text() )
            source_id = $(this).data('source-id');
            generate_settings_page(source_id);
            
        });
        
        // Finally, show the second step to the user
        $("ol.wizard.numeric").wizard('nextStep');
        show_step(2);
    });
}



function generate_settings_page(source_id){
    console.log("Generating settings for #" + source_id);
    $( "#settings" ).empty();
    
    $.getJSON( "/extract/" + source_id, function( data ) {
        console.log(data);
        var items = [];
        
        // Generate explanation HTML
        if(data.explanation != undefined){
            $("#settings-explanation").val(data.explanation);
            $("#settings-explanation-container").show();
        }
        else{
            $("#settings-explanation-container").hide();
        }
        
        // Generate Settings HTML
        if( data.settings.length > 0 ){
            $.each( data.settings, function( key, value ) {
                console.log("at item:" + key);
                if( key == 0){autofocus = "autofocus";}else{autofocus = "";}
                if (value.type == "checkbox" && value.value == 1){checked = "checked";}else{checked = "";}
                items.push( "<div class=\"form-item\"><label for=\"item" + key + "\">" + value.title + "</label><input type=" + value.type + " name=\"item" + key + "\" data-settings-form-id=" + key + " value=" + value.value +  " " + checked + " " + autofocus + "></div><p>" + value.comment + "</p>" );
            });

            $( "<form/>", {
                "id": "settings-form",
                "class":"form",
                html: items.join( "" )
            }).appendTo( "#settings" );
        }
        else{
            $( "#settings" ).append( "<p>There are no settings for you to change.</p>" );
        }
        
        // Finally, show the step to the user
        $("ol.wizard.numeric").wizard('nextStep');
        show_step(3);
    });

}



// This is called when the 'next' button on the settings step is pressed
function return_new_settings(){
    console.log("Sending new settings back for #" + source_id);
    
    // Grab new values from the form
    returnValues = [];
    $('#settings-form :input').each(function(index){
        if( $(this).is(':checkbox') ){
            console.log("checkbox found")
            if($(this).is(":checked")){
                returnValue = 1;
            }
            else{ 
                returnValue = 0; 
            }
        }
        else {
            returnValue = $(this).val();
        }
        console.log(returnValue);
        returnValues.push(returnValue);
    });
    console.log("Values to return:" + returnValues);
    
    // Send the new values back to the server (the add-on)
    $.ajax({
        url: "/generate_code/" + source_id,
        type: "POST",
        data: JSON.stringify(returnValues),
        contentType: "application/json; charset=utf-8",
        success: function(data) { 
            
            //if(data == null || data.message == undefined || data.success == undefined){
            if(data == null){
                console.error("Error while generating code");
                return;
            }
            
            console.log(data);
            if( data.success == true ){
                console.log("Python received the new settings and was able to generate new code")
                $("ol.wizard.numeric").wizard('nextStep');
                
                $('#new-code').val(data.code);
                $('#code-container').removeClass('hidden');
                show_step(4);
                check_libraries()
            }else{
                $('#settings-errors').text("Unable to generate code from the settings you provided");
                $('#settings-errors').show();
                console.log("Python was unable to integrate the desired settings into the code")
                $('#step4 button.show.code, #new_code').addClass('hidden');
            }
        }
    });
}


function check_libraries(){
    console.log("Asking to check_libraries");
    
    $.getJSON( "/check_libraries/" + source_id, function( data ) {
        console.log(data);
        
        if(data == null || data.message == undefined || data.success == undefined){
            lost_connection();
            return;
        }
        
        $("#upload-status").text(data.message);
        
        // Generate explanation HTML
        if( data.success == false ){
            console.log("ERROR. Something went wrong during libraries check:");
            show_upload_errors(data.errors)
            $('#libraries-progress').addClass('progress_failed');
        }
        else{
            console.log("Checking libraries went ok");
            $('#libraries-progress').addClass('progress_complete');
            compile();
        }
    });
}



function compile(){
    console.log("Asking to start compilation");
    
    $.getJSON( "/compile/" + source_id, function( data ) {
        console.log(data);

        if(data == null || data.message == undefined || data.success == undefined){
            lost_connection();
            return;
        }

        $("#upload-status").text(data.message);
        
        // Generate explanation HTML
        if( data.success == false ){
            console.log("ERROR. Something went wrong during compiling:");
            $('#compile-progress').addClass('progress_failed');
            show_upload_errors(data.errors)
        }
        else{
            console.log("Compile went ok");
            $('#compile-progress').addClass('progress_complete');
            test_upload();
        }
    });
}


function test_upload(){
    console.log("Asking to do a test upload");

    $.ajax({
        url: "/test_upload/" + source_id,
        type: "POST",
        data: JSON.stringify(new_port_id),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
            console.log(data);
            //var items = [];

            if(data == null || data.message == undefined || data.success == undefined){
                lost_connection();
                return;
            }

            $("#upload-status").text(data.message);


            // Generate explanation HTML
            if( data.success == false ){
                console.log("ERROR. Something went wrong during the test upload.");
                $('#test-progress').addClass('progress_failed');
                show_upload_errors(data.errors)
            }
            else{
                console.log("Test went ok, waiting 20 seconds before starting final upload.");
                $('#test-progress').addClass('progress_complete');
                setTimeout(function(){
                    console.log("Starting upload now");
                    upload();
                }, 20000);
                
            }
            
        }
    });
}



function upload(){
    console.log("Asking to start upload");


    $.ajax({
        url: "/upload/" + source_id,
        type: "POST",
        data: JSON.stringify(new_port_id),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
            console.log(data);
            //var items = [];

            if(data == null || data.message == undefined || data.success == undefined){
                lost_connection();
                return;
            }

            $("#upload-status").text(data.message);

            // Generate explanation HTML
            if( data.success == false ){
                console.log("ERROR. Something went wrong during upload.");
                console.log(data.errors);
                $('#upload-progress').addClass('progress_failed');
                show_upload_errors(data.errors)
            }
            else{
                console.log("Upload went ok");
                $('#upload-progress').addClass('progress_complete');
                setTimeout(function(){
                    //Finally, show the last step to the user
                    $("ol.wizard.numeric").wizard('nextStep');
                    show_step(5);
                    show_serial_debug();
                }, 1000);
            }
        }
    });
}



function show_upload_errors(errors){
    console.log("Showing errors");
    console.log(errors);
    var items = [];    
    
    $("#upload-output").removeClass("hidden");
    
    if(errors.length == 0){return;}
    
    $('#errors-container').slideDown('slow');
    $.each( errors, function( key, value ) {
        //console.log("at item:" + key);
        items.push( "<li><span class=\"error-number\">" + (key + 1) + "</span><span class=\"error-text\">" +  value + "</span></li>" );
    });

    $( "<ul/>", {
        "id": "errors-list",
        html: items.join( "" )
    }).appendTo( "#errors-container" );

    $('button.restart').removeClass('hidden');
}


function lost_connection(){
    console.log("Returned data object was empty");
    $("#upload-status").text("Lost connection to server");
    $("#upload-output").removeClass('hidden');
}


function show_serial_debug(){
    console.log("Showing serial debug");

    
    // Send the new values back to the server (the add-on)
    $.ajax({
        url: "/serial_output",
        type: "POST",
        data: JSON.stringify(new_port_id), //{"port_id":port_id}
        contentType: "application/json; charset=utf-8",
        success: function(data) { 
            
            //if(data == null || data.message == undefined || data.success == undefined){
            if(data == null){
                console.error("Empty response");
                return;
            }
            
            console.log(data);
            if( data.new_lines != undefined ){
                console.log("new serial lines: " + data.new_lines);
                //$('#serial-output-container').append(document.createTextNode(data.new_lines));
                $('#serial-output-container').append(data.new_lines);
            }
            
            if( new_port_id != "" ){
                setTimeout(function(){
                    show_serial_debug();
                }, 1000);
            }
            
            
        }
    });
}



function serial_close(){
    console.log("Requesting closure of serial port");

    $('#serial-output-container').empty();
    
    // Send the new values back to the server (the add-on)
    $.ajax({
        url: "/serial_close",
        type: "POST",
        data: JSON.stringify(new_port_id),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
            console.log("Got response");
            if(data == null){
                console.error("Empty response");
                return;
            }
            
            console.log(data);
            if( data.success ){
                console.log("closed port succesfully");
            }
        }
    });
}
    









/*!
 * jquery-string_to_color
 * A jQuery plugin based on string_to_color by Brandon Corbin.
 *
 * Source:
 * https://github.com/erming/jquery-string_to_color
 *
 * Version 0.1.0
 */
(function($) {
	/**
	 * Generate hex color code from a string.
	 *
	 * @param {String} str
	 */
	$.string_to_color = function(str) {
		return "#" + string_to_color(str);
	};
	
	/**
	 * Set one or more CSS properties for the set of matched elements.
	 *
	 * @param {String|Array} property
	 * @param {String} str
	 */
	$.fn.string_to_color = function(property, string) {
		if (!property || !string) {
			throw new Error("$(selector).string_to_color() takes 2 arguments");
		}
		return this.each(function() {
			var props = [].concat(property);
			var $this = $(this);
			$.map(props, function(p) {
				$this.css(p, $.string_to_color(string));
			});
		});
	};
})(jQuery);
 
/********************************************************
Name: str_to_color
Description: create a hash from a string then generates a color
Usage: alert('#'+str_to_color("Any string can be converted"));
author: Brandon Corbin [code@icorbin.com]
website: http://icorbin.com
********************************************************/

function string_to_color(str, options) {

    // Generate a Hash for the String
    this.hash = function(word) {
        var h = 0;
        for (var i = 0; i < word.length; i++) {
            h = word.charCodeAt(i) + ((h << 5) - h);
        }
        return h;
    };

    // Change the darkness or lightness
    this.shade = function(color, prc) {
        var num = parseInt(color, 16),
            amt = Math.round(2.55 * prc),
            R = (num >> 16) + amt,
            G = (num >> 8 & 0x00FF) + amt,
            B = (num & 0x0000FF) + amt;
        return (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255))
            .toString(16)
            .slice(1);

    };
    
    // Convert init to an RGBA
    this.int_to_rgba = function(i) {
        var color = ((i >> 24) & 0xFF).toString(16) +
            ((i >> 16) & 0xFF).toString(16) +
            ((i >> 8) & 0xFF).toString(16) +
            (i & 0xFF).toString(16);
        return color;
    };

    return this.shade(this.int_to_rgba(this.hash(str)), -10);

}