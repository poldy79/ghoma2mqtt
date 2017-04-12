#!/usr/bin/python
import SocketServer
import time
import socket
import mosquitto

def printHex(my_hex):
    if type(my_hex)==str:
        print " ".join(hex(ord(n)) for n in my_hex)
    if type(my_hex)==list:
        result = []
        for i in my_hex:
            result.append("0x%1x"%(i))
        print ",".join(result)
        
class InvalidMsg():
    def __init__(self,err):
        self.err = err
        pass

class GhomaMsgEncode():
    def __init__(self,cmd,payload,mode=0):
        self.msg = "\x5a\xa5"
        self.msg+=chr(mode)
        self.msg+=chr(len(payload)+1)
        self.msg+=chr(cmd)
        checksum = 0xff-cmd
        for i in payload:
            self.msg+=chr(i)
            checksum-=i
            if checksum <0:
                checksum+=256
        self.msg+=chr(checksum)
        self.msg+="\x5b\xb5"
        
        
class GhomaMsgDecode():
    def __init__(self,msg):
        if not msg.startswith("\x5a\xa5"):
            raise InvalidMsg("Invialid prefix")
            
        self.mode = ord(msg[2])
        self.length = ord(msg[3])-1
        self.cmd = ord(msg[4])
        self.payload = []
        checksum = 0xff-self.cmd
        for i in range(self.length):
            self.payload.append(ord(msg[5+i]))
            checksum-=ord(msg[5+i])
            if checksum < 0:
                checksum+=256
        #self.payload = msg[5:-3]
        if not checksum == ord(msg[5+self.length]):
            raise InvalidMsg("Invalid checksum")
        if not msg[6+self.length:].startswith("\x5b\xb5"):
            printHex(msg)
            raise InvalidMsg("Invalid postfix")
        self.next = msg[8+self.length:] 


