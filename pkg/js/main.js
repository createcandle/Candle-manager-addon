
var current_step = 1;
var source_id = -1;
var new_port_id = "";
var running = false;
var doing_serial_check = false;
var sketches_url = "https://raw.githubusercontent.com/createcandle/candle_source_code_list/master/candle_source_code_list.json";

var current_url = document.location.href;
var current_hostname = window.location.hostname;
console.log(window.location.hostname);


if (location.protocol == 'http:'){
	var flask_base = "http://" + current_hostname + ":8686";
}
else{
	var flask_base = "https://" + current_hostname + ":8686";
}
console.log(flask_base);

	console.log("document ready");
    
    //$.ajaxSetup({
    //    timeout: 60000;
    //});
    
    //var el = $("ol.wizard.numeric");
	// http://localhost:8080
	// /extensions/Candle-manager-addon/js/wizard.jquery.js
    
	
    //if( window.innerHeight == screen.height) {
        // Browser is fullscreen, so we may need a way to close this tab. Javascript can't do that anymore, so instead we restart the entire Raspberry Pi..
    //    $('#extension-Candle-manager-addon-button-close-tab').removeClass('hidden'); 
    //}
    
    $('#step3 button.back').on('click', function () {
        $("ol.extension-Candle-manager-addon-wizard.extension-Candle-manager-addon-numeric").wizard('previousStep');
        show_step(2);
    });
    
    $('#extension-Candle-manager-addon-step3 button.extension-Candle-manager-addon-next').on('click', function () {
        if( running == false ){
            running = true;
            return_new_settings();
        }
    });
    
    $('#extension-Candle-manager-addon-step4 button.extension-Candle-manager-addon-show.extension-Candle-manager-addon-code').on('click', function () {
        console.log("button clicked to toggle code display");
        $('#extension-Candle-manager-addon-new-code').toggleClass( 'extension-Candle-manager-addon-hidden' );
    });
    
    $('#step5 button.next').on('click', function () {
        $("ol.extension-Candle-manager-addon-wizard.extension-Candle-manager-addon-numeric").wizard('nextStep');
        show_step(6);
        serial_close();
        new_port_id = "";   // Reset some variables
        source_id = -1;     // Reset some variables
        running = false;
    });
    
    $('#extension-Candle-manager-addon-skip-to-check').on('click', function () {
        if( running == false ){
            running = true;
            $('#extension-Candle-manager-addon-upload-progress').addClass('extension-Candle-manager-addon-progress_complete');
            $('#extension-Candle-manager-addon-wizard-container').slideUp('fast');
            show_step(5);
            show_serial_debug();
        }
    });
    
    $('button.extension-Candle-manager-addon-restart').on('click', function () {
        location.reload();
    });
    
    $('#extension-Candle-manager-addon-check-for-updates').on('click', function () {
        update_sketches();
    });

    $('#extension-Candle-manager-addon-button-close-tab').on('click', function () {
        close_tab();
    });

    // Ask if a USB device has been plugged in.
    init();
    




function show_step(step_number){
    current_step = step_number;
    $("#extension-Candle-manager-addon-content > div").removeClass("active");
    $("#extension-Candle-manager-addon-content > #extension-Candle-manager-addon-step" + step_number).addClass("active");
}



function init(){
	console.log("INITTING");
	console.log($(".extension-Candle-manager-addon-circular-spinner").length);
	$(".extension-Candle-manager-addon-circular-spinner").fadeOut();
	
	var flask_api_url = flask_base + "/init";
	//console.log(flask_api_url);
    $.ajax({
        url: flask_api_url, 
        dataType: 'json',
        error: function(){
            console.log("Error during init ajax request (timeout?)");
            $('#extension-Candle-manager-addon-skip-update-text').removeClass('extension-Candle-manager-addon-hidden');
            $('button#extension-Candle-manager-addon-skip-update').fadeIn('slow');
        },
        success: function(data){
            if(data == null){
                console.log("Error: init function returned empty data.");
            }
            console.log(data);
            if ( data.advanced == 1 ){
                $('.extension-Candle-manager-addon-advanced').show(); // Show all the advanced interface elements.    
            }
            sketches_url = data.sketches_url;
            show_step(1);
            setInterval(poll_USB, 1000);
            $( "#extension-Candle-manager-addon-wizard-container" ).slideDown("fast");
        },
        timeout: 20000 // Sets timeout to 20 seconds.
    });
}



