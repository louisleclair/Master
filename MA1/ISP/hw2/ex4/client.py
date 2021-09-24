import base64
import websockets
import asyncio
import hashlib

# Constant parameters

email = "louis.leclair@epfl.ch"
password = "correct horse battery staple"
H = 'sha256'
N = 'EEAF0AB9ADB38DD69C33F80AFA8FC5E86072618775FF3C0B9EA2314C9C256576D674DF7496EA81D3383B4813D692C6E0E0D5D8E250B98BE48E495C1D6089DAD15DC7D7B46154D6B6CE8EF4AD69B15D4982559B297BCF1885C529F566660E57EC68EDBC3C05726CC02FD4CBF4976EAA9AFD5138FE8376435B9FC61D2FC0EB06E3'
N = int(N, 16)
g = 2

async def pake(email,password, N, g):
    h = hashlib.sha256()
    hash_pwd_U = hashlib.sha256()
    hash_x = hashlib.sha256()


    uri = 'ws://127.0.0.1:5000/'
    async with websockets.connect(uri) as websocket:
        # Send email 
        U = email
        await websocket.send(U.encode())
        # Received salt
        salt_hex = await websocket.recv()
        salt = int(salt_hex, 16)
        # Send A which is g^salt % N
        A = pow(g, salt, N)
        A_hex = format(A, "x")
        await websocket.send(A_hex.encode())
        #Received B
        B_hex = await websocket.recv()
        B = int(B_hex, 16)
        # Compute u
        u_hex = A_hex + B_hex
        h.update(u_hex.encode())
        u_hash = h.hexdigest()
        u = int(u_hash, 16)
        # Compute x
        hash_pwd_U.update((U + ':' + password).encode())
        hash_U_pass = hash_pwd_U.hexdigest()
        hash_x.update((salt_hex + hash_U_pass).encode())
        x_hex = hash_x.hexdigest()
        x = int(x_hex, 16)
        # Compute S
        S = pow((B - pow(g, x, N)), salt + u * x, N)
        S_hex = format(S, "x")
        h.update((S_hex).encode())
        await websocket.send(h.hexdigest())


asyncio.get_event_loop().run_until_complete(pake(email, password, N, g))
    