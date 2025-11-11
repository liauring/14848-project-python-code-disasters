import os

user_input = input("Enter filename: ")
os.system("cat " + user_input)  # ❗ Command Injection
