import socket
import sys
import signal
import util
import random


SERVERNAME = '152.46.20.161'
PORT = 7735
MAX_SIZE = 1100

# Create a UDP socket
try:
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  print 'Socket created'
except socket.error, msg:
  print 'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
  sys.exit()

def main(argv):
  print argv
  global newFile
  global P

  # By default, P = 0.05, receive filename = 'rec.doc'
  P = 0.05
  filename = 'test.txt'

  

  # Connect to server 
  s.sendto('Initiate Connection',(SERVERNAME, PORT))
  newFile = open(filename, 'w+')

  # Initialize the Sequence number
  lastSEQNO = -1
  max_seq_no = -1
  firstTime = True
  MSS = 0
  oldSEQNO = -1

  # Listening to port
  while 1:
    packet = s.recvfrom(MAX_SIZE)
    data = packet[0]
    serverAddr = packet[1]

    if not data: 
      print "HEY"
      continue

    if firstTime:
      MSS = len(data) - 64
      firstTime = False

    # Simulate a random drop process
    randomNum = random.random()
    # print randomNum
    if randomNum <= P:
      if oldSEQNO != lastSEQNO:
        oldSEQNO = lastSEQNO
        print "Packet loss, sequence num = " + str((lastSEQNO + 1) * MSS)
      continue

    errno, seq_no, dataText = util.parseDatagram(data, 0) 
    # print "SEQ_NO:" + str(seq_no)
    # print "LAST_ACK:" + str(lastSEQNO)
    if seq_no > max_seq_no:
      max_seq_no = seq_no
    if errno == 0:
      if seq_no == lastSEQNO + 1:
        lastSEQNO = seq_no
        newFile.write(dataText)
      reply = util.buildHeader(lastSEQNO+1, '', 1)
      s.sendto(reply, serverAddr)
    elif errno == 1:
      print "Unmatched checksum, datagram is corrupted"
      break
    elif errno == 2:
      print "Unmatched indicator, datagram is corrupted"
      break
    else:
      if seq_no == lastSEQNO + 1:
        lastSEQNO = seq_no
      reply = util.buildHeader(lastSEQNO+1, '', 3)
      s.sendto(reply, serverAddr)
      if max_seq_no == lastSEQNO:
        print "Transfer finished!"
        print "SEQ_NO "+str((lastSEQNO+1)*MSS)+ " is sent!"
        break

  newFile.close()
  s.close()
  sys.exit(0)

def signal_handler(signal, frame):
  print("\nCtrl+C detected! Exiting...")
  s.close()
  newFile.close()
  sys.exit(0)

if __name__ == "__main__":
   signal.signal(signal.SIGINT, signal_handler)
   main(sys.argv[1:])