# Homework 2
## Exercise 1: [Attack] cookie Tampering.

[E corp]: https://com402.epfl.ch/hw2/ex1

- Connect to the website [E corp][] and click on the **Hack & Spy** button.
- Open the element inspector and go to the storage category (in Safari), the place where you are going to find the cookies. 
- Find the cookie coming from com402.epfl.ch and copy the Value (The value contains some informations about the session and what you have got from the server after you try to authentificate as **Admin**).
- Use a **base 64 decoder** to decode your value. The result should have the form of (Username, 1602078051, com402, hw1, ex1, user). The first element of the result is the name placed in the Username box during authentification, it must be Username to have a working solution. The second element is the cookie's number session, it is a random number generate for the session. The third, fourth and fifth must remain unchanged and the last one is the level of access you are granted. 
- To break the authentification mechanism, you have to change the authority level granted meaning you have to change **user** by **admin**. The solution has this form: (Username, 1602078051, com402, hw1, ex1, admin) (For clarification the cookie's session number is dependent of your session so it is normal if it is not the same as mine and the parentheses are just here for the presentation).
- Finally you have to encode using a **base 64 encoder** and replace the new value in the value field in the cookies section in the element inspector.
- Now you should be able to access the Hack & Spy and have a Success page.

## Exercise 2: [Defense] HMAC for cookies.

The goal of the exercise is mainly to implement a dummy server which received request of the form: ```{"username": user,"password": password} ``` and check that the POST contain a cookie. From this POST login, it should return a blank page with different status codes. The two main methods of this server are:

- ```def login():``` This method received the request and set a cookie from it and return it. 
- ```def auth():``` This method decode the received cookie, check if it was tampered, if not if it is the admin or if no cookies were received.

## Exercise 3: [Attack] Client-side password verification.

We are going to bypass the authentication on the Very Secure<sup>TM</sup> login page [http://com402.epfl.ch/hw2/ex3/](http://com402.epfl.ch/hw2/ex3/).

To do that, we have to go to the element inspector of the webpage and find the script part of the webpage. Below a copy of some part of script.

```
if (username.length > 100) {
    alert("There's a difference between knowing the path and walking the path.");
        return;
    } 
else if (password.length > 100) {
    alert("The best answer to anger is silence.");
        return;
}
if (password != hash(username,mySecureOneTimePad)) {
    alert("I didn't say it would be easy, Neo. I just said it would be the truth.");
        return;
}
```
In this part of the code, we can see three things:

- Firstly, the username must have a size below 100 characters.
- Secondly, the password length must be below 100 characters.
- Finally the most important part, we can see that if the password is different from the hash function, we raise an alert and stop the execution of the script. 

From this part we can deduce that our password must be the hash(username, mySecureOneTimePad). knowing the oneTimePad we can deduce the password easily. To do that we can do it in two different ways:

- Either, recode the hash function used in the script in another programming language but it is cumbersome and not really recommended.
- The second way to do that is to take the javascript hash function which is:

```
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

```
And use either an online compiler or your own computer. I did it on [https://js.do](https://js.do) and put on the console:

```
<script>
var msg = 'lol';
var key = "Never send a human to do a machine's job";

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

document.write(hash(msg, key));

function show_random_number() {

  var random_number = Math.random(); // generate random number between 0 and 1
  alert(random_number); // show popup with a random number
  
}

</script>

```
Here the msg variable is in our case the username and completely random but with a length smaller than 100 and the key is our mySecureOneTimePad which written in the script has "Never send a human to do a machine's job". With this combination I got a hash which was "Igoa". 

Finally on the website, I put 'lol' as username and 'Igoa' as password to pass the test.














