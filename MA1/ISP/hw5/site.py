# Exercise 2

import sys
import populate
from flask import Flask
from flask import request, jsonify
import pymysql


app = Flask(__name__)
username = "root"
password = "root"
database = "hw5_ex2"

#app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = username
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = database

# This method returns a list of messages in a json format such as
# [
# { "name": <name>, "message": <message> },
# { "name": <name>, "message": <message> },
# ...
# ]
# If this is a POST request and there is a parameter "name" given, then only
# messages of the given name should be returned.
# If the POST parameter is invalid, then the response code must be 500.


@app.route("/messages", methods=["GET", "POST"])
def messages():
    with db.cursor() as cursor:
        # your code here
        if request.method == 'POST':
            data = request.form
            name = data.get('name')

            if name is not None :
                sql = "SELECT message FROM hw5_ex2 WHERE name =%s"
                cursor.execute(sql,(name,))
                result = cursor.fetchall()
                message = result[0][0]
            else :
                return 500
            json_ret = jsonify(name = name, message = message)
            return json_ret, 200
        else:
            sql = "SELECT name, message FROM hw5_ex2"
            cursor.execute(sql,(name,))
            result = cursor.fetchall()
            query =[jsonify(name = row[0], message= row[2]) for row in result]
            return query, 200
    return 200



# This method returns the list of users in a json format such as
# { "users": [ <user1>, <user2>, ... ] }
# This methods should limit the number of users if a GET URL parameter is given
# named limit. For example, /users?limit=4 should only return the first four
# users.
# If the paramer given is invalid, then the response code must be 500.
@app.route("/users", methods=["GET"])
def contact():
    with db.cursor() as cursor:
        # your code here
        if request.method == 'GET' :
            data = request.args
            limit = data.get('limit')
            limit = int(limit)

            if limit is not None :
                sql = "SELECT users FROM hw5_exo2 LIMIT %d"
                cursor.execute(sql,(limit,))
                result = cursor.fetchall()
                json_ret =jsonify(users = (row[0] for row in result))
                return json_ret, 200
            else:
                return 500
        else :
            return 200


if __name__ == "__main__":
    db = pymysql.connect("localhost",
                         username,
                         password,
                         database)
    with db.cursor() as cursor:
        populate.populate_db(cursor)
        db.commit()
    print("[+] database populated")

    app.run(host='0.0.0.0', port=80)
