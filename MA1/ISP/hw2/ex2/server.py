from flask import Flask, request, abort, make_response
import time
import hmac
import base64

encryption = 'utf-8'
key = 'TG91aXMgTGVjbGFpcgo'.encode(encryption)  #the key is Louis Leclair base64

app = Flask(__name__)

cookie_name = "LoginCookie"

def is_tampered(cookie, hashmac):
    """Check either the cookie has been tampered or not.

    Args:
        cookie (cookie): received cookie.
        hashmac (hexadecimal string number): received hashmac.

    Returns:
        bool: true is the cookie has been tampered false otherwise.
    """
    real_hash = hmac.new(key, cookie.encode(encryption)).hexdigest()
    return real_hash != hashmac

@app.route("/login",methods=['POST'])
def login():
    """From a usr and pwd create a cookie depending of the usr and pwd received. 
    The cookie as the form: usr, time of creation, com402, hw2, ex2, admin or user, hmac
    To chose between the user or the admin it depends of the usr and pwd received, if pwd == 42 and usr == admin we have admin otherwise it is the user.
    To create the hmac, we use a key to encrypt the cookie where the key is in this case a predefine key.

    Returns:
        a response with cookie.
    """
    usr = request.form['username']
    pwd = request.form['password']
    ts = int(time.time())
    if usr == 'admin' and pwd == '42':
        cookie = '{},{},com402,hw2,ex2,admin'.format(usr, ts)
    else:
        cookie = '{},{},com402,hw2,ex2,user'.format(usr, ts)
    hashmac = hmac.new(key, cookie.encode(encryption)).hexdigest()
    cookie += ',{}'.format(hashmac)
    cookie = base64.b64encode(cookie.encode(encryption)).decode(encryption)
    resp = make_response()
    resp.set_cookie(cookie_name, cookie)
    return resp

@app.route("/auth",methods=['GET'])
def auth():
    """From a received cookie, we want to know different things.
    - Is there a cookie? If not return the code 403.
    - If one, was it tampered ? If yes return the code 403.
    - If not tampered, is it the admin? If yes return the code, 200.
    - If not the admin, return the code 201.

    Returns:
        a response with the code it has to return depending of the situation.
    """
    cookie = request.cookies.get(cookie_name)
    if cookie:
        cookie = base64.b64decode(cookie.encode(encryption)).decode(encryption)
        cookie = cookie.split(',')

        new_cookie = ','.join(cookie[:-1])
        if is_tampered(new_cookie, cookie[-1]):
            return make_response('Code 403 if the cookie has been tampered.'), 403 
        is_admin = cookie[-2] == 'admin'
        if is_admin:
            return make_response('Code 200 if the user is the administrator.'), 200
        else:
            return make_response('Code 201 if the user is a simple user.'), 201
    else:
        return make_response('Code 403 if no cookie is present.'), 403

if __name__ == '__main__':
    app.run()

