import pickle
import socket
from collections import deque
import threading
import random
import time
import os
import sys
import platform
import datetime
import re

ipstr = "1. Add RFCs locally\n2. ADD RFCs to Server\n3. Lookup\n4. List"
rfc = list()
rfcsent = 0 # will keep counter of how many RFCs have been sent to the server and will only send those RFCs which have not been sent

class RFC():
	def __init__(self, rfcno, rfcdesc):
		self.rfcno = rfcno
		self.rfcdesc = rfcdesc

class myThread (threading.Thread):
	def __init__(self, opt, sock=None, client=None, addr=None, uphost=None, upport=None, option=None, msg=None):		
		threading.Thread.__init__(self)
		self.opt = opt
		self.option = option
		self.sock = sock
		self.uphost = uphost
		self.upport = upport
		self.client = client
		self.addr = addr
		self.msg = msg		
	
	def run(self):
		if(self.opt=="upload"):			
			while(True):				
				client,addr = self.sock.accept()
				print('*'*40)
				print(client)
				print(addr)
				print('*'*40) 
								
				thread = myThread("replytopeer", client=client,addr=addr)
				thread.start()
		else: # cmp(self.opt,"replytopeer")==0
			msg = self.client.recv(1024)
			msg = msg.decode('UTF-8')
			print()
			print('*'*20 + "Msg Start" + '*'*20)
			print(msg)
			print('*'*20 + "Msg End" + '*'*22)
			print()			
			lines = msg.split('\n')
			words = lines[0].split(' ')
			if(words[0]=="GET" and words[3]=="P2P-CI/1.0"):
				t = datetime.datetime.now()				
				try:					
					filename = '%s.txt' %words[2]
					f = open(filename, 'r')
					statbuf = os.stat(filename)	
					msg = "P2P-CI/1.0 200 OK\nDate: %s, %s %s %s %s\nOS: %s %s\nLast Modified: %s\nContent-Length: %s\nContent-Type: text/plain\n" \
					   %(t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name,statbuf.st_mtime,statbuf.st_size)
					msg+=f.read()												
				except IOError as e:
					msg = "P2P-CI/1.0 404 Not Found\nDate: %s, %s %s %s %s\nOS: %s %s\nLast Modified: %s\nContent-Length: %s\nContent-Type: text/plain\n" \
					   %(t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name,statbuf.st_mtime,statbuf.st_size)
					print("I/O error({0}): {1}".format(e.errno, e.strerror))
					msg+="File Not Found"
			elif words[0] != "GET":
				msg = "P2P-CI/1.0 400 Bad Request\nDate: %s, %s %s %s %s\nOS: %s %s" %(t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name)
			else: # If Version doesn't match
				msg = "P2P-CI/1.0 505 P2P-CI Version Not Supported\nDate: %s, %s %s %s %s\nOS: %s %s" %(t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name)
			self.client.send(bytes(msg))

