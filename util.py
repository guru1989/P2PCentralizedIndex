import binascii

# Calculate the checksum
def calculate_checksum(data):  # Form the standard IP-suite checksum
  pos = len(data)
  if (pos & 1):  # If odd...
    pos -= 1
    sum = ord(data[pos])  # Prime the sum with the odd end byte
  else:
    sum = 0
 
  #Main code: loop to calculate the checksum
  while pos > 0:
    pos -= 2
    sum += (ord(data[pos + 1]) << 8) + ord(data[pos])
 
  sum = (sum >> 16) + (sum & 0xffff)
  sum += (sum >> 16)
 
  result = (~ sum) & 0xffff #Keep lower 16 bits
  result = result >> 8 | ((result & 0xff) << 8)  # Swap bytes
  return result

# Calculate the checksum and build different headers,
# type == 0 is data, type == 1 is ACK, type == 2 is end signal
def buildHeader(seq, msg, type):
  header = ""

  # Convert the seq number to 8-digit hex
  hexResult = seq;
  while hexResult > 4294967295:
    hexResult = seq - 4294967295;
  header += "{0:032b}".format(hexResult)

  if type == 0:
    # Calculate the checksum
    checksum = calculate_checksum(msg)
    checksum = "{0:016b}".format(checksum)
    header += checksum

    # Add the data indicator
    header += "0101010101010101"
  elif type == 1:
    # Add 16-bit zeroes
    header += "0000000000000000"
    #Add the ACK indicator
    header += "1010101010101010"
  elif type == 2:
    # Calculate the checksum
    checksum = calculate_checksum(msg)
    checksum = "{0:016b}".format(checksum)
    header += checksum
    #Add the end signal indicator
    header += "0000000000000000"
  elif type == 3:
    header += "0000000000000000"
    header += "0000000000000000"

  return header

# Parse the packet from binary
# type == 0 is data, type == 1 is ACK
def parseDatagram(msg, type):
  if type == 0:
    seq_no = int(msg[0:32], 2)
    checksum = int(msg[32:48], 2)
    indicator = msg[48:64]
    data = msg[64:]
    # dataText = convertBack(data)
    errno = 0

    if checksum != calculate_checksum(data):
      errno = 1
    elif indicator != '0101010101010101':
      errno = 2
      if indicator == '0000000000000000':
        errno = 3

    return errno, seq_no, data
  else:
    seq_no = int(msg[0:32], 2)
    checksum = msg[32:48]
    indicator = msg[48:64]
    errno = 0

    if checksum != '0000000000000000':
      errno = 1
    elif indicator != '1010101010101010':
      errno = 2
      if indicator == '0000000000000000':
        errno = 0

    return errno, seq_no
