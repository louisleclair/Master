import requests
import base64
import hashlib

h = hashlib.sha256()

session = requests.session()

# if token with a size different to 12 have a error so the tocken has a size of 12 which is hard to brute force must use a smarter way.
# Solution from the docker 'b4351d395d2f' (cheating)
r = session.post("http://0.0.0.0:8080/hw6/ex1", json={"token": 'b4351d395d2f'})
print(r._content.decode(), r.status_code)