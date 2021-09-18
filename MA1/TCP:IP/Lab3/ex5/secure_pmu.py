import socket
import ssl
import sys

CERTIFICATE = sys.argv[1]
KEY = sys.argv[2]

HOST = "localhost"
PORT = 5003

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(CERTIFICATE, KEY)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock.bind((HOST, PORT))
sock.listen(1)
while True:
    connection, addr = sock.accept()
    ssock = context.wrap_socket(connection, server_side=True)
    while True:
        data = ssock.recv(32).decode()
        if data:
            if data == "CMD_short:0":                
                for i in range(10):
                    ssock.sendall(("\nThis is PMU data " + str(i)).encode())
            else :
                print("HAPPY BIRTHDAY !")
        else:
            print("No more data from", addr)
            break
        
    ssock.close()
    connection.close()