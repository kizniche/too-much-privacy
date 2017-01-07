#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import fcntl
import getpass
import gnupg
import hashlib
import logging
import os
import random
import re
import string
import sys
import termios
import threading
import tty

from gnupg import _logger
from pprint import pprint

# Set up logging
log = _logger.create_logger(9)
# Levels:
# 0    NOTSET   Disable all logging.
# 9    GNUPG    Log GnuPG's internal status messages.
# 10   DEBUG    Log module level debuging messages.
# 20   INFO     Normal user-level messages.
# 30   WARN     Warning messages.
# 40   ERROR    Error messages and tracebacks.
# 50   CRITICAL Unhandled exceptions and tracebacks.
log.setLevel(20)

NEWKEY_DIR = './TMP-bit-key'
NAME = 'Someone'
NAME_COMMENT = None
NAME_EMAIL = 'someone@example.com'
EXPIRE_DATE = None
PASSPHRASE = None
KEY_TYPE = 'RSA'
KEY_USAGE = 'cert'
KEY_LENGTH = 8192
SUBKEY_TYPE = 'RSA'
SUBKEY_USAGE = 'sign'
SUBKEY_LENGTH = 4096
KEYSERVER = None
PREFERENCES = None


def check_keys():
	gpg = gnupg.GPG(homedir=NEWKEY_DIR,
									binary='gpg',
									verbose=True)

	# Generate key if it doesn't exist
	if not os.path.isfile('keys_pub_priv.asc'):
		try:
			os.system('rm -rf TMP-bit-key')
			gpg.encoding = 'utf-8'

			NAME = raw_input("Name:")
			NAME_EMAIL = raw_input("Email:")

			phrases_dont_match = True
			while phrases_dont_match:
				PASSPHRASE = getpass.getpass("Passphrase:")
				passphrase_re = getpass.getpass("Reenter Passphrase:")
				if PASSPHRASE != passphrase_re:
					print("Passphrases don't match. Try again.")
				else:
					phrases_dont_match = False

			allparams = {'name_real': NAME,
			             'name_comment': NAME_COMMENT,
			             'name_email': NAME_EMAIL,
			             'expire_date': EXPIRE_DATE,
			             'passphrase': PASSPHRASE,
			             'key_type': KEY_TYPE,
			             'key_usage': KEY_USAGE,
			             'key_length': KEY_LENGTH,
			             'subkey_type': SUBKEY_TYPE,
			             'subkey_usage': SUBKEY_USAGE,
			             'subkey_length': SUBKEY_LENGTH,
			             'keyserver': KEYSERVER,
									 'preferences': PREFERENCES}

			useparams = {}
			for key, value in allparams.items():
				if value:
					useparams.update({key: value})

			input_data = gpg.gen_key_input(save_batchfile=True,
                                     **useparams)
			log.info("Generated GnuPG batch file:\n {batch}".format(batch=input_data))

			key = gpg.gen_key(input_data)
			fingerprint = key.fingerprint

			if not fingerprint:
				log.error("Key creation seems to have failed: %s" % key.status)
				return None, None

			log.info("Key:\n{key}".format(key=key))

			ascii_armored_public_keys = gpg.export_keys(key) # same as gpg.export_keys(key, False)
			ascii_armored_private_keys = gpg.export_keys(key, True) # True => private keys
			with open('keys_pub_priv.asc', 'w') as f:
				f.write(ascii_armored_public_keys)
				f.write(ascii_armored_private_keys)
			log.info("Key successfully generated.")
		except Exception as except_msg:
			log.error("Error while generating key: {err}".format(err=except_msg))