class pseudoThread(): # Not a THREAD
	def __init__(self, opt, sock=None, client=None, addr=None, uphost=None, upport=None, option=None):
		self.opt = opt
		self.option = option
		self.sock = sock
		self.uphost = uphost
		self.upport = upport
		self.client = client
		self.addr = addr
	
	def start(self):
		if(self.opt=="server"): #connect to server			
			if(self.option==2):
				global rfcsent
				while(rfcsent != len(rfc)):					
					tmpmsg = "ADD RFC %s P2P-CI/1.0\nHost: %s\nPort: %s\nTitle: %s" %(rfc[rfcsent].rfcno,socket.gethostbyname(socket.gethostname()),self.upport,rfc[rfcsent].rfcdesc)					
					self.sock.send(bytes(tmpmsg))
					tmpmsg = self.sock.recv(1024)
					tmpmsg = tmpmsg.decode('UTF-8')
					print()
					print('*'*20 + "Msg Start" + '*'*20)
					print(tmpmsg)
					print('*'*20 + "Msg End" + '*'*22)
					print()
					rfcsent+=1					
			elif(self.option==3): # Lookup
				temprfcno = getinput("Enter RFC# to query to Server: ")
				temptitle = input("Enter the Title of the RFC: ")
				tmpmsg = "LOOKUP RFC %s P2P-CI/1.0\nHost: %s\nPort: %s\nTitle: %s" %(temprfcno,socket.gethostbyname(socket.gethostname()),self.upport,temptitle)
				#tmpmsg = "LOOKUP RFC %s P2P-CI/1.1\nHost: %s\nPort: %s\nTitle: %s" %(temprfcno,socket.gethostbyname(socket.gethostname()),self.upport,temptitle)
				#tmpmsg = "LOOK RFC %s P2P-CI/1.0\nHost: %s\nPort: %s\nTitle: %s" %(temprfcno,socket.gethostbyname(socket.gethostname()),self.upport,temptitle)
				self.sock.send(bytes(tmpmsg))
				print('*'*40)				
				msg=self.sock.recv(4096).rstrip()
				msg = msg.decode('UTF-8')
				print()
				print('*'*20 + "Msg Start" + '*'*20)
				print(msg)
				print('*'*20 + "Msg End" + '*'*22)
				print()
								
				lines = msg.split('\n')				
								
				for i in range(1,len(lines)):
					print(str(i) + " --> " + lines[i])
				print("0 --> Do Nothing")
				x = int(input("Select Option: "))
				if (x>=1 and x<len(lines)):
					getdata(lines[x])
			elif(self.option==4): # List
				tmpmsg = "LIST ALL P2P-CI/1.0\nHost: %s\nPort: %s\n" %(socket.gethostbyname(socket.gethostname()),self.upport)				
				self.sock.send(bytes(tmpmsg))
				msg=self.sock.recv(4096)				
				msg = msg.decode('UTF-8')
				msg = msg.rstrip()
				print()
				print('*'*20 + "Msg Start" + '*'*20)
				print(msg)
				print('*'*20 + "Msg End" + '*'*22)
				print()
				lines = msg.split('\n')								
				for i in range(1,len(lines)):
					print(str(i) + " --> " + lines[i])
				print("0 --> Do Nothing")
				x = int(input("Select Option: "))
				if (x>=1 and x<len(lines)):
					getdata(lines[x])

def main():
	uploadServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	uploadServerHost = socket.gethostbyname(socket.gethostname())
	uploadServerPort = random.randint(49152,65535)
	uploadServer.bind((uploadServerHost,uploadServerPort))
	uploadServer.listen(5)
	print("Listening on Host: %s & Port: %s" %(uploadServerHost,uploadServerPort))
	thread = myThread("upload", sock=uploadServer,uphost=uploadServerHost,upport=uploadServerPort)
	thread.start()

	host = "152.46.20.161"      # IP address of server
	port = 7734
	
	count = 0
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	while(True):	
		print(ipstr)
		try:
			option = int(input()) # input() gives integer and raw_input() gives string
			if(option==1):		
				rfcno = getinput("Enter RFC#: ")
				rfcdesc = input("Enter Title for RFC: ")
				rfcPresent = False
				for r in rfc:
					if r.rfcno == rfcno:						
						rfcPresent = True
						break
				if(rfcPresent):
					print("RFC already exists")
				else:
					rfc.append(RFC(rfcno,rfcdesc))
					f = open('%s.txt' %rfcno, 'w')
					f.write("rfc")
					f.close()
					print("RFC# %s having Title: \"%s\" added to the list. Total Count of RFCs: %s" %(rfc[len(rfc)-1].rfcno, rfc[len(rfc)-1].rfcdesc, len(rfc)))	
					#print ipstr
			elif(option>=2 and option <= 4):				
				pthread = pseudoThread("server", sock=s, uphost=uploadServerHost, upport=uploadServerPort, option=option)
				pthread.start()				
			else:
				print("Incorrect Option Entered")
				#print ipstr
		except ValueError:
			print("Invalid Characters Entered.")

def getinput(msg):
	try:
		return int(input(msg))
	except ValueError:
		print("Invalid Characters enterd")
		return getinput(msg)

def getdata(line):
	#print("Line: " + line)
	global ipstr
	words = line.split(" ")
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tport = int(words[3])
	trfcno = words[0] # used as string below
	msg = "GET RFC %s P2P-CI/1.0\nHost: %s\nOS: %s %s" %(words[0], words[2], platform.system(), os.name)
	s.connect((words[2], tport))	
	s.send(bytes(msg))
	msg = s.recv(1024)
	msg = msg.decode('UTF-8')
	print()
	print('*'*20 + "Msg Start" + '*'*20)
	print(msg)
	print('*'*20 + "Msg End" + '*'*22)
	print()	
	lines = msg.split('\n')
	words = lines[0].split(' ')
	if (words[1]=='200'): # (words[0]=='P2P-CI/1.0') and (words[1]=='200')
		try:
			f = open('%s_%s.txt' %(trfcno, str(tport)), 'w')
			for i in range(6,len(lines)):
				f.write(lines[i])
			f.close()
		except IOError as e:
			print("File Not Found")	

main()
