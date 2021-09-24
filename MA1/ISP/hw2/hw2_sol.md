# COM-402 Homework 2 Solution
- [COM-402 Homework 2 Solution](#com-402-homework-2-solution)
  - [Exercise 1: Cookie tempering](#exercise-1-cookie-tempering)
    - [The initial problem](#the-initial-problem)
    - [So, where are the cookies?](#so-where-are-the-cookies)
    - [Decode and understand the cookie](#decode-and-understand-the-cookie)
    - [Haxxxing the cookie](#haxxxing-the-cookie)
  - [Exercise 2: HMAC for cookies](#exercise-2-hmac-for-cookies)
    - [HMAC ?](#hmac-)
    - [Create the cookie](#create-the-cookie)
    - [Login the user](#login-the-user)
    - [Checking a cookie](#checking-a-cookie)
    - [Authenticating the user](#authenticating-the-user)
  - [Exercise 3: Client-Side Password Verification](#exercise-3-client-side-password-verification)
    - [Understanding the setup](#understanding-the-setup)
    - [Ew, Javascript](#ew-javascript)
    - [Some explanations](#some-explanations)
    - [Hacking](#hacking)
  - [Exercise 4: PAKE implementation](#exercise-4-pake-implementation)
    - [The structure](#the-structure)
    - [Breaking down the process](#breaking-down-the-process)

The goal of the exercises is to understand the basics of networks security, such as cookies, client-side, HMAC,...

## Exercise 1: Cookie tempering
### The initial problem
The title already gives a lot of information on how you should proceed. Have a look at your [cookies](https://www.wikihow.com/View-Cookies) for now. Despite the possible `*.epfl.ch` generic cookies, there is nothing of interest here (to check that, you can open the URL in a private navigation window, that starts clean of cookies). Nothing to tamper with yet...

Open your browser console (right-click -> inspect is a good way), and open the _Network_ tab. When clicking on the "Hack & Spy" buttons, you see a request made to `api/hw2/ex1/list`. The request headers don't contain something of interest. The response is a `403 Forbidden`.

\[Optional\] You can also inspect the HTML of the page, and notice, at the very bottom a `<script>` tag, that contains the code that binds the button to HTTP requests to `api/hw2/ex1/list`, with an empty payload, and that deals with the result of the request (display the success or mock you when you fail).

### So, where are the cookies?

When you arrive on the webpage, the first things to spot is the possible interactions. Obviously, the "Hack & Spy" buttons, but also the hyperlink on the word _administrators_, which leads you to `/hw2/ex1/login.html`, and a nice login form. That's nice!

Enter some credentials (can be any dummy value, like `myusername` and `mypassword`). You're now back to the homepage, and still can't _hack & spy_ :( But, going back to your cookies, you now have a cookie!

| name          | value               | domain          | Expires |
| ---------     |:-------------------:| -------         | ------- |
| LoginCookie   | `bXl1c2VybmFtZS...` | com402.epfl.ch  | Session |

### Decode and understand the cookie
The value (that will vary for you) is quite gibberish though... But as a trained IT security expert, you immediately recognize base64! If you don't, here are a few tips:
* A long string of alphanumerical characters is most likely base64
* If it ends by one or several `=` characters, it also is.
* base64 is [very common](https://en.wikipedia.org/wiki/Base64#URL_applications) on the web and in cookies, to encode arbitrary text or content.
* There are [tools](https://www.webatic.com/encoding-explorer) online to help with that

[base64decode.org](https://base64decode.org) may be the best online tool for encoding/decoding base64 strings. Input the above value, and you'll obtain something along the lines of `myusername,1594232326,com402,hw2,ex1,user`. You can try multiple times (go to the login page, and enter credentials again), and you will notice that:
* The first value (`myusername`) is always your username
* The second value changes each time, but slightly (this is a good indicator of a [timestamp](https://www.unixtimestamp.com/))
* The next 3 values never ever change.

The interesting thing about base64 is that it is completely and deterministically reversible. This means that you can change anything in that string, and re-encode it at will.

Try again to _Hack & Spy_, nothing changes. But now, you see in the request headers that the cookie is sent along. This means, your login information also is. Maybe we can **temper** with that. The last (decoded) value of the cookie is `user`. Maybe we can try to change it?

### Haxxxing the cookie

Copy-paste the decoded string to [base64encode.org](https://base64encode.org), and modify the characters you are interested in. At this point, you don't know the "roles" in the page, except `user`. There are many keywords you can try, such as `root`, `editor`, `owner`, `administrator`, `admin`,... We'll settle for the latter! Change `user` by `admin`,  (to obtain something like `myusername,1594232326,com402,hw2,ex1,admin`), and encode.

Now go to your browser again, modify your cookie with the newly encoded string, and now you can _Hack & Spy_!


## Exercise 2: HMAC for cookies
We are again having fun with cookies. It's now time to be on the other side, and be smarter than Evil Corp.

### HMAC ?
First of all, it's important to remember what a [HMAC](https://en.wikipedia.org/wiki/HMAC) is. Basically, you store on your server a _secret key_ (some arbitrary string, only known to you, a _one-time pad_). Then, when you need to ensure integrity of a content, you xor the content with your key, hash it, and append it to the content. With that, if someone wants to tamper with the content, they must also modify the HMAC (which they can't, because they don't have the secret).

### Create the cookie
First step, we need a function to create the cookie. As mentioned, we need the username and password to determine if a user is an admin, then we create the cookie, compute its HMAC and append it. Here is a snippet that does that:

```python
import time # for the timestamp
import hmac # standard lib for the HMAC
from hashlib import sha1 # hashing library to provide to hmac
import base64 # encode/decode base64 strings

# your secret key
SECRET_KEY_YOU_WILL_NEVER_FIND = "ducks".encode()

def create_cookie(username, password):
    # the infos required for the cookie
    t = str(int(time.time())) # create the timestamp
    domain = "com402"
    hw = "hw2"
    ex = "ex2"

    # decide the role based on the username/password
    if username == "admin" and password == "42":
        role = "admin"
    else:
        role = "user"

    # create the "base" cookie, that will be hashed
    base_cookie = ",".join([username,t,domain,hw,ex,role])

    #create the HMAC
    my_hmac = hmac.new(SECRET_KEY_YOU_WILL_NEVER_FIND,
                   base_cookie.encode(), #message must be binary
                   sha1)
    final_cookie = base_cookie + "," + my_hmac.hexdigest() # append digest
    # base64encode the cookie (with .encode() for binary format),
    # then back to utf-8 for a readable cookie
    return base64.b64encode(final_cookie.encode()).decode('utf-8')
```
Note a few specialties there:
* The `hmac` library works with binary values, this is why we have to use `.encode()` on the secret key and the base cookie, to change them from utf-8 strings to binary strings.
* We used here sha1, which is a rather standard hashing algorithm, but other  (md5, sha2,...) can be used.
* base64 also works with binary values: we first encode `final_cookie` to binary, then change it to base64 (which yields a result in binary), then decode it again to utf-8 for a usable format.
* The method used to authenticate the admins is absolutely terrible, never apply that in real life. This is purely a demonstration.
* Same apply for the secret key, you should use a longer and more random one.

### Login the user
Now that we have a way to create the cookie, we can login the user. We reuse the template that was provided, and complete the `/login` route.

```python
from flask import Flask, make_response, request

@app.route("/login", methods=["POST"]) # only accept POST
def login():
    # get the username/password from the payload
    username = request.form.get('username')
    password = request.form.get("password")
    ####
    # [optional] here, you can perform sanity checks
    # (are they both non-null, etc.)
    ####
    # create your cookie
    c = create_cookie(username, password)
    # prepare your response (the text is useless)
    resp = make_response("Logged in")
    # set the cookie with the correct cookie name
    resp.set_cookie(cookie_name, c)
    # return your response
    return resp
```
Nothing too crazy here: get the values from the POST request, create your cookie, prepare a response, set the cookie and send it.

You can already test that in your lab. Do a POST request, and then check the session cookies. You should see the cookie, with the base64-encoded value (that you can decode as in ex1, to ensure it's correct)

### Checking a cookie
Now that the user has a cookie, we must build a function that, provided the cookie, will answer if the cookie is legit. We will first take the cookie, base64decode it, put aside the HMAC, re-compute it, and compare them.

```python
def cookie_validate(cookie):
    try: # optional: try to decode, but don't trust too much
        decoded = base64.b64decode(cookie.encode()).decode("utf-8")
    except:
        # The cookie isn't even a base64 encoding anymore,
        # it definitely has been tempered with...
        return False
    # separate base cookie from hmac
    base_cookie, cookie_hmac = decoded.rsplit(",", 1)
    # re-compute the hmac from the base cookie
    reference_hmac = hmac.new(SECRET_KEY_YOU_WILL_NEVER_FIND,
                     base_cookie.encode(),
                     sha1).hexdigest()

    # return whether or not they are equal
    return cookie_hmac == reference_hmac
```

### Authenticating the user
Now that we can ensure the cookie is valid, we can do the complete authentication step.
```python
@app.route("/auth",methods=['GET'])
def auth():
    # get the LoginCookie from the cookie jar
    cookie = request.cookies.get(cookie_name)
    if cookie is None or not cookie_validate(cookie):
        # no cookie found, or not valid
        return "Naughty, naughty, naughty...", bad_or_no_cookie
    # decode the cookie
    decoded = base64.b64decode(cookie.encode()).decode("utf-8")
    # get the role
    role = decoded.split(",")[5]
    # compare and return the correct code
    if role == "admin":
        return "My lord...", success_admin
    return "User", success_user
```

## Exercise 3: Client-Side Password Verification
As you may suspect, this exercise will focus on the verification of a password without actually sending the password to the server, and letting the user do the work.

### Understanding the setup
When you arrive on the login screen, first thing first, open the browser console, on the Network tab. Then fill in any dummy data, and login. Strangely, no request was made to the server. Interesting! It looks like _client-side password verification_. So where does the error message come from ? Surely from some javascript method.

### Ew, Javascript
Now, before you pull out the debugger and understand the process, have a look at the HTML. At the very bottom, as previously, you have a `<script>` tag that contains all the interesting code. Here is a copy, for convenience:

```javascript

            function ascii (a) { return a.charCodeAt(0); }
            function toChar(i) { return String.fromCharCode(i); }

            function hash(msg,key) {
                if (key.length < msg.length) {
                    var diff = msg.length - key.length;
                    key += key.substring(0,diff);
                }

                var amsg = msg.split("").map(ascii);
                var akey = key.substring(0,msg.length).split("").map(ascii);
                return btoa(amsg.map(function(v,i) {
                    return v ^ akey[i];
                }).map(toChar).join(""));
            }

            $('#loginForm').submit(function(e) {
                e.preventDefault();
                var mySecureOneTimePad = "Never send a human to do a machine's job";
                var username = $('#username').val();
                var password = $('#password').val();

                if (username.length > 100) {
                    alert("There's a difference between knowing the path and walking the path.");
                    return;
                } else if (password.length > 100) {
                    alert("The best answer to anger is silence.");
                    return;
                }
                if (password != hash(username,mySecureOneTimePad)) {
                    alert("I didn't say it would be easy, Neo. I just said it would be the truth.");
                    return;
                }
                postJSON = function(url,data){
                    return $.ajax({url:url, data:JSON.stringify(data), type:'POST', contentType:'application/json'});
                };
                postJSON("/api/hw2/ex3",{"username":username,"password":password})
                    .done(function(data) {
                        //if you get a 200 OK status, that means you successfully
                        // completed the challenge.
                        document.write("Sucess! Token: " + data);
                    }).fail(function(resp,status) {
                        alert("Pain is temporary. Quitting lasts forever.");
                    });
            });
```

### Some explanations
We won't go into too much details there, because not everything is relevant. But the interesting parts to notice are the following:
* There is a function `hash` that takes a message and a key, and apparently returns some hash,
* The submit action of the submit button is intercepted and replaced by the big block,
* This block defines a OTP, and retrieves the username/password from the form,
* It checks the length of both of them,
* Then compare the password to the resulting hash of the username and the OTP,
* Then, if it matches, it sends the username and password to the server for a second check.

The second check is necessary to ensure we don't bypass the function entirely and simply send the username/password ourselves. So it's either the exact same mechanism (but server-side), or a different one.

### Hacking
The weakness of this client-side verification, is that it relies on a HMAC but gives out the OTP, that is supposed to be secret. It then simple to guess a password: input any username and the OTP into the hash function (both kindly provided), and use the output as a password!

You don't even need to understand how the hash function works. Simply use it as a blackbox. Go to the javascript console (the _console_ tab of your browser console), then copy the OTP, and input it with some username to the hash function (already defined):
```javascript
> let otp = "Never send a human to do a machine's job";
> hash("myusername", otp)
"IxwDFhdSHQQDAQ=="
```

Go now to the form, and input `myusername` and `IxwDFhdSHQQDAQ==`, granting you access!

## Exercise 4: PAKE implementation
This exercise is a bit more complex than the previous ones. You really only have one procedure to implement, but the juggling with types, and the wrestling with websockets make it more challenging. Let's start from the beginning.

### The structure
As we are working with asynchronous websockets, we can't just put everything as a script and run it. We must tell python that we expect asynchronous outputs. For that, we will use the following skeleton:

```python
import websockets
import asyncio
import ...

# CONSTANTS, as provided
EMAIL = "your.email@epfl.ch"
PASSWORD = "correct horse battery staple"
N = int("EEAF0AB9ADB38DD69C33F80AFA8FC5E86072618775FF3C0B9EA2314C9C256576D674DF7496EA81D3383B4813D692C6E0E0D5D8E250B98BE48E495C1D6089DAD15DC7D7B46154D6B6CE8EF4AD69B15D4982559B297BCF1885C529F566660E57EC68EDBC3C05726CC02FD4CBF4976EAA9AFD5138FE8376435B9FC61D2FC0EB06E3",16)
g = 2
NUMBER_LENGTH = 32

def some_standard_function():
  #normal functions

async def websocket_function(websocket, param):
  # asynchronous functions that interact with the websocket

async def srp():
  # the core of the procedure


asyncio.get_event_loop().run_until_complete(srp())
```

### Breaking down the process
As you can guess, we can break down our core procedure in a bunch of _send_ and _receive_. Everything will be done within one opening of a websocket. We can then start our procedure with the following:
```python
uri = "ws://127.0.0.1:5000"
async with websockets.connect(uri) as websocket:
    # then work here
```

***

The first step of the protocol is to send the email. This one isn't too hard:
```python
await websocket.send(EMAIL)
```

***

Then, you need to receive the salt. It arrives in hexadecimal form, and you want to convert it,
```python
salt_hex = await websocket.recv()
salt_int = int(salt_hex, 16)
salt_bin = format(salt_int, "x").encode()
# alternatively: salt_bin = salt_hex.encode()
```

***

Next you want to generate a random `a`, then compute `A` using `g, a, N`.
```python
import os
a = int.from_bytes(os.urandom(NUMBER_LENGTH), "big")
A_hex = format(A, "x").encode()
await websocket.send(A_hex)
```
Note that the `os` library can create random bytes, encoded in big-endian, and we need to convert it tho int, thus the `int.from_bytes(..., "big")`

***

Then, we await the `B`, quite straightforward:

```python
B_hex = await websocket.recv()
B = int(B_hex, 16)
```

***

We get to the hashing library. This one requires to use, as mentioned, binary-encoded hexadecimal representations of the numbers. Note that we could use any binary-encoded representation (bytes, int, hex,...); it doesn't matter as long as we are consistent with ourselves and the server.

We create an empty hash, hash A and B, and retrieve the result (_digest_):
```python
import hashlib
h = hashlib.sha256()
h.update(format(A, "x").encode)
h.update(format(B, "x").encode)

u_hex = h.hexdigest()
u = int(u_hex, 16)
```
***

Now, we have a nested hash. We could compute it in one go, but it's simpler to consider this as an _inner_ hash, and an _outer_ hash. We first compute the inner.
```python
# H(U || ":" || PASSWORD)
inner = hashlib.sha256()
inner.update(EMAIL.encode())
inner.update(b":")
inner.update(PASSWORD.encode())
```

And the outer hash, that requires the inner digest; you then get `x` as the digest of the outer hash:
```python
outer = hashlib.sha256()
outer.update(salt_bin)
outer.update(inner.hexdigest().encode())

x = int(outer.hexdigest(), 16)
```

***

Some math now: we now have `g,x,N,a,u`, we can then compute the secret!
```python
#S = (B - g^x)^(a + u * x) % N
S = pow(B - pow(g, x, N), (a + u * x), N)
```
Note that we can't compute `g^x` directly, at the risk of an overflow. We can simply modulo it to `N`, as the result is identical (hence the `pow(g,x,N)`). And we now have the shared secret!

***

Last step (necessary for verification purpose, but optional for a real-life scenario) is to verify we have the same secret as the server. For that, we have to compute `H(A || B || S)`, and send it. This is straightforward, and very similar as what we did before:
```python
# create the hash
h = hashlib.sha256()
h.update(itob(A))
h.update(itob(B))
h.update(itob(S))

# send the hex digest
await websocket.send(h.hexdigest().encode())

# receive confirmation (or not) that the secret is the same.
resp = await websocket.recv()
print("Response: {}".format(resp))
```