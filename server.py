import socket
import sys
import time

mySocket = socket.socket()
host = socket.gethostname()
port = 12397
size = 1024

mySocket.bind(('',port))
mySocket.listen(5)
print ("Test server listening on port {0}\n".format(port))
data,addr = mySocket.accept()

while True:
        print("Got connection from {}".format(addr))
	data.send("Message from server")
	time.sleep(2)
