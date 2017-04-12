#!/usr/bin/python
import socket,time

def send(data):
    print "Sending ",
    printHex(data)
    s.sendall(buffer(bytearray(data)))
    time.sleep(.1)

def printHex(my_hex):
    print " ".join(hex(ord(n)) for n in my_hex)

s = socket.create_connection(('127.0.0.1', 4196))
data = ""
while True:
    tmp = s.recv(1000)
    if len(tmp) == 0:
        time.sleep(.1)
        continue
        
    data += tmp 
    printHex(data)
    if data == "\x5a\0xa5\x00\x07\x02\x0a\x11\x01\x03\x0f\x0c\xc3\x5b\xb5":
        print "Received Init 1 part 1"
        data = ""
    elif data == "\x5a\xa5\x00\x01\x02\xfd\x5b\xb5":
        print "Received Init 1 part 2"
        send("\x5a\xa5\x00\x0b\x03\x01\x0a\xc0\x32\x23\xd7\x8a\x6c\x01\x00\x0e\x5b\xb5")
        data = ""        
    elif data == "\x5a\xa5\x00\x02\x05\x01\xf9\x5b\xb5":
        print "Received Init 2"
        data = ""
        send("\x5a\xa5\x00\x12\x07\x01\x0a\xc0\x32\x23\xd7\x8a\x6c\x00\x01\x06\xac\xcf\x23\xd7\x8a\x6c\x99\x5b\xb5")
        send("\x5a\xa5\x00\x11\x07\x01\x0a\xc0\x32\x23\xd7\x8a\x6c\x00\x02\x05\x00\x01\x01\x08\x1a\xe0\x5b\xb5")
        send("\x5a\xa5\x00\x15\x90\x01\x0a\xe0\x32\x23\xd7\x8a\x6c\xff\xfe\x01\x81\x11\x00\x00\x01\x00\x00\x00\x00\xd1\x5b\xb5")
        print "Finished Startup"  
        break      
    else:
        print "unknown data"
        print len(data)

while True:
    
    

    
    
    print "Sending alive to server"
    send("\x5a\xa5\x00\x09\x04\x01\x0a\xc0\x32\x23\xd7\x8a\x6c\x0e\x5b\xb5")
    time.sleep(.5)
    data = s.recv(1000)
    printHex(data)
    time.sleep(4.5)
    
    
s.close()