def encrypt_letter(input_letter):
	"""Encrypt every character entered using PGP"""
	# input_letter = raw_input('Letter: ')
	if len(input_letter) > 1:
		log.error("Error: Greater than 1 character: {char}".format(char=len(input_letter)))
		sys.exit()
		
	# Create random string of 125 characters
	random_id = ''.join([random.choice(
		string.ascii_letters + string.digits + string.punctuation + ' ') for _ in xrange(124)])

	# Chose random number between 0 and 124
	int_place_in_string = random.randint(0, 124)

	# Create random number and random string, then place input letter
	# into string at position determined by random number
	str_secret = "{0:0>3}".format(int_place_in_string) + random_id[:int_place_in_string-1] + input_letter + random_id[int_place_in_string-1:]
	# print(str_secret)

	# Create SHA256 hash from secret string
	input_str_hash = hashlib.sha512(str_secret.encode('utf-8'))
	hex_dig = input_str_hash.hexdigest()
	# print(hex_dig)

	# Import Key
	gpg = gnupg.GPG(homedir='gpghome')
	key_data = open('keys_pub_priv.asc').read()
	import_result = gpg.import_keys(key_data)
	# pprint(import_result.results)

	# List Keys
	public_keys = gpg.list_keys()
	private_keys = gpg.list_keys(True)
	# print('public keys:')
	# pprint(public_keys)
	# print('private keys:')
	# pprint(private_keys)

	# Encrypt Data
	unencrypted_string = str_secret
	encrypted_data = gpg.encrypt(unencrypted_string, public_keys[0]['keyid'])
	encrypted_string = str(encrypted_data)
	# print('\nok: {ok}'.format(ok=encrypted_data.ok))
	# print('\nstatus: {stat}'.format(stat=encrypted_data.status))
	# print('\nstderr: {err}'.format(err=encrypted_data.stderr))
	log.info('unencrypted_string:\n{ue_str}'.format(ue_str=unencrypted_string))
	log.info('encrypted string:\n{e_str}'.format(e_str=encrypted_string))

	return encrypted_string


def decrypt_letter(encrypted_string):
	gpg = gnupg.GPG(homedir='gpghome')

	# Import Key
	key_data = open('keys_pub_priv.asc').read()
	import_result = gpg.import_keys(key_data)
	# pprint(import_result.results)

	# Decrypt string
	decrypted_data = gpg.decrypt(encrypted_string, passphrase='my passphrase')
	log.info("Decrypted string:\n{msg}".format(msg=decrypted_data))

	# Get letter position from first 3 numbers
	letter_position = int(str(decrypted_data)[:3])
	log.info("Letter position:\n{pos}".format(pos=letter_position))

	# Determine letter
	decrypted_letter = str(decrypted_data)[letter_position+2]
	log.info("Decrypted letter:\n{letter}".format(letter=decrypted_letter))


def is_ascii(letter):
	"""Check if ascii"""
	try:
		letter.decode('ascii')
	except UnicodeDecodeError:
		return False
	return True

def getch():
	"""Get one character at a time"""
	fd = sys.stdin.fileno()

	oldterm = termios.tcgetattr(fd)
	newattr = termios.tcgetattr(fd)
	newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
	termios.tcsetattr(fd, termios.TCSANOW, newattr)

	oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

	try:        
		while 1:
			try:
				c = sys.stdin.read(1)
				break
			except IOError:
				pass
	finally:
		termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
		fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
	return c

class ReadChar():
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setraw(sys.stdin.fileno())
        return sys.stdin.read(1)
    def __exit__(self, type, value, traceback):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)


class DataController(threading.Thread):
	def __init__(self, ready):
		threading.Thread.__init__(self)
		self.letter = ''
		self.string = ''
		self.ready = ready
		self.running = True

	def run(self):
		self.ready.set()
		while self.running:
			if len(self.string) > 0:
				encrypted_string = encrypt_letter(self.string[0])
				decrypted_letter = decrypt_letter(encrypted_string)
				self.string = self.string[1:]
		log.info("Letter thread stopped")

	def letter_add(self, letter):
		self.string = self.string + letter

	def stopController(self):
		self.running = False

	def isRunning(self):
		return self.running


if __name__ == "__main__":
	check_keys()
	log.info("Initializing letter thread")
	ready = threading.Event()
	thread_letters = DataController(ready)
	thread_letters.daemon = True
	thread_letters.start()
	ready.wait()
	print("Initialization complete. Begin Typing:\n")
	while True:
		try:
			# with ReadChar() as rc:
				# letter = rc
			letter = getch()
			if is_ascii(letter):
				print(letter, end="")
				thread_letters.letter_add(letter)
		except KeyboardInterrupt:
			log.info("Keyboard Interrupt: Closing program.")
			if thread_letters.isRunning():
				thread_letters.stopController()
				thread_letters.join()
			sys.exit()
