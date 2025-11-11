import os

user_input = input("Enter filename: ")
os.system("cat " + user_input)  # ❗ Command Injection

import sqlite3

user = input("Enter username: ")
db = sqlite3.connect("users.db")
cursor = db.cursor()
cursor.execute("SELECT * FROM users WHERE name = '" + user + "'")  # ❗ SQL Injection

import sys


def do_eval(user_input):
    # insecure: eval on user-supplied input
    return eval(user_input)


if __name__ == "__main__":
    # simulate untrusted input
    print(do_eval(sys.argv[1]))
