import socket
import sys

server = sys.argv[1]
port = int(sys.argv[2])
command = sys.argv[3]

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server, port))

sock.sendall(command.encode())

size = 2**20 if 'CMD_floodme' == command else 18
count = 0
length = size
while True:
	if command != 'CMD_floodme':
		length = size + count//10
	data = sock.recv(length).decode()
	if data:
		print(data)
		count += 1
	else:
		break
sock.close()