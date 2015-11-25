import socket
import sys
import signal
import util
import random


def FTPReceiver(s, p=0.05):
  global P
  # By default, P = 0.05
  P = p
  
  # Initialize the Sequence number
  lastSEQNO = -1
  max_seq_no = -1
  firstTime = True
  MSS = 0
  oldSEQNO = -1
  buffer=""

 
  while 1:
    packet = s.recvfrom(1100)
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
        buffer+=dataText
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
  s.close()
  return buffer

def signal_handler(signal, frame):
  print("\nCtrl+C detected! Exiting...")
  s.close()
  newFile.close()
  sys.exit(0)

if __name__ == "__main__":
   signal.signal(signal.SIGINT, signal_handler)
   main(sys.argv[1:])