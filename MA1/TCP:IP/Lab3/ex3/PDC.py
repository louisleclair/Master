import socket
import sys
import time
import functools

counts = []

for i in range(60):
	count = 0
	server = sys.argv[1]
	port = int(sys.argv[2])

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
	sock.setblocking(False)
	sock6.setblocking(False)

	command = 'RESET:20'
	ack = False
	while not ack:
		sock.sendto(command.encode(),(server, port))
		time.sleep(1)
		sock6.sendto(command.encode(),(server, port))
		time.sleep(1)
		try:
			data = sock.recv(32).decode()
		except socket.error:
			pass
		else:
			if data:
				print(data)
				ack = True
		if not ack:
			try:
				data6 = sock6.recv(32).decode()
			except socket.error:
				pass
			else:
				if data6:
					print(data6)
					ack = True
		count += 1
	print(count)
	sock6.close()
	sock.close()
	counts.append(count)
print('---------------------------------------------')
print(functools.reduce(lambda a,b: a+b, counts)/len(counts))
print(functools.reduce(lambda a,b: a+b, list(map(lambda a: (a-1)/a, counts)))/len(counts))