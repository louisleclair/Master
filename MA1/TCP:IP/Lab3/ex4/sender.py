import socket
import sys
import struct
import time

GROUP = sys.argv[1]
PORT = int(sys.argv[2])
SCIPER = sys.argv[3]

multicast_group = (GROUP, PORT)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setblocking(False)

ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    entry = input()
    message = (SCIPER+entry).encode()
    
    try:
        sent = sock.sendto(message, multicast_group)
        time.sleep(1)
        data = sock.recvfrom(16)
        if data:
            pass
    except :
        pass

finally:
    sock.close()