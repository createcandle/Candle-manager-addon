# Candle-manager-addon
An add-on for the Mozilla WebThings Gateway. It allows you to upload code to Arduino's with the click of a button.

![Candle manager start screen](https://github.com/createcandle/Candle-manager-addon/blob/master/candle_manager_screenshot.png?raw=true)


0. Install the add-on and reload the webpage.
1. Open the Candle Manager from the menu.
2. Plug in your Arduino via USB when asked to do so.
3. Select which sketch you want to upload from the list. You can add your own sketches.
4. Optional: change settings of your sketch if you want.
5. Click 'next' and wait for the upload process to complete.
6. You can now see and check the serial output from your new Arduino device.
7. Done


## Adding your own sketches

Open the settings page of the add-on and paste a link to your .ino file into the link field. Click 'apply'.

Your sketch has now been added.

You can also add multiple sketches by creating a JSON file with URL's to those sketches. Check ouf the example here:
https://github.com/createcandle/candle_source_code_list
