import requests

# create a session
session = requests.session()

# perform a GET
session.get("http://127.0.0.1:5000")

# perform a POST with a payload
session.post("http://127.0.0.1:5000/login", data={"username": "test", "password": "test"})

# inspect your cookies
print(session.cookies)

# modify your cookies
session.cookies.update({"": ""})
