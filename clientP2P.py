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
import serverPeer_FTPSender
import clientPeer_FTPReceiver

ipstr = "1. ADD RFCs to Server\n2. Lookup\n3. List"
rfc = list()

class RFC():
	def __init__(self, rfcno, rfcdesc):
		self.rfcno = rfcno
		self.rfcdesc = rfcdesc

class myThread(threading.Thread):
	def __init__(self, opt, sock=None, client=None, addr=None, uphost=None, upport=None, option=None, msg=None, mss = 1000, n=10):		
		threading.Thread.__init__(self)
		self.opt = opt
		self.option = option
		self.sock = sock
		self.uphost = uphost
		self.upport = upport
		self.client = client
		self.addr = addr
		self.msg = msg		
		self.mss = mss
		self.n = n
	def run(self):
		if(self.opt == "upload"):			
			while(True):				
				data, clientAddr = self.sock.recvfrom(1024)
				print('*' * 40)
				print(data)
				print(clientAddr)
				print('*' * 40) 
								
				thread = myThread("replytopeer", msg=data,addr=clientAddr, mss=self.mss, n = self.n)
				thread.start()
		else: # cmp(self.opt,"replytopeer")==0
			#msg = self.client.recv(1024)
			msg = self.msg.decode('UTF-8')
			print()
			print('*' * 20 + "Msg Start" + '*' * 20)
			print(msg)
			print('*' * 20 + "Msg End" + '*' * 22)
			print()			
			lines = msg.split('\n')
			words = lines[0].split(' ')
			if(words[0] == "GET" and words[3] == "P2P-CI/1.0"):
				t = datetime.datetime.now()				
				try:					
					filename = '%s.txt' % words[2]
					f = open(filename, 'r')
					statbuf = os.stat(filename)	
					msg = "P2P-CI/1.0 200 OK\nDate: %s, %s %s %s %s\nOS: %s %s\nLast Modified: %s\nContent-Length: %s\nContent-Type: text/plain\n" \
					   % (t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name,statbuf.st_mtime,statbuf.st_size)
					msg+=f.read()												
				except IOError as e:
					msg = "P2P-CI/1.0 404 Not Found\nDate: %s, %s %s %s %s\nOS: %s %s\nLast Modified: %s\nContent-Length: %s\nContent-Type: text/plain\n" \
					   % (t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name,statbuf.st_mtime,statbuf.st_size)
					print("I/O error({0}): {1}".format(e.errno, e.strerror))
					msg+="File Not Found"
			elif words[0] != "GET":
				msg = "P2P-CI/1.0 400 Bad Request\nDate: %s, %s %s %s %s\nOS: %s %s" % (t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name)
			else: # If Version doesn't match
				msg = "P2P-CI/1.0 505 P2P-CI Version Not Supported\nDate: %s, %s %s %s %s\nOS: %s %s" % (t.strftime("%a"),t.strftime("%d"),t.strftime("%b"),t.strftime("%Y"),t.strftime("%H:%M:%S"),platform.system(),os.name)
			serverPeer_FTPSender.FTPsender(self.addr, bytes(msg), self.mss, self.n)