function poll_USB(){
    // make Ajax call here, inside the callback call:
    $.getJSON(flask_base + "/scanUSB",function(json){
        
        if(json.state != undefined){
            if ( json.state == "stable" ) {
                console.log("No change in connected USB devices")// No change in the number of attached USB devices.
            }
            else if ( json.state == "added" && json.new_port_id != undefined ){
                
                console.log("New USB device connected at " + json.new_port_id)
                if(current_step == 1){
                    console.log("json.new_port_id = " + json.new_port_id);
                    new_port_id = json.new_port_id;
                    $('.extension-Candle-manager-addon-new-port-id').text(new_port_id);
                    generate_sources_list();
                }
                //else{
                //    location.reload();
                //}
            }
            else if ( json.state == "removed" && json.removed_port_ids != undefined){
                console.log("USB device removed!");
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
        
    $.getJSON( flask_base + "/source", function( data ) {
        console.log(data);
        var items = [];
        $.each( data, function( key, value ) {
            //console.log("at item:" + key);
            items.push( "<li id=extension-Candle-manager-addon-source" + key + " data-source-id=" + key + ">" + value + "</li>" );
        });
        
        $( "<ul/>", {
            "id": "sources-list",
            "class":"list",
            html: items.join( "" )
        }).appendTo( "#extension-Candle-manager-addon-sources-container" );
        
        $( "#extension-Candle-manager-addon-sources-list > li" ).each(function(index){
            $(this).string_to_color(["background-color"], $(this).text());
        });
        
        $("#extension-Candle-manager-addon-sources-list > li").click(function(){
            //returnValue = ;
            console.log("clicked on " + $(this).text() );
            $('#extension-Candle-manager-addon-settings_device_name').text( $(this).text() );
            source_id = $(this).data('source-id');
            generate_settings_page(source_id);
            
        });
        
        // Finally, show the second step to the user
        $("ol.extension-Candle-manager-addon-wizard.extension-Candle-manager-addon-numeric").wizard('nextStep');
        show_step(2);
    });
}



function update_sketches(){
    console.log("Checking for updates to sketches, url:" + sketches_url);
    $( "#extension-Candle-manager-addon-sources-container" ).empty();
    
    $.ajax({
        url: flask_base + "/update_sketches",
        type: "POST",
        data: JSON.stringify(sketches_url),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
            console.log(data);
        
            if(data == null || data.success == undefined){
                return;
            }
           
            generate_sources_list();
        }
    });
}



function generate_settings_page(source_id){
    console.log("Generating settings for #" + source_id);
    $( "#extension-Candle-manager-addon-settings" ).empty();
    
    $.getJSON( flask_base + "/extract/" + source_id, function( data ) {
        console.log(data);
        var items = [];
        
        // Generate explanation HTML
        if(data.explanation != undefined){
            $("#extension-Candle-manager-addon-settings-explanation").val(data.explanation);
            $("#extension-Candle-manager-addon-settings-explanation-container").show();
        }
        else{
            $("#extension-Candle-manager-addon-settings-explanation-container").hide();
        }
        
        item_counter = 0;
        // Generate Settings HTML
        if( data.settings.length > 0 ){
            $.each( data.settings, function( key, value ) {
                console.log("at item:" + key);
                if( key == 0){autofocus = "autofocus";}else{autofocus = "";}
                if( value.type == "checkbox" && value.value == 1 ){ checked = "checked"; }else{ checked = ""; }
                
                if( value.type == "hr" ){
                    items.push( "<br/><br/>");
                }
                else{
                    items.push( "<div class=\"extension-Candle-manager-addon-form-item\"><label for=\"item" + item_counter + "\">" + value.title + "</label><input type=" + value.type + " name=\"item" + item_counter + "\" data-settings-form-id=" + item_counter + " value=" + value.value +  " " + checked + " " + autofocus + "></div><p>" + value.comment + "</p>" );
                    item_counter++;
                }
            });
            
            $( "<form/>", {
                "id": "settings-form",
                "class":"form",
                html: items.join( "" )
            }).appendTo( "#extension-Candle-manager-addon-settings" );
        }
        else{
            $( "#extension-Candle-manager-addon-settings" ).append( "<p>There are no settings for you to change.</p>" );
        }
        
        // Finally, show the step to the user
        $("ol.extension-Candle-manager-addon-wizard.extension-Candle-manager-addon-numeric").wizard('nextStep');
        show_step(3);
    });

}



// This is called when the 'next' button on the settings step is pressed
function return_new_settings(){
    console.log("Sending new settings back for #" + source_id);
    
    // Grab new values from the form
    returnValues = [];
    $('#extension-Candle-manager-addon-settings-form :input').each(function(index){
        if( $(this).is(':checkbox') ){
            console.log("checkbox found");
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
        url: flask_base + "/generate_code/" + source_id,
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
                console.log("Python received the new settings and was able to generate new code");
                $("ol.extension-Candle-manager-addon-wizard.extension-Candle-manager-addon-numeric").wizard('nextStep');
                
                $('#extension-Candle-manager-addon-new-code').val(data.code);
                
                console.log("Added code to textarea");
                //$("#new-code").linedtextarea(
                //    {selectedLine: -1, selectedClass: 'lineselect'}
                //);
                
                $('#extension-Candle-manager-addon-code-container').removeClass('extension-Candle-manager-addon-hidden');
                show_step(4);
                check_libraries();
            }else{
                $('#extension-Candle-manager-addon-settings-errors').text("Unable to generate code from the settings you provided");
                $('#extension-Candle-manager-addon-settings-errors').show();
                console.log("Python was unable to integrate the desired settings into the code");
                $('#extension-Candle-manager-addon-step4 button.extension-Candle-manager-addon-show.extension-Candle-manager-addon-code, #extension-Candle-manager-addon-new_code').addClass('extension-Candle-manager-addon-hidden');
            }
        }
    });
}



function check_libraries(){
    console.log("Asking to check_libraries");
    
    $.getJSON( flask_base + "/check_libraries/" + source_id, function( data ) {
        console.log(data);
        
        if(data == null || data.message == undefined || data.success == undefined){
            lost_connection();
            return;
        }
        
        $("#extension-Candle-manager-addon-upload-status").text(data.message);
        
        // Generate explanation HTML
        if( data.success == false ){
            console.log("ERROR. Something went wrong during libraries check:");
            show_upload_errors(data.errors);
            $('#extension-Candle-manager-addon-libraries-progress').addClass('extension-Candle-manager-addon-progress_failed');
        }
        else{
            console.log("Checking libraries went ok");
            $('#extension-Candle-manager-addon-libraries-progress').addClass('extension-Candle-manager-addon-progress_complete');
            compile();
        }
    });
}



function compile(){
    console.log("Asking to start compilation");
    
    $.getJSON( flask_base + "/compile/" + source_id, function( data ) {
        console.log(data);
        
        if(data == null || data.message == undefined || data.success == undefined){
            lost_connection();
            return;
        }
        
        $("#extension-Candle-manager-addon-upload-status").text(data.message);
        
        // Generate explanation HTML
        if( data.success == false ){
            console.log("ERROR. Something went wrong during compiling:");
            $('#extension-Candle-manager-addon-compile-progress').addClass('extension-Candle-manager-addon-progress_failed');
            show_upload_errors(data.errors);
        }
        else{
            console.log("Compile went ok");
            $('#extension-Candle-manager-addon-compile-progress').addClass('extension-Candle-manager-addon-progress_complete');
            test_upload();
        }
    });
}



function test_upload(){
    console.log("Asking to do a test upload");

    $.ajax({
        url: flask_base + "/test_upload/" + source_id,
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
            
            $("#extension-Candle-manager-addon-upload-status").text(data.message);
            
            // Generate explanation HTML
            if( data.success == false ){
                console.log("ERROR. Something went wrong during the test upload.");
                $('#extension-Candle-manager-addon-test-progress').addClass('extension-Candle-manager-addon-progress_failed');
                show_upload_errors(data.errors);
            }
            else{
                console.log("Test went ok, waiting 20 seconds before starting final upload.");
                $('#extension-Candle-manager-addon-test-progress').addClass('extension-Candle-manager-addon-progress_complete');
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
        url: flask_base + "/upload/" + source_id,
        type: "POST",
        data: JSON.stringify(new_port_id),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
            console.log(data);
            
            if(data == null || data.message == undefined || data.success == undefined){
                lost_connection();
                return;
            }
            
            $("#extension-Candle-manager-addon-upload-status").text(data.message);
            
            // Generate explanation HTML
            if( data.success == false ){
                console.log("ERROR. Something went wrong during upload.");
                console.log(data.errors);
                $('#extension-Candle-manager-addon-upload-progress').addClass('extension-Candle-manager-addon-progress_failed');
                show_upload_errors(data.errors);
            }
            else{
                console.log("Upload went ok");
                $('#extension-Candle-manager-addon-upload-progress').addClass('extension-Candle-manager-addon-progress_complete');
                setTimeout(function(){
                    //Finally, show the last step to the user
                    $("ol.extension-Candle-manager-addon-wizard.extension-Candle-manager-addon-numeric").wizard('nextStep');
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
    
    $("#extension-Candle-manager-addon-upload-output").removeClass("extension-Candle-manager-addon-hidden");
    
    if(errors.length == 0){return;}
    
    $('#extension-Candle-manager-addon-errors-container').slideDown('slow');
    $.each( errors, function( key, value ) {
        //console.log("at item:" + key);
        items.push( "<li><span class=\"extension-Candle-manager-addon-error-number\">" + (key + 1) + "</span><span class=\"extension-Candle-manager-addon-error-text\">" +  value + "</span></li>" );
    });
    
    $( "<ul/>", {
        "id": "extension-Candle-manager-addon-errors-list",
        html: items.join( "" )
    }).appendTo( "#extension-Candle-manager-addon-errors-container" );
    
    $('button.extension-Candle-manager-addon-restart').removeClass('extension-Candle-manager-addon-hidden');
}



function lost_connection(){
    console.log("Returned data object was empty");
    $("#extension-Candle-manager-addon-upload-status").text("Lost connection to server");
    $("#extension-Candle-manager-addon-upload-output").removeClass('extension-Candle-manager-addon-hidden');
}



function show_serial_debug(){
    console.log("Showing serial debug");

    
    // Send the new values back to the server (the add-on)
    $.ajax({
        url: flask_base + "/serial_output",
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
            $('#extension-Candle-manager-addon-serial-output-container-spinner').remove();
            if( data.new_lines != undefined ){
                console.log("new serial lines: " + data.new_lines);
                //$('#serial-output-container').append(document.createTextNode(data.new_lines));
                $('#extension-Candle-manager-addon-serial-output-container').append(data.new_lines);
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
    
    $('#extension-Candle-manager-addon-serial-output-container').empty();
    
    // Send the new values back to the server (the add-on)
    $.ajax({
        url: flask_base + "/serial_close",
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
    


function close_tab(){
    $.get( flask_base + "/close_tab");
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