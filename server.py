import socket
import sys
from common import calculateChecksum, TERMINATOR
import random
server_port = int(sys.argv[1])
file_name = sys.argv[2]
loss_probability = float(sys.argv[3])

ack_type_code = b'\xaa\xaa'
ack_checksum = b'\x00\x00'
local_ip = socket.gethostbyname(socket.gethostname())
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((local_ip, server_port))
print(local_ip)
print("Server ready to receive!")
f = open(file_name, "w")

last_ack = 0
while 1:
    message, clientAddress = serverSocket.recvfrom(2048)
    if TERMINATOR == message:
        print("File transfer complete")
        last_ack = 0
        continue
    
    seq_number = int.from_bytes(message[0:4], byteorder='big')
    checksum = message[4:6]
    type_code = int.from_bytes(message[6:8], byteorder='big')
    payload = str(message[8:], 'utf-8')
    if random.random() < loss_probability:
        print("Packet loss, sequence number = ", seq_number+len(payload))
        continue

    if calculateChecksum(payload) == checksum:
        if seq_number == last_ack:
            f.write(payload)
            f.flush()
            ack_number = seq_number + len(payload)
            ack_number_bytes = ack_number.to_bytes(4, byteorder='big')
            ack_payload = ack_number_bytes + ack_checksum + ack_type_code
            last_ack = ack_number
            serverSocket.sendto(ack_payload, clientAddress)
        
