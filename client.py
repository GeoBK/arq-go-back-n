#!/usr/bin/python3
from socket import *
import sys
import threading
import os
import time
from common import calculateChecksum, TERMINATOR

outstanding_frames = 0
latest_ack=0
data_type_code = b'\x55' + b'\x55'

lock = threading.Lock()
total_length = None
byte = True
RTO_TIMEOUT = 10
def sendFile(f_name, cs, server_addr):
    global outstanding_frames
    global byte
    global total_length
    # Read from file 
    f = open(f_name, "r")
    seq_number = 0
    wait_counter = 0
    byte_counter = 0
    while 1:
        curr_packet = ""
        # retransmit unacked packets
        # Build packet
        while len(curr_packet) < mss and byte:
            byte = f.read(1)
            byte_counter += 1
            curr_packet += byte
        seq_number_bytes = seq_number.to_bytes(4, byteorder='big')
        seq_number += len(curr_packet)
        checksum = calculateChecksum(curr_packet)
        datagram = seq_number_bytes + checksum + data_type_code + bytes(curr_packet, 'utf-8')
        lock.acquire()
        # This sequence number would actually be the sequence number of the corresponding ACK
        rto_timers[seq_number] = RTO_TIMEOUT
        rto_buffer[seq_number] = datagram
        cs.sendto(datagram, server_addr)
        outstanding_frames+=1
        lock.release()
        if not byte:
            total_length = byte_counter
            break

        while outstanding_frames >= window_size:
            wait_counter += 1

def recvAcks(cs):
    global outstanding_frames
    global latest_ack
    while 1:
        if not byte and outstanding_frames == 0:
            return
        resp, serverAddress = cs.recvfrom(1024)
        seq_number = int.from_bytes(resp[0:4], byteorder='big')
        seq_id = int.from_bytes(resp[4:6], byteorder='big')
        ack_type_code = int.from_bytes(resp[6:8], byteorder='big')
        if total_length is not None and seq_number > total_length:
            exit()
        
        lock.acquire()
        latest_ack = seq_number
        del rto_buffer[seq_number]
        del rto_timers[seq_number]
        outstanding_frames -= 1
        lock.release()
        

def timer(cs, server_addr):
    while byte or outstanding_frames > 0:
        lock.acquire()
        for key in rto_timers:
            if rto_timers[key] > 0:
                rto_timers[key] -= 1
            if rto_timers[key] == 0:
                # print("Timeout, sequence number = ", key)
                if key < latest_ack:
                    del rto_buffer[key]
                    del rto_timers[key]
                else:
                    cs.sendto(rto_buffer[key], server_addr)
                    rto_timers[key] = RTO_TIMEOUT

        lock.release()
        time.sleep(0.01)

# Parse command line arguments
server_name = sys.argv[1]
server_port = int(sys.argv[2])
file_name = sys.argv[3]
window_size = int(sys.argv[4])
mss = int(sys.argv[5])

rto_buffer = {}
rto_timers = {}
# Establish connection
clientSocket = socket(AF_INET, SOCK_DGRAM)
print("Starting client")
start = time.time()
ack_thread = threading.Thread(target=recvAcks, args=(clientSocket,))
send_thread = threading.Thread(target=sendFile, args=(file_name, clientSocket, (server_name, server_port)))
timer_thread = threading.Thread(target=timer, args=(clientSocket, (server_name, server_port)))
ack_thread.start()
send_thread.start()
timer_thread.start()
send_thread.join()
timer_thread.join()
clientSocket.sendto(TERMINATOR, (server_name, server_port))
duration = time.time()-start
print("Time taken for loss_probability: {}, window_size: {}, mss: {} = {}".format(0.05, window_size, mss,duration))
clientSocket.close()
