## Useful commands

docker exec -it client /bin/sh
docker exec -it mitm /bin/bash

### Exercise 1

mitm IP:
172.20.0.3

Del and add gateway: 
route del default gw 172.20.0.1
route add default gw 172.20.0.3

To become a router between the router and the client: 
iptables -A FORWARD -i eth0 -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

To forward the traffic to the queue:
iptables -D FORWARD -i eth0 -j ACCEPT
iptables -A FORWARD -j NFQUEUE --queue-num 1

secret to find:
cc --- 8452.8214.9088.8566
pwd --- VERYSECURE1111
pwd --- UQXI5I06UX924

### Exercise 2
Del and add gateway: 
route del default gw 172.21.0.1
route add default gw 172.21.0.3

To become a router between the router and the client: 
iptables -A FORWARD -i eth0 -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

To forward the traffic to the queue:
iptables -D FORWARD -i eth0 -j ACCEPT
iptables -A FORWARD -j NFQUEUE --queue-num 1


### Exercise 3

create certificate: openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /certs/nginx-selfsigned.key -out /certs/nginx-selfsigned.crt