class pseudoThread(): # Not a THREAD
	def __init__(self, sock=None, client=None, addr=None, uphost=None, upport=None, option=None):
		self.option = option
		self.sock = sock
		self.uphost = uphost
		self.upport = upport
		self.client = client
		self.addr = addr


	def start(self):
		# 1 ADD RFCs to Server
		if(self.option == 1):		
			rfcno = raw_input("Enter RFC#: ")
			rfcdesc = raw_input("Enter Title for RFC: ")
			rfcPresent = False
			for r in rfc:
				if r.rfcno == rfcno:						
					rfcPresent = True
					break
			if(rfcPresent):
				print("RFC already exists")
			else:
				addRFCtoServer(rfcno, rfcdesc, self.upport, self.sock)

		# 2 Lookup
		elif(self.option == 2):
			temprfcno = raw_input("Enter RFC# to query to Server: ")
			temptitle = raw_input("Enter the Title of the RFC: ")
			tmpmsg = "LOOKUP RFC %s P2P-CI/1.0\nHost: %s\nPort: %s\nTitle: %s" % (temprfcno,socket.gethostbyname(socket.gethostname()),self.upport,temptitle)
			self.sock.send(bytes(tmpmsg))
			print('*' * 40)				
			msg = self.sock.recv(4096).rstrip()
			msg = msg.decode('UTF-8')
			print()
			print('*' * 20 + "Msg Start" + '*' * 20)
			print(msg)
			print('*' * 20 + "Msg End" + '*' * 22)
			print()
								
			lines = msg.split('\n')				
								
			for i in range(1,len(lines)):
				print(str(i) + " --> " + lines[i])
			print("0 --> Do Nothing")
			x = int(input("Select Option: "))
			if (x >= 1 and x < len(lines)):
				if getdata(lines[x]):
					addRFCtoServer(temprfcno, temptitle, self.upport, self.sock)


		# 3. LIST
		elif(self.option == 3): 
			tmpmsg = "LIST ALL P2P-CI/1.0\nHost: %s\nPort: %s\n" % (socket.gethostbyname(socket.gethostname()),self.upport)				
			self.sock.send(bytes(tmpmsg))
			msg = self.sock.recv(4096)				
			msg = msg.decode('UTF-8')
			msg = msg.rstrip()
			print()
			print('*' * 20 + "Msg Start" + '*' * 20)
			print(msg)
			print('*' * 20 + "Msg End" + '*' * 22)
			print()
			lines = msg.split('\n')								
			for i in range(1,len(lines)):
				print(str(i) + " --> " + lines[i])
			print("0 --> Do Nothing")
			x = int(input("Select Option: "))
			if (x >= 1 and x < len(lines)):
				if getdata(lines[x]):
					words = lines[x].split(" ")
					rfcno = words[0]
					rfctitle = words[1]
					addRFCtoServer(rfcno, rfctitle, self.upport, self.sock)

def main():
	uploadServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	uploadServerHost = socket.gethostbyname(socket.gethostname())
	uploadServerPort = random.randint(49152,65535)
	uploadServer.bind((uploadServerHost,uploadServerPort))
	print("Listening on Host: %s & Port: %s" % (uploadServerHost,uploadServerPort))
	MSS = int(raw_input("Enter the MSS value for the server peer"))
	N = int(raw_input("Enter the window size for the server peer"))
	thread = myThread("upload", sock=uploadServer,uphost=uploadServerHost,upport=uploadServerPort, mss=MSS, n=N)
	thread.start()

	host =raw_input("Enter IP address of server to connect to")      # IP address of server
	port = 7734
	
	count = 0
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	while(True):	
		print(ipstr)
		try:
			option = int(input()) # input() gives integer and raw_input() gives string
			if(option==1 or option==2 or option==3):
				pthread = pseudoThread(sock=s, uphost=uploadServerHost, upport=uploadServerPort, option=option)
				pthread.start()				
			else:
				print("Incorrect Option Entered")
				print ipstr
		except ValueError:
			print("Invalid Characters Entered.")

def getinput(msg):
	try:
		return int(input(msg))
	except ValueError:
		print("Invalid Characters enterd")
		return getinput(msg)

def addRFCtoServer(rfcno, rfcdesc, upport, soc):
	f = open('%s.txt' % rfcno, 'r')
	f.close()
	rfc.append(RFC(rfcno,rfcdesc))
	tmpmsg = "ADD RFC %s P2P-CI/1.0\nHost: %s\nPort: %s\nTitle: %s" % (rfcno,socket.gethostbyname(socket.gethostname()),upport,rfcdesc)					
	soc.send(bytes(tmpmsg))
	tmpmsg = soc.recv(1024)
	tmpmsg = tmpmsg.decode('UTF-8')
	print()
	print('*' * 20 + "Msg Start" + '*' * 20)
	print(tmpmsg)
	print('*' * 20 + "Msg End" + '*' * 22)
	print()

def getdata(line):
	P = float(raw_input("Enter the probability value for Probabilistic Loss Service"))
	words = line.split(" ")
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	tport = int(words[3])
	trfcno = words[0] # used as string below
	msg = "GET RFC %s P2P-CI/1.0\nHost: %s\nOS: %s %s" % (words[0], words[2], platform.system(), os.name)
	s.sendto(bytes(msg),(words[2], tport))
	msg = clientPeer_FTPReceiver.FTPReceiver(s, P)
	msg = msg.decode('UTF-8')
	lines = msg.split('\n')
	words = lines[0].split(' ')
	if (words[1] == '200'): # (words[0]=='P2P-CI/1.0') and (words[1]=='200')
		try:
			f = open('%s.txt' % trfcno, 'w')
			for i in range(6,len(lines)):
				f.write(lines[i] + "\n")
			f.close()
			return True


		except IOError as e:
			print("File Not Found")	
			return False
	return False

main()
