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

###############################################################


# This class consists of all the logic being used 
class Encryptor:
	partnum=0

# Constructor tackles the key generation using the SHA256 to be used for the AES encrytion
	def __init__(self, password):
		hasher=SHA256.new(password)
		self.key = bytes(hasher.digest())

# This function is intended to provide the padding for the block size if the data left out doesnt fit the 16byte so padding is added, otherwise AES won't encrypt
	def pad(self, s):
		return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

# Encrypting the Message 
	def encrypt(self, message, key, key_size=256):
		message = self.pad(message)
		iv = Random.new().read(AES.block_size)
		cipher = AES.new(key, AES.MODE_CBC, iv)
		return iv + cipher.encrypt(message)


# Decrypting the Message
	def decrypt(self, ciphertext, key):
		iv = ciphertext[:AES.block_size]
		cipher = AES.new(key, AES.MODE_CBC, iv)
		plaintext = cipher.decrypt(ciphertext[AES.block_size:])
		return plaintext.rstrip(b"\0")


# Reading file and fedding the data to decrypt and some other logic
	def decrypt_file(self, file_name,flag=None):
		with open(file_name, 'rb') as fo:
			ciphertext = fo.read()

		dec = self.decrypt(ciphertext, self.key)

		if flag==1:
			with open("hash.txt","r+") as hsh:
				hashFile = hsh.read().strip()
				hashData = hashlib.md5(dec).hexdigest()
				print("hashfile = {}".format(hashFile))
				print("hashData = {}".format(hashData))
				time.sleep(2)
				if hashFile != hashData:
					return False

		with open(file_name[:-4], 'wb') as fo:
			fo.write(dec)
		os.remove(file_name)


# Reading file and fedding the data to encrypt and some other logic
	def encrypt_file(self, file_name,flag=None):
		with open(file_name, 'rb') as fo:
			plaintext = fo.read()
		
		if flag==1:
			if not os.path.exists("hash.txt"):                  # caller handles errors
				os.mknod("hash.txt") 
			with open("hash.txt","w+") as hsh:
				hsh.write(hashlib.md5(plaintext).hexdigest())

		enc = self.encrypt(plaintext, self.key)
		with open(file_name + ".enc", 'wb') as fo:
			fo.write(enc)
		os.remove(file_name)


