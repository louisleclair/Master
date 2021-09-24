- [Exercise 1: [attack] P0wn it](#exercise-1-attack-p0wn-it)
  - [Exercise 1.1](#exercise-11)
    - [Where is the vulnerability?](#where-is-the-vulnerability)
    - [[Optional] Detour: the SQL table](#optional-detour-the-sql-table)
    - [How to attack it](#how-to-attack-it)
      - [Solution 1: blind attack](#solution-1-blind-attack)
      - [Solution 2: Filtering junk](#solution-2-filtering-junk)
    - [Python to the rescue](#python-to-the-rescue)
      - [A requests' request](#a-requests-request)
      - [Making a beautiful soup out of that](#making-a-beautiful-soup-out-of-that)
  - [Exercise 1.2](#exercise-12)
    - [Where is the vulnerability (II)?](#where-is-the-vulnerability-ii)
    - [[Optional] Detour: the second SQL table](#optional-detour-the-second-sql-table)
    - [The Attack](#the-attack)
    - [A wild Python sneaks in](#a-wild-python-sneaks-in)
- [Exercise 2: [defense] No SQL Injection!](#exercise-2-defense-no-sql-injection)
  - [You should know](#you-should-know)
    - [Flask](#flask)
      - [Routes](#routes)
    - [PyMysql](#pymysql)
    - [Python](#python)
  - [The solution](#the-solution)
    - [/messages](#messages)
      - [Errors](#errors)
    - [/users](#users)
      - [Simple case: no limit](#simple-case-no-limit)
      - [Going to the limit](#going-to-the-limit)
      - [Errors](#errors-1)

# Exercise 1: [attack] P0wn it

## Exercise 1.1

### Where is the vulnerability?

Before writing any code, let's try to understand what the injection is all about. As the hint suggests, we won't be attacking the form. We don't know enough about the internals of the webserver to blindly enter some text, and hope it will somehow return something.

We are interested in a hidden message. It makes sense to look at the `/message` page then. There should be one message, that exists in the database, that doesn't show here. By clicking one message ("_Show message_"), we see the author name, and some text. But more interesting is the URL: `http://<ip>/messages/id=9` (or some other integer). If we manually change that number to some other (like 2), we have an other message.

What (probably) happens behind is that this value is retrieved by the server, and inputted in a request of the like `SELECT ... WHERE ... AND id=...`. There are valid methods to input the ID in that request. And there are not so valid methods. For example, such an invalid method is to do the following:

```
request = "SELECT ... WHERE ... AND id='"
id = retrieve_id_from_url()
request = request + id + "'"
```

We can check our hypothesis. If we input some valid number (between 1 and 21 roughly), we have a message. If we input a number too big or some invalid string (containing letters for example), then we have _nothing_ (blank page, but it's a code 200 OK). But if we input the special character `'`, we have a nice cynical error page. This indicates that the SQL request failed.

### [Optional] Detour: the SQL table
Before going further, we can have a look at the SQL table for a better understanding. You can skip this step if you are already familiar with SQL.

Once connected to the docker, and logged in MySQL with the correct credential, what do we do? As you see in the interpreter, no database is selected (because before the input is written `[(none)]`). Let's see which database(s) exist:
```
>show databases;
+--------------------+
| Database           |
+--------------------+
| com402_1           |
| information_schema |
+--------------------+
```

`information_schema` is a by-product of Flask, not so interesting for us. Let's focus on the other one, and tell MySQL we will use it:
```
>use com402_1
```
Now, we can have a look at what table(s) are inside:

```
>show tables;
+--------------------+
| Tables_in_com402_1 |
+--------------------+
| contact_messages   |
+--------------------+
```
Quite simple, only one table. To understand what it consists of, we can ask MySQL to explain the table to us.
```
>explain contact_messages;
+---------+-----------------+------+-----+---------+----------------+
| Field   | Type            | Null | Key | Default | Extra          |
+---------+-----------------+------+-----+---------+----------------+
| id      | int(6) unsigned | NO   | PRI | NULL    | auto_increment |
| name    | varchar(100)    | NO   |     | NULL    |                |
| mail    | varchar(100)    | NO   |     | NULL    |                |
| message | varchar(200)    | NO   |     | NULL    |                |
+---------+-----------------+------+-----+---------+----------------+
```
This tells us everything we need to know. An unsigned int ID, and 3 texts (VARCHAR, texts of variable length, capped to 100 or 200).

Note that we don't look at the content of the database, because that would be cheating. We can perfectly manage without (and even without knowing any of this).



### How to attack it
Now we have our goal: carefully craft `id`, so that when it is appended to the request, we bypass the restriction on James Bond. So we have a request of the type `SELECT ... FROM ... WHERE ... AND id=' + id + '`. Somewhere, James Bond is filtered out. Either in the `WHERE` clause (like, `WHERE email NOT LIKE "james@bond%"`) or later in the webserver. In the latter case, it will be hard/impossible to bypass the restriction. So let's hope the filtering is done within SQL.

The goal is to corrupt the logic of the request. Let's imagine a base request for better understanding:

```sql
SELECT name, mail, message FROM com402_1 WHERE mail NOT LIKE 'james@bond%' AND id='<INPUT_HERE>'
```

Testing and debugging is not easy in the browser, because special characters are getting modified to "url-safe" ones. Trying multiple times is tedious. This is why using python (or another framework) is convenient. While we'll explain multiple solutions right below, see [Python to the rescue](#python-to-the-rescue) to have a somewhat automated framework.

#### Solution 1: blind attack
Probably the simplest way: add an "always true" logic: `or '1' = '1'`. Though, we have to be careful about quotes. If we just input `or '1' = '1'` as an ID, we would obtain

```sql
SELECT name, mail, message FROM com402_1 WHERE mail NOT LIKE 'james@bond%' AND id='or '1' = '1''
```
Which is totally incorrect. We would prefer
```sql
SELECT name, mail, message FROM com402_1 WHERE mail NOT LIKE 'james@bond%' AND id='1' or '1' = '1'
```

By extracting the interesting part (leaving the last quote, and not touching anything before the 1), we have our input: `1' or '1' = '1`

By sending this request, we completely obliterate any logic previously established in the query. Because in a `WHERE` clause, the `AND` and `OR` follow the [PEMDAS](https://en.wikipedia.org/wiki/Order_of_operations) rule, and because `AND` "is" a multiplication while `OR` "is" an addition, then the `AND` takes precedence over the `OR`. This means that whatever happens before in the query, adding a `OR True` will always validate. This means that the selection will grab everything.

**[Example]PEDMAS applied to SQL**<br>
Consider the following query (borrowed from [bennadel.com](https://www.bennadel.com/blog/126-sql-and-or-order-of-operations.htm))
```sql
SELECT
	name
FROM
	tag
WHERE
	1 = 0
AND
	1 = 0
OR
	1 = 1
AND
	1 = 0
AND
	2 = 2
OR
	1 = 1
AND
	2 = 2
```

Without parenthesis, it becomes hard to see what will happen. What is the order here ? The order of evaluation will change the outcome. Considering that `AND` is equivalent to a multiplication (`1 AND 0 = 0`, `1 AND 1 = 1`) and the `OR` is an addition (`1 OR 0 = 1`, `0 OR 0 = 0`), we use PEMDAS, and can draw parenthesis:

```sql
SELECT
	name
FROM
	tag
WHERE
	(
			1 = 0
		AND
			1 = 0
	)
OR
	(
			1 = 1
		AND
			1 = 0
		AND
			2 = 2
	)
OR
	(
			1 = 1
		AND
			2 = 2
	)
```
This is why adding a final `OR` will remove previous restrictions. Though, this method can't add a restriction: if a row was selected by the logic before the `OR`, it can't be "removed" with the one after.

#### Solution 2: Filtering junk
The previous solution works, but it's kind of ugly. We have a database with roughly 20 messages, and apparently only one from a "James" and it's the only hidden. It is easy for us to filter, or catch which one is different. But in a database with billions of entries, this becomes quite more cumbersome. Let's try and filter that.

As we saw before, a final `OR` will be evaluated last. It would be neat to use that to filter more than simply _select everything_

Consider the `WHERE` as two part: on the right side of our malicious `OR`, we can do whatever we want, while on the left side we can only chose the ID, and the rest of the logic is imposed. Thus the following idea: chose an ID that will select nothing on the left, and craft the right side to select exactly what we want.

First thing first: left side. An ID that select nothing is relatively easy. Try and change the ID to another integer (0, 100,...) and you will get nothing. Try a random string (not "too wild", with only alphanumeric), and you again get nothing. So the ID `298dfi` is sure to select nothing. Plus, if you took a look at the database, you saw that the ID is an integer and filtering by an ID that isn't an integer won't work. But not crash.

Then, the right side. It's not too difficult to craft a filter that only select the secret message: `... OR mail like 'james%` (don't forget to exclude the trailing quote). The name of the column is not too hard to guess, if you haven't looked at the database schema. It's very common to have names like `mail`, `email`, `user_email`,... Trying a few of them surely will work.

Small problem there: if you try this, you will get an error. The issue is that the percent sign `%` doesn't really go well in URLs. This sign is reserved to express other characters, and doesn't go through nicely (it's called [percent encoding](https://en.wikipedia.org/wiki/Percent-encoding)). Best to avoid it. Fortunately, we know the full email address of our target, and can get away with looking for it directly: `... OR mail = 'james@bond.mi5`

The final input will look like this:
```sql
e398w' OR mail = 'james@bond.mi5
```
Sending this input, you will get all the messages (well, only one in our case) sent by your target.

### Python to the rescue
Once you have installed the packages with your preferred method (pip, conda, pip3, virtualenv,...), we can start. The first (and actually not trivial) step is to import the two packages. `requests` is easy, but BeautifulSoup is a bit more tedious:
```python
import requests
from bs4 import BeautifulSoup
```

Then, we define some useful constants:

```python
addr = "http://0.0.0.0:5001"
url = addr + "/messages"
```

#### A requests' request
Working with `requests` is fairly easy. You just do `requests.get(url)`, or `requests.post(url)`,... We can also specify headers, parameters, and a bunch of other things. For parameters (in our case, `id=...`), we can either "hardcode" them in the URL (`/messages?id=...`), or specify them with a dictionary (see [the doc](https://requests.readthedocs.io/en/latest/user/quickstart/#passing-parameters-in-urls)). A request simply becomes

```python
payload = {"id": "SOME_MALICIOUS_INPUT"}
r = requests.get(url, params=payload)
```
Note that `r` is a complex object, that contains the whole response. Some interesting properties:
* `r.text` is the actual HTML of the response, what we usually are interested in,
* `r.status_code` is the HTTP status code of the response (e.g. 200 for OK),
* `r.headers` contains a dictionary with the headers of the response.

#### Making a beautiful soup out of that
Now that we sent a request to the server and got a response, we are stuck with one giant string containing the whole HTML of the webpage. Yuck! Parsing that manually will take ages!

That's the exact reason BeautifulSoup came to be: save that time. It will parse that HTML, and leave us with a nice high-level object that we can query. It allows to query for specific tags, with specific parameters, look for children or parents of some elements.

The first step is to put on your chef's hat, and _prepare the soup_, from the big string of HTML we spoke about earlier:

```python
soup = BeautifulSoup(r.text, "html.parser")
```

If you take a look at the HTML of `/messages`, you will see that messages follow a pattern: they are contained in `div` (a fundamental HTML tag), have classes `p-2`, `m-2`, and `card`. So we create a filter and iterate through all such elements:
```python
for div in soup.find_all('div',{"class":"p-2 m-2 card"}):
    ...
```
Note the syntax: we search all div that have the mentioned classes, and iterate through them. Those elements `div` are high-level objects that again contain a lot of methods, such as the ability to find parents or children, or start a new search in them.

We don't have much indicator for what the secret message will look like; our best shot is to look for a message written by `james`. So we check whether `james` is present within each div:

```python
    if "james" in div.text:
        ...
```
Finally, we look for the children of those div of type `blockquote`, and print their content:
```python
        for blockquote in div.find_all('blockquote'):
			print(blockquote.text)
```

Great! We now have a nice framework to test our injections, by modifying the text we want and launch a script. This could be improved even more, with additional debug info, and perhaps reading the injection from the arguments of the script. This way, there would be nothing to change in the script, just adapt the call of the script.


## Exercise 1.2
Like before, we will solve the exercise in two ways: we will first take a quick look at the database, and then solve the exercise with and without the supposition that we did.

### Where is the vulnerability (II)?
We now apparently focus on the `/users` page. As before, we have no reason to believe the homepage's form allows for an injection, as we don't receive significant feedback when we submit a text. We _may_ use XSS, but it's not the point here.

In modern applications, when you have such a table to display and want to allow client-side filtering, you usually select the superset of what you want to display, and send that to the client. Then, with client-side methods (such as a flavour of JS), you allow for dynamic filtering. You have everything, but only filter the view.

The website makes a huge mistake here: They have their initial query do display "everything", but then every time you enter a query, it is sent to the server, a SQL query is done with that, and you receive your result. We can see that by taking a look at the _Network_ tab of the development console of your browser. When you hit _Enter_, a `POST` request is made and in the request (in the `form-data` field), you have your request. As a result, the server responds with the filtered content, and some css/js. Your input is being processed by the server, that's interesting! If they don't sanitize your input (spoiler, they don't), you found a powerful vulnerability.
### [Optional] Detour: the second SQL table
 This will be quick and crude. For a more detailed _how-to_, refer to the [same section](#optional-detour-the-sql-table) in the other exercise.

 We login using the provided credentials (different from the first exercise), and find a different database, with one table `users` . After asking MySQL to explain its schema to us, we have the following one:

 ```
 > explain users;
+----------+-----------------+------+-----+---------+----------------+
| Field    | Type            | Null | Key | Default | Extra          |
+----------+-----------------+------+-----+---------+----------------+
| id       | int(6) unsigned | NO   | PRI | NULL    | auto_increment |
| name     | varchar(100)    | NO   |     | NULL    |                |
| password | varchar(40)     | NO   |     | NULL    |                |
+----------+-----------------+------+-----+---------+----------------+
```

Nothing fancy here, but it's useful to have the names of the fields. This is just a help, because we could easily have guessed the name of the table and the fields, even without access.

### The Attack
What (likely) happens after a query, behind the scene? Notice each line is accompanied with the ID (or _some_ ID) of the user. Thus, there most likely is a request of the type
```python
"SELECT id, name FROM users WHERE name = '" + QUERY_FROM_USER + "'"
```
Keep in mind that it's in the event that there is a vulnerability, so it's a supposition. It's also possible that our input is sanitized, or that they do that in a viable way that doesn't simply append our text. But if there was no vulnerability, the exercise would be over, and you would be sad.

Our goal is different from before. In the first exercise, we had a limit on _rows_: some were filtered out, and we had to use SQL logic to broaden the selection and select the rows that were interesting. Here, we have a limit on _columns_: we see all rows, but somehow have to get information from another column that the ones selected.

This is a common task in SQL. The method of choice for that is to use the `UNION` operator. This operator allows you to write a completely new request (`SELECT ... FROM ...`), and append it below the previous results, as additional rows. With this method, we can arbitrary content from arbitrary columns and append it to the result intended by the web app. There is a catch however: the number of columns must match. If the first statement selected 19 columns, the second statement of the `UNION` must also select 19 columns. This number can be a bit tedious to find, and often requires several tries. Luckily in our case, we can suspect that there are only 2 columns selected in the original query: `id` and `name`.

So, we have to write a complete query, that selects what we want, and has exactly 2 columns. It's knowing (or not) the names of the columns and tables, it's fairly easy:

 ```sql
 SELECT name,password FROM users WHERE name = 'inspector_derrick'
 ```

 This will append one (or multiple, if applicable) rows to the query, and will contain the name and password of Inspector Derrick. If you want to be extra-evil, you can modify the `WHERE` clause to include everyone: `WHERE '1'='1'`, or `WHERE name != 'someBodyOnceToldMe'`. You can't remove the clause altogether, because you need to take into account the quote that will be appended after your query. If it's extraneous, the query won't run. So you need to have a quote as the very last character of your query, and remove it.

 The final step is to craft a complete input to give to the form. Nothing fancy: as before, we have to take care of quotes, and add our query with a union. You can chose to input an "invalid" query for the first part, in order to have a clean output, or put any name. A correct string to send would be the following:

 ```
somebodynotindatabase' UNION SELECT name,password FROM users WHERE name = 'inspector_derrick
```

### A wild Python sneaks in
Once again, we will showcase the use of Python. It may not be necessary, but by gaining insight on how to use Python, requests and BeautifulSoup, you surely will step up your hacking game. We won't be as detailed as for the first exercise. You can go back if you need better understanding of requests and BS4

Just like for GET, `requests` allows to make POST requests. The syntax is [fairly similar](https://www.w3schools.com/PYTHON/ref_requests_post.asp). You must specify the URL, and if you wish to add form-data you pass a dictionary as the `data` parameter.

To know the form of the dictionary, you must take a look at the request your browser does when doing a legitimate search. Open the console/developers tools of your browser, go to the _Network_ tab, and do a search. By digging a little bit, you will find that the data of the request is within a parameter `name`. The request looks like `name=inspector_derrick`. Great, you have your parameter name!

The payload and the code will look like that:

```python
payload = {"name": "MALICIOUS_INPUT_HERE"}
r = requests.post(url, data=payload)
```

Now for the cooking of the soup: if you take a look at the HTML of the page, you will see that entries are in `<p>` tags, with class `list-group-item`. You thus simply have to filter by that, and print the text:

```python
soup = bs4.BeautifulSoup(r.text, "html.parser")
for entry in soup.find_all("p", {"class": "list-group-item"}):
    print(entry.text)
```

Which will print every line of your request.

Bonus: the output seems to have the form `firstParOfTheRequest:SecondPartOfTheRequest`. By splitting at that colon, you can better parse the output.

```python
username, password = entry.text.split(":", 1)
```
Specify the `1` in `split` to ensure a colon in the password is not split, if any.


# Exercise 2: [defense] No SQL Injection!
In this exercise, we will have to re-do some of what you hacked in the previous exercise. Fortunately, we only have to return raw data, which is easier to handle rather than templates and HTML. First we'll go through some background information about Flask, Python, PyMysql,... and get to actual coding later. If you already are familiar with everything here, feel free to skip.

##  You should know
### Flask
Flask is a great framework for quick-and-dirty webservers. It allows to setup a PoC server in a few lines, and showcase your content easily. More in-depth apps are also possible, but require a bit more work.
#### Routes
In the provided template, you can see two functions (`contact` and `messages`), both of which have a [_decorator_](https://realpython.com/primer-on-python-decorators/) (the `@app.route` above). This indicates to flask that this function should be called whenever a request to the indicated path (respectively `/users` and `/messages`) is done. You can also specify which methods (by default, only GET) is/are accepted.

The return value from these methods is the actual content of your HTTP response. If it only contains raw data, raw data will be displayed (great for a REST API). You can also specify, with your content, an integer that will be the HTTP status code (by default, 200).

```python
return "Some content" # <-- this will be displayed in the browser, status 200
return "Some other content", 301 # <-- Browser knows it's a 301, displays the string.
```

When in a function that accepts multiple methods (`GET` and `POST` notably), you don't immediately know which one it is. For that, you must first import `flask.request` (which provides a bunch of great functions), and then switch on `request.method`:
```python
from flask import request # already done in the template
...

@app.route(...)
def someroute():
    if request.method == "GET":
        #do stuff
        return "Absolutely valid", 200
    elif request.method == "POST":
        # some more stuff
        return "All good" # 200 is returned by default
    else:
        return "Nope, only GET or POST", 418
```

Finally, when returning "raw" data (not a webpage), it's good practice to "jsonify" it (make it interpretable by JS).

Finally, in a `GET` or `POST` request, you can easily retrieve the form data (for `POST`) or arguments values (like `/messages?arg1=somevalue&arg2=someothervalue`). Respectively:
* Form values: `request.form`, a dictionary `{argname: argvalue}`
* Arguments: `request.args`, identical structure.

Remember that it's good practice to not directly access the desired value, but do a `.get`, more robust

```python
args = request.args

value = args["argument_name"]  # <- OK: will throw an error if the key is not in the dict

value = args.get("argument_name", "default_value")  # <- Best: if key not found, returns the default value
```
### PyMysql
PyMysql is a great client library to connect to MySQL databases. Its basic functionalities can be boiled down to 4 steps:
1. Create a connection (the `db` object, provided in template)
2. When necessary (JIT), create (then destroy) a _cursor_, on which you can execute queries (also already provided)
3. On this cursor, _execute_ your query (append it to the database's queue of orders). Nothing is done yet, neither returned yet.
4. Actually commit:
   * If you don't expect a result (`INSERT`, `CREATE`, `DELETE`,...), you must simply call `commit()` on the cursor (not needed here)
   * If you expect a result (`SELECT`), you must _fetch_ the results (either one by one with `fetchone()`, or all at once with `fetchall()`).

We already provided a skeleton code, on which the connection and the cursors are created. Now you only have to create the queries, execute them and fetch the results.

**About queries**<br>
As hinted, there is a _bad_ way, and a _good_ way of executing a query. The bad way is what you attacked during exercise 1: you create a single string with everything in it, and call `cursor.execute()` on it. It may not be terrible if you only use trusted data source, or hardcoded queries. But cursors can execute multiple queries within one call, and don't do many checks. You can try and sanitize the user's input yourself but it's generally a bad idea (we know you're smart, but smarter people have already done a better job for you).

The _good_ way is to use parameters to your call. In your query, specify with a placeholder where data is supposed to go, and give to the cursor the query and the data separately. PyMysql will ensure there is no malicious code here, and only allow for your query to run.

```python
## BAD WAY
username = get_data_from_user()
bad_query = "SELECT id, name FROM users WHERE name LIKE '" + username + "'"
cursor.execute(bad_query)
```
This is exactly what went wrong in exercise 1. You allow the user to put anything int he username, including injections.

```python
## CORRECT WAY
username = get_data_from_user()
good_query = "SELECT id, name FROM users WHERE name LIKE %s"
cursor.execute(good_query, username)
```
With that method, `username` will automatically be parsed. If it only contains odd values, it will be just another string, without injection. If an injection is tried, it will simply break the query, and throw an error without completing. As a good programmer, you must expect this to happen, and catch the error, to have a normal flow.

### Python
Speaking about errors: because our code will throw a lot of errors when processing malicious input, we must catch them and "[fail gracefully](https://en.wikipedia.org/w/index.php?title=Fail_gracefully)".

The Python way of doing so is to use `try/except`, like so:

```python
try:
    x = 1/0
except ArithmeticError:
    print("Can't divide by 0")

# and continue
```
Everything between the `try` and the `except` that throws an error will be intercepted, and go to the `except` clause. You can also catch multiple errors at once:

```python
try:
    ...
except (ArithmeticError, OSError, ValueError):
    ...
```

And finally, if you want to be fool-proof, simply catch everything:

```python
try:
    ...
except Exception: # the base class of all errors
    ...
```


## The solution
### /messages
Let's get on to the first step, `/messages`. Let's start simply, and add some checks and safeties later. The first step is to differentiate between a `GET` and a `POST`:

```python
if request.method == "GET":
    pass
elif request.method == "POST":
    pass
```

The `GET` is the simplest, as it doesn't require users' input:
```python
if request.method == "GET":
    sql = "SELECT name, message FROM messages"
    cursor.execute(sql)
    json = []
    for name, message in cursor.fetchall():
        json.append({"name": name, "message": message})
    return jsonify(json)
```

Very simple and straightforward. Execute a simple query, fetch the results, and output a JSON object as required (list of dictionaries). No possible trouble here. Nice warmup.

The `POST` becomes more interesting. Now you have to retrieve data from the request's body, and use it wisely
```py
elif request.method == "POST":
    form = request.form
    name_value = form.get("name", None)
    if name_value is None:
        return "You must provide a 'name' when POSTing", 500
    sql = "SELECT name, message FROM messages WHERE name like %s"
    cursor.execute(sql, name_value)
    json = []
    for n, m in cursor.fetchall():
        json.append({"name": n, "message": m})
    return jsonify(json)
```

Let's break this down:
1. We retrieve the form data
2. We look for a `name` field.
3. If not present, reject, this is mandatory on `POST`.
4. If present, craft your query safely, say where the value should be, and give the query and the name to the cursor.
5. Finally, retrieve the results, format them, and return

Note that if someone give more than 1 field in the form (`name` and `malicious_arg` for example), our code simply ignores it.

#### Errors
Now, this code looks almost complete. There are some redundancies that are easy to fix, but globally it does the job. On a malicious input, our code won't execute the injection, but throw an error. In case of an error, Flask will automatically return a `500 Server Error` status, but it's not exactly a "failed gracefully". We surround then everything with a `try/except`. We could catch every exceptions, but it's bad practice. If something else goes wrong, we won't see it and mistake it for a malicious input. For example, if the database was to shut down, our website will be down and no error will appear. We restrict ourselves to the necessary. On a query with odd arguments, pymysql will throw a `ProgrammingError`.

```py
try:
    with db.cursor() as cursor:
        if request.method == "GET":
            ...
        elif request.method == "POST":
            ...
except pymysql.err.ProgrammingError:
    print("Sounds like a malicious input")
    return "Trying to hack me?" 500
```
With that, only `ProgrammingError`s will be caught, and we will notice the rest.

### /users
The procedure for this endpoint is roughly the same. Prepare a request, check if there is a valid argument in the URL, adapt consequently the query, get your results, format them, and return. The whole procedure will as before be surrounded by a `try/except` to ensure the program runs smoothly.

#### Simple case: no limit
Without worrying about user input, the code is quite simple:

```py
sql = "SELECT name FROM users"
cursor.execute(sql)
all_names = []
for name in cursor.fetchall():
    all_names.append(name[0])
json = {"users": all_names}
return jsonify(json)
```

Nothing fancy, it's exactly what we explained above. We must put `name[0]` and not just `name`, as opposed to before, because it's a tuple of size 1. When we select a multiple columns (as in `/messages`), by doing `for a,b in cursor.fetchall()`, we do _tuple unpacking_. It's also a tuple, but we split it. With only 1 column, Python doesn't know if we want to iterate through the tuples, or "unpack" the one element within.

#### Going to the limit
Now, we expect a user input. As explained in [the dedicated section](#flask), the way to read arguments in a URl is to do use `request.args`, that behaves like a dictionary. We check whether the user asked for a limit, adapt our query consequently, and execute.

```py
sql = "SELECT name FROM users"
args = request.args
limit = args.get("limit", None)
if limit is not None:
    sql += " LIMIT 0, %s"
    cursor.execute(sql, int(limit))
else:
    cursor.execute(sql)
# then fetchall(), format and return
```

Notice again how we don't simply append the limit, but specify a placeholder (`%s`) in the query, and let PyMysql do the replacement job. Much safer.

#### Errors
Just as before, we must check for a `ProgrammingError`, in case of a bad/malformed/malicious input. But we may encounter an error before: the `int(limit)` may very well crash if `limit` can't be interpreted as an int. In this case, it will throw a `ValueError`. We simply add this to our `try/except`:

```py
try:
    with db.cursor() as cursor:
        sql = "SELECT name FROM users"
        #....
        return jsonify(json)
except (pymysql.err.ProgrammingError, ValueError):
    return "Bad user, bad!", 500
```
