# This code has intentional issues that should trigger SonarQube blockers
import os
import sys


# SQL Injection vulnerability (should be detected as blocker)
def unsafe_query(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return query


# Command injection vulnerability
def unsafe_command(user_input):
    os.system("echo " + user_input)


# Hardcoded credentials (blocker)
