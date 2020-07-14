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


# This method is responsible for splitting the files into pieces
	def splitFile(self,fromfile, todir, chunksize):
		file = fromfile.split("/")[-1]
		if not os.path.exists(todir):                  # caller handles errors
			os.mkdir(todir)                            # make dir, read/write parts
		else:
			for fname in os.listdir(todir):            # delete any existing files
				os.remove(os.path.join(todir, fname)) 
		
		time.sleep(1)
		input1 = open(fromfile, 'rb')                   # use binary mode on Windows
		while True:                                       # eof=empty string from read
			chunk = input1.read(chunksize)              # get next part <= chunksize
			if not chunk: break
			self.partnum  = self.partnum+1
			filename = os.path.join(todir, ("{}{:04}".format(file,self.partnum)))
			fileobj  = open(filename, 'wb')
			fileobj.write(chunk)
			fileobj.close() 
			self.encrypt_file(filename)                           # or simply open(  ).write(  )
		input1.close()

		os.remove(fromfile)


# This is to retrieve the chunks from their locations
	def retrieveChunks(self,todir,filename,folder1,folder2):
		if not os.path.exists(todir):                  # caller handles errors
			os.mkdir(todir) 
		else:
			for fname in os.listdir(todir):            # delete any existing files
				os.remove(os.path.join(todir, fname)) 
		time.sleep(1)
		db = sqlite3.connect("data.db")
		cursor = db.execute("select parts from Files where fname='"+filename.strip()+"'")
		files=""

		data = cursor.fetchall()
		
		if len(data) == 0:
			print("There is no such encrypted file!")
			time.sleep(1)
			db.commit()
			db.close()
			self.encrypt_file("data.db")
			exit()

		for line in data:				
			files+=''.join(line)

		filechunks = files.split(",")[:-1]

		for fi in filechunks:
			if (int(fi.split(".")[-2][-4:]) % 2 ) == 0:
				shutil.move(os.path.join(folder1,fi),os.path.join(todir,fi))
			else:
				shutil.move(os.path.join(folder2,fi),os.path.join(todir,fi))

		for fname in os.listdir(todir):           # decrypt parts
				self.decrypt_file(os.path.join(todir, fname))
		db.execute("delete from Files where fname='"+filename.strip()+"'")
		db.commit()
		db.close()

# this is to hide the parts of files to different locations
	def hideChunks(self,filename,fromdir,folder1,folder2):
		files=""
		
		if not os.path.exists(folder1):                  # caller handles errors
			os.mkdir(folder1)
		if not os.path.exists(folder2):                  # caller handles errors
			os.mkdir(folder2)  

		time.sleep(1)
		for fname in os.listdir(fromdir):            # decrypt parts
				files+=fname+","
				if (int(fname.split(".")[-2][-4:]) % 2 ) == 0 :
					shutil.move(os.path.join(fromdir,fname),os.path.join(folder1,fname))
				else:
					shutil.move(os.path.join(fromdir,fname),os.path.join(folder2,fname))
		db=sqlite3.connect("data.db")
		db.execute("insert into Files(fname,parts) values('"+filename+"','"+files+"')")
		db.commit()
		for fname in os.listdir(fromdir):
			os.remove(os.path.join(fromdir,fname))
		db.close()

# Joining the file chunks to remake the original file
	def joinFile(self,fromdir, tofile,readsize):
		output = open(tofile, 'wb')
		parts  = os.listdir(fromdir)
		parts.sort()
		for filename in parts:
			filepath = os.path.join(fromdir, filename)
			fileobj  = open(filepath, 'rb')
			while 1:
				filebytes = fileobj.read(readsize)
				if not filebytes: break
				output.write(filebytes)
			fileobj.close()
		output.close()


