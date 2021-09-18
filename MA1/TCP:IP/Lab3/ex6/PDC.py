import websocket
import sys

server = sys.argv[1]
port = sys.argv[2]
command = sys.argv[3]

ws = websocket.create_connection('ws://'+server+':'+port)

ws.send(command)
while True:
    data = ws.recv()
    if data:
        print(data.decode())
    else:
        break
ws.close()