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

ipstr = "1. ADD RFCs to Server\n2. Lookup RFC from Server\n3. List all RFCs available in P2P system\n4. Exit"
rfclist = list()

class RFC():
	def __init__(self, rfcno, rfcdesc):
		self.rfcno = rfcno
		self.rfcdesc = rfcdesc

''' This thread handles the file upload for a sender peer'''
class uploadServerThread(threading.Thread):
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
				print("New request for file transfer:")
				print(data)
				print("Requesting client: "+str(clientAddr))
				print('*' * 40) 
								
				thread = uploadServerThread("replytopeer", msg=data,addr=clientAddr, mss=self.mss, n = self.n)
				thread.start()
		else:
			msg = self.msg.decode('UTF-8')
			lines = msg.split('\n')
			words = lines[0].split(' ')
			if(words[0] == "GET" and words[3] == "P2P-CI/1.0"):
				t = datetime.datetime.now()				
				try:					
					rfcTitle=""
					for r in rfclist:
						if r.rfcno==words[2]:
							rfcTitle = r.rfcdesc
					filename = 'RFC%s, %s.pdf' %(words[2],rfcTitle)
					f = open(filename, 'rb')
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
			print(ipstr)


''' This is a pseudoThread for handling all communication to the server'''
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
			rfcfileName = raw_input("Enter the file name of the RFC in the format RFCXXXX, Title.pdf\n")
			matchObj = re.match(r'RFC([0-9]*), ([^.]*)',rfcfileName)
			if(not matchObj):
				print("Filename not in proper format\n")
				return
			rfcno = matchObj.group(1)
			rfcdesc = matchObj.group(2)
			rfcPresent = False
			for r in rfclist:
				if r.rfcno == rfcno:						
					rfcPresent = True
					break
			if(rfcPresent):
				print("RFC already exists")
			else:
				print("Adding the newly received RFC file to Server:")
				addRFCtoServer(rfcno, rfcdesc, self.upport, self.sock)

		# 2 Lookup
		elif(self.option == 2):
			temprfcno = raw_input("Enter RFC# to query to Server:\n")
			temptitle = raw_input("Enter the Title of the RFC:\n")
			tmpmsg = "LOOKUP RFC %s P2P-CI/1.0\nHost: %s\nPort: %s\nTitle: %s" % (temprfcno,socket.gethostbyname(socket.gethostname()),self.upport,temptitle)
			self.sock.send(bytes(tmpmsg))
			print('*' * 40)				
			msg = self.sock.recv(4096).rstrip()
			msg = msg.decode('UTF-8')
			print()
			print("Server Response:")
			print('*' * 20 + "Msg Start" + '*' * 20)
			print(msg)
			print('*' * 20 + "Msg End" + '*' * 22)
			print()
								
			lines = msg.split('\n')				
								
			for i in range(1,len(lines)):
				print(str(i) + " --> " + lines[i])
			print("0 --> Do Nothing")
			x = int(input("Select Option: "))
			# Get the RFC file from the Server peer
			if (x >= 1 and x < len(lines)):
				if getdata(lines[x]):
					print("Adding the newly received RFC file to Server:")
					addRFCtoServer(temprfcno, temptitle, self.upport, self.sock)


		# 3. LIST
		elif(self.option == 3): 
			tmpmsg = "LIST ALL P2P-CI/1.0\nHost: %s\nPort: %s\n" % (socket.gethostbyname(socket.gethostname()),self.upport)				
			self.sock.send(bytes(tmpmsg))
			msg = self.sock.recv(4096)				
			msg = msg.decode('UTF-8')
			msg = msg.rstrip()
			print()
			print("Server Response:")
			print('*' * 20 + "Msg Start" + '*' * 20)
			print(msg)
			print('*' * 20 + "Msg End" + '*' * 22)
			print()
			lines = msg.split('\n')								
			for i in range(1,len(lines)):
				print(str(i) + " --> " + lines[i])
			print("0 --> Do Nothing")
			x = int(input("Select Option: "))
			# Get the RFC file from the Server peer
			if (x >= 1 and x < len(lines)):
				if getdata(lines[x]):
					words = lines[x].split(" ")
					rfcno = words[0]
					rfctitle = words[1]
					addRFCtoServer(rfcno, rfctitle, self.upport, self.sock)



def main():
	#Create an upload server for handling file uploads
	uploadServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	uploadServerHost = socket.gethostbyname(socket.gethostname())
	uploadServerPort = random.randint(49152,65535)
	uploadServer.bind((uploadServerHost,uploadServerPort))
	print("UploadServer Listening on Host: %s & Port: %s" % (uploadServerHost,uploadServerPort))

	serverhost =raw_input("Enter IP address of server to connect to\n")      # IP address of server
	serverport = 7734    

	MSS = int(raw_input("Enter the MSS value for the server peer\n"))
	N = int(raw_input("Enter the window size for the server peer\n"))
	thread = uploadServerThread("upload", sock=uploadServer,uphost=uploadServerHost,upport=uploadServerPort, mss=MSS, n=N)
	thread.start()

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((serverhost, serverport))
	while(True):	
		print(ipstr)
		try:
			option = int(input())
			if(option==1 or option==2 or option==3):
				pthread = pseudoThread(sock=s, uphost=uploadServerHost, upport=uploadServerPort, option=option)
				pthread.start()				
			elif(option==4):
				sys.exit(0)
			else:
				print("Incorrect Option Entered")
				print ipstr
		except ValueError:
			print("Invalid Characters Entered.")
			exit()

''' This method is used to get interger input from console'''
def getinput(msg):
	try:
		return int(input(msg))
	except ValueError:
		print("Invalid Characters enterd")
		return getinput(msg)


''' This method creates an HTTP request to add an RFC entry to Server'''
def addRFCtoServer(rfcno, rfcdesc, upport, soc):
    try:
	    f = open('RFC%s, %s.pdf' %(rfcno,rfcdesc), 'rb')
	    f.close()
	    rfclist.append(RFC(rfcno,rfcdesc))
	    tmpmsg = "ADD RFC %s P2P-CI/1.0\nHost: %s\nPort: %s\nTitle: %s" % (rfcno,socket.gethostbyname(socket.gethostname()),upport,rfcdesc)					
	    soc.send(bytes(tmpmsg))
	    tmpmsg = soc.recv(1024)
	    tmpmsg = tmpmsg.decode('UTF-8')
	    print()
	    print("Server response:")
	    print('*' * 20 + "Msg Start" + '*' * 20)
	    print(tmpmsg)
	    print('*' * 20 + "Msg End" + '*' * 22)
	    print()
    except:
        print("File not present on the system")


''' This method gets RFC from the sender peer in the P2P system'''
def getdata(line):
	P = float(raw_input("Enter the probability value for Probabilistic Loss Service\n"))
	words = line.split(" ")
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	tport = int(words[3])
	trfcno = words[0] # used as string below
	trfctitle = words[1]
	msg = "GET RFC %s P2P-CI/1.0\nHost: %s\nOS: %s %s" % (words[0], words[2], platform.system(), os.name)
	s.sendto(bytes(msg),(words[2], tport))
	msg = clientPeer_FTPReceiver.FTPReceiver(s, P)
	lines = msg.split('\n')
	words = lines[0].split(' ')
	if (words[1] == '200'): # (words[0]=='P2P-CI/1.0') and (words[1]=='200')
		try:
			f = open('RFC%s, %s.pdf' %(trfcno,trfctitle), 'wb')
			for i in range(6,len(lines)):
				f.write(lines[i] + "\n")
			f.close()
			return True


		except IOError as e:
			print("File Not Found")	
			return False
	return False




main()
