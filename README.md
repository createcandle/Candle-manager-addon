# Candle manager addon
An add-on for the Candle Controller / WebThings Gateway. It allows you to upload code to Arduino's with the click of a button.

An overview of available devies can be found on the Candle website under "research":

https://www.candlesmarthome.com/

![Candle manager start screen](https://github.com/createcandle/Candle-manager-addon/blob/master/candle_manager_screenshot.png?raw=true)


0. Install the add-on using the Candle store.
1. Select the Candle Manager in the main menu.
2. Plug in your Arduino via USB when asked to do so.
3. Select which sketch you want to upload from the list. You can add your own sketches. You should create the Candle Receiver first.
4. Optional: change settings of the sketch if you want.
5. Click 'next' and wait for the upload process to complete.
6. You can now see and check the serial output from your new Arduino device.
7. Once you have created the Candle receiver, keep it plugged in and install/start the MySensors addons. That will enable wireless communication with the devices you create after that.
8. Done



## Adding your own sketches

Open the settings page of the add-on and paste a link to your .ino file into the link field. Click 'apply'.

Your sketch has now been added.

You can also add multiple sketches by creating a JSON file with URL's to those sketches. Check ouf the example here:
https://github.com/createcandle/candle_source_code_list
