#!/usr/bin/python3
################################################

# Some important Libraries to be added
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import os
import os.path
from os import listdir
from os.path import isfile, join
import time
import shutil
import sqlite3
import hashlib
from sys import platform


##############################################################

# Function intended to be used to clear the display after the input or other menu operations for CLI mode
clear = ""
if platform == "linux" or platform == "linux2":
    clear = lambda: os.system('clear')
elif platform == "darwin":
    clear = lambda: os.system('clear')
elif platform == "win32":
	clear = lambda: os.system('cls')


