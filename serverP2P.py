import socket
import threading
import re

lock = threading.Lock()
peerlist = list()
rfc = list()

def displayPeer():
	for p in peerlist:
		print("P: %s %s" %(p.host,p.port))

def displayRFC():
	for r in rfc:
		for hp in r.hostportlist:
			print("R: %s %s %s %s" %(r.rfcno,r.title,hp.host,hp.port))

class Peers():
	def __init__(self,host,port):
		self.host = host
		self.port = port

	@staticmethod
	def addPeer(host,port):
		for p in peerlist:
			if p.host == host and p.port == port:				
				return
		peerlist.append(Peers(host,port))

class RFC():
	def __init__(self,rfcno,title,host,port):
		self.rfcno = rfcno
		self.title = title
		self.hostportlist = list()
		self.hostportlist.append(Peers(host,port))
	
	@staticmethod
	def addRFC(rfcno,title,host,port):
		for r in rfc:
			if r.rfcno == rfcno:
				for hp in r.hostportlist:
					if hp.host == host and hp.port == port:
						return				
				r.hostportlist.append(Peers(host,port))
				return
		rfc.append(RFC(rfcno,title,host,port))
	
	@staticmethod	
	def remRFC(host, port):		#l[:] = [tl for tl in l if tl>16]
		for r in rfc:
			r.hostportlist[:] = [hp for hp in r.hostportlist if hp.host!=host or hp.port!=port]          


class myThread (threading.Thread):
	def __init__(self, client, addr):
		threading.Thread.__init__(self)
		self.client = client 
		self.addr = addr 
		
	
	def run(self):		
		host =""
		port = ""
		while True:
			try:
				msg = self.client.recv(1024)				
				msg = msg.decode('UTF-8')				
				line = msg.split('\n')

				
				word = line[0].split(' ')                                        
				host = line[1].split(' ')[1]			
				port = line[2].split(' ')[1]  

				
				if(word[0]=='ADD'):
					if(word[3] == 'P2P-CI/1.0'):
						rfcno = word[2]					
						''' use of RegEx to get spaced title'''
						title = re.split(' ', line[3], 1)[1]
						lock.acquire()
						Peers.addPeer(host,port) # adds only if the peer is not already present						
						RFC.addRFC(rfcno,title,host,port)
						lock.release()
						tmpmsg = "P2P-CI/1.0 200 OK\nRFC %s %s %s %s" %(rfcno,title,host,port)
						self.client.send(bytes(tmpmsg))
					else:
						tmpmsg = "P2P-CI/1.0 505 P2P-CI Version Not Supported"
						self.client.send(bytes(tmpmsg))
				elif(word[0]=='LOOKUP'):
					if(word[3] == 'P2P-CI/1.0'):
						rfcno = word[2]
						title = re.split(' ', line[3], 1)[1]
						flag = False
						tempmsg = ""
						lock.acquire()
						for r in rfc:
							if r.rfcno == rfcno and r.title == title:
								flag = True
								for hp in r.hostportlist:
									tempmsg += ("%s %s %s %s\n" %(r.rfcno,r.title,hp.host,hp.port))
						lock.release()
						tempmsg.strip()
						if flag:
							tmpmsg = "P2P-CI/1.0 200 OK\n%s" %tempmsg
							self.client.send(bytes(tmpmsg))
						else:
							tmpmsg = "P2P-CI/1.0 404 Not Found\n"
							self.client.send(bytes(tmpmsg))
					else:
						tmpmsg = "P2P-CI/1.0 505 P2P-CI Version Not Supported"
						self.client.send(bytes(tmpmsg))
				elif(word[0]=='LIST'):
					if(word[2] == 'P2P-CI/1.0'):
						tempmsg = ""
						lock.acquire()
						for r in rfc:
							for hp in r.hostportlist:
								tempmsg += ("%s %s %s %s\n" %(r.rfcno,r.title,hp.host,hp.port))
						lock.release()						
						tempmsg.strip()
						tmpmsg = "P2P-CI/1.0 200 OK\n%s" %tempmsg						
						self.client.send(bytes(tmpmsg))
					else:
						tmpmsg = "P2P-CI/1.0 505 P2P-CI Version Not Supported"
						self.client.send(bytes(tmpmsg))
				else: # 400 Bad Request
					tmpmsg = "P2P-CI/1.0 400 Bad Request"
					self.client.send(bytes(tmpmsg))				
			except Exception as e:
				print("Error %s" %e)
				print(self.addr[0] + "  Client ends connection  " + str(self.addr[1]))
				print(host + "  Client's Upload Server also goes down  " + port)
				RFC.remRFC(host, port)				
				self.client.close()
				break
			
def main():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print(s)
	host = socket.gethostbyname(socket.gethostname())
	print "Server IP address is "+host
	port = 7734
	s.bind((host, port))
	prev = []
	s.listen(5)             # parameter is the max number of server backlog connections
	conn = 0
	while True:
		conn+=1
		client, addr = s.accept()
		print()
		print('*'*20 + "Msg Start" + '*'*20)
		print(client)
		print(addr)
		print('*'*20 + "Msg End" + '*'*22)
		print()
		thread = myThread(client, addr)
		thread.start()		
	
main()
