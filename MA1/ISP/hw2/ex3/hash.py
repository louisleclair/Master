import base64

def hash(msg, key):
    if len(key) < len(msg):
        diff = len(msg) - len(key)
        key += key[:diff]
    amsg = [ord(x) for x in msg]
    akey = [ord(x) for x in key[:len(msg)]]
    res = [chr(m ^ k) for m, k in zip(amsg, akey)]
    res = "".join(res).encode('ascii')
    return base64.b64encode(res).decode('utf-8')

msg = 'lol'
key = "Never send a human to do a machine's job"

print(hash(msg, key))