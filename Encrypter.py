#!/usr/bin/python3
################################################
'''
- This script takes the file input from the user.
- Break the file into parts each with 25KB size
- Encrypt those parts
- Move those parts to the 2 folders provided by user 
- Odd parts to be added to the folder2 & even to folder1
- All the record of the files and parts is to be maintined in the database file 
- The database file containing the records is also encrypted based in the key/password provided by the user.
- It can also encrypt the complete folders performing the above mentioned operations on each of the files of in the folder
- All the encryption here in this is Symmetric AES CBC


Author: Umair Ahmed (E@gle Invectus)
Created on: 29th Mar, 2020
'''

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

def main():
	if os.path.isfile('data.db.enc'):
		while True:
			password = str(input("Enter password: "))
			enc = Encryptor(bytes(password,"utf-8"))
			enc.decrypt_file("data.db.enc")
############################
# to be tackled Latter		
		# if not enc.decrypt_file("data.db.enc"):
		# 	print("Wrong Password Entered!")
		# 	time.sleep(1)
		# 	exit()
#######################
			p = ''
			db=sqlite3.connect("data.db")
			cursor = db.execute("select pwd from Password")
			for line in cursor:
				p+=line[0]
			if p == password:
				db.close()
				enc.encrypt_file("data.db")
				break

		while True:
			clear()
			choice = int(input(
				"1. Press '1' to encrypt file.\n2. Press '2' to decrypt file.\n3. Press '3' to Encrypt all files in the directory.\n4. Press '4' to decrypt all files in the directory.\n5. Press '5' to exit.\n"))
			clear()
			if choice == 1:
				enc.decrypt_file("data.db.enc")
				filename=str(input("Enter name of file to encrypt: "))
				enc.splitFile(os.getcwd()+"/"+filename,os.getcwd()+"/folder",25000)
				enc.hideChunks(filename,os.getcwd()+"/folder",os.getcwd()+"/folder1",os.getcwd()+"/folder2")
				enc.encrypt_file("data.db")
			elif choice == 2:
				enc.decrypt_file("data.db.enc")
				filename=str(input("Enter name of file to decrypt: "))
				enc.retrieveChunks(os.getcwd()+"/folder",filename,os.getcwd()+"/folder1",os.getcwd()+"/folder2")
				enc.joinFile(os.getcwd()+"/folder",os.getcwd()+"/"+filename,25000)
				enc.encrypt_file("data.db")
			elif choice == 3:
				enc.encrypt_all_files()
			elif choice == 4:
				enc.decrypt_all_files()
			elif choice == 5:
				exit()
			else:
				print("Please select a valid option!")

	else:
		while True:
			clear()
			password = str(input("Setting up stuff. Enter a password that will be used for decryption: "))
			repassword = str(input("Confirm password: "))
			if password == repassword:
				enc = Encryptor(bytes(password,"utf-8"))
				break
			else:
				print("Passwords Mismatched!")
		db=sqlite3.connect("data.db")
		db.execute("create table if not exists Password(pwd varchar(500) primary key)")
		db.execute("create table if not exists Files(fname varchar(500) primary key, parts varchar(500))")
		db.execute("insert into Password(pwd) values('"+password.strip()+"')")
		db.commit()
		db.close()

	#######################
		enc.encrypt_file("data.db")
		print("Please restart the program after exit to complete the setup")
		time.sleep(2)


if __name__ == '__main__':
	main()
