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

# Ensure log file path exists
log_path = os.path.join(os.path.join(os.getcwd(), 'gnupg'), 'test')
if not os.path.exists(log_path):
    os.makedirs(log_path)

# Set up logging
log = _logger.create_logger(0)
# Levels:
# 0    NOTSET   Disable all logging.
# 9    GNUPG    Log GnuPG's internal status messages.
# 10   DEBUG    Log module level debuging messages.
# 20   INFO     Normal user-level messages.
# 30   WARN     Warning messages.
# 40   ERROR    Error messages and tracebacks.
# 50   CRITICAL Unhandled exceptions and tracebacks.
log.setLevel(0)

NEWKEY_DIR = './gnupg-key'
# NAME = 'Someone'
NAME_COMMENT = None
# NAME_EMAIL = 'someone@example.com'
EXPIRE_DATE = None
# PASSPHRASE = None
KEY_TYPE = 'RSA'
KEY_USAGE = 'cert'
KEY_LENGTH = 4096
SUBKEY_TYPE = 'RSA'
SUBKEY_USAGE = 'sign'
SUBKEY_LENGTH = 4096
KEYSERVER = None
PREFERENCES = None

KEY_FILE_MINE = 'keys_mine_pub_priv.asc'
KEY_FILE_THEIR = 'keys_their_pub.asc'


