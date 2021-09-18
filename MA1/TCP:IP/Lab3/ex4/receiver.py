import socket
import struct
import sys

try :
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))

    mreq = struct.pack("=4sl", socket.inet_aton(HOST), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data = sock.recv(10240).decode()
        if data:
            print(data[6:], flush=True)
        else:
            break

    sock.close()
except:
    print("ERROR")