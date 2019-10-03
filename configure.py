#!/usr/bin/python
import time
from socket import *
import sys

def waitFor(msg,answer=None):
    print "Waiting for %s"%(msg.strip())
    while True:
        reply = s.recvfrom(1024)
        if reply[0]==msg:
            if answer != None:
                send(answer)
            return
def send(msg):
    s.sendto(msg,m[1])

def read():
    while True:
        reply = s.recvfrom(1024)
        print reply

s=socket(AF_INET, SOCK_DGRAM)
s.bind(('',48899))
print("Wait for broadcast from app")
m=s.recvfrom(1024)
printr(m)

SSID="YOUR-SSID"
BSSID="YOUR BSSID" #i.e. the WIFI MAC of the AP
PASSWORD="YOUR WIFI Password" 
IP="your IP" # ip where ghoma2mqtt will run later? Or current local IP? Or IP of Device?

print("Step 2: sending 10.10.100.254,ACCF23D78A6C,HF-LPB100 to app")
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.sendto('%s,ACCF23D78A6C,HF-LPB100'%(IP),m[1])
waitFor("+ok")
waitFor("AT+WSCAN\r","+ok=\rCh,SSID,BSSID,Security,Indicator\r")
send('1,%s,%s,WPA2PSK/AES,88\r\n\r\n'%(SSID,BSSID))
send('\n')
waitFor('AT+WSSSID=%s\r'%SSID,'+ok=%s\r\n\r\n'%(SSID))
waitFor('AT+WSKEY=wpa2psk,aes,%s\r'%(PASSWORD),'+ok=wpa2psk,aes,%s\r\n\r\n'%(PASSWORD))
read()


