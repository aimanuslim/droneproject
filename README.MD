How drone.py works?
[Depex: RPi.GPIO, lib_nrf24.py, graphics.py]

Basically, drone.py has three main processes running in three threads:

1) GUI Handling (processGUI) running in the Main Thread
2) Gesture Handling (processGesture) running in 2nd Thread
3) Radio Handling (processRadio) running in 3rd Thread

There are three global variables shared between these threads:

1) menuElements		# represents boxes 0-8 in the GUI Window
2) boxSelected		# flags to represent if boxes 0-8 are selected (bool)
3) transmitSelection # flag to signal processRadio to transmit to receiver (bool)


Flow of script
	When drone.py runs, it launches the gestureThread and radioThread. Upon entering these threads, there is a 0.3s sleep to wait for processGui() in the main thread to finish initializing.

	Once setup is complete, these three threads will run in infinite while loop concurrently while listening to each other via the three global variables defined earlier

	Main Thread: processGui():
		Monitors the values of boxSelected and changes the color of the corresponding elements in menuElements via setFill()

	Second Thread (gestureThread): processGesture():
		Processes the gesture detected from user. 

		There will be three different gestures for different functionalities:
			a) 5 fingers = Navigate
			b) Fist/Grip/0 fingers = Select/Unselect individual rectangle and set corresponding boxSelected to True/False
			c)	Thumbs up = Finalize selection, set the transmitSelection flag to True

	Third Thread (radioThread): processRadio():
		Monitors the transmitSelection flag. If True, transmit the values of boxSelected to the receiver module on the other Rpi. 

		Values transmitted are in a list of 1 and 0. Upon successful transmission, the transmitSelection flag is set to False and the values in boxSelected are set to False to start a new round of selection.

		If false, the thread will sleep momentarily and re-run.



*******************************************************
*******************************************************

Login credentials for Rpi:

RPi I
Hostname: monday
Function: receiver
Static IP: 10.221.121.74
User: pi
Pass: popsicles

RPi II
Hostname: tuesday
Function: transmitter (OpenCV is installed on this)
Static IP: 10.221.121.72
User: pi
Pass: popsicles

The scripts are in ~/Documents/drone_[receiver,transmitter]. 