class TooMuchPrivacy:
    """
    Too Much Privacy
    A class for encrypting and decrypting communication
    """

    def __init__(self, key_dir):
        self.gpg = gnupg.GPG(homedir=key_dir,
                             binary='gpg2')
        self.gpg.encoding = 'utf-8'
        self.passphrase = None

    def check_keys_exist(self):
        """
        Check if a PGP key already exists and if not, create one.
        Return True if yes or suscessfully created
        Return False if there was an error
        """
        # Generate key if it doesn't exist
        if os.path.isfile(KEY_FILE_MINE):
            self.passphrase = getpass.getpass("Enter passphrase to decrypt messages: ")
            self.import_keys()
            return True

        print("Key file not found. Let's generate one.")
        try:
            os.system('rm -rf TMP-bit-key')

            # Prompt user for name and email
            name = raw_input("Name:")
            email = raw_input("Email:")

            # Continuously ask for repeated passphrases until passphrases match
            phrases_do_not_match = True
            while phrases_do_not_match:
                self.passphrase = getpass.getpass("Passphrase:")
                passphrase_re = getpass.getpass("Reenter Passphrase:")
                if self.passphrase != passphrase_re:
                    print("Passphrases don't match. Try again.")
                else:
                    phrases_do_not_match = False

            # Dictionary of all gnupg parameters
            allparams = {'name_real': name,
                         'name_comment': NAME_COMMENT,
                         'name_email': email,
                         'expire_date': EXPIRE_DATE,
                         'passphrase': self.passphrase,
                         'key_type': KEY_TYPE,
                         'key_usage': KEY_USAGE,
                         'key_length': KEY_LENGTH,
                         'subkey_type': SUBKEY_TYPE,
                         'subkey_usage': SUBKEY_USAGE,
                         'subkey_length': SUBKEY_LENGTH,
                         'keyserver': KEYSERVER,
                         'preferences': PREFERENCES}

            # Create the batch file
            batchfile = self.create_batch_file(allparams)
            # Create the key
            key, fingerprint = self.create_key(batchfile)
            # Export private and public key
            self.export_keys(key)
            # Import keys
            self.import_keys()
            return True

        except Exception as except_msg:
            log.error("Error while generating key: {err}".format(err=except_msg))
            return False

    def create_batch_file(self, keyparams):
        """
        Create the batchfile for a new PGP key.
        :params dict keyparams: A dictionary of arguments for creating the key.
        :rtype: str
        :returns: A string containing the entire GnuPG batchfile.
        """
        useparams = {}
        for key, value in keyparams.items():
            if value:
                useparams.update({key: value})

        # Generate batchfile from gnupg parameters
        batchfile = self.gpg.gen_key_input(save_batchfile=True,
                                           **useparams)
        log.info("Generated GnuPG batch file:\n {batch}".format(batch=batchfile))
        return batchfile

    def create_key(self, batchfile):
        """Create PGP keys"""
        log.info("Generating key (this may take a while)...")
        key = self.gpg.gen_key(batchfile)
        fingerprint = key.fingerprint

        # Check if fingerprint exists
        if not fingerprint:
            log.error("Key creation seems to have failed: "
                      "{key_stat}".format(key_stat=key.status))
            return None, None

        return key, fingerprint

    def decrypt_string(self, str_encrypted):
        """Decrypt an encrypted string"""
        test = True
        while test:
            decrypted_data = self.gpg.decrypt(str_encrypted,
                                              passphrase=self.passphrase)
            if str(decrypted_data) == '':
                log.info("The passphrase you entered previously could not "
                         "decrypt the data. Please enter a new passphrase.")
                self.passphrase = getpass.getpass("Passphrase: ")
            else:
                test = False
        return decrypted_data

    def decrypt_letter(self, str_encrypted):
        """
        Decrypt an encrypted string, then return a single letter from the
        decrypted string based on the first three digits of the decrypted
        string that represents the position in the characters after the
        first three characters.
        """
        decrypted_data = self.gpg.decrypt(str_encrypted,
                                          passphrase=self.passphrase)
        log.info("Decrypted string:\n{msg}".format(msg=str(decrypted_data)))

        if str(decrypted_data) == '':
            log.info("The passphrase you entered previously could not "
                     "decrypt the data. Please enter a new passphrase.")
            self.passphrase = getpass.getpass("Passphrase: ")
            print("New passphrase accepted. Begin Typing:\n")
            return None

        # Get letter position from first 3 numbers
        letter_position = int(str(decrypted_data)[:3])
        log.info("Letter position:\n{pos}".format(pos=letter_position))

        # Determine letter
        decrypted_letter = str(decrypted_data)[letter_position + 3]
        log.info("Letter:\n{letter}".format(letter=decrypted_letter))

        return decrypted_letter

    def encrypt_letter(self, input_letter):
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
        str_secret = "{0:0>3}".format(int_place_in_string) + random_id[:int_place_in_string] + input_letter + random_id[
                                                                                                              int_place_in_string:]
        # print(str_secret)

        # Create SHA256 hash from secret string
        input_str_hash = hashlib.sha512(str_secret.encode('utf-8'))
        hex_dig = input_str_hash.hexdigest()
        # print(hex_dig)

        # List Keys
        public_keys = self.gpg.list_keys()
        private_keys = self.gpg.list_keys(True)
        # log.info('public keys:\n{pub_keys}'.format(pub_keys=public_keys))
        # pprint(public_keys)
        # print('private keys:')
        # pprint(private_keys)

        # Encrypt Data
        unstr_encrypted = str_secret
        encrypted_data = self.gpg.encrypt(unstr_encrypted, public_keys[0]['keyid'])
        str_encrypted = str(encrypted_data)
        # print('\nok: {ok}'.format(ok=encrypted_data.ok))
        # print('\nstatus: {stat}'.format(stat=encrypted_data.status))
        # print('\nstderr: {err}'.format(err=encrypted_data.stderr))
        log.info('unstr_encrypted:\n{ue_str}'.format(ue_str=unstr_encrypted))
        log.info('encrypted string:\n{e_str}'.format(e_str=str_encrypted))

        return str_encrypted

    def encrypt_string(self, str_unencrypted):
        """Encrypt every character entered using PGP"""
        # List Keys
        public_keys = self.gpg.list_keys()
        private_keys = self.gpg.list_keys(True)
        # log.info('public keys:\n{pub_keys}'.format(pub_keys=public_keys))
        # pprint(public_keys)
        # print('private keys:')
        # pprint(private_keys)

        # Encrypt Data
        encrypted_data = self.gpg.encrypt(str_unencrypted, public_keys[0]['keyid'])
        str_encrypted = str(encrypted_data)
        # print('\nok: {ok}'.format(ok=encrypted_data.ok))
        # print('\nstatus: {stat}'.format(stat=encrypted_data.status))
        # print('\nstderr: {err}'.format(err=encrypted_data.stderr))
        log.info('unencrypted string:\n{ue_str}'.format(ue_str=str_unencrypted))
        log.info('encrypted string:\n{e_str}'.format(e_str=str_encrypted))

        return str_encrypted

    def export_keys(self, key):
        """Export PGP keys"""
        ascii_armored_public_keys = self.gpg.export_keys(key)  # same as gpg.export_keys(key, False)
        ascii_armored_private_keys = self.gpg.export_keys(key, True)  # True => private keys
        with open(KEY_FILE_MINE, 'w') as f:
            f.write(ascii_armored_public_keys)
            f.write(ascii_armored_private_keys)
        log.info("Key successfully exported as {key_filename}".format(key_filename=KEY_FILE_MINE))

    def import_keys(self):
        key_data = open(KEY_FILE_MINE).read()
        import_result = self.gpg.import_keys(key_data)
        log.info("Key import results:\n{results}".format(
            results=import_result.results))

    @staticmethod
    def is_ascii(letter):
        """Check if ascii"""
        try:
            letter.decode('ascii')
        except UnicodeDecodeError:
            return False
        return True


if __name__ == "__main__":
    tmp = TooMuchPrivacy(NEWKEY_DIR)
    if not tmp.check_keys_exist():
        log.error("Key creation did not seem to succeed. Shutting program "
                  "down.")
        sys.exit()

    try:
        while True:
            print("\nEnter text to encrypt, then press "
                  "Enter:\n")
            str_unencrypted = raw_input()
            str_encrypted = tmp.encrypt_string(str_unencrypted)
            print("Encrypted string'{}'".format(str_encrypted))
            str_decrypted = tmp.decrypt_string(str_encrypted)
            print("Decrypted string:\n{}".format(str_decrypted))
            log.info("Decrypted string:\n{str_decrypt}".format(
                str_decrypt=str_decrypted))
    except KeyboardInterrupt:
        log.info("Keyboard Interrupt: Closing program.")
        sys.exit()
