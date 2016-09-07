import sys
import time
import socket

SERVER_IP   = "192.168.150.1"
PORT_NUMBER = 12397
SIZE = 1024
print ("Test client sending packets to IP {0}, via port {1}\n".format(SERVER_IP, PORT_NUMBER))

mySocket = socket.socket()
mySocket.connect((SERVER_IP,PORT_NUMBER))

while True:
        msg = mySocket.recv(1024)
        print(msg)
        time.sleep(2)