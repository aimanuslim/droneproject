import sys
import time
import socket

SERVER_IP   = "192.168.150.1"
#SERVER_IP = "192.168.10.124"
PORT_NUMBER = 11850
SIZE = 1024
print ("Test client sending packets to IP {0}, via port {1}\n".format(SERVER_IP, PORT_NUMBER))

mySocket = socket.socket()

while True:
	try:
		print("Trying")
		mySocket.connect((SERVER_IP,PORT_NUMBER))
	except:
		print("Server not started yet. Sleeping....")
		time.sleep(5)
		continue

	print("Connected to server!")
	break


while True:
        msg = mySocket.recv(1024)
        print(msg)
        time.sleep(2)
