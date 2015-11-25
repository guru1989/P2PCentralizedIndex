import socket
import sys
import signal
import util
import threading
import time

def prepareDatagram(seq_no, data):
  startIndex = seq_no * MSS
  content = data[startIndex:startIndex+MSS]
  
  if not content: return None

  # print "seq_no: " + str(seq_no)
  hdr = util.buildHeader(seq_no, content, 0)
  return hdr + content


def receiver():
  # receive data from server (data, addr)
  global LASTACK
  global EXIT_THREAD
  global SEND_BUF
  global SEND_BUF_SEQ
  global TIMER
  global EXPIRED
  recv_buf = []
  toDisplay = -1
  time.sleep(0.01)
  while EXIT_THREAD != 1:
    try:
      d = s.recvfrom(64)
      recv_buf.append(d)
      # print "Receiving.."
    except:
      # print "error here"
      pass

    for datagram in recv_buf:
      errno, seq_no = util.parseDatagram(datagram[0], 1)
      if errno == 0:
        if len(SEND_BUF_SEQ) > 0 and (seq_no >= SEND_BUF_SEQ[0]):
          # print "ACK #" + str(seq_no)
          # print SEND_BUF_SEQ
          diff = seq_no - SEND_BUF_SEQ[0]
          THREAD_LOCK.acquire()
          for tc in range(diff):
            SEND_BUF.pop(0)
            SEND_BUF_SEQ.pop(0)
          THREAD_LOCK.release()
          recv_buf.pop(0)
          TIMER.cancel()
          # TIMER.join()
          THREAD_LOCK.acquire()
          EXPIRED = 0
          TIMER = threading.Timer(TIMER_SET, timerHandler)
          TIMER.start()
          THREAD_LOCK.release()
        LASTACK = seq_no - 1
      elif errno == 1:
        print "Unmatched checksum, datagram is corrupted"
      elif errno == 2:
        print "Unmatched indicator, datagram is corrupted"

def timerHandler():
  global EXPIRED
  EXPIRED = 1

def rdt_send(clientAddr, data):
  global TO_SEND_SEQ
  global SEND_BUF
  global SEND_BUF_SEQ
  global TIMER
  global EXPIRED
  TIMER = threading.Timer(TIMER_SET, timerHandler)
  TIMER.start()
  print 'TIMER should start'
  endSignal = 1
  checkpoint = 0
  while 1:
    if len(SEND_BUF_SEQ) < N:
      m = prepareDatagram(TO_SEND_SEQ, data)
      if not m:
        if endSignal == 1:
          print "making END"
          endSignal = 0
          m = util.buildHeader(TO_SEND_SEQ, 'END', 2)
          m += 'END'
        elif len(SEND_BUF_SEQ) == 0:
          break
        else:
          checkpoint = 1

      if checkpoint == 0:
        try:
          THREAD_LOCK.acquire()
          s.sendto(m, clientAddr)
          SEND_BUF.append(m)
          SEND_BUF_SEQ.append(TO_SEND_SEQ)
          # print "TO_SEND_SEQ: " + str(TO_SEND_SEQ)
          TO_SEND_SEQ = TO_SEND_SEQ + 1
          # time.sleep(0.01)
          THREAD_LOCK.release()
        except socket.error, msg:
          print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
          sys.exit()
          
    if EXPIRED == 1 and len(SEND_BUF) > 0:
      # print "waiting to resend all..."
      print "Time Out, sequence number = " + str(SEND_BUF_SEQ[0]*MSS)
      THREAD_LOCK.acquire()
      TIMER.cancel()
      # TIMER.join()
      THREAD_LOCK.release()
      THREAD_LOCK.acquire()
      # print "SEND_BUF_SEQ: " + str(SEND_BUF_SEQ)
      for m in SEND_BUF:
        # errno, seq_no, dataText = util.parseDatagram(m, 0) 
        # print "IN RESEND" + str(seq_no)
        s.sendto(m, clientAddr)
      # print "SEND_BUF ALL SENT!!"
      THREAD_LOCK.release()
      EXPIRED = 0
      THREAD_LOCK.acquire()
      TIMER = threading.Timer(TIMER_SET, timerHandler)
      TIMER.start()
      THREAD_LOCK.release()

def FTPsender(clientAddr, msg, mss, n):
  
    global HOSTNAME
    global PORT
    global FILENAME
    global N
    global MSS
    global TO_SEND_SEQ
    global receiverThread
    global LASTACK
    global EXIT_THREAD
    global SEND_BUF
    global SEND_BUF_SEQ
    global EXPIRED
    global TIMER_SET
    global THREAD_LOCK
    global s
  
    MSS = mss
    N = n
  
    TO_SEND_SEQ = 0
    LASTACK = -1
    EXIT_THREAD = 0
    SEND_BUF = []
    SEND_BUF_SEQ = []
    EXPIRED = 0
    TIMER_SET = 0.1 
    THREAD_LOCK = threading.Lock()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
    # This block is for receiving acknowledgements.
    receiverThread = threading.Thread(target=receiver)
    receiverThread.start()
    start = time.time()

    # rdt_send is to send data segments to client.
    rdt_send(clientAddr, msg)
    while len(SEND_BUF) > 0:
        print LASTACK
        print TO_SEND_SEQ
        print len(SEND_BUF)
        continue
    print "Used time: " + str(time.time() - start)
    print "FINISHED!"
    EXIT_THREAD = 1
    receiverThread.join()
    

def signal_handler(signal, frame):
  global EXIT_THREAD
  print("\nCtrl+C detected! Exiting...")
  EXIT_THREAD = 1
  receiverThread.join()
  s.close()
  sys.exit(0)

if __name__ == "__main__":
   signal.signal(signal.SIGINT, signal_handler)
   main(sys.argv[1:])