class ThreadedEchoRequestHandler(
        SocketServer.BaseRequestHandler,
        
):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def publishState(self):
        t = "ghoma/%s/state"%(self.mac)
        print "Publish %s:%s"%(t,self.state)
        self.client.publish(t, self.state)
        self.client.publish("ghoma",self.mac)
        
    def handle(self):
        def on_message(client, userdata, msg):
            if msg.payload == "1":
                self.request.sendall(GhomaMsgEncode(cmd=0x10,payload=[0x01,01,0x0a,0xe0,0x32,0x23,0xd7,0x8a,0x6c,0xff,0xfe,0x00,0x00,0x10,0x11,0x00,0x00,0x01,0x00,0x00,0x00,0xff]).msg)
            elif msg.payload == "0":
                self.request.sendall(GhomaMsgEncode(cmd=0x10,payload=[0x01,01,0x0a,0xe0,0x32,0x23,0xd7,0x8a,0x6c,0xff,0xfe,0x00,0x00,0x10,0x11,0x00,0x00,0x01,0x00,0x00,0x00,0x00]).msg)
        
        def on_connect(client, userdata, flags):
            #client.subscribe("ghoma/ac:cf:23:d7:8a:6c/set")
            print "Connected to broker"
        
        self.mac = "00:00:00:00:00:00"
        self.state = "unknown"
        
        self.client = mosquitto.Mosquitto()
        self.client.connect(host="localhost",port=1883)
        self.client.on_message = on_message
        self.client.on_connect = on_connect
        self.client.loop_start()

        print "Sending Init 1 Part 1"
        self.request.sendall(GhomaMsgEncode(cmd=2,payload=[0x0a,0x11,0x01,0x03,0x0f,0x0c]).msg)
        print "Sending Init 1 Part 2"
        self.request.sendall(GhomaMsgEncode(cmd=2,payload=[]).msg)
        print "Sending Init 2"
        self.request.sendall(GhomaMsgEncode(cmd=5,payload=[0x01]).msg)
        alive = time.time()
        while True:
            try:
                self.data = self.request.recv(1024)
            except:
                return
            if len(self.data) == 0:
                time.sleep(.1)
                if time.time() - alive > 30:
                    print "Timeout exceeded"
                    return
                continue
            while not self.data == "":
                msg = GhomaMsgDecode(self.data)

                if msg.cmd == 0x03 and msg.payload==[0x01,0x0a,0xc0,0x32,0x23,0xd7,0x8a,0x6c,0x01,0x00]:
                    print "Received Init 1 reply"
                    print "Sending Init 2"
                    self.request.sendall(GhomaMsgEncode(cmd=0x05,payload=[0x01]).msg)
                elif msg.cmd == 0x04 and msg.payload==[0x01,0x0a,0xc0,0x32,0x23,0xd7,0x8a,0x6c]:
                    print "Received Alive"
                    self.request.sendall(GhomaMsgEncode(cmd=0x06,mode=1,payload=[]).msg)
                    self.publishState()

                elif msg.cmd==0x07 and msg.payload==[0x01,0x0a,0xc0,0x32,0x23,0xd7,0x8a,0x6c,0x00,0x01,0x06,0xac,0xcf,0x23,0xd7,0x8a,0x6c]:
                    #last 6 bytes are the MAC [0xac,0xcf,0x23,0xd7,0x8a,0x6c]
                    self.mac= ":".join("%02x"%(n) for n in msg.payload[-6:])
                    print "Recieved Init 2 part 1 reply"
                    self.publishState()
                    self.client.subscribe("ghoma/%s/set"%(self.mac))
                elif msg.cmd==0x07 and msg.payload==[0x01,0x0a,0xc0,0x32,0x23,0xd7,0x8a,0x6c,0x00,0x02,0x05,0x00,0x01,0x01,0x08,0x1a,0xe0,0x5b,0xb5,0x5a,0xa5,0x0,0x15,0x90,0x1,0xa,0xe0,0x32,0x23,0xd7,0x8a,0x6c,0xff,0xfe,0x1,0x81,0x11,0x0,0x0,0x1,0x0,0x0,0x0,0x0]:
                    print "Received known sequence with cmd id 7 during initialize"
                    printHex(msg.payload)
                elif msg.cmd==0x07 and msg.payload==[0x01,0x0a,0xc0,0x32,0x23,0xd7,0x8a,0x6c,0x00,0x02,0x05,0x00,0x01,0x08,0x1a]:
                    print "Received Init 2 part 2 reply"
                elif msg.cmd==0x07 and msg.payload==[0x01,0x0a,0xc0,0x8,0x32,0x13,0xd7,0x8a,0x6c,0x00,0x00,0x00,0x1f]:
                    print "Received known sequence with cmd id 7 during initialize"
                    printHex(msg.payload)
                elif msg.cmd==0x07 and msg.payload==[0x1,0xa,0xc0,0x32,0x23,0xd7,0x8a,0x6c,0x0,0x2,0x5,0x0,0x1,0x1,0x8,0x1a]:
                    print "Received known sequence with cmd id 7 during initialize"
                    printHex(msg.payload)
                                   
                elif msg.cmd==0x90:
                         
                    if   msg.payload==[0x01,0x0a,0xe0,0x32,0x23,0xd7,0x8a,0x6c,0xff,0xfe,0x01,0x81,0x11,0x00,0x00,0x01,0x00,0x00,0x00,0x00]:
                        print "Someone pressed the switch from on->off"
                        self.state = "0"
                        self.publishState()
                    elif msg.payload==[0x01,0x0a,0xe0,0x32,0x23,0xd7,0x8a,0x6c,0xff,0xfe,0x01,0x81,0x11,0x00,0x00,0x01,0x00,0x00,0x00,0xff]:
                        print "Someone pressed the switch from off->on"
                        self.state = "1"
                        self.publishState()
                    elif msg.payload==[0x01,0x0a,0xe0,0x32,0x23,0xd7,0x8a,0x6c,0xff,0xfe,0x01,0x11,0x11,0x00,0x00,0x01,0x00,0x00,0x00,0x00]:
                        print "Switch AUS confirmed"
                        self.state = "0"
                        self.publishState()
                    elif msg.payload==[0x01,0x0a,0xe0,0x32,0x23,0xd7,0x8a,0x6c,0xff,0xfe,0x01,0x11,0x11,0x00,0x00,0x01,0x00,0x00,0x00,0xff]:
                        print "Switch EIN confirmed"
                        self.state = "1"
                        self.publishState()
                    else:
                        print "Unknown Payload with cmd 0x90"
                
                elif msg.cmd==0xfe and msg.payload==[0x01,0xa,0xc0,0x32,0x23,0xd7,0x8a,0x6c,0x00,0x00,0x00,0x1f]:
                    print "Received cmd 254 - propably something went wrong"
                    printHex(msg.payload)
                else:
                    print "Received unknown data with cmd id %i"%(msg.cmd)
                    printHex(msg.payload)
                    
                    #printHex(self.data[2:-3])
                self.data = msg.next
            alive = time.time()
        return 
    
    
class ThreadedEchoServer(SocketServer.ThreadingMixIn,
                         SocketServer.TCPServer,
                         ):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
    pass


if __name__ == "__main__":
    HOST, PORT = "", 4196

    while True:
        try:
            server = ThreadedEchoServer((HOST, PORT),ThreadedEchoRequestHandler)
            print "Server started!"
            break
        except:
            print "Port still busy..."
            time.sleep(1)
            pass
    
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
